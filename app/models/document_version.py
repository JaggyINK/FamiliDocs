# modele versions docs
from datetime import datetime
from . import db


class DocumentVersion(db.Model):
    __tablename__ = 'document_versions'
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    version_number = db.Column(db.Integer, nullable=False, default=1)
    stored_filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))
    comment = db.Column(db.Text, nullable=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # delete quand doc supprime
    document = db.relationship('Document', backref=db.backref(
        'versions', lazy='dynamic', order_by='DocumentVersion.version_number.desc()',
        cascade='all, delete-orphan'
    ))
    uploader = db.relationship('User', backref=db.backref('uploaded_versions', lazy='dynamic'))

    #fcntio pr afficher l'objet : nom + id + num de version
    def __repr__(self):
        return f'<DocumentVersion {self.document_id} v{self.version_number}>'

    #affichage simple nb octets
    def get_human_readable_size(self):
        if not self.file_size:
            return 'Inconnu'
        size = self.file_size
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if size < 1024:
                return f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} To'

    #check derniere version du doc
    @staticmethod
    def get_latest_version_number(document_id):
        latest = DocumentVersion.query.filter_by(
            document_id=document_id
        ).order_by(DocumentVersion.version_number.desc()).first()
        return latest.version_number if latest else 0

    #recup toute les versions du doc
    @staticmethod
    def get_versions(document_id):
        return DocumentVersion.query.filter_by(
            document_id=document_id
        ).order_by(DocumentVersion.version_number.desc()).all()
