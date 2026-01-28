"""
FamiliDocs - Coffre Administratif Numérique Familial
Application Flask pour la gestion documentaire familiale
"""
import os
from flask import Flask
from flask_login import LoginManager

from app.models import db
from app.config import config


# Initialisation de Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'warning'


def create_app(config_name=None):
    """Factory function pour créer l'application Flask"""

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialisation des extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Création des dossiers nécessaires
    _create_directories(app)

    # Enregistrement des blueprints
    _register_blueprints(app)

    # Configuration du user_loader
    _setup_login_manager(app)

    # Création des tables de la base de données
    with app.app_context():
        db.create_all()
        _create_admin_user(app)

    return app


def _create_directories(app):
    """Crée les dossiers nécessaires à l'application"""
    directories = [
        app.config.get('UPLOAD_FOLDER'),
        app.config.get('BACKUP_FOLDER')
    ]
    for directory in directories:
        if directory and not os.path.exists(directory):
            os.makedirs(directory)


def _register_blueprints(app):
    """Enregistre tous les blueprints de l'application"""
    from app.routes.auth_routes import auth_bp
    from app.routes.user_routes import user_bp
    from app.routes.document_routes import document_bp
    from app.routes.task_routes import task_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.notification_routes import notification_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notification_bp)


def _setup_login_manager(app):
    """Configure le gestionnaire de connexion"""
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


def _create_admin_user(app):
    """Crée l'utilisateur administrateur par défaut s'il n'existe pas"""
    from app.models.user import User
    from app.services.auth_service import AuthService

    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            email='admin@familidocs.local',
            username='admin',
            password_hash=AuthService.hash_password('Admin123!'),
            first_name='Administrateur',
            last_name='FamiliDocs',
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
