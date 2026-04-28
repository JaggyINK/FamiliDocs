# routes auth connextion inscription
import pyotp
import qrcode
import io
import base64
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user

from app.services.auth_service import AuthService
from app.models import db
from app.models.user import User
from app.models.family import Family, FamilyMember, ShareLink
from app.services.notification_service import NotificationService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    """redirect accueil"""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """page connextion"""
    if current_user.is_authenticated:
        # check invitation en attente
        pending_token = session.pop('pending_invite_token', None)
        if pending_token:
            return redirect(url_for('family.accept_invite', token=pending_token))
        return redirect(url_for('user.dashboard'))

    # recup infos invitation pr affichage
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
            # check 2FA
            if result.is_2fa_enabled and result.totp_secret:
                session['2fa_user_id'] = result.id
                session['2fa_remember'] = remember
                return redirect(url_for('auth.verify_2fa'))

            AuthService.login(result, remember=remember)
            flash(f'Bienvenue, {result.first_name} !', 'success')

            pending_token = session.pop('pending_invite_token', None)
            if pending_token:
                return redirect(url_for('family.accept_invite', token=pending_token))

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
    """deconnextion"""
    AuthService.logout(current_user)
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """inscription"""
    if current_user.is_authenticated:
        pending_token = session.pop('pending_invite_token', None)
        if pending_token:
            return redirect(url_for('family.accept_invite', token=pending_token))
        return redirect(url_for('user.dashboard'))

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

        if not all([email, username, password, password_confirm, first_name, last_name]):
            flash('Veuillez remplir tous les champs.', 'warning')
            return render_template('register.html', pending_invite=pending_invite, form_data=request.form)

        if password != password_confirm:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return render_template('register.html', pending_invite=pending_invite, form_data=request.form)

        success, result = AuthService.register_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        if success:
            # auto login apres inscription
            from app.models.user import User
            new_user = User.query.filter_by(email=email).first()
            if new_user:
                AuthService.login(new_user, remember=True)
                # notif bienvenue
                try:
                    NotificationService.notify_welcome(new_user)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Erreur notification bienvenue: {e}")
                flash(f'Bienvenue {first_name} ! Compte cree.', 'success')

                pending_token = session.pop('pending_invite_token', None)
                if pending_token:
                    return redirect(url_for('family.accept_invite', token=pending_token))

                return redirect(url_for('user.dashboard'))

            flash('Compte cree, vous pouvez vous connecter.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(result, 'danger')
            return render_template('register.html', pending_invite=pending_invite, form_data=request.form)

    return render_template('register.html', pending_invite=pending_invite)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """changement mdp"""
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


@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    """verif code 2FA apres login"""
    user_id = session.get('2fa_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    if not user:
        session.pop('2fa_user_id', None)
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        if not code:
            flash('Veuillez entrer le code de verification.', 'warning')
            return render_template('verify_2fa.html')

        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(code, valid_window=1):
            remember = session.pop('2fa_remember', False)
            session.pop('2fa_user_id', None)
            AuthService.login(user, remember=remember)
            flash(f'Bienvenue, {user.first_name} !', 'success')

            pending_token = session.pop('pending_invite_token', None)
            if pending_token:
                return redirect(url_for('family.accept_invite', token=pending_token))

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                return redirect(next_page)
            return redirect(url_for('user.dashboard'))
        else:
            flash('Code incorrect ou expire. Veuillez reessayer.', 'danger')

    return render_template('verify_2fa.html')


@auth_bp.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    """cfg 2FA"""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'enable':
            code = request.form.get('code', '').strip()
            secret = session.get('2fa_setup_secret')

            if not secret or not code:
                flash('Erreur de configuration. Veuillez recommencer.', 'danger')
                return redirect(url_for('auth.setup_2fa'))

            totp = pyotp.TOTP(secret)
            if totp.verify(code, valid_window=1):
                current_user.totp_secret = secret
                current_user.is_2fa_enabled = True
                db.session.commit()
                session.pop('2fa_setup_secret', None)
                flash('2FA activee.', 'success')
                return redirect(url_for('user.profile'))
            else:
                flash('Code incorrect. Veuillez reessayer.', 'danger')
                return redirect(url_for('auth.setup_2fa'))

        elif action == 'disable':
            code = request.form.get('code', '').strip()
            if current_user.totp_secret:
                totp = pyotp.TOTP(current_user.totp_secret)
                if totp.verify(code, valid_window=1):
                    current_user.totp_secret = None
                    current_user.is_2fa_enabled = False
                    db.session.commit()
                    flash('Authentification a deux facteurs desactivee.', 'info')
                    return redirect(url_for('user.profile'))
                else:
                    flash('Code incorrect. La 2FA n\'a pas ete desactivee.', 'danger')

    # generer secret pour cfg
    secret = pyotp.random_base32()
    session['2fa_setup_secret'] = secret

    # generer QR code
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name='FamiliDocs'
    )

    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # convert base64 pr affichage
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return render_template(
        'setup_2fa.html',
        qr_code=qr_base64,
        secret=secret,
        is_enabled=current_user.is_2fa_enabled
    )
