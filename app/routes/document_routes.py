"""
Routes de gestion des documents
"""
import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, abort
from flask_login import login_required, current_user

from app.models import db
from app.models.document import Document
from app.models.folder import Folder
from app.models.log import Log
from app.models.user import User
from app.services.document_service import DocumentService
from app.services.permission_service import PermissionService
from app.config import Config

document_bp = Blueprint('document', __name__, url_prefix='/documents')


@document_bp.route('/')
@login_required
def list_documents():
    """Liste tous les documents de l'utilisateur"""
    # Filtres
    folder_id = request.args.get('folder', type=int)
    search = request.args.get('search', '').strip()
    file_type = request.args.get('type', '').strip()

    documents = DocumentService.get_user_documents(
        user_id=current_user.id,
        folder_id=folder_id,
        search=search,
        file_type=file_type
    )

    # Dossiers pour le filtre
    folders = Folder.query.filter_by(owner_id=current_user.id).all()

    return render_template(
        'documents.html',
        documents=documents,
        folders=folders,
        selected_folder=folder_id,
        search=search,
        file_type=file_type
    )


@document_bp.route('/shared')
@login_required
def shared_documents():
    """Liste des documents partagés avec l'utilisateur"""
    documents = DocumentService.get_shared_documents(current_user.id)
    return render_template('shared_documents.html', documents=documents)


@document_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload d'un nouveau document"""
    if request.method == 'POST':
        file = request.files.get('file')
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        folder_id = request.form.get('folder_id', type=int)
        confidentiality = request.form.get('confidentiality', 'private')
        expiry_date_str = request.form.get('expiry_date', '').strip()

        # Validation
        if not file or file.filename == '':
            flash('Veuillez sélectionner un fichier.', 'warning')
            return redirect(url_for('document.upload'))

        if not name:
            name = file.filename

        # Conversion de la date d'échéance
        expiry_date = None
        if expiry_date_str:
            try:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Format de date invalide.', 'warning')
                return redirect(url_for('document.upload'))

        # Upload
        success, result = DocumentService.upload_document(
            file=file,
            name=name,
            owner_id=current_user.id,
            folder_id=folder_id if folder_id else None,
            description=description,
            confidentiality=confidentiality,
            expiry_date=expiry_date,
            user=current_user
        )

        if success:
            flash(f'Document "{name}" uploadé avec succès.', 'success')
            return redirect(url_for('document.view', document_id=result.id))
        else:
            flash(result, 'danger')

    folders = Folder.query.filter_by(owner_id=current_user.id).all()
    confidentiality_levels = Config.CONFIDENTIALITY_LEVELS

    return render_template(
        'upload_document.html',
        folders=folders,
        confidentiality_levels=confidentiality_levels
    )


@document_bp.route('/<int:document_id>')
@login_required
def view(document_id):
    """Affiche les détails d'un document"""
    document = Document.query.get_or_404(document_id)

    # Vérification des droits
    if not current_user.can_access_document(document):
        flash('Vous n\'avez pas accès à ce document.', 'danger')
        return redirect(url_for('document.list_documents'))

    # Log de consultation
    Log.create_log(
        user_id=current_user.id,
        action='document_view',
        document_id=document.id,
        details=f"Consultation du document '{document.name}'"
    )
    db.session.commit()

    # Permissions du document
    permissions = PermissionService.get_document_permissions(document.id)

    # Historique du document
    logs = Log.get_document_logs(document.id, limit=10)

    return render_template(
        'view_document.html',
        document=document,
        permissions=permissions,
        logs=logs,
        can_edit=current_user.can_edit_document(document)
    )


@document_bp.route('/<int:document_id>/download')
@login_required
def download(document_id):
    """Télécharge un document"""
    document = Document.query.get_or_404(document_id)

    # Vérification des droits
    if not PermissionService.check_permission(document_id, current_user.id, 'download'):
        flash('Vous n\'avez pas le droit de télécharger ce document.', 'danger')
        return redirect(url_for('document.view', document_id=document_id))

    file_path = DocumentService.get_document_path(document)

    if not os.path.exists(file_path):
        flash('Fichier introuvable sur le serveur.', 'danger')
        return redirect(url_for('document.view', document_id=document_id))

    # Log du téléchargement
    Log.create_log(
        user_id=current_user.id,
        action='document_download',
        document_id=document.id,
        details=f"Téléchargement du document '{document.name}'"
    )
    db.session.commit()

    return send_file(
        file_path,
        download_name=document.original_filename,
        as_attachment=True
    )


@document_bp.route('/<int:document_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(document_id):
    """Modification des métadonnées d'un document"""
    document = Document.query.get_or_404(document_id)

    # Vérification des droits
    if not current_user.can_edit_document(document):
        flash('Vous n\'avez pas le droit de modifier ce document.', 'danger')
        return redirect(url_for('document.view', document_id=document_id))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        folder_id = request.form.get('folder_id', type=int)
        confidentiality = request.form.get('confidentiality', 'private')
        expiry_date_str = request.form.get('expiry_date', '').strip()

        expiry_date = None
        if expiry_date_str:
            try:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Format de date invalide.', 'warning')
                return redirect(url_for('document.edit', document_id=document_id))

        success, message = DocumentService.update_document(
            document=document,
            name=name,
            description=description,
            confidentiality=confidentiality,
            folder_id=folder_id,
            expiry_date=expiry_date,
            user=current_user
        )

        if success:
            flash(message, 'success')
            return redirect(url_for('document.view', document_id=document_id))
        else:
            flash(message, 'danger')

    folders = Folder.query.filter_by(owner_id=current_user.id).all()
    confidentiality_levels = Config.CONFIDENTIALITY_LEVELS

    return render_template(
        'edit_document.html',
        document=document,
        folders=folders,
        confidentiality_levels=confidentiality_levels
    )


@document_bp.route('/<int:document_id>/delete', methods=['POST'])
@login_required
def delete(document_id):
    """Suppression d'un document"""
    document = Document.query.get_or_404(document_id)

    # Seul le propriétaire ou un admin peut supprimer
    if document.owner_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas le droit de supprimer ce document.', 'danger')
        return redirect(url_for('document.view', document_id=document_id))

    success, message = DocumentService.delete_document(document, user=current_user)

    if success:
        flash(message, 'success')
        return redirect(url_for('document.list_documents'))
    else:
        flash(message, 'danger')
        return redirect(url_for('document.view', document_id=document_id))


@document_bp.route('/<int:document_id>/share', methods=['GET', 'POST'])
@login_required
def share(document_id):
    """Partage d'un document"""
    document = Document.query.get_or_404(document_id)

    # Vérification des droits de partage
    if document.owner_id != current_user.id:
        if not PermissionService.check_permission(document_id, current_user.id, 'share'):
            flash('Vous n\'avez pas le droit de partager ce document.', 'danger')
            return redirect(url_for('document.view', document_id=document_id))

    if request.method == 'POST':
        user_id = request.form.get('user_id', type=int)
        can_edit = request.form.get('can_edit') == 'on'
        can_download = request.form.get('can_download', 'on') == 'on'
        can_share = request.form.get('can_share') == 'on'
        end_date_str = request.form.get('end_date', '').strip()
        notes = request.form.get('notes', '').strip()

        if not user_id:
            flash('Veuillez sélectionner un utilisateur.', 'warning')
            return redirect(url_for('document.share', document_id=document_id))

        end_date = None
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Format de date invalide.', 'warning')
                return redirect(url_for('document.share', document_id=document_id))

        success, result = PermissionService.grant_permission(
            document_id=document_id,
            user_id=user_id,
            granted_by=current_user.id,
            can_edit=can_edit,
            can_download=can_download,
            can_share=can_share,
            end_date=end_date,
            notes=notes
        )

        if success:
            user = User.query.get(user_id)
            flash(f'Document partagé avec {user.full_name}.', 'success')
            return redirect(url_for('document.view', document_id=document_id))
        else:
            flash(result, 'danger')

    # Utilisateurs disponibles pour le partage
    available_users = PermissionService.get_accessible_users_for_sharing(current_user.id)

    # Permissions existantes
    existing_permissions = PermissionService.get_document_permissions(document_id)

    # Liens de partage actifs
    from app.models.family import ShareLink
    share_links = ShareLink.get_active_links_for_document(document_id)

    return render_template(
        'share_document.html',
        document=document,
        available_users=available_users,
        existing_permissions=existing_permissions,
        share_links=share_links
    )


@document_bp.route('/<int:document_id>/revoke/<int:user_id>', methods=['POST'])
@login_required
def revoke_access(document_id, user_id):
    """Révoque l'accès d'un utilisateur à un document"""
    document = Document.query.get_or_404(document_id)

    if document.owner_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas le droit de révoquer cette permission.', 'danger')
        return redirect(url_for('document.view', document_id=document_id))

    success, message = PermissionService.revoke_permission(
        document_id=document_id,
        user_id=user_id,
        revoked_by=current_user.id
    )

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('document.share', document_id=document_id))
