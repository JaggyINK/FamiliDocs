"""
Routes d'authentification
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.services.auth_service import AuthService

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
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember') == 'on'

        if not email or not password:
            flash('Veuillez remplir tous les champs.', 'warning')
            return render_template('login.html')

        success, result = AuthService.authenticate(email, password)

        if success:
            AuthService.login(result, remember=remember)
            flash(f'Bienvenue, {result.first_name} !', 'success')

            # Redirection vers la page demandée ou le dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('user.dashboard'))
        else:
            flash(result, 'danger')

    return render_template('login.html')


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
        return redirect(url_for('user.dashboard'))

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
            return render_template('register.html')

        if password != password_confirm:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return render_template('register.html')

        # Tentative d'inscription
        success, result = AuthService.register_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        if success:
            flash('Compte créé avec succès ! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(result, 'danger')

    return render_template('register.html')


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
