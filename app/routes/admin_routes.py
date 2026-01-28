"""
Routes d'administration
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps

from app.models import db
from app.models.user import User
from app.models.document import Document
from app.models.folder import Folder
from app.models.task import Task
from app.models.log import Log
from app.services.auth_service import AuthService
from app.services.backup_service import BackupService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Décorateur pour restreindre l'accès aux administrateurs"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Accès réservé aux administrateurs.', 'danger')
            return redirect(url_for('user.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_required
def dashboard():
    """Tableau de bord administrateur"""
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(is_active=True).count(),
        'total_documents': Document.query.count(),
        'total_folders': Folder.query.count(),
        'total_tasks': Task.query.count(),
        'pending_tasks': Task.query.filter_by(status='pending').count()
    }

    recent_logs = Log.get_recent_logs(limit=20)
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_logs=recent_logs,
        recent_users=recent_users
    )


@admin_bp.route('/users')
@admin_required
def users():
    """Liste des utilisateurs"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()

    query = User.query

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                User.email.ilike(search_pattern),
                User.username.ilike(search_pattern),
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern)
            )
        )

    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template('admin/users.html', users=users, search=search)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@admin_required
def create_user():
    """Création d'un utilisateur"""
    from app.config import Config

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        role = request.form.get('role', 'user')

        if role not in Config.USER_ROLES:
            flash('Rôle invalide.', 'danger')
            return redirect(url_for('admin.create_user'))

        success, result = AuthService.register_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role
        )

        if success:
            Log.create_log(
                user_id=current_user.id,
                action='user_create',
                details=f"Utilisateur '{username}' créé par l'admin"
            )
            db.session.commit()

            flash(f'Utilisateur "{username}" créé avec succès.', 'success')
            return redirect(url_for('admin.users'))
        else:
            flash(result, 'danger')

    roles = Config.USER_ROLES
    return render_template('admin/create_user.html', roles=roles)


@admin_bp.route('/users/<int:user_id>')
@admin_required
def view_user(user_id):
    """Affiche les détails d'un utilisateur"""
    user = User.query.get_or_404(user_id)

    stats = {
        'documents': Document.query.filter_by(owner_id=user_id).count(),
        'folders': Folder.query.filter_by(owner_id=user_id).count(),
        'tasks': Task.query.filter_by(owner_id=user_id).count()
    }

    recent_logs = Log.get_user_logs(user_id, limit=10)

    return render_template(
        'admin/view_user.html',
        user=user,
        stats=stats,
        recent_logs=recent_logs
    )


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Modification d'un utilisateur"""
    from app.config import Config

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.email = request.form.get('email', '').strip()
        user.first_name = request.form.get('first_name', '').strip()
        user.last_name = request.form.get('last_name', '').strip()
        user.role = request.form.get('role', 'user')
        user.is_active = request.form.get('is_active') == 'on'

        db.session.commit()

        Log.create_log(
            user_id=current_user.id,
            action='user_edit',
            details=f"Utilisateur '{user.username}' modifié"
        )
        db.session.commit()

        flash('Utilisateur mis à jour.', 'success')
        return redirect(url_for('admin.view_user', user_id=user_id))

    roles = Config.USER_ROLES
    return render_template('admin/edit_user.html', user=user, roles=roles)


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    """Réinitialise le mot de passe d'un utilisateur"""
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password', '')

    if not new_password:
        flash('Veuillez fournir un nouveau mot de passe.', 'warning')
        return redirect(url_for('admin.view_user', user_id=user_id))

    success, message = AuthService.reset_password(user, new_password)

    if success:
        Log.create_log(
            user_id=current_user.id,
            action='user_edit',
            details=f"Mot de passe de '{user.username}' réinitialisé"
        )
        db.session.commit()
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('admin.view_user', user_id=user_id))


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@admin_required
def toggle_user_active(user_id):
    """Active/Désactive un utilisateur"""
    user = User.query.get_or_404(user_id)

    # Empêcher la désactivation de son propre compte
    if user.id == current_user.id:
        flash('Vous ne pouvez pas désactiver votre propre compte.', 'warning')
        return redirect(url_for('admin.view_user', user_id=user_id))

    user.is_active = not user.is_active
    db.session.commit()

    status = 'activé' if user.is_active else 'désactivé'
    Log.create_log(
        user_id=current_user.id,
        action='user_edit',
        details=f"Utilisateur '{user.username}' {status}"
    )
    db.session.commit()

    flash(f'Utilisateur {status}.', 'success')
    return redirect(url_for('admin.view_user', user_id=user_id))


@admin_bp.route('/logs')
@admin_required
def logs():
    """Historique global des actions"""
    page = request.args.get('page', 1, type=int)
    action = request.args.get('action', '')
    user_id = request.args.get('user_id', type=int)

    query = Log.query

    if action:
        query = query.filter_by(action=action)
    if user_id:
        query = query.filter_by(user_id=user_id)

    logs = query.order_by(Log.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )

    # Liste des actions pour le filtre
    actions = list(Log.ACTION_TYPES.keys())
    users = User.query.order_by(User.username).all()

    return render_template(
        'admin/logs.html',
        logs=logs,
        actions=actions,
        action_types=Log.ACTION_TYPES,
        users=users,
        selected_action=action,
        selected_user_id=user_id
    )


@admin_bp.route('/backups')
@admin_required
def backups():
    """Gestion des sauvegardes"""
    backup_list = BackupService.list_backups()
    return render_template('admin/backups.html', backups=backup_list)


@admin_bp.route('/backups/create', methods=['POST'])
@admin_required
def create_backup():
    """Crée une nouvelle sauvegarde"""
    include_files = request.form.get('include_files') == 'on'

    success, result = BackupService.create_backup(
        user_id=current_user.id,
        include_files=include_files
    )

    if success:
        flash('Sauvegarde créée avec succès.', 'success')
    else:
        flash(result, 'danger')

    return redirect(url_for('admin.backups'))


@admin_bp.route('/backups/restore', methods=['POST'])
@admin_required
def restore_backup():
    """Restaure une sauvegarde"""
    backup_path = request.form.get('backup_path', '')

    if not backup_path:
        flash('Veuillez sélectionner une sauvegarde.', 'warning')
        return redirect(url_for('admin.backups'))

    success, message = BackupService.restore_backup(
        backup_path=backup_path,
        user_id=current_user.id
    )

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('admin.backups'))


@admin_bp.route('/backups/delete', methods=['POST'])
@admin_required
def delete_backup():
    """Supprime une sauvegarde"""
    backup_path = request.form.get('backup_path', '')

    success, message = BackupService.delete_backup(backup_path)

    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('admin.backups'))
