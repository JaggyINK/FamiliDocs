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
    sort = request.args.get('sort', 'updated_at')
    order = request.args.get('order', 'desc')

    page = request.args.get('page', 1, type=int)

    query = DocumentService.get_user_documents_query(
        user_id=current_user.id,
        folder_id=folder_id,
        search=search,
        file_type=file_type
    )

    # T16 - Tri colonnes
    if sort == 'name':
        sort_col = Document.name
    elif sort == 'file_size':
        sort_col = Document.file_size
    elif sort == 'created_at':
        sort_col = Document.created_at
    else:
        sort_col = Document.updated_at

    if order == 'asc':
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    pagination = query.paginate(page=page, per_page=20, error_out=False)

    # Dossiers pour le filtre
    folders = Folder.query.filter_by(owner_id=current_user.id).all()

    return render_template(
        'documents.html',
        documents=pagination.items,
        pagination=pagination,
        folders=folders,
        selected_folder=folder_id,
        search=search,
        file_type=file_type,
        sort=sort,
        order=order
    )


@document_bp.route('/shared')
@login_required
def shared_documents():
    """Liste des documents partagés avec l'utilisateur"""
    documents = DocumentService.get_shared_documents(current_user.id)
    return render_template('shared_documents.html', documents=documents)


@document_bp.route('/my-shares')
@login_required
def my_shared_documents():
    """Liste des documents que j'ai partagés avec d'autres"""
    shared_docs = PermissionService.get_documents_shared_by_user(current_user.id)

    # Enrichir avec les infos de partage
    docs_with_shares = []
    for doc in shared_docs:
        perms = PermissionService.get_document_permissions(doc.id)
        # Exclure le propriétaire des permissions
        # Garder seulement les permissions des autres utilisateurs
        filtered_perms = []
        for p in perms:
            if p.user_id != current_user.id:
                filtered_perms.append(p)
        perms = filtered_perms
        docs_with_shares.append({
            'document': doc,
            'permissions': perms,
            'share_count': len(perms)
        })

    return render_template('my_shared_documents.html', docs_with_shares=docs_with_shares)


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
        if confidentiality not in Config.CONFIDENTIALITY_LEVELS:
            confidentiality = 'private'
        expiry_date_str = request.form.get('expiry_date', '').strip()

        # Validation
        if not file or file.filename == '':
            flash('Veuillez selectionner un fichier.', 'warning')
            folders = Folder.query.filter_by(owner_id=current_user.id).all()
            confidentiality_levels = Config.CONFIDENTIALITY_LEVELS
            return render_template('upload_document.html', folders=folders, confidentiality_levels=confidentiality_levels, form_data=request.form)

        if not name:
            name = file.filename

        # Conversion de la date d'echeance
        expiry_date = None
        if expiry_date_str:
            try:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Format de date invalide.', 'warning')
                folders = Folder.query.filter_by(owner_id=current_user.id).all()
                confidentiality_levels = Config.CONFIDENTIALITY_LEVELS
                return render_template('upload_document.html', folders=folders, confidentiality_levels=confidentiality_levels, form_data=request.form)

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

    # T8 - Dechiffrement si le document est chiffre
    temp_decrypted = None
    if document.is_encrypted:
        from app.services.encryption_service import EncryptionService
        success, result = EncryptionService.decrypt_to_memory(file_path)
        if not success:
            flash('Erreur lors du dechiffrement du document.', 'danger')
            return redirect(url_for('document.view', document_id=document_id))
        # Creer un fichier temporaire pour l'envoi
        import tempfile
        temp_decrypted = tempfile.NamedTemporaryFile(delete=False, suffix='_' + document.original_filename)
        temp_decrypted.write(result)
        temp_decrypted.close()
        file_path = temp_decrypted.name

    # Log du téléchargement
    Log.create_log(
        user_id=current_user.id,
        action='document_download',
        document_id=document.id,
        details=f"Telechargement du document '{document.name}'"
    )
    db.session.commit()

    response = send_file(
        file_path,
        download_name=document.original_filename,
        as_attachment=True
    )

    # Nettoyage du fichier temporaire dechiffre
    if temp_decrypted:
        from flask import after_this_request
        temp_path = temp_decrypted.name

        @after_this_request
        def cleanup(resp):
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except OSError:
                pass
            return resp

    return response


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
        next_review_date_str = request.form.get('next_review_date', '').strip()

        expiry_date = None
        if expiry_date_str:
            try:
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Format de date invalide.', 'warning')
                return redirect(url_for('document.edit', document_id=document_id))

        next_review_date = None
        if next_review_date_str:
            try:
                next_review_date = datetime.strptime(next_review_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Format de date de revision invalide.', 'warning')
                return redirect(url_for('document.edit', document_id=document_id))

        success, message = DocumentService.update_document(
            document=document,
            name=name,
            description=description,
            confidentiality=confidentiality,
            folder_id=folder_id,
            expiry_date=expiry_date,
            next_review_date=next_review_date,
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
    """Partage d'un document (supporte le partage multiple)"""
    from datetime import date, timedelta

    document = Document.query.get_or_404(document_id)

    # Vérification des droits de partage
    if document.owner_id != current_user.id:
        if not PermissionService.check_permission(document_id, current_user.id, 'share'):
            flash('Vous n\'avez pas le droit de partager ce document.', 'danger')
            return redirect(url_for('document.view', document_id=document_id))

    if request.method == 'POST':
        # Récupérer la liste des user_ids (partage multiple)
        user_ids = request.form.getlist('user_ids', type=int)

        # Fallback pour l'ancien formulaire (single user_id)
        if not user_ids:
            single_user_id = request.form.get('user_id', type=int)
            if single_user_id:
                user_ids = [single_user_id]

        can_edit = request.form.get('can_edit') == 'on'
        can_download = request.form.get('can_download', 'on') == 'on'
        can_share = request.form.get('can_share') == 'on'
        end_date_str = request.form.get('end_date', '').strip()
        notes = request.form.get('notes', '').strip()

        if not user_ids:
            flash('Veuillez sélectionner au moins un utilisateur.', 'warning')
            return redirect(url_for('document.share', document_id=document_id))

        end_date = None
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                # Limite max 90 jours
                max_allowed = date.today() + timedelta(days=90)
                if end_date > max_allowed:
                    end_date = max_allowed
                    flash('La durée a été limitée à 90 jours maximum.', 'info')
            except ValueError:
                flash('Format de date invalide.', 'warning')
                return redirect(url_for('document.share', document_id=document_id))

        # Partage multiple
        success, result = PermissionService.grant_multiple_permissions(
            document_id=document_id,
            user_ids=user_ids,
            granted_by=current_user.id,
            can_edit=can_edit,
            can_download=can_download,
            can_share=can_share,
            end_date=end_date,
            notes=notes
        )

        if success:
            # T9 - Notification de partage pour chaque destinataire
            from app.services.notification_service import NotificationService
            for uid in user_ids:
                if uid != current_user.id:
                    try:
                        NotificationService.notify_document_shared(document, uid, current_user)
                    except Exception:
                        pass  # Ne pas bloquer le partage si la notification echoue
            flash(result, 'success')
            return redirect(url_for('document.view', document_id=document_id))
        else:
            flash(result, 'danger')

    # Utilisateurs disponibles (exclut soi-même et ceux qui ont déjà accès)
    available_users = PermissionService.get_accessible_users_for_sharing(current_user.id, document_id)

    # Membres de famille disponibles
    family_members = PermissionService.get_family_members_for_sharing(current_user.id, document_id)

    # Permissions existantes
    existing_permissions = PermissionService.get_document_permissions(document_id)

    # Liens de partage actifs
    from app.models.family import ShareLink
    share_links = ShareLink.get_active_links_for_document(document_id)

    # Dates pour le formulaire (limite 90 jours)
    today = date.today().isoformat()
    max_date = (date.today() + timedelta(days=90)).isoformat()

    return render_template(
        'share_document.html',
        document=document,
        available_users=available_users,
        family_members=family_members,
        existing_permissions=existing_permissions,
        share_links=share_links,
        today=today,
        max_date=max_date
    )


@document_bp.route('/<int:document_id>/revoke-all', methods=['POST'])
@login_required
def revoke_all_access(document_id):
    """Révoque tous les accès à un document"""
    document = Document.query.get_or_404(document_id)

    if document.owner_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas le droit de révoquer ces permissions.', 'danger')
        return redirect(url_for('document.view', document_id=document_id))

    permissions = PermissionService.get_document_permissions(document_id)
    count = 0
    for perm in permissions:
        success, _ = PermissionService.revoke_permission(
            document_id=document_id,
            user_id=perm.user_id,
            revoked_by=current_user.id
        )
        if success:
            count += 1

    flash(f'{count} accès révoqué(s).', 'success')
    return redirect(url_for('document.share', document_id=document_id))


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


@document_bp.route('/<int:document_id>/mark-reviewed', methods=['POST'])
@login_required
def mark_reviewed(document_id):
    """Marque un document comme révisé (N2)"""
    document = Document.query.get_or_404(document_id)

    if document.owner_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas le droit de marquer ce document.', 'danger')
        return redirect(url_for('document.view', document_id=document_id))

    document.mark_reviewed()

    # Log de l'action
    Log.create_log(
        user_id=current_user.id,
        action='document_review',
        document_id=document.id,
        details=f"Document '{document.name}' marqué comme révisé"
    )
    db.session.commit()

    flash('Document marqué comme révisé.', 'success')
    return redirect(url_for('document.view', document_id=document_id))


@document_bp.route('/bulk-action', methods=['POST'])
@login_required
def bulk_action():
    """T17 - Operations en masse sur les documents"""
    action = request.form.get('action')
    doc_ids = request.form.getlist('doc_ids', type=int)

    if not doc_ids:
        flash('Aucun document selectionne.', 'warning')
        return redirect(url_for('document.list_documents'))

    if action == 'delete':
        count = 0
        for doc_id in doc_ids:
            doc = Document.query.get(doc_id)
            if doc and (doc.owner_id == current_user.id or current_user.is_admin()):
                success, _ = DocumentService.delete_document(doc, user=current_user)
                if success:
                    count += 1
        flash(f'{count} document(s) supprime(s).', 'success')
    else:
        flash('Action non reconnue.', 'warning')

    return redirect(url_for('document.list_documents'))
