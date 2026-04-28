# modele dossier
from datetime import datetime
from . import db


class Folder(db.Model):
    """table dossiers"""

    __tablename__ = 'folders'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False, default='Autres')
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = db.relationship('Document', backref='folder', lazy='dynamic')
    subfolders = db.relationship('Folder', backref=db.backref('parent', remote_side=[id]),
                                 lazy='dynamic',
                                 cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Folder {self.name}>'

    @property
    def document_count(self):
        """nb docs dans dossier"""
        return self.documents.count()

    @property
    def total_size(self):
        """taille totale docs"""
        total = 0
        for doc in self.documents:
            if doc.file_size:
                total = total + doc.file_size
        return total

    def get_path(self):
        """chemin complet dossier"""
        path = [self.name]
        parent = self.parent
        max_depth = 20
        depth = 0
        while parent:
            depth += 1
            if depth > max_depth:
                path.insert(0, '...')
                break
            path.insert(0, parent.name)
            parent = parent.parent
        return ' / '.join(path)

    @staticmethod
    def create_default_folders(user_id):
        """cree dossiers par defaut nouvel user"""
        from app.config import Config

        folders = []
        for category in Config.DEFAULT_CATEGORIES:
            folder = Folder(
                name=category,
                category=category,
                owner_id=user_id,
                description=f'Dossier {category}'
            )
            folders.append(folder)
        return folders
