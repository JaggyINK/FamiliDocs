# FamiliDocs - app Flask gest docs familial
import os
import logging
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

from app.models import db
from app.config import config


# flask-login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Veuillez vous connecter pour acceder a cette page.'
login_manager.login_message_category = 'warning'

# CSRF
csrf = CSRFProtect()

# migrate
migrate = Migrate()


def create_app(config_name=None):
    """factory Flask"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # validation cfg (prod surtout)
    config_class = config[config_name]
    if hasattr(config_class, 'init_app'):
        config_class.init_app(app)

    _setup_logging(app)

    # extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    _create_directories(app)
    _register_blueprints(app)
    _setup_login_manager(app)
    _setup_security_headers(app)
    _setup_context_processors(app)
    _setup_error_handlers(app)

    # tables bdd
    with app.app_context():
        db.create_all()
        _ensure_admin_exists(app)
        _cleanup_old_logs(app)

    # scheduler (pas en mode test)
    if not app.config.get('TESTING', False):
        try:
            from app.services.scheduler_service import SchedulerService
            SchedulerService.start(app)
        except Exception as e:
            app.logger.warning(f"Scheduler KO: {e}")

    return app


def _setup_logging(app):
    levels = {'DEBUG': logging.DEBUG, 'WARNING': logging.WARNING, 'ERROR': logging.ERROR}
    log_level = levels.get(app.config.get('LOG_LEVEL', 'INFO'), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    app.logger.setLevel(log_level)


def _create_directories(app):
    upload = app.config.get('UPLOAD_FOLDER')
    backup = app.config.get('BACKUP_FOLDER')
    download = app.config.get('DOWNLOAD_FOLDER')
    for d in [upload, backup, download, os.path.join(upload, 'avatars') if upload else None]:
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)


def _register_blueprints(app):
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
    from app.routes.download_routes import download_bp

    for bp in (auth_bp, user_bp, document_bp, task_bp, admin_bp,
               notification_bp, version_bp, search_bp, family_bp, message_bp,
               download_bp):
        app.register_blueprint(bp)


def _setup_login_manager(app):
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))


def _setup_security_headers(app):
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        # HSTS uniquement en HTTPS : l'envoyer en HTTP forcerait le navigateur
        # a passer en HTTPS et casserait l'acces sur une expo HTTP (IP:port)
        if not app.debug and app.config.get('SESSION_COOKIE_SECURE'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response


def _setup_context_processors(app):
    @app.context_processor
    def inject_notification_count():
        from flask_login import current_user
        if current_user.is_authenticated:
            from app.models.notification import Notification
            return {'notification_count': Notification.get_unread_count(current_user.id)}
        return {'notification_count': 0}


def _setup_error_handlers(app):
    from flask import render_template

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500


def _ensure_admin_exists(app):
    """promeut le 1er user admin si aucun admin"""
    from app.models.user import User
    if User.query.filter_by(role='admin').first():
        return
    first_user = User.query.first()
    if first_user:
        first_user.role = 'admin'
        db.session.commit()
        app.logger.info(f"Aucun admin : {first_user.email} promu administrateur")
    else:
        app.logger.warning("Aucun utilisateur en base. Lancez seed_demo_data.py ou /register")


def _cleanup_old_logs(app):
    """cleanup RGPD vieux logs"""
    from app.models.log import Log
    try:
        deleted = Log.cleanup_old_logs()
        if deleted > 0:
            app.logger.info(f"RGPD: {deleted} log(s) supprime(s)")
    except Exception as e:
        app.logger.warning(f"Erreur cleanup logs: {e}")
