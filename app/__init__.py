"""
FamiliDocs - Coffre Administratif Numerique Familial
Application Flask pour la gestion documentaire familiale
"""
import os
import logging
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

from app.models import db
from app.config import config


# Initialisation de Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Veuillez vous connecter pour acceder a cette page.'
login_manager.login_message_category = 'warning'

# Initialisation de la protection CSRF
csrf = CSRFProtect()

# Initialisation de Flask-Migrate
migrate = Migrate()


def create_app(config_name=None):
    """Factory function pour creer l'application Flask"""

    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Appeler init_app si disponible (validation production)
    config_class = config[config_name]
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)

    # Configuration du logging
    _setup_logging(app)

    # Initialisation des extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Creation des dossiers necessaires
    _create_directories(app)

    # Enregistrement des blueprints
    _register_blueprints(app)

    # Configuration du user_loader
    _setup_login_manager(app)

    # En-tetes de securite HTTP
    _setup_security_headers(app)

    # Injection du compteur de notifications dans les templates
    _setup_context_processors(app)

    # Gestionnaires d'erreurs
    _setup_error_handlers(app)

    # Creation des tables de la base de donnees
    with app.app_context():
        db.create_all()
        _create_admin_user(app)
        _cleanup_old_logs(app)

    # Demarrer le scheduler (sauf en mode TESTING)
    if not app.config.get('TESTING', False):
        try:
            from app.services.scheduler_service import SchedulerService
            SchedulerService.start(app)
        except Exception as e:
            app.logger.warning(f"Impossible de demarrer le scheduler: {e}")

    return app


def _setup_logging(app):
    """Configure le logging de l'application"""
    # Determiner le niveau de log selon la configuration
    log_level_name = app.config.get('LOG_LEVEL', 'INFO')
    if log_level_name == 'DEBUG':
        log_level = logging.DEBUG
    elif log_level_name == 'WARNING':
        log_level = logging.WARNING
    elif log_level_name == 'ERROR':
        log_level = logging.ERROR
    else:
        log_level = logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    app.logger.setLevel(log_level)


def _create_directories(app):
    """Cree les dossiers necessaires a l'application"""
    directories = [
        app.config.get('UPLOAD_FOLDER'),
        app.config.get('BACKUP_FOLDER'),
    ]
    # Sous-dossier pour les avatars
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder:
        directories.append(os.path.join(upload_folder, 'avatars'))

    for directory in directories:
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)


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
    from app.routes.message_routes import message_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notification_bp)
    app.register_blueprint(version_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(family_bp)
    app.register_blueprint(message_bp)


def _setup_login_manager(app):
    """Configure le gestionnaire de connexion"""
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))


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



def _setup_error_handlers(app):
    """Configure les pages d'erreur personnalisees"""

    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        from flask import render_template
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        from flask import render_template
        return render_template('errors/500.html'), 500


def _create_admin_user(app):
    """Cree l'utilisateur administrateur par defaut s'il n'existe pas"""
    from app.models.user import User
    from app.services.auth_service import AuthService

    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin_password = app.config.get('ADMIN_DEFAULT_PASSWORD', 'Admin123!')
        admin = User(
            email='admin@familidocs.local',
            username='admin',
            password_hash=AuthService.hash_password(admin_password),
            first_name='Administrateur',
            last_name='FamiliDocs',
            role='admin',
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        app.logger.info("Utilisateur admin cree avec succes")


def _cleanup_old_logs(app):
    """Nettoyage RGPD : supprime les logs depasses la duree de retention"""
    from app.models.log import Log
    try:
        deleted = Log.cleanup_old_logs()
        if deleted > 0:
            app.logger.info(f"RGPD: {deleted} ancien(s) log(s) supprime(s) au demarrage")
    except Exception as e:
        app.logger.warning(f"Erreur nettoyage logs RGPD: {e}")
