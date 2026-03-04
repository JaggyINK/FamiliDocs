"""
Service de planification des taches automatiques
FamiliDocs - Scheduler daemon thread
"""
import threading
import logging
import schedule
import time

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service de planification des taches periodiques"""

    _thread = None
    _running = False

    @staticmethod
    def start(app):
        """Demarre le scheduler dans un thread daemon"""
        if SchedulerService._running:
            return

        SchedulerService._running = True

        # Planifier les jobs
        schedule.every(1).hours.do(SchedulerService._check_deadlines, app)
        schedule.every().day.at("02:00").do(SchedulerService._cleanup_notifications, app)
        schedule.every().day.at("03:00").do(SchedulerService._cleanup_expired_permissions, app)

        # Lancer le thread daemon
        SchedulerService._thread = threading.Thread(
            target=SchedulerService._run_loop,
            daemon=True,
            name="familidocs-scheduler"
        )
        SchedulerService._thread.start()
        logger.info("Scheduler demarre avec succes")

    @staticmethod
    def _run_loop():
        """Boucle principale du scheduler"""
        while SchedulerService._running:
            schedule.run_pending()
            time.sleep(60)

    @staticmethod
    def stop():
        """Arrete le scheduler"""
        SchedulerService._running = False
        schedule.clear()

    @staticmethod
    def _check_deadlines(app):
        """Verifie les echeances de taches et documents"""
        try:
            with app.app_context():
                from app.services.notification_service import NotificationService
                count = NotificationService.check_and_create_due_notifications()
                if count > 0:
                    logger.info(f"Scheduler: {count} notification(s) d'echeance creee(s)")
        except Exception as e:
            logger.error(f"Scheduler erreur check_deadlines: {e}")

    @staticmethod
    def _cleanup_notifications(app):
        """Nettoie les anciennes notifications"""
        try:
            with app.app_context():
                from app.services.notification_service import NotificationService
                result = NotificationService.cleanup()
                logger.info(f"Scheduler: cleanup notifications - {result}")
        except Exception as e:
            logger.error(f"Scheduler erreur cleanup_notifications: {e}")

    @staticmethod
    def _cleanup_expired_permissions(app):
        """Nettoie les permissions expirees"""
        try:
            with app.app_context():
                from app.models.permission import Permission
                from app.models import db
                from datetime import date
                expired = Permission.query.filter(
                    Permission.end_date < date.today()
                ).delete()
                db.session.commit()
                if expired > 0:
                    logger.info(f"Scheduler: {expired} permission(s) expiree(s) supprimee(s)")
        except Exception as e:
            logger.error(f"Scheduler erreur cleanup_permissions: {e}")
