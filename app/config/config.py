"""
Configuration générale de l'application FamiliDocs
"""
import os
from datetime import timedelta

# Répertoire de base
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    """Configuration de base"""

    # Clé secrète pour les sessions (à changer en production)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'familidocs-secret-key-change-in-production'

    # Base de données SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'database', 'familidocs.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuration des sessions
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    # Configuration des uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'database', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'txt', 'xls', 'xlsx'}

    # Configuration du chiffrement
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or None

    # Dossier de sauvegarde
    BACKUP_FOLDER = os.path.join(os.path.dirname(BASE_DIR), 'backups')

    # Catégories de documents par défaut
    DEFAULT_CATEGORIES = [
        'Administratif',
        'Santé',
        'Banque',
        'Logement',
        'Autres'
    ]

    # Niveaux de confidentialité
    CONFIDENTIALITY_LEVELS = {
        'public': 'Public - Visible par tous les membres autorisés',
        'private': 'Privé - Visible uniquement par le propriétaire',
        'restricted': 'Restreint - Visible par les personnes choisies'
    }

    # Rôles utilisateurs
    USER_ROLES = {
        'admin': 'Administrateur',
        'user': 'Utilisateur',
        'trusted': 'Personne de confiance'
    }


class DevelopmentConfig(Config):
    """Configuration de développement"""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Configuration de test"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """Configuration de production"""
    DEBUG = False
    TESTING = False


# Dictionnaire des configurations
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
