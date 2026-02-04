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

    # En-tetes de securite HTTP
    _setup_security_headers(app)

    # Injection du compteur de notifications dans les templates
    _setup_context_processors(app)

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
    from app.routes.version_routes import version_bp
    from app.routes.search_routes import search_bp
    from app.routes.family_routes import family_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(version_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(family_bp)


def _setup_login_manager(app):
    """Configure le gestionnaire de connexion"""
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


def _setup_security_headers(app):
    """Configure les en-tetes de securite HTTP"""

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        return response


def _setup_context_processors(app):
    """Configure les variables injectees dans tous les templates"""

    @app.context_processor
    def inject_notification_count():
        from flask_login import current_user
        if current_user.is_authenticated:
            from app.models.notification import Notification
            count = Notification.get_unread_count(current_user.id)
            return {'notification_count': count}
        return {'notification_count': 0}


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
