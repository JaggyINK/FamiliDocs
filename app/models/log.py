# modele logs actions
import logging
from datetime import datetime, timedelta
from . import db

logger = logging.getLogger(__name__)

# ============================================================================
# RGPD / CNIL - duree conservation logs
# ============================================================================
# configurable via env, 7j par defaut (dev), 180 en prod
import os
LOG_RETENTION_DAYS = int(os.environ.get('LOG_RETENTION_DAYS', '180'))

# --- PRODUCTION : decommenter ci-dessous ---
# RGPD/CNIL :
# - Logs connextion (login/logout/login_failed) : 6 mois (art. L34-1 CPCE)
# - Logs activite user (document_*, task_*, folder_*) : 12 mois max
# - Logs admin (user_*, permission_*, backup_*) : 12 mois max
# LOG_RETENTION_DAYS = 180  # 6 mois
# ============================================================================


class Log(db.Model):
    """entree journal"""

    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False, index=True)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))  # IPv6
    user_agent = db.Column(db.String(255))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    ACTION_TYPES = {
        'login': 'Connexion',
        'logout': 'Déconnexion',
        'login_failed': 'Échec de connexion',
        'document_view': 'Consultation document',
        'document_download': 'Téléchargement document',
        'document_upload': 'Ajout document',
        'document_edit': 'Modification document',
        'document_delete': 'Suppression document',
        'document_share': 'Partage document',
        'permission_grant': 'Attribution permission',
        'permission_revoke': 'Révocation permission',
        'permission_update': 'Mise à jour permission',
        'user_create': 'Création utilisateur',
        'user_edit': 'Modification utilisateur',
        'user_delete': 'Suppression utilisateur',
        'profile_update': 'Mise à jour profil',
        'avatar_upload': 'Upload avatar',
        'avatar_delete': 'Suppression avatar',
        'folder_create': 'Création dossier',
        'folder_edit': 'Modification dossier',
        'folder_delete': 'Suppression dossier',
        'task_create': 'Création tâche',
        'task_edit': 'Modification tâche',
        'task_complete': 'Tâche terminée',
        'backup_create': 'Sauvegarde créée',
        'backup_restore': 'Restauration effectuée',
        'document_review': 'Révision document',
        'desktop_app_download': 'Téléchargement application bureau'
    }

    def __repr__(self):
        return f'<Log {self.action} by user {self.user_id}>'

    @property
    def action_label(self):
        """label action"""
        return self.ACTION_TYPES.get(self.action, self.action)

    @staticmethod
    def create_log(user_id, action, document_id=None, details=None,
                   ip_address=None, user_agent=None):
        """cree entree log"""
        log = Log(
            user_id=user_id,
            action=action,
            document_id=document_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        return log

    @staticmethod
    def get_user_logs(user_id, limit=100):
        """recup logs user"""
        return Log.query.filter_by(user_id=user_id)\
            .order_by(Log.created_at.desc())\
            .limit(limit)\
            .all()

    @staticmethod
    def get_document_logs(document_id, limit=50):
        """recup logs doc"""
        return Log.query.filter_by(document_id=document_id)\
            .order_by(Log.created_at.desc())\
            .limit(limit)\
            .all()

    @staticmethod
    def get_recent_logs(limit=100):
        """recup derniers logs (admin)"""
        return Log.query.order_by(Log.created_at.desc())\
            .limit(limit)\
            .all()

    @staticmethod
    def cleanup_old_logs(retention_days=None):
        """supprime vieux logs (RGPD)"""
        if retention_days is None:
            retention_days = LOG_RETENTION_DAYS
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        deleted = Log.query.filter(Log.created_at < cutoff_date).delete()
        db.session.commit()
        if deleted > 0:
            logger.info(f"RGPD: {deleted} log(s) supprimes (anterieurs au {cutoff_date.strftime('%d/%m/%Y')})")
        return deleted
