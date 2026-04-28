# modele perm acces docs
from datetime import datetime, date
from . import db


class Permission(db.Model):
    """perm acces doc"""

    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    can_view = db.Column(db.Boolean, default=True)
    can_edit = db.Column(db.Boolean, default=False)
    can_download = db.Column(db.Boolean, default=True)
    can_share = db.Column(db.Boolean, default=False)

    start_date = db.Column(db.Date, default=date.today)
    end_date = db.Column(db.Date, nullable=True)  # None = permanent

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)

    __table_args__ = (
        db.UniqueConstraint('document_id', 'user_id', name='unique_document_user_permission'),
    )

    def __repr__(self):
        return f'<Permission doc={self.document_id} user={self.user_id}>'

    def is_valid(self):
        """verif perm valide"""
        today = date.today()

        if self.start_date and self.start_date > today:
            return False

        if self.end_date and self.end_date < today:
            return False

        return True

    def is_expiring_soon(self):
        """expire dans 7j ?"""
        if not self.end_date:
            return False
        from datetime import timedelta
        return date.today() <= self.end_date <= date.today() + timedelta(days=7)

    @property
    def status(self):
        """statut perm"""
        today = date.today()

        if self.start_date and self.start_date > today:
            return 'pending'

        if self.end_date and self.end_date < today:
            return 'expired'

        if not self.end_date:
            return 'permanent'

        return 'active'

    @staticmethod
    def grant_access(document_id, user_id, granted_by, can_edit=False,
                     can_download=True, can_share=False, end_date=None, notes=None):
        """accorder acces doc"""
        # verif si perm existe deja
        existing = Permission.query.filter_by(
            document_id=document_id,
            user_id=user_id
        ).first()

        if existing:
            # maj perm existante
            existing.can_edit = can_edit
            existing.can_download = can_download
            existing.can_share = can_share
            existing.end_date = end_date
            existing.notes = notes
            existing.updated_at = datetime.utcnow()
            return existing

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
        """revoquer acces doc"""
        permission = Permission.query.filter_by(
            document_id=document_id,
            user_id=user_id
        ).first()
        if permission:
            db.session.delete(permission)
            return True
        return False
