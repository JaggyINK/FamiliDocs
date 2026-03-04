"""
Modèle Utilisateur - Gestion des comptes utilisateurs
"""
from datetime import datetime
from flask_login import UserMixin
from . import db


class User(UserMixin, db.Model):
    """Modèle représentant un utilisateur de l'application"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # N3 - Photo de profil (chemin vers le fichier)
    profile_photo = db.Column(db.String(255), nullable=True)
    # N4 - Titre/Role familial personnalise (Papa, Maman, Fils, etc.)
    family_title = db.Column(db.String(50), nullable=True)

    # Relations
    folders = db.relationship('Folder', backref='owner', lazy='dynamic',
                              foreign_keys='Folder.owner_id')
    documents = db.relationship('Document', backref='owner', lazy='dynamic',
                                foreign_keys='Document.owner_id')
    tasks = db.relationship('Task', backref='owner', lazy='dynamic',
                            foreign_keys='Task.owner_id')
    logs = db.relationship('Log', backref='user', lazy='dynamic')

    # Permissions accordées à cet utilisateur
    permissions_received = db.relationship('Permission', backref='granted_user',
                                           lazy='dynamic',
                                           foreign_keys='Permission.user_id')
    # Permissions accordées par cet utilisateur
    permissions_granted = db.relationship('Permission', backref='granting_user',
                                          lazy='dynamic',
                                          foreign_keys='Permission.granted_by')

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def full_name(self):
        """Retourne le nom complet de l'utilisateur"""
        return f'{self.first_name} {self.last_name}'

    def is_admin(self):
        """Vérifie si l'utilisateur est administrateur"""
        return self.role == 'admin'

    def is_trusted(self):
        """Vérifie si l'utilisateur est une personne de confiance"""
        return self.role == 'trusted'

    def can_access_document(self, document):
        """Vérifie si l'utilisateur peut accéder à un document"""
        # Propriétaire
        if document.owner_id == self.id:
            return True
        # Admin
        if self.is_admin():
            return True
        # Permission explicite
        permission = Permission.query.filter_by(
            document_id=document.id,
            user_id=self.id
        ).first()
        if permission and permission.is_valid():
            return True
        return False

    def can_edit_document(self, document):
        """Vérifie si l'utilisateur peut modifier un document"""
        if document.owner_id == self.id:
            return True
        if self.is_admin():
            return True
        permission = Permission.query.filter_by(
            document_id=document.id,
            user_id=self.id
        ).first()
        if permission and permission.can_edit and permission.is_valid():
            return True
        return False

    @property
    def display_name(self):
        """Retourne le nom d'affichage avec le titre familial si defini"""
        if self.family_title:
            return f"{self.family_title} ({self.first_name})"
        return self.full_name

    @property
    def avatar_url(self):
        """Retourne l'URL de l'avatar ou un placeholder"""
        if self.profile_photo:
            return f'/uploads/avatars/{self.profile_photo}'
        # Placeholder avec initiales
        return None

    @property
    def initials(self):
        """Retourne les initiales de l'utilisateur"""
        return f"{self.first_name[0]}{self.last_name[0]}".upper()

    # Titres familiaux predefinies
    FAMILY_TITLES = [
        ('', 'Aucun'),
        ('Papa', 'Papa'),
        ('Maman', 'Maman'),
        ('Fils', 'Fils'),
        ('Fille', 'Fille'),
        ('Grand-Pere', 'Grand-Pere'),
        ('Grand-Mere', 'Grand-Mere'),
        ('Oncle', 'Oncle'),
        ('Tante', 'Tante'),
        ('Cousin', 'Cousin'),
        ('Cousine', 'Cousine'),
        ('Autre', 'Autre')
    ]


# Import ici pour éviter l'import circulaire
from .permission import Permission
