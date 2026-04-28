# modele utilisatuer
from datetime import datetime
from flask_login import UserMixin
from . import db


class User(UserMixin, db.Model):
    """table users"""

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

    # photo profil
    profile_photo = db.Column(db.String(255), nullable=True)
    # titre familial custom
    family_title = db.Column(db.String(50), nullable=True)

    # 2FA TOTP
    totp_secret = db.Column(db.String(32), nullable=True)
    is_2fa_enabled = db.Column(db.Boolean, default=False)

    folders = db.relationship('Folder', backref='owner', lazy='dynamic',
                              foreign_keys='Folder.owner_id',
                              cascade='all, delete-orphan')
    documents = db.relationship('Document', backref='owner', lazy='dynamic',
                                foreign_keys='Document.owner_id',
                                cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='owner', lazy='dynamic',
                            foreign_keys='Task.owner_id',
                            cascade='all, delete-orphan')
    logs = db.relationship('Log', backref='user', lazy='dynamic',
                           cascade='all, delete-orphan')

    # perm recues
    permissions_received = db.relationship('Permission', backref='granted_user',
                                           lazy='dynamic',
                                           foreign_keys='Permission.user_id')
    # perm donnees
    permissions_granted = db.relationship('Permission', backref='granting_user',
                                          lazy='dynamic',
                                          foreign_keys='Permission.granted_by')

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def full_name(self):
        """nom complet"""
        return f'{self.first_name} {self.last_name}'

    def is_admin(self):
        """check admin"""
        return self.role == 'admin'

    def is_trusted(self):
        """check personne de confiance"""
        return self.role == 'trusted'

    def can_access_document(self, document):
        """verif acces doc"""
        if document.owner_id == self.id:
            return True
        if self.is_admin():
            return True
        # perm explicite
        permission = Permission.query.filter_by(
            document_id=document.id,
            user_id=self.id
        ).first()
        if permission and permission.is_valid():
            return True
        return False

    def can_edit_document(self, document):
        """verif edit doc"""
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
        """nom affichage avec titre familial"""
        if self.family_title:
            return f"{self.family_title} ({self.first_name})"
        return self.full_name

    @property
    def avatar_url(self):
        """url avatar ou None"""
        if self.profile_photo:
            return f'/uploads/avatars/{self.profile_photo}'
        return None

    @property
    def initials(self):
        """initiales user"""
        f = self.first_name[0] if self.first_name else '?'
        l = self.last_name[0] if self.last_name else '?'
        return f"{f}{l}".upper()

    # titres familiaux dispo
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


# marche pas sans ca (import circulaire)
from .permission import Permission
