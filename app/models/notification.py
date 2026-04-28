# modele notif
from datetime import datetime
from . import db


class Notification(db.Model):
    """notif utilisatuer"""

    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    type = db.Column(db.String(50), nullable=False)  # task_due, document_expiry, share, system
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)

    priority = db.Column(db.String(20), default='normal')
    is_read = db.Column(db.Boolean, default=False)
    is_email_sent = db.Column(db.Boolean, default=False)

    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)

    extra_data = db.Column(db.Text, nullable=True)  # JSON data

    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
    document = db.relationship('Document', backref=db.backref('notifications', lazy='dynamic'))
    task = db.relationship('Task', backref=db.backref('notifications', lazy='dynamic'))

    # types dispo
    NOTIFICATION_TYPES = {
        'task_due': 'Tache a echeance',
        'task_overdue': 'Tache en retard',
        'document_expiry': 'Document expire bientot',
        'document_expired': 'Document expire',
        'document_shared': 'Document partage avec vous',
        'permission_granted': 'Acces accorde',
        'permission_revoked': 'Acces revoque',
        'permission_expiring': 'Acces expire bientot',
        'task_assigned': 'Tache assignee',
        'system': 'Notification systeme',
        'backup_complete': 'Sauvegarde terminee',
        'welcome': 'Bienvenue'
    }

    PRIORITY_COLORS = {
        'low': 'secondary',
        'normal': 'primary',
        'high': 'warning',
        'urgent': 'danger'
    }

    def __repr__(self):
        return f'<Notification {self.id} - {self.type} for user {self.user_id}>'

    @property
    def type_label(self):
        """label type notif"""
        return self.NOTIFICATION_TYPES.get(self.type, self.type)

    @property
    def priority_color(self):
        """couleur bootstrap priorite"""
        return self.PRIORITY_COLORS.get(self.priority, 'primary')

    @property
    def icon(self):
        """icone bootstrap type"""
        icons = {
            'task_due': 'bi-clock',
            'task_overdue': 'bi-exclamation-triangle',
            'document_expiry': 'bi-calendar-x',
            'document_expired': 'bi-file-earmark-x',
            'document_shared': 'bi-share',
            'permission_granted': 'bi-shield-check',
            'permission_revoked': 'bi-shield-x',
            'permission_expiring': 'bi-shield-exclamation',
            'task_assigned': 'bi-person-check',
            'system': 'bi-info-circle',
            'backup_complete': 'bi-cloud-check',
            'welcome': 'bi-hand-wave'
        }
        return icons.get(self.type, 'bi-bell')

    @property
    def is_expired(self):
        """notif expiree ?"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def time_ago(self):
        """temps ecoule depuis creation"""
        delta = datetime.utcnow() - self.created_at
        jours = delta.days
        secondes = delta.seconds

        if jours > 30:
            mois = jours // 30
            return f"{mois} mois"

        if jours > 1:
            return f"{jours} jours"
        if jours == 1:
            return "1 jour"

        heures = secondes // 3600
        if heures > 1:
            return f"{heures} heures"
        if heures == 1:
            return "1 heure"

        minutes = secondes // 60
        if minutes > 1:
            return f"{minutes} minutes"
        if minutes == 1:
            return "1 minute"

        return "A l'instant"

    def mark_as_read(self):
        """marque lue"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()

    def mark_as_unread(self):
        """marque non lue"""
        self.is_read = False
        self.read_at = None

    @staticmethod
    def create_notification(user_id, type, title, message, priority='normal',
                           document_id=None, task_id=None, expires_at=None,
                           extra_data=None):
        """cree notif"""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            priority=priority,
            document_id=document_id,
            task_id=task_id,
            expires_at=expires_at,
            extra_data=extra_data
        )
        db.session.add(notification)
        return notification

    @staticmethod
    def get_unread_count(user_id):
        """nb notifs non lues"""
        return Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).count()

    @staticmethod
    def get_user_notifications(user_id, unread_only=False, limit=50):
        """recup notifs user"""
        query = Notification.query.filter_by(user_id=user_id)

        if unread_only:
            query = query.filter_by(is_read=False)

        # exclure expirees
        query = query.filter(
            db.or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )

        return query.order_by(Notification.created_at.desc()).limit(limit).all()

    @staticmethod
    def mark_all_as_read(user_id):
        """tout marquer lu"""
        Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).update({
            'is_read': True,
            'read_at': datetime.utcnow()
        })
        db.session.commit()

    @staticmethod
    def delete_old_notifications(days=90):
        """supprime notifs lues anciennes"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)

        deleted = Notification.query.filter(
            Notification.is_read == True,
            Notification.created_at < cutoff
        ).delete()

        db.session.commit()
        return deleted

    @staticmethod
    def cleanup_expired():
        """supprime notifs expirees"""
        deleted = Notification.query.filter(
            Notification.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()
        return deleted
