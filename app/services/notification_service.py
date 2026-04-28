# service notifs
import os
from datetime import datetime, timedelta
import json
import logging
import smtplib
from email.mime.text import MIMEText

from app.models import db

logger = logging.getLogger(__name__)
from app.models.notification import Notification
from app.models.task import Task
from app.models.document import Document
from app.models.permission import Permission
from app.models.user import User


class NotificationService:
    """gest notifs"""

    # cfg email (env vars)
    EMAIL_ENABLED = os.environ.get('EMAIL_ENABLED', 'false').lower() == 'true'
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
    SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@familidocs.local')

    @staticmethod
    def notify_task_due(task, days_before=0):
        """notif tache echeance"""
        if days_before == 0:
            title = f"Tache a faire aujourd'hui : {task.title}"
            message = f"La tache '{task.title}' arrive a echeance aujourd'hui."
            notif_type = 'task_due'
            priority = 'high'
        elif days_before < 0:
            title = f"Tache en retard : {task.title}"
            message = f"La tache '{task.title}' est en retard de {abs(days_before)} jour(s)."
            notif_type = 'task_overdue'
            priority = 'urgent'
        else:
            title = f"Tache a venir : {task.title}"
            message = f"La tache '{task.title}' arrive a echeance dans {days_before} jour(s)."
            notif_type = 'task_due'
            priority = 'normal' if days_before > 3 else 'high'

        notification = Notification.create_notification(
            user_id=task.owner_id,
            type=notif_type,
            title=title,
            message=message,
            priority=priority,
            task_id=task.id,
            document_id=task.document_id,
            extra_data=json.dumps({'due_date': task.due_date.isoformat()})
        )

        db.session.commit()

        # Envoi email si active
        if NotificationService.EMAIL_ENABLED:
            user = User.query.get(task.owner_id)
            NotificationService._send_email_notification(user.email, title, message)

        return notification

    @staticmethod
    def notify_document_expiry(document, days_before=0):
        """notif doc expire"""
        if days_before == 0:
            title = f"Document expire aujourd'hui : {document.name}"
            message = f"Le document '{document.name}' expire aujourd'hui."
            notif_type = 'document_expired'
            priority = 'urgent'
        elif days_before < 0:
            title = f"Document expire : {document.name}"
            message = f"Le document '{document.name}' a expire il y a {abs(days_before)} jour(s)."
            notif_type = 'document_expired'
            priority = 'urgent'
        else:
            title = f"Document expire bientot : {document.name}"
            message = f"Le document '{document.name}' expire dans {days_before} jour(s)."
            notif_type = 'document_expiry'
            priority = 'high' if days_before <= 7 else 'normal'

        notification = Notification.create_notification(
            user_id=document.owner_id,
            type=notif_type,
            title=title,
            message=message,
            priority=priority,
            document_id=document.id,
            extra_data=json.dumps({'expiry_date': document.expiry_date.isoformat()})
        )

        db.session.commit()
        return notification

    @staticmethod
    def notify_document_shared(document, shared_with_user_id, shared_by_user):
        """notif doc partage"""
        notification = Notification.create_notification(
            user_id=shared_with_user_id,
            type='document_shared',
            title=f"Nouveau document partage",
            message=f"{shared_by_user.full_name} a partage le document '{document.name}' avec vous.",
            priority='normal',
            document_id=document.id,
            extra_data=json.dumps({'shared_by': shared_by_user.id})
        )

        db.session.commit()
        return notification

    @staticmethod
    def notify_permission_granted(permission, granting_user):
        """notif perm accordee"""
        document = Document.query.get(permission.document_id)
        user = User.query.get(permission.user_id)

        rights = []
        if permission.can_view:
            rights.append("lecture")
        if permission.can_edit:
            rights.append("modification")
        if permission.can_download:
            rights.append("telechargement")
        if permission.can_share:
            rights.append("partage")

        notification = Notification.create_notification(
            user_id=permission.user_id,
            type='permission_granted',
            title=f"Acces accorde : {document.name}",
            message=f"{granting_user.full_name} vous a accorde l'acces au document '{document.name}' (droits: {', '.join(rights)}).",
            priority='normal',
            document_id=permission.document_id,
            extra_data=json.dumps({
                'rights': rights,
                'end_date': permission.end_date.isoformat() if permission.end_date else None
            })
        )

        db.session.commit()
        return notification

    @staticmethod
    def notify_permission_revoked(document, revoked_user_id, revoking_user):
        """notif perm revoquee"""
        notification = Notification.create_notification(
            user_id=revoked_user_id,
            type='permission_revoked',
            title=f"Acces revoque : {document.name}",
            message=f"Votre acces au document '{document.name}' a ete revoque par {revoking_user.full_name}.",
            priority='high',
            document_id=document.id
        )

        db.session.commit()
        return notification

    @staticmethod
    def notify_permission_expiring(permission, days_before):
        """notif perm expire bientot"""
        document = Document.query.get(permission.document_id)

        notification = Notification.create_notification(
            user_id=permission.user_id,
            type='permission_expiring',
            title=f"Acces expire bientot : {document.name}",
            message=f"Votre acces au document '{document.name}' expire dans {days_before} jour(s).",
            priority='normal',
            document_id=permission.document_id,
            extra_data=json.dumps({'end_date': permission.end_date.isoformat()})
        )

        db.session.commit()
        return notification

    @staticmethod
    def notify_task_assigned(task, assigned_by_user):
        """notif tache assignee"""
        notification = Notification.create_notification(
            user_id=task.assigned_to_id,
            type='task_assigned',
            title=f"Nouvelle tache assignee : {task.title}",
            message=f"{assigned_by_user.full_name} vous a assigne la tache '{task.title}' a faire avant le {task.due_date.strftime('%d/%m/%Y')}.",
            priority='normal',
            task_id=task.id,
            extra_data=json.dumps({'assigned_by': assigned_by_user.id})
        )

        db.session.commit()
        return notification

    @staticmethod
    def notify_welcome(user):
        """notif bienvenue"""
        notification = Notification.create_notification(
            user_id=user.id,
            type='welcome',
            title=f"Bienvenue sur FamiliDocs, {user.first_name} !",
            message="Votre compte a ete cree avec succes. Commencez par ajouter vos premiers documents.",
            priority='low',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )

        db.session.commit()
        return notification

    @staticmethod
    def notify_backup_complete(user_id, backup_filename):
        """notif backup ok"""
        notification = Notification.create_notification(
            user_id=user_id,
            type='backup_complete',
            title="Sauvegarde terminee",
            message=f"La sauvegarde '{backup_filename}' a ete creee avec succes.",
            priority='low',
            expires_at=datetime.utcnow() + timedelta(days=3)
        )

        db.session.commit()
        return notification

    @staticmethod
    def notify_system(user_id, title, message, priority='normal'):
        """cree notif systeme"""
        notification = Notification.create_notification(
            user_id=user_id,
            type='system',
            title=title,
            message=message,
            priority=priority
        )

        db.session.commit()
        return notification

    @staticmethod
    def check_and_create_due_notifications():
        """check echeances + cree notifs (cron)"""
        today = datetime.utcnow().date()
        notifications_created = 0

        # Verifier les taches
        tasks = Task.query.filter(
            Task.status.notin_(['completed', 'cancelled'])
        ).all()

        for task in tasks:
            days_diff = (task.due_date - today).days

            # Verifier si notification deja envoyee aujourd'hui pour cette tache
            existing = Notification.query.filter(
                Notification.task_id == task.id,
                Notification.type.in_(['task_due', 'task_overdue']),
                db.func.date(Notification.created_at) == today
            ).first()

            if existing:
                continue

            # Creer notification selon l'echeance
            if days_diff < 0:  # En retard
                NotificationService.notify_task_due(task, days_diff)
                notifications_created += 1
            elif days_diff == 0:  # Aujourd'hui
                NotificationService.notify_task_due(task, 0)
                notifications_created += 1
            elif days_diff <= task.reminder_days:  # Dans les jours de rappel
                NotificationService.notify_task_due(task, days_diff)
                notifications_created += 1

        # Verifier les documents avec echeance
        documents = Document.query.filter(
            Document.expiry_date.isnot(None)
        ).all()

        for doc in documents:
            days_diff = (doc.expiry_date - today).days

            # Verifier si notification deja envoyee
            existing = Notification.query.filter(
                Notification.document_id == doc.id,
                Notification.type.in_(['document_expiry', 'document_expired']),
                db.func.date(Notification.created_at) == today
            ).first()

            if existing:
                continue

            # Creer notification si dans les 30 jours ou expire
            if days_diff < 0:  # Expire
                NotificationService.notify_document_expiry(doc, days_diff)
                notifications_created += 1
            elif days_diff <= 30:  # Expire dans 30 jours ou moins
                NotificationService.notify_document_expiry(doc, days_diff)
                notifications_created += 1

        # Verifier les permissions qui expirent
        permissions = Permission.query.filter(
            Permission.end_date.isnot(None)
        ).all()

        for perm in permissions:
            days_diff = (perm.end_date - today).days

            if 0 < days_diff <= 7:  # Expire dans 7 jours ou moins
                existing = Notification.query.filter(
                    Notification.document_id == perm.document_id,
                    Notification.user_id == perm.user_id,
                    Notification.type == 'permission_expiring',
                    db.func.date(Notification.created_at) == today
                ).first()

                if not existing:
                    NotificationService.notify_permission_expiring(perm, days_diff)
                    notifications_created += 1

        return notifications_created

    @staticmethod
    def _send_email_notification(to_email, subject, body):
        """envoi email (simule en dev)"""
        if not NotificationService.EMAIL_ENABLED:
            logger.info(f"[EMAIL SIMULE] To: {to_email}, Subject: {subject}")
            return True

        try:
            msg = MIMEText(f"FamiliDocs\n\n{subject}\n\n{body}")
            msg['From'] = NotificationService.SENDER_EMAIL
            msg['To'] = to_email
            msg['Subject'] = f"[FamiliDocs] {subject}"

            with smtplib.SMTP(NotificationService.SMTP_SERVER, NotificationService.SMTP_PORT) as server:
                server.starttls()
                server.login(NotificationService.SMTP_USER, NotificationService.SMTP_PASSWORD)
                server.send_message(msg)
            return True
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
            return False

    @staticmethod
    def get_notification_summary(user_id):
        """resume notifs dashboard"""
        unread_count = Notification.get_unread_count(user_id)

        urgent_count = Notification.query.filter_by(
            user_id=user_id,
            is_read=False,
            priority='urgent'
        ).count()

        high_count = Notification.query.filter_by(
            user_id=user_id,
            is_read=False,
            priority='high'
        ).count()

        recent = Notification.get_user_notifications(user_id, limit=5)

        return {
            'unread_count': unread_count,
            'urgent_count': urgent_count,
            'high_count': high_count,
            'recent': recent
        }

    @staticmethod
    def cleanup():
        """cleanup vieilles notifs"""
        expired = Notification.cleanup_expired()
        old = Notification.delete_old_notifications(days=90)
        return {'expired_deleted': expired, 'old_deleted': old}
