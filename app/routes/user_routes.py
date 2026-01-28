"""
Routes utilisateur - Dashboard et profil
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.models import db
from app.models.document import Document
from app.models.folder import Folder
from app.models.task import Task
from app.models.log import Log
from app.services.document_service import DocumentService

user_bp = Blueprint('user', __name__)


@user_bp.route('/dashboard')
@login_required
def dashboard():
    """Page d'accueil utilisateur"""
    # Statistiques
    stats = {
        'total_documents': Document.query.filter_by(owner_id=current_user.id).count(),
        'total_folders': Folder.query.filter_by(owner_id=current_user.id).count(),
        'pending_tasks': Task.query.filter_by(
            owner_id=current_user.id,
            status='pending'
        ).count(),
        'shared_documents': len(DocumentService.get_shared_documents(current_user.id))
    }

    # Documents récents
    recent_documents = Document.query.filter_by(owner_id=current_user.id)\
        .order_by(Document.updated_at.desc())\
        .limit(5)\
        .all()

    # Tâches à venir
    upcoming_tasks = Task.get_upcoming_tasks(current_user.id, days=14)[:5]

    # Tâches en retard
    overdue_tasks = Task.get_overdue_tasks(current_user.id)

    # Documents qui expirent bientôt
    expiring_documents = DocumentService.get_expiring_documents(current_user.id, days=30)

    return render_template(
        'dashboard.html',
        stats=stats,
        recent_documents=recent_documents,
        upcoming_tasks=upcoming_tasks,
        overdue_tasks=overdue_tasks,
        expiring_documents=expiring_documents
    )


@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Page de profil utilisateur"""
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()

        if not all([first_name, last_name, email]):
            flash('Veuillez remplir tous les champs obligatoires.', 'warning')
            return render_template('profile.html')

        # Vérifier si l'email est déjà utilisé par un autre utilisateur
        from app.models.user import User
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Cet email est déjà utilisé.', 'danger')
            return render_template('profile.html')

        # Mise à jour du profil
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        db.session.commit()

        flash('Profil mis à jour avec succès.', 'success')

    return render_template('profile.html')


@user_bp.route('/folders')
@login_required
def folders():
    """Liste des dossiers de l'utilisateur"""
    user_folders = Folder.query.filter_by(
        owner_id=current_user.id,
        parent_id=None  # Dossiers racine uniquement
    ).order_by(Folder.category, Folder.name).all()

    return render_template('folders.html', folders=user_folders)


@user_bp.route('/folders/create', methods=['GET', 'POST'])
@login_required
def create_folder():
    """Création d'un nouveau dossier"""
    from app.config import Config

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'Autres')
        parent_id = request.form.get('parent_id', type=int)

        if not name:
            flash('Le nom du dossier est obligatoire.', 'warning')
            return redirect(url_for('user.create_folder'))

        folder = Folder(
            name=name,
            description=description,
            category=category,
            owner_id=current_user.id,
            parent_id=parent_id if parent_id else None
        )

        db.session.add(folder)
        db.session.commit()

        # Log
        Log.create_log(
            user_id=current_user.id,
            action='folder_create',
            details=f"Dossier '{name}' créé"
        )
        db.session.commit()

        flash(f'Dossier "{name}" créé avec succès.', 'success')
        return redirect(url_for('user.folders'))

    categories = Config.DEFAULT_CATEGORIES
    parent_folders = Folder.query.filter_by(
        owner_id=current_user.id,
        parent_id=None
    ).all()

    return render_template(
        'create_folder.html',
        categories=categories,
        parent_folders=parent_folders
    )


@user_bp.route('/folders/<int:folder_id>')
@login_required
def view_folder(folder_id):
    """Affiche le contenu d'un dossier"""
    folder = Folder.query.get_or_404(folder_id)

    # Vérification des droits
    if folder.owner_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas accès à ce dossier.', 'danger')
        return redirect(url_for('user.folders'))

    documents = folder.documents.order_by(Document.updated_at.desc()).all()
    subfolders = folder.subfolders.all()

    return render_template(
        'view_folder.html',
        folder=folder,
        documents=documents,
        subfolders=subfolders
    )


@user_bp.route('/folders/<int:folder_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_folder(folder_id):
    """Modification d'un dossier"""
    from app.config import Config

    folder = Folder.query.get_or_404(folder_id)

    if folder.owner_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas le droit de modifier ce dossier.', 'danger')
        return redirect(url_for('user.folders'))

    if request.method == 'POST':
        folder.name = request.form.get('name', '').strip()
        folder.description = request.form.get('description', '').strip()
        folder.category = request.form.get('category', 'Autres')

        db.session.commit()

        Log.create_log(
            user_id=current_user.id,
            action='folder_edit',
            details=f"Dossier '{folder.name}' modifié"
        )
        db.session.commit()

        flash('Dossier mis à jour avec succès.', 'success')
        return redirect(url_for('user.view_folder', folder_id=folder_id))

    categories = Config.DEFAULT_CATEGORIES
    return render_template('edit_folder.html', folder=folder, categories=categories)


@user_bp.route('/folders/<int:folder_id>/delete', methods=['POST'])
@login_required
def delete_folder(folder_id):
    """Suppression d'un dossier"""
    folder = Folder.query.get_or_404(folder_id)

    if folder.owner_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas le droit de supprimer ce dossier.', 'danger')
        return redirect(url_for('user.folders'))

    # Vérifier s'il y a des documents ou sous-dossiers
    if folder.documents.count() > 0:
        flash('Impossible de supprimer un dossier contenant des documents.', 'warning')
        return redirect(url_for('user.view_folder', folder_id=folder_id))

    if folder.subfolders.count() > 0:
        flash('Impossible de supprimer un dossier contenant des sous-dossiers.', 'warning')
        return redirect(url_for('user.view_folder', folder_id=folder_id))

    folder_name = folder.name
    db.session.delete(folder)
    db.session.commit()

    Log.create_log(
        user_id=current_user.id,
        action='folder_delete',
        details=f"Dossier '{folder_name}' supprimé"
    )
    db.session.commit()

    flash(f'Dossier "{folder_name}" supprimé.', 'success')
    return redirect(url_for('user.folders'))


@user_bp.route('/activity')
@login_required
def activity():
    """Historique d'activité de l'utilisateur"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    logs = Log.query.filter_by(user_id=current_user.id)\
        .order_by(Log.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return render_template('activity.html', logs=logs)
