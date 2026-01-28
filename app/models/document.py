"""
Modèle Document - Gestion des documents
"""
from datetime import datetime
from . import db


class Document(db.Model):
    """Modèle représentant un document"""

    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)  # Taille en octets
    description = db.Column(db.Text)
    confidentiality = db.Column(db.String(20), nullable=False, default='private')
    is_encrypted = db.Column(db.Boolean, default=False)

    # Dates importantes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expiry_date = db.Column(db.Date, nullable=True)  # Date d'échéance du document

    # Relations
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)

    # Permissions et tâches liées
    permissions = db.relationship('Permission', backref='document', lazy='dynamic',
                                  cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='document', lazy='dynamic',
                            cascade='all, delete-orphan')
    logs = db.relationship('Log', backref='document', lazy='dynamic')

    def __repr__(self):
        return f'<Document {self.name}>'

    @property
    def is_expiring_soon(self):
        """Vérifie si le document expire dans les 30 prochains jours"""
        if not self.expiry_date:
            return False
        from datetime import date, timedelta
        return date.today() <= self.expiry_date <= date.today() + timedelta(days=30)

    @property
    def is_expired(self):
        """Vérifie si le document est expiré"""
        if not self.expiry_date:
            return False
        from datetime import date
        return self.expiry_date < date.today()

    @property
    def file_extension(self):
        """Retourne l'extension du fichier"""
        if '.' in self.original_filename:
            return self.original_filename.rsplit('.', 1)[1].lower()
        return ''

    def get_human_readable_size(self):
        """Retourne la taille du fichier en format lisible"""
        if not self.file_size:
            return 'Inconnu'
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if self.file_size < 1024:
                return f'{self.file_size:.1f} {unit}'
            self.file_size /= 1024
        return f'{self.file_size:.1f} To'

    def is_shared_with(self, user):
        """Vérifie si le document est partagé avec un utilisateur"""
        permission = self.permissions.filter_by(user_id=user.id).first()
        return permission is not None and permission.is_valid()
