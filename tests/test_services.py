"""
Tests pour les services de FamiliDocs
Couverture : AuthService, DocumentService, PermissionService, NotificationService
"""
import pytest
import os
import tempfile
from io import BytesIO
from datetime import date, datetime, timedelta

from app.models import db as _db
from app.models.user import User
from app.models.document import Document
from app.models.task import Task
from app.models.folder import Folder
from app.models.permission import Permission
from app.models.notification import Notification
from app.services.auth_service import AuthService
from app.services.document_service import DocumentService
from app.services.notification_service import NotificationService

db = _db


# ============================================================
# Tests AuthService
# ============================================================
class TestAuthService:
    """Tests pour le service d'authentification"""

    def test_hash_password(self):
        """Hash de mot de passe"""
        hashed = AuthService.hash_password('Test123!')
        assert hashed != 'Test123!'
        assert len(hashed) > 50

    def test_verify_password_correct(self):
        """Verification mot de passe correct"""
        hashed = AuthService.hash_password('Test123!')
        assert AuthService.verify_password('Test123!', hashed) is True

    def test_verify_password_incorrect(self):
        """Verification mot de passe incorrect"""
        hashed = AuthService.hash_password('Test123!')
        assert AuthService.verify_password('Wrong123!', hashed) is False

    def test_validate_password_valid(self):
        """Mot de passe valide"""
        valid, msg = AuthService.validate_password('Test123!')
        assert valid is True

    def test_validate_password_too_short(self):
        """Mot de passe trop court"""
        valid, msg = AuthService.validate_password('Ab1!')
        assert valid is False
        assert '8' in msg

    def test_validate_password_no_uppercase(self):
        """Sans majuscule"""
        valid, msg = AuthService.validate_password('test1234!')
        assert valid is False
        assert 'majuscule' in msg

    def test_validate_password_no_lowercase(self):
        """Sans minuscule"""
        valid, msg = AuthService.validate_password('ABCDEF1!')
        assert valid is False
        assert 'minuscule' in msg

    def test_validate_password_no_digit(self):
        """Sans chiffre"""
        valid, msg = AuthService.validate_password('TestTest!')
        assert valid is False
        assert 'chiffre' in msg

    def test_validate_password_no_special(self):
        """Sans caractere special"""
        valid, msg = AuthService.validate_password('TestTest1')
        assert valid is False

    def test_register_user_success(self, app):
        """Inscription reussie"""
        success, result = AuthService.register_user(
            email='register@test.local',
            username='registeruser',
            password='Register123!',
            first_name='Register',
            last_name='Test'
        )
        assert success is True
        assert isinstance(result, User)
        assert result.email == 'register@test.local'

    def test_register_user_duplicate_email(self, test_user):
        """Email deja utilise"""
        success, msg = AuthService.register_user(
            email='test@familidocs.local',
            username='newname',
            password='Test123!',
            first_name='New',
            last_name='User'
        )
        assert success is False
        assert 'email' in msg.lower()

    def test_register_user_duplicate_username(self, test_user):
        """Username deja utilise"""
        success, msg = AuthService.register_user(
            email='new@test.local',
            username='testuser',
            password='Test123!',
            first_name='New',
            last_name='User'
        )
        assert success is False
        assert 'utilisateur' in msg.lower()

    def test_register_user_weak_password(self, app):
        """Mot de passe trop faible"""
        success, msg = AuthService.register_user(
            email='weak@test.local',
            username='weakuser',
            password='weak',
            first_name='Weak',
            last_name='User'
        )
        assert success is False

    def test_register_creates_default_folders(self, app):
        """L'inscription cree les dossiers par defaut"""
        success, user = AuthService.register_user(
            email='folders@test.local',
            username='folderuser',
            password='Folders123!',
            first_name='Folder',
            last_name='User'
        )
        assert success is True
        folders = Folder.query.filter_by(owner_id=user.id).all()
        assert len(folders) == 5

    def test_rate_limit_allows_initial(self):
        """Premieres tentatives autorisees"""
        AuthService._failed_attempts.clear()
        allowed, msg = AuthService._check_rate_limit('127.0.0.1')
        assert allowed is True

    def test_rate_limit_blocks_after_max(self):
        """Blocage apres max tentatives"""
        AuthService._failed_attempts.clear()
        ip = '10.10.10.10'
        for _ in range(AuthService.MAX_LOGIN_ATTEMPTS):
            AuthService._record_failed_attempt(ip)
        allowed, msg = AuthService._check_rate_limit(ip)
        assert allowed is False
        assert 'Trop de tentatives' in msg

    def test_rate_limit_clears_on_success(self):
        """Reinitialisation apres succes"""
        AuthService._failed_attempts.clear()
        ip = '10.10.10.11'
        AuthService._record_failed_attempt(ip)
        AuthService._record_failed_attempt(ip)
        assert ip in AuthService._failed_attempts
        AuthService._clear_failed_attempts(ip)
        assert ip not in AuthService._failed_attempts


# ============================================================
# Tests DocumentService
# ============================================================
class TestDocumentService:
    """Tests pour le service Document"""

    def test_allowed_file_pdf(self, app):
        """PDF autorise"""
        with app.app_context():
            assert DocumentService.allowed_file('doc.pdf') is True

    def test_allowed_file_image(self, app):
        """Image autorisee"""
        with app.app_context():
            assert DocumentService.allowed_file('photo.jpg') is True
            assert DocumentService.allowed_file('photo.png') is True

    def test_allowed_file_invalid(self, app):
        """Fichier non autorise"""
        with app.app_context():
            assert DocumentService.allowed_file('virus.exe') is False

    def test_allowed_file_no_extension(self, app):
        """Fichier sans extension"""
        with app.app_context():
            assert DocumentService.allowed_file('noext') is False

    def test_generate_stored_filename(self, app):
        """Generation nom unique"""
        with app.app_context():
            name = DocumentService.generate_stored_filename('test.pdf')
            assert name.endswith('.pdf')
            assert len(name) > 10

    def test_generate_stored_filename_unique(self, app):
        """Noms uniques"""
        with app.app_context():
            n1 = DocumentService.generate_stored_filename('a.pdf')
            n2 = DocumentService.generate_stored_filename('a.pdf')
            assert n1 != n2

    def test_get_file_type(self, app):
        """Detection du type de fichier"""
        with app.app_context():
            assert DocumentService.get_file_type('doc.pdf') == 'pdf'
            assert DocumentService.get_file_type('img.png') == 'image'
            assert DocumentService.get_file_type('data.xlsx') == 'excel'
            assert DocumentService.get_file_type('text.txt') == 'text'
            assert DocumentService.get_file_type('doc.docx') == 'word'
            assert DocumentService.get_file_type('unknown.xyz') == 'other'
            assert DocumentService.get_file_type('noext') == 'other'

    def test_get_user_documents(self, test_user, test_document):
        """Recuperation des documents"""
        docs = DocumentService.get_user_documents(test_user.id)
        assert len(docs) >= 1

    def test_get_user_documents_search(self, test_user, test_document):
        """Recherche de documents"""
        docs = DocumentService.get_user_documents(test_user.id, search='Test')
        assert len(docs) >= 1

    def test_get_user_documents_no_results(self, test_user):
        """Recherche sans resultats"""
        docs = DocumentService.get_user_documents(test_user.id, search='xxxxxxxxx')
        assert len(docs) == 0

    def test_update_document(self, test_user, test_document):
        """Mise a jour d'un document"""
        success, msg = DocumentService.update_document(
            document=test_document,
            name='Nouveau Nom',
            user=test_user
        )
        assert success is True
        assert test_document.name == 'Nouveau Nom'

    def test_update_document_confidentiality(self, test_user, test_document):
        """Mise a jour de la confidentialite"""
        success, msg = DocumentService.update_document(
            document=test_document,
            confidentiality='public',
            user=test_user
        )
        assert success is True
        assert test_document.confidentiality == 'public'


# ============================================================
# Tests NotificationService
# ============================================================
class TestNotificationService:
    """Tests pour le service de notifications"""

    def test_notify_welcome(self, test_user):
        """Notification de bienvenue"""
        notif = NotificationService.notify_welcome(test_user)
        assert notif.type == 'welcome'
        assert test_user.first_name in notif.title

    def test_notify_system(self, test_user):
        """Notification systeme"""
        notif = NotificationService.notify_system(
            test_user.id, 'Titre Test', 'Message test'
        )
        assert notif.type == 'system'
        assert notif.title == 'Titre Test'

    def test_notify_task_due_today(self, test_user):
        """Notification tache du jour"""
        task = Task(
            title='Tache urgente',
            due_date=date.today(),
            owner_id=test_user.id,
            status='pending'
        )
        db.session.add(task)
        db.session.flush()

        notif = NotificationService.notify_task_due(task, 0)
        assert notif.type == 'task_due'
        assert notif.priority == 'high'

    def test_notify_task_overdue(self, test_user):
        """Notification tache en retard"""
        task = Task(
            title='Tache retard',
            due_date=date.today() - timedelta(days=3),
            owner_id=test_user.id,
            status='pending'
        )
        db.session.add(task)
        db.session.flush()

        notif = NotificationService.notify_task_due(task, -3)
        assert notif.type == 'task_overdue'
        assert notif.priority == 'urgent'

    def test_notify_task_upcoming(self, test_user):
        """Notification tache a venir"""
        task = Task(
            title='Tache future',
            due_date=date.today() + timedelta(days=5),
            owner_id=test_user.id,
            status='pending'
        )
        db.session.add(task)
        db.session.flush()

        notif = NotificationService.notify_task_due(task, 5)
        assert notif.type == 'task_due'

    def test_notify_document_expiry(self, test_document):
        """Notification expiration document"""
        test_document.expiry_date = date.today() + timedelta(days=10)
        notif = NotificationService.notify_document_expiry(test_document, 10)
        assert notif.type == 'document_expiry'

    def test_notify_document_expired(self, test_document):
        """Notification document expire"""
        test_document.expiry_date = date.today() - timedelta(days=2)
        notif = NotificationService.notify_document_expiry(test_document, -2)
        assert notif.type == 'document_expired'
        assert notif.priority == 'urgent'

    def test_notify_document_shared(self, test_document, test_user, second_user):
        """Notification de partage"""
        notif = NotificationService.notify_document_shared(
            test_document, second_user.id, test_user
        )
        assert notif.type == 'document_shared'
        assert notif.user_id == second_user.id

    def test_notify_backup_complete(self, test_user):
        """Notification sauvegarde terminee"""
        notif = NotificationService.notify_backup_complete(
            test_user.id, 'backup_2026.zip'
        )
        assert notif.type == 'backup_complete'
        assert 'backup_2026.zip' in notif.message

    def test_get_notification_summary(self, test_user):
        """Resume des notifications"""
        NotificationService.notify_system(test_user.id, 'Test', 'Msg')
        summary = NotificationService.get_notification_summary(test_user.id)
        assert 'unread_count' in summary
        assert 'urgent_count' in summary
        assert 'recent' in summary

    def test_cleanup(self, test_user):
        """Nettoyage des notifications"""
        result = NotificationService.cleanup()
        assert 'expired_deleted' in result
        assert 'old_deleted' in result
