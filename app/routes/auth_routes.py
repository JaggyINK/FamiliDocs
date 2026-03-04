"""
Routes d'authentification
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user

from app.services.auth_service import AuthService
from app.models import db
from app.models.family import Family, FamilyMember, ShareLink
from app.services.notification_service import NotificationService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    """Page d'accueil - redirige vers le dashboard si connecté"""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if current_user.is_authenticated:
        # Vérifier s'il y a une invitation en attente
        pending_token = session.pop('pending_invite_token', None)
        if pending_token:
            return redirect(url_for('family.accept_invite', token=pending_token))
        return redirect(url_for('user.dashboard'))

    # Récupérer les infos d'invitation pour l'affichage
    pending_invite = None
    pending_token = session.get('pending_invite_token')
    if pending_token:
        link = ShareLink.query.filter_by(token=pending_token).first()
        if link and link.is_valid and link.family_id:
            family = Family.query.get(link.family_id)
            if family:
                pending_invite = {
                    'family_name': family.name,
                    'role': FamilyMember.ROLES.get(link.granted_role, 'Membre')
                }

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        if not email or not password:
            flash('Veuillez remplir tous les champs.', 'warning')
            return render_template('login.html', pending_invite=pending_invite)

        success, result = AuthService.authenticate(email, password)

        if success:
            AuthService.login(result, remember=remember)
            flash(f'Bienvenue, {result.first_name} !', 'success')

            # Traiter l'invitation en attente
            pending_token = session.pop('pending_invite_token', None)
            if pending_token:
                return redirect(url_for('family.accept_invite', token=pending_token))

            # Redirection vers la page demandée ou le dashboard
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                return redirect(next_page)
            return redirect(url_for('user.dashboard'))
        else:
            flash(result, 'danger')

    return render_template('login.html', pending_invite=pending_invite)


@auth_bp.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    AuthService.logout(current_user)
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription"""
    if current_user.is_authenticated:
        # Vérifier s'il y a une invitation en attente
        pending_token = session.pop('pending_invite_token', None)
        if pending_token:
            return redirect(url_for('family.accept_invite', token=pending_token))
        return redirect(url_for('user.dashboard'))

    # Récupérer les infos d'invitation pour l'affichage
    pending_invite = None
    pending_token = session.get('pending_invite_token')
    if pending_token:
        link = ShareLink.query.filter_by(token=pending_token).first()
        if link and link.is_valid and link.family_id:
            family = Family.query.get(link.family_id)
            if family:
                pending_invite = {
                    'family_name': family.name,
                    'role': FamilyMember.ROLES.get(link.granted_role, 'Membre'),
                    'token': pending_token
                }

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()

        # Validation de base
        if not all([email, username, password, password_confirm, first_name, last_name]):
            flash('Veuillez remplir tous les champs.', 'warning')
            return render_template('register.html', pending_invite=pending_invite)

        if password != password_confirm:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return render_template('register.html', pending_invite=pending_invite)

        # Tentative d'inscription
        success, result = AuthService.register_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        if success:
            # Connexion automatique après inscription
            from app.models.user import User
            new_user = User.query.filter_by(email=email).first()
            if new_user:
                AuthService.login(new_user, remember=True)
                # T13 - Message de bienvenue
                try:
                    NotificationService.notify_welcome(new_user)
                except Exception:
                    pass
                flash(f'Bienvenue {first_name} ! Votre compte a été créé avec succès.', 'success')

                # Traiter l'invitation en attente
                pending_token = session.pop('pending_invite_token', None)
                if pending_token:
                    return redirect(url_for('family.accept_invite', token=pending_token))

                return redirect(url_for('user.dashboard'))

            flash('Compte créé avec succès ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(result, 'danger')

    return render_template('register.html', pending_invite=pending_invite)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Changement de mot de passe"""
    if request.method == 'POST':
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        new_password_confirm = request.form.get('new_password_confirm', '')

        if not all([old_password, new_password, new_password_confirm]):
            flash('Veuillez remplir tous les champs.', 'warning')
            return render_template('change_password.html')

        if new_password != new_password_confirm:
            flash('Les nouveaux mots de passe ne correspondent pas.', 'danger')
            return render_template('change_password.html')

        success, message = AuthService.change_password(
            user=current_user,
            old_password=old_password,
            new_password=new_password
        )

        if success:
            flash(message, 'success')
            return redirect(url_for('user.profile'))
        else:
            flash(message, 'danger')

    return render_template('change_password.html')
