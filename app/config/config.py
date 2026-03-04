"""
Configuration generale de l'application FamiliDocs
"""
import os
import sys
import logging
import secrets
from datetime import timedelta
from dotenv import load_dotenv

# Charger .env avant toute lecture d'os.environ
load_dotenv()

# Repertoire de base (compatible PyInstaller)
if getattr(sys, 'frozen', False):
    # Mode .exe (PyInstaller)
    BASE_DIR = sys._MEIPASS
    USER_DATA_DIR = os.path.join(os.path.dirname(sys.executable), 'app', 'database')
else:
    # Mode developpement normal
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    USER_DATA_DIR = os.path.join(BASE_DIR, 'database')


def _generate_secret_key():
    """Genere une cle secrete persistante pour le developpement"""
    key_file = os.path.join(USER_DATA_DIR, '.secret_key')
    if os.path.exists(key_file):
        with open(key_file, 'r') as f:
            return f.read().strip()
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    key = secrets.token_hex(32)
    with open(key_file, 'w') as f:
        f.write(key)
    return key


def _get_engine_options():
    """Retourne les options moteur pour PostgreSQL"""
    return {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }


class Config:
    """Configuration de base"""

    # Cle secrete : variable d'environnement obligatoire en production
    SECRET_KEY = os.environ.get('SECRET_KEY') or _generate_secret_key()

    # Base de donnees PostgreSQL (partagee entre web et desktop .exe)
    # Les deux modes utilisent la meme BDD pour que les donnees soient synchronisees
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://jagadmin:pass@localhost:5432/familidocs'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = _get_engine_options()

    # Sessions
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Uploads
    UPLOAD_FOLDER = os.environ.get('FAMILIDOCS_UPLOAD_FOLDER') or os.path.join(USER_DATA_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'gif'}

    # Chiffrement
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or None

    # Sauvegardes
    BACKUP_FOLDER = os.environ.get('FAMILIDOCS_BACKUP_FOLDER') or os.path.join(USER_DATA_DIR, 'backups')

    # Mot de passe admin par defaut (configurable via env)
    ADMIN_DEFAULT_PASSWORD = os.environ.get('ADMIN_DEFAULT_PASSWORD') or 'Admin123!'

    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    # Categories de documents
    DEFAULT_CATEGORIES = [
        'Administratif',
        'Sante',
        'Banque',
        'Logement',
        'Autres'
    ]

    # Niveaux de confidentialite
    CONFIDENTIALITY_LEVELS = {
        'public': 'Public - Visible par tous les membres autorises',
        'private': 'Prive - Visible uniquement par le proprietaire',
        'restricted': 'Restreint - Visible par les personnes choisies'
    }

    # Valeurs autorisees pour la validation
    VALID_PRIORITIES = {'low', 'normal', 'high', 'urgent'}
    VALID_TASK_STATUSES = {'pending', 'in_progress', 'completed', 'cancelled'}

    # Roles utilisateurs
    USER_ROLES = {
        'admin': 'Administrateur',
        'user': 'Utilisateur',
        'trusted': 'Personne de confiance'
    }



class DevelopmentConfig(Config):
    """Configuration de developpement"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'
    # Herite de Config.SQLALCHEMY_DATABASE_URI (PostgreSQL)


class TestingConfig(Config):
    """Configuration de test"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    LOG_LEVEL = 'WARNING'


class ProductionConfig(Config):
    """Configuration de production"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

    @classmethod
    def init_app(cls, app):
        """Validation de la configuration en production"""
        if app.config['SECRET_KEY'] == _generate_secret_key():
            app.logger.warning(
                "ATTENTION: SECRET_KEY non definie en production! "
                "Definissez la variable d'environnement SECRET_KEY."
            )


# Dictionnaire des configurations
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
