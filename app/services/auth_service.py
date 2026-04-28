# service auth connextion mdp
import bcrypt
from datetime import datetime
from flask import request
from flask_login import login_user, logout_user

from app.models import db
from app.models.user import User
from app.models.log import Log
from app.models.folder import Folder


class AuthService:
    """auth service"""
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15 minutes en secondes
    # rate limiting en memoire : suffisant pour un projet d'ecole mono-instance
    # en prod multi-workers il faudrait Redis ou la bdd pour partager le compteur
    _failed_attempts = {}  # {ip: {'count': int, 'last_attempt': datetime}}

    @classmethod
    def _check_rate_limit(cls, ip_address):
        """check rate limit IP"""
        if ip_address not in cls._failed_attempts:
            return True, None

        attempt_data = cls._failed_attempts[ip_address]
        elapsed = (datetime.utcnow() - attempt_data['last_attempt']).total_seconds()

        # reset apres blocage
        if elapsed > cls.LOCKOUT_DURATION:
            del cls._failed_attempts[ip_address]
            return True, None

        if attempt_data['count'] >= cls.MAX_LOGIN_ATTEMPTS:
            remaining = int(cls.LOCKOUT_DURATION - elapsed)
            minutes = remaining // 60
            return False, f"Trop de tentatives. Reessayez dans {minutes + 1} minute(s)."

        return True, None

    @classmethod
    def _record_failed_attempt(cls, ip_address):
        """enregistre tentative echouee"""
        if ip_address not in cls._failed_attempts:
            cls._failed_attempts[ip_address] = {'count': 0, 'last_attempt': datetime.utcnow()}

        cls._failed_attempts[ip_address]['count'] += 1
        cls._failed_attempts[ip_address]['last_attempt'] = datetime.utcnow()

    @classmethod
    def _clear_failed_attempts(cls, ip_address):
        """reset tentatives IP"""
        if ip_address in cls._failed_attempts:
            del cls._failed_attempts[ip_address]

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash pass bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """check pas hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )

    @classmethod
    def authenticate(cls, email: str, password: str) -> tuple:
        """auth user avec rate limit"""
        ip_address = request.remote_addr
        # check rate limit
        allowed, error_msg = cls._check_rate_limit(ip_address)
        if not allowed:
            return False, error_msg
        user = User.query.filter_by(email=email).first()
        if not user:
            cls._record_failed_attempt(ip_address)
            return False, "Email ou mot de passe incorrect"
        if not user.is_active:
            return False, "Ce compte est desactive"
        if not AuthService.verify_password(password, user.password_hash):
            cls._record_failed_attempt(ip_address)
            # Log connexion
            Log.create_log(
                user_id=user.id,
                action='login_failed',
                details=f"Tentative de connexion echouee ({cls._failed_attempts.get(ip_address, {}).get('count', 0)}/{cls.MAX_LOGIN_ATTEMPTS})",
                ip_address=ip_address,
                user_agent=request.user_agent.string[:255] if request.user_agent.string else None
            )
            db.session.commit()
            # message identique a "email inexistant" pour ne pas reveler les comptes existants
            return False, "Email ou mot de passe incorrect"
        # ok - reset tentatives
        cls._clear_failed_attempts(ip_address)
        return True, user

    @staticmethod
    def login(user: User, remember: bool = False) -> bool:
        """login user"""
        user.last_login = datetime.utcnow()
        db.session.commit()

        # flask-login
        login_user(user, remember=remember)

        # log connextion
        Log.create_log(
            user_id=user.id,
            action='login',
            details="Connexion réussie",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string[:255] if request.user_agent.string else None
        )
        db.session.commit()

        return True

    @staticmethod
    def logout(user: User):
        """logout user"""
        if user and user.is_authenticated:
            Log.create_log(
                user_id=user.id,
                action='logout',
                details="Déconnexion",
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string[:255] if request.user_agent.string else None
            )
            db.session.commit()
        logout_user()

    @staticmethod
    def register_user(email: str, username: str, password: str,
                      first_name: str, last_name: str, role: str = 'user') -> tuple:
        """inscription nouvel user"""
        # email unique
        if User.query.filter_by(email=email).first():
            return False, "Cet email est déjà utilisé"

        # username unique
        if User.query.filter_by(username=username).first():
            return False, "Ce nom d'utilisateur est déjà utilisé"

        # validation mdp
        is_valid, message = AuthService.validate_password(password)
        if not is_valid:
            return False, message

        # creation user
        user = User(
            email=email,
            username=username,
            password_hash=AuthService.hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role=role
        )

        db.session.add(user)
        db.session.commit()

        # dossiers par defaut
        default_folders = Folder.create_default_folders(user.id)
        for folder in default_folders:
            db.session.add(folder)
        db.session.commit()

        return True, user

    @staticmethod
    def validate_password(password: str) -> tuple:
        """check complexite mdp"""
        if len(password) < 8:
            return False, "Le mot de passe doit contenir au moins 8 caractères"

        if not any(c.isupper() for c in password):
            return False, "Le mot de passe doit contenir au moins une majuscule"

        if not any(c.islower() for c in password):
            return False, "Le mot de passe doit contenir au moins une minuscule"

        if not any(c.isdigit() for c in password):
            return False, "Le mot de passe doit contenir au moins un chiffre"

        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            return False, "Le mot de passe doit contenir au moins un caractère spécial"

        return True, "Mot de passe valide"

    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> tuple:
        """change mdp user"""
        # verif ancien mdp
        if not AuthService.verify_password(old_password, user.password_hash):
            return False, "Mot de passe actuel incorrect"

        # validation nouveau mdp
        is_valid, message = AuthService.validate_password(new_password)
        if not is_valid:
            return False, message

        user.password_hash = AuthService.hash_password(new_password)
        db.session.commit()

        return True, "Mot de passe modifie"

    @staticmethod
    def reset_password(user: User, new_password: str) -> tuple:
        """reset mdp (admin)"""
        is_valid, message = AuthService.validate_password(new_password)
        if not is_valid:
            return False, message

        user.password_hash = AuthService.hash_password(new_password)
        db.session.commit()

        return True, "Mot de passe reinitialise"
