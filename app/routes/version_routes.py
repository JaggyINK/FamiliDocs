"""
Routes de gestion du versioning des documents
"""
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user

from app.models import db
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.log import Log
from app.services.document_service import DocumentService
from flask import current_app

version_bp = Blueprint('version', __name__, url_prefix='/documents')


@version_bp.route('/<int:document_id>/versions')
@login_required
def list_versions(document_id):
    """Affiche l'historique des versions d'un document"""
    document = Document.query.get_or_404(document_id)

    if not current_user.can_access_document(document):
        flash("Vous n'avez pas acces a ce document.", 'danger')
        return redirect(url_for('document.list_documents'))

    versions = DocumentVersion.get_versions(document_id)

    return render_template(
        'document_versions.html',
        document=document,
        versions=versions
    )


@version_bp.route('/<int:document_id>/versions/upload', methods=['POST'])
@login_required
def upload_version(document_id):
    """Upload une nouvelle version du document"""
    document = Document.query.get_or_404(document_id)

    if not current_user.can_edit_document(document):
        flash("Vous n'avez pas le droit de modifier ce document.", 'danger')
        return redirect(url_for('document.view', document_id=document_id))

    file = request.files.get('file')
    comment = request.form.get('comment', '').strip()

    if not file or file.filename == '':
        flash('Veuillez selectionner un fichier.', 'warning')
        return redirect(url_for('version.list_versions', document_id=document_id))

    from werkzeug.utils import secure_filename
    original_filename = secure_filename(file.filename)

    if not DocumentService.allowed_file(original_filename):
        flash('Type de fichier non autorise.', 'danger')
        return redirect(url_for('version.list_versions', document_id=document_id))

    try:
        # Sauvegarder la version actuelle avant remplacement
        current_version_number = DocumentVersion.get_latest_version_number(document_id)

        # Si c'est la premiere mise a jour, sauvegarder la version originale (v1)
        if current_version_number == 0:
            original_version = DocumentVersion(
                document_id=document_id,
                version_number=1,
                stored_filename=document.stored_filename,
                original_filename=document.original_filename,
                file_size=document.file_size,
                file_type=document.file_type,
                comment='Version originale',
                uploaded_by=document.owner_id
            )
            original_version.created_at = document.created_at
            db.session.add(original_version)
            current_version_number = 1

        # Generer un nouveau nom de fichier pour la nouvelle version
        stored_filename = DocumentService.generate_stored_filename(original_filename)
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        file_path = os.path.join(upload_folder, stored_filename)

        file.save(file_path)
        file_size = os.path.getsize(file_path)

        # Creer l'entree de version
        new_version = DocumentVersion(
            document_id=document_id,
            version_number=current_version_number + 1,
            stored_filename=stored_filename,
            original_filename=original_filename,
            file_size=file_size,
            file_type=DocumentService.get_file_type(original_filename),
            comment=comment,
            uploaded_by=current_user.id
        )
        db.session.add(new_version)

        # Mettre a jour le document principal avec la nouvelle version
        document.stored_filename = stored_filename
        document.original_filename = original_filename
        document.file_size = file_size
        document.file_type = DocumentService.get_file_type(original_filename)

        # Log
        Log.create_log(
            user_id=current_user.id,
            action='document_edit',
            document_id=document_id,
            details=f"Nouvelle version v{current_version_number + 1} uploadee"
        )

        db.session.commit()
        flash(f'Version {current_version_number + 1} uploadee avec succes.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l\'upload: {str(e)}', 'danger')

    return redirect(url_for('version.list_versions', document_id=document_id))


@version_bp.route('/<int:document_id>/versions/<int:version_id>/download')
@login_required
def download_version(document_id, version_id):
    """Telecharge une version specifique"""
    document = Document.query.get_or_404(document_id)

    if not current_user.can_access_document(document):
        flash("Vous n'avez pas acces a ce document.", 'danger')
        return redirect(url_for('document.list_documents'))

    version = DocumentVersion.query.get_or_404(version_id)

    if version.document_id != document_id:
        flash('Version invalide.', 'danger')
        return redirect(url_for('version.list_versions', document_id=document_id))

    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    file_path = os.path.join(upload_folder, version.stored_filename)

    if not os.path.exists(file_path):
        flash('Fichier introuvable.', 'danger')
        return redirect(url_for('version.list_versions', document_id=document_id))

    Log.create_log(
        user_id=current_user.id,
        action='document_download',
        document_id=document_id,
        details=f"Telechargement version v{version.version_number}"
    )
    db.session.commit()

    return send_file(
        file_path,
        download_name=f"v{version.version_number}_{version.original_filename}",
        as_attachment=True
    )


@version_bp.route('/<int:document_id>/versions/<int:version_id>/restore', methods=['POST'])
@login_required
def restore_version(document_id, version_id):
    """Restaure une ancienne version comme version courante"""
    document = Document.query.get_or_404(document_id)

    if not current_user.can_edit_document(document):
        flash("Vous n'avez pas le droit de modifier ce document.", 'danger')
        return redirect(url_for('version.list_versions', document_id=document_id))

    version = DocumentVersion.query.get_or_404(version_id)

    if version.document_id != document_id:
        flash('Version invalide.', 'danger')
        return redirect(url_for('version.list_versions', document_id=document_id))

    try:
        # Sauvegarder la version courante
        current_version_number = DocumentVersion.get_latest_version_number(document_id)
        save_current = DocumentVersion(
            document_id=document_id,
            version_number=current_version_number + 1,
            stored_filename=document.stored_filename,
            original_filename=document.original_filename,
            file_size=document.file_size,
            file_type=document.file_type,
            comment=f'Sauvegarde avant restauration de la v{version.version_number}',
            uploaded_by=current_user.id
        )
        db.session.add(save_current)

        # Restaurer l'ancienne version
        document.stored_filename = version.stored_filename
        document.original_filename = version.original_filename
        document.file_size = version.file_size
        document.file_type = version.file_type

        Log.create_log(
            user_id=current_user.id,
            action='document_edit',
            document_id=document_id,
            details=f"Restauration de la version v{version.version_number}"
        )

        db.session.commit()
        flash(f'Version v{version.version_number} restauree avec succes.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')

    return redirect(url_for('version.list_versions', document_id=document_id))
