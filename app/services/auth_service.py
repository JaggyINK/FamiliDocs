"""
Service d'authentification - Gestion des connexions et mots de passe
"""
import bcrypt
from datetime import datetime
from flask import request
from flask_login import login_user, logout_user

from app.models import db
from app.models.user import User
from app.models.log import Log
from app.models.folder import Folder


class AuthService:
    """Service pour la gestion de l'authentification"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash un mot de passe avec bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Vérifie un mot de passe contre son hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )

    @staticmethod
    def authenticate(email: str, password: str) -> tuple:
        """
        Authentifie un utilisateur
        Retourne (success, user_or_error_message)
        """
        user = User.query.filter_by(email=email).first()

        if not user:
            return False, "Email ou mot de passe incorrect"

        if not user.is_active:
            return False, "Ce compte est désactivé"

        if not AuthService.verify_password(password, user.password_hash):
            # Log de l'échec de connexion
            Log.create_log(
                user_id=user.id,
                action='login_failed',
                details=f"Tentative de connexion échouée pour {email}",
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string[:255] if request.user_agent.string else None
            )
            db.session.commit()
            return False, "Email ou mot de passe incorrect"

        return True, user

    @staticmethod
    def login(user: User, remember: bool = False) -> bool:
        """Connecte un utilisateur"""
        # Mise à jour de la dernière connexion
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Connexion via Flask-Login
        login_user(user, remember=remember)

        # Log de la connexion
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
        """Déconnecte un utilisateur"""
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
        """
        Enregistre un nouvel utilisateur
        Retourne (success, user_or_error_message)
        """
        # Vérification de l'email unique
        if User.query.filter_by(email=email).first():
            return False, "Cet email est déjà utilisé"

        # Vérification du username unique
        if User.query.filter_by(username=username).first():
            return False, "Ce nom d'utilisateur est déjà utilisé"

        # Validation du mot de passe
        is_valid, message = AuthService.validate_password(password)
        if not is_valid:
            return False, message

        # Création de l'utilisateur
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

        # Création des dossiers par défaut
        default_folders = Folder.create_default_folders(user.id)
        for folder in default_folders:
            db.session.add(folder)
        db.session.commit()

        return True, user

    @staticmethod
    def validate_password(password: str) -> tuple:
        """
        Valide la complexité d'un mot de passe
        Retourne (is_valid, message)
        """
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
        """
        Change le mot de passe d'un utilisateur
        Retourne (success, message)
        """
        # Vérification de l'ancien mot de passe
        if not AuthService.verify_password(old_password, user.password_hash):
            return False, "Mot de passe actuel incorrect"

        # Validation du nouveau mot de passe
        is_valid, message = AuthService.validate_password(new_password)
        if not is_valid:
            return False, message

        # Mise à jour du mot de passe
        user.password_hash = AuthService.hash_password(new_password)
        db.session.commit()

        return True, "Mot de passe modifié avec succès"

    @staticmethod
    def reset_password(user: User, new_password: str) -> tuple:
        """
        Réinitialise le mot de passe d'un utilisateur (admin)
        Retourne (success, message)
        """
        # Validation du nouveau mot de passe
        is_valid, message = AuthService.validate_password(new_password)
        if not is_valid:
            return False, message

        # Mise à jour du mot de passe
        user.password_hash = AuthService.hash_password(new_password)
        db.session.commit()

        return True, "Mot de passe réinitialisé avec succès"
