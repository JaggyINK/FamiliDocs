# routes user dashboard profil
import os
import uuid
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app, abort
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

ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_avatar_file(filename):
    """check extension avatar"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AVATAR_EXTENSIONS


@user_bp.route('/dashboard')
@login_required
def dashboard():
    """dashboard user"""
    stats = {
        'total_documents': Document.query.filter_by(owner_id=current_user.id).count(),
        'total_folders': Folder.query.filter_by(owner_id=current_user.id).count(),
        'pending_tasks': Task.query.filter_by(
            owner_id=current_user.id,
            status='pending'
        ).count(),
        'shared_documents': len(DocumentService.get_shared_documents(current_user.id))
    }

    # docs recents
    recent_documents = Document.query.filter_by(owner_id=current_user.id)\
        .order_by(Document.updated_at.desc())\
        .limit(5)\
        .all()

    upcoming_tasks = Task.get_upcoming_tasks(current_user.id, days=14)[:5]
    overdue_tasks = Task.get_overdue_tasks(current_user.id)
    expiring_documents = DocumentService.get_expiring_documents(current_user.id, days=30)
    detailed_stats = SearchService.get_statistics(current_user.id)

    # widget familles : eager loading creator pour eviter une requete N+1 sur creator
    # (members reste en lazy='dynamic' pour supporter .count() et le filtrage)
    from sqlalchemy.orm import joinedload
    user_families = db.session.query(Family).join(FamilyMember).filter(
        FamilyMember.user_id == current_user.id
    ).options(
        joinedload(Family.creator)
    ).all()

    # widget notifs
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
    """profil user"""
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        family_title = request.form.get('family_title', '').strip()

        if not all([first_name, last_name, email]):
            flash('Veuillez remplir tous les champs obligatoires.', 'warning')
            return render_template('profile.html', family_titles=User.FAMILY_TITLES)

        # verif email deja pris
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Cet email est déjà utilisé.', 'danger')
            return render_template('profile.html', family_titles=User.FAMILY_TITLES)

        # maj profil
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        current_user.family_title = family_title if family_title else None
        db.session.commit()

        flash('Profil mis a jour.', 'success')

    return render_template('profile.html', family_titles=User.FAMILY_TITLES)


@user_bp.route('/profile/export-data')
@login_required
def export_data():
    """export RGPD data user"""
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
    """upload avatar"""
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

    # max 2 Mo
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > 2 * 1024 * 1024:
        flash('Le fichier est trop volumineux (max 2 Mo).', 'danger')
        return redirect(url_for('user.profile'))

    # nom unique
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"

    # dossier avatars
    avatar_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'avatars')
    if not os.path.exists(avatar_folder):
        os.makedirs(avatar_folder)

    # suppr ancien avatar
    if current_user.profile_photo:
        old_path = os.path.join(avatar_folder, current_user.profile_photo)
        if os.path.exists(old_path):
            os.remove(old_path)

    # save nouveau fichier
    file.save(os.path.join(avatar_folder, filename))

    # maj bdd
    current_user.profile_photo = filename
    db.session.commit()

    flash('Photo de profil mise a jour.', 'success')
    return redirect(url_for('user.profile'))


@user_bp.route('/profile/avatar/delete', methods=['POST'])
@login_required
def delete_avatar():
    """suppr avatar"""
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
@login_required
def avatar(filename):
    """sert fichiers avatar"""
    # fix: path traversal
    if not filename.startswith('avatar_') or '..' in filename:
        abort(404)
    avatar_folder = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'avatars')
    return send_from_directory(avatar_folder, filename)


@user_bp.route('/folders')
@login_required
def folders():
    """liste dossiers"""
    page = request.args.get('page', 1, type=int)
    pagination = Folder.query.filter_by(
        owner_id=current_user.id,
        parent_id=None
    ).order_by(Folder.category, Folder.name).paginate(page=page, per_page=20, error_out=False)

    return render_template('folders.html', folders=pagination.items, pagination=pagination)


@user_bp.route('/folders/create', methods=['GET', 'POST'])
@login_required
def create_folder():
    """cree dossier"""
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

        Log.create_log(
            user_id=current_user.id,
            action='folder_create',
            details=f"Dossier '{name}' créé"
        )
        db.session.commit()

        flash(f'Dossier "{name}" cree.', 'success')
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
    """contenu dossier"""
    folder = Folder.query.get_or_404(folder_id)

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
    """edit dossier"""
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

        flash('Dossier mis a jour.', 'success')
        return redirect(url_for('user.view_folder', folder_id=folder_id))

    categories = Config.DEFAULT_CATEGORIES
    return render_template('edit_folder.html', folder=folder, categories=categories)


@user_bp.route('/folders/<int:folder_id>/delete', methods=['POST'])
@login_required
def delete_folder(folder_id):
    """suppr dossier"""
    folder = Folder.query.get_or_404(folder_id)

    if folder.owner_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas le droit de supprimer ce dossier.', 'danger')
        return redirect(url_for('user.folders'))

    # check docs ou sous-dossiers
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
    """historique activite"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    logs = Log.query.filter_by(user_id=current_user.id)\
        .order_by(Log.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return render_template('activity.html', logs=logs)


@user_bp.route('/activity/detailed')
@login_required
def activity_detailed():
    """activite detaillee filtres + stats 6 mois"""
    from datetime import timedelta
    from app.models.family import FamilyMember

    page = request.args.get('page', 1, type=int)
    per_page = 30
    filter_action = request.args.get('action', '')
    filter_period = request.args.get('period', '6m')  # 1w, 1m, 3m, 6m
    view_user_id = request.args.get('user_id', type=int)

    # calcul periode
    period_days = {
        '1w': 7,
        '1m': 30,
        '3m': 90,
        '6m': 180
    }
    days = period_days.get(filter_period, 180)
    start_date = datetime.utcnow() - timedelta(days=days)

    # quel user afficher
    target_user_id = current_user.id
    target_user = current_user
    can_view_family = False
    family_members_to_view = []

    # admin/responsable peut voir membres famille
    seen_user_ids = set()
    if current_user.is_admin():
        can_view_family = True
        # admin voit tous les membres de toutes ses familles (creees + membre)
        from app.models.family import Family
        admin_memberships = FamilyMember.query.filter_by(user_id=current_user.id).all()
        family_ids = {m.family_id for m in admin_memberships}
        # ajouter aussi les familles creees par l'admin
        created_families = Family.query.filter_by(creator_id=current_user.id).all()
        for f in created_families:
            family_ids.add(f.id)
        for fid in family_ids:
            family = Family.query.get(fid)
            if family is None:
                continue
            for member in family.members:
                if member.user_id != current_user.id and member.user is not None and member.user_id not in seen_user_ids:
                    seen_user_ids.add(member.user_id)
                    family_members_to_view.append({
                        'user': member.user,
                        'family': family.name,
                        'role': member.role
                    })
    else:
        # check si responsable
        memberships = FamilyMember.query.filter_by(user_id=current_user.id).all()
        for membership in memberships:
            if membership.role in ('responsable', 'admin'):
                can_view_family = True
                for member in membership.family.members:
                    if member.user_id != current_user.id and member.user is not None and member.user_id not in seen_user_ids:
                        seen_user_ids.add(member.user_id)
                        family_members_to_view.append({
                            'user': member.user,
                            'family': membership.family.name,
                            'role': member.role
                        })

    # demande voir autre user
    if view_user_id and can_view_family:
        # verif user dans la liste
        allowed_ids = []
        for m in family_members_to_view:
            allowed_ids.append(m['user'].id)
        if view_user_id in allowed_ids:
            target_user = User.query.get(view_user_id)
            if target_user is None:
                abort(404)
            target_user_id = view_user_id

    # query logs
    query = Log.query.filter(
        Log.user_id == target_user_id,
        Log.created_at >= start_date
    )

    if filter_action:
        query = query.filter(Log.action.like(f'%{filter_action}%'))

    logs = query.order_by(Log.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    # stats periode
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

    # types actions filtre
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
    """partage docs dossier"""
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
                # limite 90j
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

    # users dispo
    family_members = PermissionService.get_family_members_for_sharing(current_user.id)
    available_users = PermissionService.get_accessible_users_for_sharing(current_user.id)

    # stats dossier
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
