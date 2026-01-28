"""
Modèle Permission - Gestion des droits d'accès aux documents
"""
from datetime import datetime, date
from . import db


class Permission(db.Model):
    """Modèle représentant une permission d'accès à un document"""

    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Type de permission
    can_view = db.Column(db.Boolean, default=True)
    can_edit = db.Column(db.Boolean, default=False)
    can_download = db.Column(db.Boolean, default=True)
    can_share = db.Column(db.Boolean, default=False)

    # Validité temporelle
    start_date = db.Column(db.Date, default=date.today)
    end_date = db.Column(db.Date, nullable=True)  # None = permanent

    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)  # Notes sur pourquoi l'accès a été accordé

    # Contrainte d'unicité : un seul enregistrement par document/utilisateur
    __table_args__ = (
        db.UniqueConstraint('document_id', 'user_id', name='unique_document_user_permission'),
    )

    def __repr__(self):
        return f'<Permission doc={self.document_id} user={self.user_id}>'

    def is_valid(self):
        """Vérifie si la permission est actuellement valide"""
        today = date.today()

        # Vérifier la date de début
        if self.start_date and self.start_date > today:
            return False

        # Vérifier la date de fin
        if self.end_date and self.end_date < today:
            return False

        return True

    def is_expiring_soon(self):
        """Vérifie si la permission expire dans les 7 prochains jours"""
        if not self.end_date:
            return False
        from datetime import timedelta
        return date.today() <= self.end_date <= date.today() + timedelta(days=7)

    @property
    def status(self):
        """Retourne le statut de la permission"""
        today = date.today()

        if self.start_date and self.start_date > today:
            return 'pending'  # Pas encore active

        if self.end_date and self.end_date < today:
            return 'expired'  # Expirée

        if not self.end_date:
            return 'permanent'  # Permanente

        return 'active'  # Active

    @staticmethod
    def grant_access(document_id, user_id, granted_by, can_edit=False,
                     can_download=True, can_share=False, end_date=None, notes=None):
        """Méthode pour accorder l'accès à un document"""
        # Vérifier si une permission existe déjà
        existing = Permission.query.filter_by(
            document_id=document_id,
            user_id=user_id
        ).first()

        if existing:
            # Mettre à jour la permission existante
            existing.can_edit = can_edit
            existing.can_download = can_download
            existing.can_share = can_share
            existing.end_date = end_date
            existing.notes = notes
            existing.updated_at = datetime.utcnow()
            return existing

        # Créer une nouvelle permission
        permission = Permission(
            document_id=document_id,
            user_id=user_id,
            granted_by=granted_by,
            can_edit=can_edit,
            can_download=can_download,
            can_share=can_share,
            end_date=end_date,
            notes=notes
        )
        return permission

    @staticmethod
    def revoke_access(document_id, user_id):
        """Méthode pour révoquer l'accès à un document"""
        permission = Permission.query.filter_by(
            document_id=document_id,
            user_id=user_id
        ).first()
        if permission:
            db.session.delete(permission)
            return True
        return False
