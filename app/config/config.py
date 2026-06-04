#bdd , clé secrete, session user, upload fichier, sauvegardes, roles, catégories : mode dev/test/prod

import os
import sys
import secrets
from datetime import timedelta
from dotenv import load_dotenv

# check mode de dev/compil dpuis .env
if getattr(sys, 'frozen', False):
    load_dotenv(os.path.join(os.path.dirname(sys.executable), '.env'))
else:
    load_dotenv()
# base repertoire
if getattr(sys, 'frozen', False):
    # mode .exe
    BASE_DIR = sys._MEIPASS
    USER_DATA_DIR = os.path.join(os.path.dirname(sys.executable), 'app', 'database')
else:
    # mode dev
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    USER_DATA_DIR = os.path.join(BASE_DIR, 'database')

def _generate_secret_key():
    """secret key"""
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
    """options pool postgresql (verifie connexion avant requete)"""
    return {'pool_pre_ping': True}

class Config:
    """cfg"""
    # secret key env var prod
    SECRET_KEY = os.environ.get('SECRET_KEY') or _generate_secret_key()
    # bdd postgresql (web + desktop: meme bdd)
    # pas de fallback en dur : DATABASE_URL doit etre dans .env
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = _get_engine_options()
    # Sessions
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Upload
    UPLOAD_FOLDER = os.environ.get('FAMILIDOCS_UPLOAD_FOLDER') or os.path.join(USER_DATA_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'gif'}
    # Chifrement
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or None
    # Sauvegarde
    BACKUP_FOLDER = os.environ.get('FAMILIDOCS_BACKUP_FOLDER') or os.path.join(USER_DATA_DIR, 'backups')
    # Telechargement de l'application desktop (.exe depose sur le volume persistant du serveur)
    DOWNLOAD_FOLDER = os.environ.get('FAMILIDOCS_DOWNLOAD_FOLDER') or os.path.join(USER_DATA_DIR, 'downloads')
    DESKTOP_APP_FILENAME = os.environ.get('FAMILIDOCS_DESKTOP_FILENAME', 'FamiliDocs.exe')
    # Logs
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    # Categorie de doc
    DEFAULT_CATEGORIES = [
        'Administratif',
        'Sante',
        'Banque',
        'Logement',
        'Autres'
    ]
    # Niveau confidentialite
    CONFIDENTIALITY_LEVELS = {
        'public': 'Public - Visible par tous les membres autorises',
        'private': 'Prive - Visible uniquement par le proprietaire',
        'restricted': 'Restreint - Visible par les personnes choisies'
    }
    VALID_PRIORITIES = {'low', 'normal', 'high', 'urgent'}
    VALID_TASK_STATUSES = {'pending', 'in_progress', 'completed', 'cancelled'}

    # roles users
    USER_ROLES = {
        'admin': 'Administrateur',
        'user': 'Utilisateur',
        'trusted': 'Personne de confiance'
    }

class DevelopmentConfig(Config):
    """cfg dev"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'
    # herite bdd postgresql

    @classmethod
    def init_app(cls, app):
        """verif cfg dev"""
        if not os.environ.get('DATABASE_URL'):
            raise RuntimeError(
                "DATABASE_URL non definie. "
                "Copiez .env.example en .env et configurez la connexion PostgreSQL."
            )


class TestingConfig(Config):
    """cfg test"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    LOG_LEVEL = 'WARNING'


class ProductionConfig(Config):
    """cfg prod"""
    DEBUG = False
    TESTING = False
    # cookie de session reserve au HTTPS par defaut.
    # mettre SESSION_COOKIE_SECURE=False si l'app est exposee en HTTP (ex: IP:port sans TLS),
    # sinon le navigateur n'enverra pas le cookie et la connexion echouera.
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True').lower() not in ('false', '0', 'no')

    @classmethod
    def init_app(cls, app):
        """verif cfg prod"""
        if not os.environ.get('SECRET_KEY'):
            raise ValueError(
                "SECRET_KEY non definie en prod "
                "Definissez la variable env SECRET_KEY."
            )
        # DATABASE_URL prod
        if not os.environ.get('DATABASE_URL'):
            raise ValueError(
                "DATABASE_URL non definie en production ! "
                "Definissez la variable d'environnement DATABASE_URL."
            )

# dict configs
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
