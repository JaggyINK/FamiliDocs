"""
Modele DocumentVersion - Historique des versions de documents
"""
from datetime import datetime
from . import db


class DocumentVersion(db.Model):
    """Modele representant une version d'un document"""

    __tablename__ = 'document_versions'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False, default=1)

    # Fichier de la version
    stored_filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))

    # Metadonnees
    comment = db.Column(db.Text, nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relations
    document = db.relationship('Document', backref=db.backref(
        'versions', lazy='dynamic', order_by='DocumentVersion.version_number.desc()'
    ))
    uploader = db.relationship('User', backref=db.backref('uploaded_versions', lazy='dynamic'))

    def __repr__(self):
        return f'<DocumentVersion {self.document_id} v{self.version_number}>'

    def get_human_readable_size(self):
        """Retourne la taille en format lisible"""
        if not self.file_size:
            return 'Inconnu'
        size = self.file_size
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} To'

    @staticmethod
    def get_latest_version_number(document_id):
        """Retourne le dernier numero de version pour un document"""
        latest = DocumentVersion.query.filter_by(
            document_id=document_id
        ).order_by(DocumentVersion.version_number.desc()).first()
        return latest.version_number if latest else 0

    @staticmethod
    def get_versions(document_id):
        """Recupere toutes les versions d'un document"""
        return DocumentVersion.query.filter_by(
            document_id=document_id
        ).order_by(DocumentVersion.version_number.desc()).all()
