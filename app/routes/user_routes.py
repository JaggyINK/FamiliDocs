"""
Routes utilisateur - Dashboard et profil
"""
import os
import uuid
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.models import db
from app.models.document import Document
from app.models.folder import Folder
from app.models.task import Task
from app.models.log import Log
from app.models.user import User
from app.models.family import FamilyMember, Family
from app.services.document_service import DocumentService
from app.services.search_service import SearchService
from app.services.permission_service import PermissionService
from app.services.backup_service import BackupService
from app.services.notification_service import NotificationService

user_bp = Blueprint('user', __name__)

# Extensions autorisees pour les avatars
ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_avatar_file(filename):
    """Verifie si l'extension du fichier est autorisee"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AVATAR_EXTENSIONS


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

    # Statistiques detaillees
    detailed_stats = SearchService.get_statistics(current_user.id)

    # T28 - Widget familles
    user_families = db.session.query(Family).join(FamilyMember).filter(
        FamilyMember.user_id == current_user.id
    ).all()

    # T29 - Widget notifications
    notification_summary = NotificationService.get_notification_summary(current_user.id)

    return render_template(
        'dashboard.html',
        stats=stats,
        detailed_stats=detailed_stats,
        recent_documents=recent_documents,
        upcoming_tasks=upcoming_tasks,
        overdue_tasks=overdue_tasks,
        expiring_documents=expiring_documents,
        user_families=user_families,
        notification_summary=notification_summary
    )


@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Page de profil utilisateur"""
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        family_title = request.form.get('family_title', '').strip()

        if not all([first_name, last_name, email]):
            flash('Veuillez remplir tous les champs obligatoires.', 'warning')
            return render_template('profile.html', family_titles=User.FAMILY_TITLES)

        # Vérifier si l'email est déjà utilisé par un autre utilisateur
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Cet email est déjà utilisé.', 'danger')
            return render_template('profile.html', family_titles=User.FAMILY_TITLES)

        # Mise à jour du profil
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        current_user.family_title = family_title if family_title else None
        db.session.commit()

        flash('Profil mis à jour avec succès.', 'success')

    return render_template('profile.html', family_titles=User.FAMILY_TITLES)


@user_bp.route('/profile/export-data')
@login_required
def export_data():
    """T7 - Export RGPD des donnees utilisateur"""
    from flask import Response
    import json

    success, data = BackupService.export_user_data(current_user.id)

    if not success:
        flash('Erreur lors de l\'export des donnees.', 'danger')
        return redirect(url_for('user.profile'))

    json_data = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    return Response(
        json_data,
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment;filename=familidocs_export_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.json'}
    )


@user_bp.route('/profile/avatar', methods=['POST'])
@login_required
def upload_avatar():
    """Upload de la photo de profil"""
    if 'avatar' not in request.files:
        flash('Aucun fichier selectionne.', 'warning')
        return redirect(url_for('user.profile'))

    file = request.files['avatar']
    if file.filename == '':
        flash('Aucun fichier selectionne.', 'warning')
        return redirect(url_for('user.profile'))

    if not allowed_avatar_file(file.filename):
        flash('Type de fichier non autorise. Utilisez JPG, PNG ou GIF.', 'danger')
        return redirect(url_for('user.profile'))

    # Verifier la taille (max 2 Mo)
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > 2 * 1024 * 1024:
        flash('Le fichier est trop volumineux (max 2 Mo).', 'danger')
        return redirect(url_for('user.profile'))

    # Generer un nom unique
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"

    # Creer le dossier avatars si necessaire
    avatar_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'avatars')
    if not os.path.exists(avatar_folder):
        os.makedirs(avatar_folder)

    # Supprimer l'ancien avatar si existe
    if current_user.profile_photo:
        old_path = os.path.join(avatar_folder, current_user.profile_photo)
        if os.path.exists(old_path):
            os.remove(old_path)

    # Sauvegarder le nouveau fichier
    file.save(os.path.join(avatar_folder, filename))

    # Mettre a jour la base de donnees
    current_user.profile_photo = filename
    db.session.commit()

    flash('Photo de profil mise a jour.', 'success')
    return redirect(url_for('user.profile'))


@user_bp.route('/profile/avatar/delete', methods=['POST'])
@login_required
def delete_avatar():
    """Supprime la photo de profil"""
    if current_user.profile_photo:
        avatar_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'avatars')
        old_path = os.path.join(avatar_folder, current_user.profile_photo)
        if os.path.exists(old_path):
            os.remove(old_path)

        current_user.profile_photo = None
        db.session.commit()

        flash('Photo de profil supprimee.', 'success')

    return redirect(url_for('user.profile'))


@user_bp.route('/avatars/<filename>')
def avatar(filename):
    """Sert les fichiers avatar"""
    avatar_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'avatars')
    return send_from_directory(avatar_folder, filename)


@user_bp.route('/folders')
@login_required
def folders():
    """Liste des dossiers de l'utilisateur"""
    page = request.args.get('page', 1, type=int)
    pagination = Folder.query.filter_by(
        owner_id=current_user.id,
        parent_id=None
    ).order_by(Folder.category, Folder.name).paginate(page=page, per_page=20, error_out=False)

    return render_template('folders.html', folders=pagination.items, pagination=pagination)


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


@user_bp.route('/activity/detailed')
@login_required
def activity_detailed():
    """N6 - Page d'activité détaillée avec filtres et stats sur 6 mois"""
    from datetime import timedelta
    from app.models.family import FamilyMember

    page = request.args.get('page', 1, type=int)
    per_page = 30
    filter_action = request.args.get('action', '')
    filter_period = request.args.get('period', '6m')  # 1w, 1m, 3m, 6m
    view_user_id = request.args.get('user_id', type=int)

    # Calcul de la période
    period_days = {
        '1w': 7,
        '1m': 30,
        '3m': 90,
        '6m': 180
    }
    days = period_days.get(filter_period, 180)
    start_date = datetime.utcnow() - timedelta(days=days)

    # Déterminer quel utilisateur afficher
    target_user_id = current_user.id
    target_user = current_user
    can_view_family = False
    family_members_to_view = []

    # Si admin ou chef de famille, peut voir les membres de sa famille
    if current_user.is_admin():
        can_view_family = True
        # Récupérer tous les membres des familles créées par l'admin
        from app.models.family import Family
        families = Family.query.filter_by(creator_id=current_user.id).all()
        for family in families:
            for member in family.members:
                if member.user_id != current_user.id:
                    family_members_to_view.append({
                        'user': member.user,
                        'family': family.name,
                        'role': member.role
                    })
    else:
        # Vérifier si chef de famille
        memberships = FamilyMember.query.filter_by(user_id=current_user.id).all()
        for membership in memberships:
            if membership.role in ('chef_famille', 'admin'):
                can_view_family = True
                for member in membership.family.members:
                    if member.user_id != current_user.id:
                        family_members_to_view.append({
                            'user': member.user,
                            'family': membership.family.name,
                            'role': member.role
                        })

    # Si demande de voir un autre utilisateur
    if view_user_id and can_view_family:
        # Vérifier que l'utilisateur demandé est dans la liste
        allowed_ids = []
        for m in family_members_to_view:
            allowed_ids.append(m['user'].id)
        if view_user_id in allowed_ids:
            target_user = User.query.get(view_user_id)
            target_user_id = view_user_id

    # Query des logs
    query = Log.query.filter(
        Log.user_id == target_user_id,
        Log.created_at >= start_date
    )

    if filter_action:
        query = query.filter(Log.action.like(f'%{filter_action}%'))

    logs = query.order_by(Log.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    # Statistiques sur la période
    stats = {
        'total_actions': Log.query.filter(
            Log.user_id == target_user_id,
            Log.created_at >= start_date
        ).count(),
        'documents_uploaded': Log.query.filter(
            Log.user_id == target_user_id,
            Log.action == 'document_upload',
            Log.created_at >= start_date
        ).count(),
        'documents_downloaded': Log.query.filter(
            Log.user_id == target_user_id,
            Log.action == 'document_download',
            Log.created_at >= start_date
        ).count(),
        'logins': Log.query.filter(
            Log.user_id == target_user_id,
            Log.action == 'login',
            Log.created_at >= start_date
        ).count(),
        'tasks_completed': Log.query.filter(
            Log.user_id == target_user_id,
            Log.action == 'task_complete',
            Log.created_at >= start_date
        ).count()
    }

    # Types d'actions pour le filtre
    action_types = [
        ('', 'Toutes'),
        ('login', 'Connexions'),
        ('document', 'Documents'),
        ('task', 'Tâches'),
        ('folder', 'Dossiers'),
        ('share', 'Partages')
    ]

    return render_template(
        'activity_detailed.html',
        logs=logs,
        stats=stats,
        target_user=target_user,
        filter_action=filter_action,
        filter_period=filter_period,
        action_types=action_types,
        can_view_family=can_view_family,
        family_members=family_members_to_view
    )


@user_bp.route('/folders/<int:folder_id>/share', methods=['GET', 'POST'])
@login_required
def share_folder(folder_id):
    """Partage tous les documents d'un dossier"""
    from datetime import date, timedelta
    from app.services.permission_service import PermissionService

    folder = Folder.query.get_or_404(folder_id)

    if folder.owner_id != current_user.id and not current_user.is_admin():
        flash("Vous n'avez pas le droit de partager ce dossier.", 'danger')
        return redirect(url_for('user.view_folder', folder_id=folder_id))

    if request.method == 'POST':
        user_ids = request.form.getlist('user_ids', type=int)
        can_edit = request.form.get('can_edit') == 'on'
        can_download = request.form.get('can_download', 'on') == 'on'
        can_share = request.form.get('can_share') == 'on'
        end_date_str = request.form.get('end_date', '').strip()

        if not user_ids:
            flash('Veuillez sélectionner au moins une personne.', 'warning')
            return redirect(url_for('user.share_folder', folder_id=folder_id))

        end_date = None
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                # Limite 90 jours
                max_allowed = date.today() + timedelta(days=90)
                if end_date > max_allowed:
                    end_date = max_allowed
            except ValueError:
                pass

        success, message = PermissionService.share_folder(
            folder_id=folder_id,
            user_ids=user_ids,
            granted_by=current_user.id,
            can_edit=can_edit,
            can_download=can_download,
            can_share=can_share,
            end_date=end_date
        )

        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')

        return redirect(url_for('user.view_folder', folder_id=folder_id))

    # Utilisateurs disponibles
    family_members = PermissionService.get_family_members_for_sharing(current_user.id)
    available_users = PermissionService.get_accessible_users_for_sharing(current_user.id)

    # Stats du dossier
    doc_count = folder.documents.count()

    today = date.today().isoformat()
    max_date = (date.today() + timedelta(days=90)).isoformat()

    return render_template(
        'share_folder.html',
        folder=folder,
        family_members=family_members,
        available_users=available_users,
        doc_count=doc_count,
        today=today,
        max_date=max_date
    )
