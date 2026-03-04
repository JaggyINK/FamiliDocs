"""
Tests d'integration pour FamiliDocs
Workflows complets : inscription -> document -> partage -> tache
"""
import pytest
from datetime import date, timedelta

from app.models import db as _db
from app.models.user import User
from app.models.document import Document
from app.models.task import Task
from app.models.folder import Folder
from app.models.family import Family, FamilyMember
from app.models.permission import Permission
from app.models.notification import Notification
from app.services.auth_service import AuthService
from app.services.document_service import DocumentService
from app.services.permission_service import PermissionService
from app.services.notification_service import NotificationService

db = _db


class TestUserWorkflow:
    """Test du workflow complet d'un utilisateur"""

    def test_register_creates_user_with_folders(self, app):
        """L'inscription cree un utilisateur avec dossiers par defaut"""
        success, user = AuthService.register_user(
            email='workflow@test.local',
            username='workflowuser',
            password='Workflow123!',
            first_name='Workflow',
            last_name='Test'
        )
        assert success is True

        # Verifier les dossiers par defaut
        folders = Folder.query.filter_by(owner_id=user.id).all()
        assert len(folders) == 5

        folder_names = [f.name for f in folders]
        assert 'Administratif' in folder_names
        assert 'Sante' in folder_names
        assert 'Banque' in folder_names
        assert 'Logement' in folder_names
        assert 'Autres' in folder_names


class TestDocumentSharingWorkflow:
    """Test du workflow complet de partage de document"""

    def test_share_document_creates_permission(self, test_user, test_document, second_user, app):
        """Le partage cree une permission"""
        with app.test_request_context():
            success, result = PermissionService.grant_permission(
                document_id=test_document.id,
                user_id=second_user.id,
                granted_by=test_user.id,
                can_edit=False,
                can_download=True
            )
            assert success is True

            # Verifier que la permission existe
            perm = Permission.query.filter_by(
                document_id=test_document.id,
                user_id=second_user.id
            ).first()
            assert perm is not None
            assert perm.can_download is True
            assert perm.can_edit is False

    def test_shared_user_can_access(self, test_user, test_document, second_user, app):
        """L'utilisateur avec permission peut acceder"""
        with app.test_request_context():
            PermissionService.grant_permission(
                document_id=test_document.id,
                user_id=second_user.id,
                granted_by=test_user.id
            )

            assert second_user.can_access_document(test_document) is True

    def test_revoke_removes_access(self, test_user, test_document, second_user, app):
        """La revocation supprime l'acces"""
        with app.test_request_context():
            PermissionService.grant_permission(
                document_id=test_document.id,
                user_id=second_user.id,
                granted_by=test_user.id
            )
            assert second_user.can_access_document(test_document) is True

            PermissionService.revoke_permission(
                document_id=test_document.id,
                user_id=second_user.id,
                revoked_by=test_user.id
            )
            assert second_user.can_access_document(test_document) is False

    def test_share_multiple_users(self, test_user, test_document, app):
        """Partage avec plusieurs utilisateurs"""
        users = []
        for i in range(3):
            u = User(
                email=f'multi{i}@test.local',
                username=f'multi{i}',
                password_hash=AuthService.hash_password('Test123!'),
                first_name=f'Multi{i}',
                last_name='User',
                role='user'
            )
            db.session.add(u)
            users.append(u)
        db.session.flush()

        with app.test_request_context():
            success, msg = PermissionService.grant_multiple_permissions(
                document_id=test_document.id,
                user_ids=[u.id for u in users],
                granted_by=test_user.id
            )
            assert success is True
            assert '3' in msg

    def test_share_permission_90_day_limit(self, test_user, test_document, second_user, app):
        """Limite de 90 jours sur les permissions"""
        with app.test_request_context():
            far_future = date.today() + timedelta(days=365)
            success, msg = PermissionService.grant_multiple_permissions(
                document_id=test_document.id,
                user_ids=[second_user.id],
                granted_by=test_user.id,
                end_date=far_future
            )
            assert success is True

            perm = Permission.query.filter_by(
                document_id=test_document.id,
                user_id=second_user.id
            ).first()
            max_date = date.today() + timedelta(days=90)
            assert perm.end_date <= max_date


class TestFamilyWorkflow:
    """Test du workflow familial"""

    def test_create_family_and_add_member(self, test_user, second_user):
        """Creation de famille et ajout de membre"""
        family = Family(
            name='Ma Famille',
            description='Test',
            creator_id=test_user.id
        )
        db.session.add(family)
        db.session.flush()

        # Createur comme admin
        member1 = FamilyMember(
            family_id=family.id,
            user_id=test_user.id,
            role='chef_famille'
        )
        db.session.add(member1)

        # Ajouter un membre
        member2 = FamilyMember(
            family_id=family.id,
            user_id=second_user.id,
            role='parent',
            invited_by=test_user.id
        )
        db.session.add(member2)
        db.session.flush()

        assert family.member_count == 2
        assert family.is_member(second_user.id) is True
        assert family.can_manage(test_user.id) is True

    def test_family_role_management(self, test_user, second_user):
        """Gestion des roles familiaux"""
        family = Family(
            name='Famille Roles',
            creator_id=test_user.id
        )
        db.session.add(family)
        db.session.flush()

        # Lecteur ne peut pas gerer
        member = FamilyMember(
            family_id=family.id,
            user_id=second_user.id,
            role='lecteur'
        )
        db.session.add(member)
        db.session.flush()

        assert family.can_manage(second_user.id) is False
        assert family.get_member_role(second_user.id) == 'lecteur'


class TestTaskDocumentWorkflow:
    """Test du workflow tache-document"""

    def test_document_with_expiry_creates_task(self, test_user, test_folder, app):
        """Un document avec echeance genere une tache"""
        expiry = date.today() + timedelta(days=60)
        doc = Document(
            name='Passeport',
            original_filename='passeport.pdf',
            stored_filename='passport_xyz.pdf',
            file_type='pdf',
            file_size=1024,
            owner_id=test_user.id,
            folder_id=test_folder.id,
            expiry_date=expiry
        )
        db.session.add(doc)
        db.session.flush()

        task = Task.create_from_document(doc, title='Renouveler passeport')
        db.session.add(task)
        db.session.flush()

        assert task.document_id == doc.id
        assert task.due_date == expiry
        assert task.owner_id == test_user.id

    def test_task_lifecycle(self, test_user):
        """Cycle de vie complet d'une tache"""
        task = Task(
            title='Lifecycle Test',
            due_date=date.today() + timedelta(days=10),
            owner_id=test_user.id
        )
        db.session.add(task)
        db.session.flush()

        # Pending -> In Progress -> Completed
        assert task.status == 'pending'

        task.mark_in_progress()
        assert task.status == 'in_progress'

        task.mark_completed()
        assert task.status == 'completed'
        assert task.completed_at is not None
        assert task.is_overdue is False


class TestNotificationWorkflow:
    """Test du workflow de notifications"""

    def test_notification_lifecycle(self, test_user):
        """Cycle de vie complet d'une notification"""
        # Creation
        notif = Notification.create_notification(
            user_id=test_user.id,
            type='system',
            title='Test Lifecycle',
            message='Message de test'
        )
        db.session.flush()

        # Verifier non lue
        assert notif.is_read is False
        count = Notification.get_unread_count(test_user.id)
        assert count >= 1

        # Marquer comme lue
        notif.mark_as_read()
        db.session.flush()
        assert notif.is_read is True

        # Verifier compteur
        new_count = Notification.get_unread_count(test_user.id)
        assert new_count == count - 1

    def test_share_triggers_notification(self, test_user, test_document, second_user):
        """Le partage declenche une notification"""
        notif = NotificationService.notify_document_shared(
            test_document, second_user.id, test_user
        )
        assert notif.user_id == second_user.id
        assert notif.type == 'document_shared'
        assert test_document.name in notif.message


class TestPermissionCheckWorkflow:
    """Test des verifications de permissions"""

    def test_owner_has_all_permissions(self, test_user, test_document, app):
        """Le proprietaire a toutes les permissions"""
        with app.test_request_context():
            assert PermissionService.check_permission(
                test_document.id, test_user.id, 'view') is True
            assert PermissionService.check_permission(
                test_document.id, test_user.id, 'edit') is True
            assert PermissionService.check_permission(
                test_document.id, test_user.id, 'download') is True
            assert PermissionService.check_permission(
                test_document.id, test_user.id, 'share') is True

    def test_admin_has_all_permissions(self, admin_user, test_document, app):
        """L'admin a toutes les permissions"""
        with app.test_request_context():
            assert PermissionService.check_permission(
                test_document.id, admin_user.id, 'view') is True
            assert PermissionService.check_permission(
                test_document.id, admin_user.id, 'edit') is True

    def test_no_permission_by_default(self, second_user, test_document, app):
        """Pas de permission par defaut"""
        with app.test_request_context():
            assert PermissionService.check_permission(
                test_document.id, second_user.id, 'view') is False

    def test_granular_permissions(self, test_user, test_document, second_user, app):
        """Permissions granulaires : view oui, edit non"""
        with app.test_request_context():
            PermissionService.grant_permission(
                document_id=test_document.id,
                user_id=second_user.id,
                granted_by=test_user.id,
                can_edit=False,
                can_download=True,
                can_share=False
            )

            assert PermissionService.check_permission(
                test_document.id, second_user.id, 'view') is True
            assert PermissionService.check_permission(
                test_document.id, second_user.id, 'download') is True
            assert PermissionService.check_permission(
                test_document.id, second_user.id, 'edit') is False
            assert PermissionService.check_permission(
                test_document.id, second_user.id, 'share') is False

    def test_expired_permission_denied(self, test_user, test_document, second_user, app):
        """Permission expiree = acces refuse"""
        perm = Permission(
            document_id=test_document.id,
            user_id=second_user.id,
            granted_by=test_user.id,
            end_date=date.today() - timedelta(days=1)
        )
        db.session.add(perm)
        db.session.flush()

        with app.test_request_context():
            assert PermissionService.check_permission(
                test_document.id, second_user.id, 'view') is False
