"""
Modele Notification - Gestion des notifications utilisateurs
FamiliDocs v2.0 - Amelioration BTS SIO SLAM
"""
from datetime import datetime
from . import db


class Notification(db.Model):
    """Modele representant une notification utilisateur"""

    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Type de notification
    type = db.Column(db.String(50), nullable=False)  # task_due, document_expiry, share, system
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)

    # Priorite et statut
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    is_read = db.Column(db.Boolean, default=False)
    is_email_sent = db.Column(db.Boolean, default=False)

    # References optionnelles
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)

    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)  # Notification auto-supprimee apres

    # Donnees supplementaires (JSON)
    extra_data = db.Column(db.Text, nullable=True)  # JSON pour donnees flexibles

    # Relations
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
    document = db.relationship('Document', backref=db.backref('notifications', lazy='dynamic'))
    task = db.relationship('Task', backref=db.backref('notifications', lazy='dynamic'))

    # Types de notifications disponibles
    NOTIFICATION_TYPES = {
        'task_due': 'Tache a echeance',
        'task_overdue': 'Tache en retard',
        'document_expiry': 'Document expire bientot',
        'document_expired': 'Document expire',
        'document_shared': 'Document partage avec vous',
        'permission_granted': 'Acces accorde',
        'permission_revoked': 'Acces revoque',
        'permission_expiring': 'Acces expire bientot',
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
        """Retourne le libelle du type de notification"""
        return self.NOTIFICATION_TYPES.get(self.type, self.type)

    @property
    def priority_color(self):
        """Retourne la couleur Bootstrap associee a la priorite"""
        return self.PRIORITY_COLORS.get(self.priority, 'primary')

    @property
    def icon(self):
        """Retourne l'icone Bootstrap associee au type"""
        icons = {
            'task_due': 'bi-clock',
            'task_overdue': 'bi-exclamation-triangle',
            'document_expiry': 'bi-calendar-x',
            'document_expired': 'bi-file-earmark-x',
            'document_shared': 'bi-share',
            'permission_granted': 'bi-shield-check',
            'permission_revoked': 'bi-shield-x',
            'permission_expiring': 'bi-shield-exclamation',
            'system': 'bi-info-circle',
            'backup_complete': 'bi-cloud-check',
            'welcome': 'bi-hand-wave'
        }
        return icons.get(self.type, 'bi-bell')

    @property
    def is_expired(self):
        """Verifie si la notification a expire"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def time_ago(self):
        """Retourne le temps ecoule depuis la creation"""
        delta = datetime.utcnow() - self.created_at

        if delta.days > 30:
            return f"{delta.days // 30} mois"
        elif delta.days > 0:
            return f"{delta.days} jour{'s' if delta.days > 1 else ''}"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} heure{'s' if hours > 1 else ''}"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return "A l'instant"

    def mark_as_read(self):
        """Marque la notification comme lue"""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()

    def mark_as_unread(self):
        """Marque la notification comme non lue"""
        self.is_read = False
        self.read_at = None

    @staticmethod
    def create_notification(user_id, type, title, message, priority='normal',
                           document_id=None, task_id=None, expires_at=None,
                           extra_data=None):
        """Cree une nouvelle notification"""
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
        """Retourne le nombre de notifications non lues"""
        return Notification.query.filter_by(
            user_id=user_id,
            is_read=False
        ).count()

    @staticmethod
    def get_user_notifications(user_id, unread_only=False, limit=50):
        """Recupere les notifications d'un utilisateur"""
        query = Notification.query.filter_by(user_id=user_id)

        if unread_only:
            query = query.filter_by(is_read=False)

        # Exclure les notifications expirees
        query = query.filter(
            db.or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )

        return query.order_by(Notification.created_at.desc()).limit(limit).all()

    @staticmethod
    def mark_all_as_read(user_id):
        """Marque toutes les notifications d'un utilisateur comme lues"""
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
        """Supprime les notifications lues de plus de X jours"""
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
        """Supprime les notifications expirees"""
        deleted = Notification.query.filter(
            Notification.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()
        return deleted
