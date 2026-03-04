"""
Tests pour tous les modeles de FamiliDocs
Couverture : User, Document, Task, Folder, Family, Permission, Notification, Log
"""
import pytest
from datetime import date, datetime, timedelta

from app.models import db as _db
from app.models.user import User
from app.models.document import Document
from app.models.task import Task
from app.models.folder import Folder
from app.models.family import Family, FamilyMember, ShareLink
from app.models.permission import Permission
from app.models.notification import Notification
from app.models.log import Log
from app.services.auth_service import AuthService

db = _db


# ============================================================
# Tests User
# ============================================================
class TestUserModel:
    """Tests pour le modele User"""

    def test_create_user(self, test_user):
        """Creation d'un utilisateur"""
        assert test_user.id is not None
        assert test_user.email == 'test@familidocs.local'
        assert test_user.username == 'testuser'
        assert test_user.role == 'user'

    def test_full_name(self, test_user):
        """Propriete full_name"""
        assert test_user.full_name == 'Test User'

    def test_is_admin_false(self, test_user):
        """Un utilisateur standard n'est pas admin"""
        assert test_user.is_admin() is False

    def test_is_admin_true(self, admin_user):
        """Un admin est bien admin"""
        assert admin_user.is_admin() is True

    def test_is_trusted(self, app):
        """Test role trusted"""
        user = User(
            email='trusted@test.local', username='trusted',
            password_hash='hash', first_name='T', last_name='U',
            role='trusted'
        )
        assert user.is_trusted() is True

    def test_initials(self, test_user):
        """Propriete initials"""
        assert test_user.initials == 'TU'

    def test_display_name_without_title(self, test_user):
        """display_name sans titre familial"""
        assert test_user.display_name == 'Test User'

    def test_display_name_with_title(self, test_user):
        """display_name avec titre familial"""
        test_user.family_title = 'Papa'
        assert test_user.display_name == 'Papa (Test)'

    def test_avatar_url_none(self, test_user):
        """avatar_url sans photo"""
        assert test_user.avatar_url is None

    def test_avatar_url_with_photo(self, test_user):
        """avatar_url avec photo"""
        test_user.profile_photo = 'avatar.jpg'
        assert test_user.avatar_url == '/uploads/avatars/avatar.jpg'

    def test_can_access_own_document(self, test_user, test_document):
        """Proprietaire peut acceder a son document"""
        assert test_user.can_access_document(test_document) is True

    def test_admin_can_access_any_document(self, admin_user, test_document):
        """Admin peut acceder a tout document"""
        assert admin_user.can_access_document(test_document) is True

    def test_other_user_cannot_access(self, second_user, test_document):
        """Utilisateur sans permission ne peut pas acceder"""
        assert second_user.can_access_document(test_document) is False

    def test_can_edit_own_document(self, test_user, test_document):
        """Proprietaire peut modifier son document"""
        assert test_user.can_edit_document(test_document) is True

    def test_other_user_cannot_edit(self, second_user, test_document):
        """Utilisateur sans permission ne peut pas modifier"""
        assert second_user.can_edit_document(test_document) is False

    def test_user_repr(self, test_user):
        """Representation string du user"""
        assert 'testuser' in repr(test_user)


# ============================================================
# Tests Document
# ============================================================
class TestDocumentModel:
    """Tests pour le modele Document"""

    def test_create_document(self, test_document):
        """Creation d'un document"""
        assert test_document.id is not None
        assert test_document.name == 'Test Document'
        assert test_document.file_type == 'pdf'

    def test_file_extension(self, test_document):
        """Extension du fichier"""
        assert test_document.file_extension == 'pdf'

    def test_file_extension_no_ext(self, test_user):
        """Extension quand pas d'extension"""
        doc = Document(
            name='NoExt', original_filename='noext',
            stored_filename='x', owner_id=test_user.id
        )
        assert doc.file_extension == ''

    def test_human_readable_size_bytes(self, test_user):
        """Taille en octets"""
        doc = Document(
            name='T', original_filename='t.pdf',
            stored_filename='x', file_size=500, owner_id=test_user.id
        )
        assert '500.0 o' == doc.get_human_readable_size()

    def test_human_readable_size_ko(self, test_document):
        """Taille en Ko"""
        size = test_document.get_human_readable_size()
        assert 'Ko' in size

    def test_human_readable_size_mo(self, test_user):
        """Taille en Mo"""
        doc = Document(
            name='T', original_filename='t.pdf',
            stored_filename='x', file_size=5 * 1024 * 1024, owner_id=test_user.id
        )
        assert 'Mo' in doc.get_human_readable_size()

    def test_human_readable_size_none(self, test_user):
        """Taille inconnue"""
        doc = Document(
            name='T', original_filename='t.pdf',
            stored_filename='x', file_size=None, owner_id=test_user.id
        )
        assert doc.get_human_readable_size() == 'Inconnu'

    def test_human_readable_size_not_mutated(self, test_document):
        """La taille n'est pas mutee apres appel"""
        original_size = test_document.file_size
        test_document.get_human_readable_size()
        assert test_document.file_size == original_size

    def test_is_expired_no_date(self, test_document):
        """Pas expire si pas de date"""
        assert test_document.is_expired is False

    def test_is_expired_future(self, test_document):
        """Pas expire si date future"""
        test_document.expiry_date = date.today() + timedelta(days=30)
        assert test_document.is_expired is False

    def test_is_expired_past(self, test_document):
        """Expire si date passee"""
        test_document.expiry_date = date.today() - timedelta(days=1)
        assert test_document.is_expired is True

    def test_is_expiring_soon(self, test_document):
        """Expire bientot dans les 30 jours"""
        test_document.expiry_date = date.today() + timedelta(days=15)
        assert test_document.is_expiring_soon is True

    def test_not_expiring_soon(self, test_document):
        """N'expire pas bientot si > 30 jours"""
        test_document.expiry_date = date.today() + timedelta(days=60)
        assert test_document.is_expiring_soon is False

    def test_needs_review_no_date(self, test_document):
        """Pas de revision si pas de date"""
        assert test_document.needs_review is False

    def test_needs_review_today(self, test_document):
        """Revision necessaire si date aujourd'hui"""
        test_document.next_review_date = date.today()
        assert test_document.needs_review is True

    def test_review_soon(self, test_document):
        """Revision bientot dans 7 jours"""
        test_document.next_review_date = date.today() + timedelta(days=5)
        assert test_document.review_soon is True

    def test_mark_reviewed(self, test_document):
        """Marquer comme revise"""
        test_document.mark_reviewed()
        assert test_document.last_reviewed_at is not None

    def test_document_repr(self, test_document):
        """Representation string"""
        assert 'Test Document' in repr(test_document)


# ============================================================
# Tests Task
# ============================================================
class TestTaskModel:
    """Tests pour le modele Task"""

    def test_create_task(self, test_task):
        """Creation d'une tache"""
        assert test_task.id is not None
        assert test_task.title == 'Tache de test'
        assert test_task.status == 'pending'

    def test_is_overdue_false(self, test_task):
        """Tache non en retard"""
        assert test_task.is_overdue is False

    def test_is_overdue_true(self, test_user):
        """Tache en retard"""
        task = Task(
            title='Retard', due_date=date.today() - timedelta(days=1),
            owner_id=test_user.id, status='pending'
        )
        assert task.is_overdue is True

    def test_is_overdue_completed(self, test_user):
        """Tache terminee n'est pas en retard"""
        task = Task(
            title='Done', due_date=date.today() - timedelta(days=1),
            owner_id=test_user.id, status='completed'
        )
        assert task.is_overdue is False

    def test_is_due_soon(self, test_task):
        """Tache a echeance bientot"""
        test_task.due_date = date.today() + timedelta(days=2)
        test_task.reminder_days = 3
        assert test_task.is_due_soon is True

    def test_days_until_due(self, test_task):
        """Jours avant echeance"""
        test_task.due_date = date.today() + timedelta(days=5)
        assert test_task.days_until_due == 5

    def test_priority_color(self, test_task):
        """Couleur de priorite"""
        test_task.priority = 'urgent'
        assert test_task.priority_color == 'danger'
        test_task.priority = 'normal'
        assert test_task.priority_color == 'primary'

    def test_status_color(self, test_task):
        """Couleur de statut"""
        assert test_task.status_color == 'secondary'
        test_task.status = 'completed'
        assert test_task.status_color == 'success'

    def test_mark_completed(self, test_task):
        """Marquer comme termine"""
        test_task.mark_completed()
        assert test_task.status == 'completed'
        assert test_task.completed_at is not None

    def test_mark_in_progress(self, test_task):
        """Marquer en cours"""
        test_task.mark_in_progress()
        assert test_task.status == 'in_progress'

    def test_mark_cancelled(self, test_task):
        """Marquer comme annule"""
        test_task.mark_cancelled()
        assert test_task.status == 'cancelled'

    def test_get_overdue_tasks(self, test_user):
        """Recuperer taches en retard"""
        task = Task(
            title='En retard', due_date=date.today() - timedelta(days=5),
            owner_id=test_user.id, status='pending'
        )
        db.session.add(task)
        db.session.flush()

        overdue = Task.get_overdue_tasks(test_user.id)
        assert len(overdue) >= 1
        assert any(t.title == 'En retard' for t in overdue)

    def test_get_upcoming_tasks(self, test_user):
        """Recuperer taches a venir"""
        task = Task(
            title='A venir', due_date=date.today() + timedelta(days=10),
            owner_id=test_user.id, status='pending'
        )
        db.session.add(task)
        db.session.flush()

        upcoming = Task.get_upcoming_tasks(test_user.id, days=30)
        assert any(t.title == 'A venir' for t in upcoming)

    def test_create_from_document(self, test_document):
        """Creer tache depuis document"""
        test_document.expiry_date = date.today() + timedelta(days=30)
        task = Task.create_from_document(test_document)
        assert task.document_id == test_document.id
        assert task.due_date == test_document.expiry_date
        assert 'Renouveler' in task.title

    def test_create_from_document_no_date(self, test_document):
        """Erreur si pas de date d'echeance"""
        test_document.expiry_date = None
        with pytest.raises(ValueError):
            Task.create_from_document(test_document)

    def test_task_repr(self, test_task):
        """Representation string"""
        assert 'Tache de test' in repr(test_task)


# ============================================================
# Tests Folder
# ============================================================
class TestFolderModel:
    """Tests pour le modele Folder"""

    def test_create_folder(self, test_folder):
        """Creation d'un dossier"""
        assert test_folder.id is not None
        assert test_folder.name == 'Test Folder'

    def test_document_count(self, test_folder, test_document):
        """Comptage des documents"""
        assert test_folder.document_count == 1

    def test_get_path_simple(self, test_folder):
        """Chemin simple sans parent"""
        assert test_folder.get_path() == 'Test Folder'

    def test_subfolder_path(self, test_user, test_folder):
        """Chemin avec sous-dossier"""
        sub = Folder(
            name='Sub', category='Autres',
            owner_id=test_user.id, parent_id=test_folder.id
        )
        db.session.add(sub)
        db.session.flush()
        assert sub.get_path() == 'Test Folder / Sub'

    def test_create_default_folders(self, test_user):
        """Creation des dossiers par defaut"""
        folders = Folder.create_default_folders(test_user.id)
        assert len(folders) == 5
        names = [f.name for f in folders]
        assert 'Administratif' in names
        assert 'Sante' in names

    def test_folder_repr(self, test_folder):
        """Representation string"""
        assert 'Test Folder' in repr(test_folder)


# ============================================================
# Tests Family
# ============================================================
class TestFamilyModel:
    """Tests pour le modele Family"""

    def test_create_family(self, test_family):
        """Creation d'une famille"""
        assert test_family.id is not None
        assert test_family.name == 'Famille Test'

    def test_member_count(self, test_family):
        """Comptage des membres"""
        assert test_family.member_count == 1

    def test_is_member(self, test_family, test_user):
        """Verification d'appartenance"""
        assert test_family.is_member(test_user.id) is True

    def test_is_not_member(self, test_family, second_user):
        """Non-membre"""
        assert test_family.is_member(second_user.id) is False

    def test_get_member_role(self, test_family, test_user):
        """Role d'un membre"""
        role = test_family.get_member_role(test_user.id)
        assert role == 'chef_famille'

    def test_get_member_role_none(self, test_family, second_user):
        """Pas de role si pas membre"""
        assert test_family.get_member_role(second_user.id) is None

    def test_can_manage_creator(self, test_family, test_user):
        """Createur peut gerer"""
        assert test_family.can_manage(test_user.id) is True

    def test_cannot_manage_non_member(self, test_family, second_user):
        """Non-membre ne peut pas gerer"""
        assert not test_family.can_manage(second_user.id)


class TestFamilyMemberModel:
    """Tests pour le modele FamilyMember"""

    def test_roles_defined(self):
        """Les roles sont definis"""
        assert 'chef_famille' in FamilyMember.ROLES
        assert 'lecteur' in FamilyMember.ROLES
        assert len(FamilyMember.ROLES) == 8

    def test_unique_constraint(self, test_family, test_user):
        """Contrainte d'unicite famille+user"""
        duplicate = FamilyMember(
            family_id=test_family.id,
            user_id=test_user.id,
            role='lecteur'
        )
        db.session.add(duplicate)
        with pytest.raises(Exception):
            db.session.flush()
        db.session.rollback()


class TestShareLinkModel:
    """Tests pour le modele ShareLink"""

    def test_create_share_link(self, test_user, test_document):
        """Creation d'un lien de partage"""
        link = ShareLink.create_share_link(
            document_id=test_document.id,
            created_by=test_user.id,
            expires_hours=24,
            max_uses=3
        )
        db.session.flush()

        assert link.id is not None
        assert link.token is not None
        assert len(link.token) > 20
        assert link.max_uses == 3

    def test_is_valid(self, test_user, test_document):
        """Lien valide"""
        link = ShareLink.create_share_link(
            document_id=test_document.id,
            created_by=test_user.id,
            expires_hours=24
        )
        db.session.flush()
        assert link.is_valid is True

    def test_is_valid_revoked(self, test_user, test_document):
        """Lien revoque"""
        link = ShareLink.create_share_link(
            document_id=test_document.id,
            created_by=test_user.id
        )
        link.revoke()
        assert link.is_valid is False

    def test_is_valid_expired(self, test_user, test_document):
        """Lien expire"""
        link = ShareLink.create_share_link(
            document_id=test_document.id,
            created_by=test_user.id,
            expires_hours=0
        )
        link.expires_at = datetime.utcnow() - timedelta(hours=1)
        assert link.is_valid is False

    def test_use_count(self, test_user, test_document):
        """Compteur d'utilisation"""
        link = ShareLink.create_share_link(
            document_id=test_document.id,
            created_by=test_user.id,
            max_uses=2
        )
        db.session.flush()

        link.use()
        assert link.use_count == 1
        assert link.remaining_uses == 1

        link.use()
        assert link.is_valid is False

    def test_generate_token_unique(self):
        """Tokens uniques"""
        t1 = ShareLink.generate_token()
        t2 = ShareLink.generate_token()
        assert t1 != t2


# ============================================================
# Tests Permission
# ============================================================
class TestPermissionModel:
    """Tests pour le modele Permission"""

    def test_create_permission(self, test_document, second_user, test_user):
        """Creation d'une permission"""
        perm = Permission(
            document_id=test_document.id,
            user_id=second_user.id,
            granted_by=test_user.id,
            can_view=True,
            can_edit=False,
            can_download=True
        )
        db.session.add(perm)
        db.session.flush()
        assert perm.id is not None

    def test_is_valid_active(self, test_document, second_user, test_user):
        """Permission active est valide"""
        perm = Permission(
            document_id=test_document.id,
            user_id=second_user.id,
            granted_by=test_user.id
        )
        assert perm.is_valid() is True

    def test_is_valid_expired(self, test_document, second_user, test_user):
        """Permission expiree n'est pas valide"""
        perm = Permission(
            document_id=test_document.id,
            user_id=second_user.id,
            granted_by=test_user.id,
            end_date=date.today() - timedelta(days=1)
        )
        assert perm.is_valid() is False

    def test_is_valid_future_start(self, test_document, second_user, test_user):
        """Permission avec date future n'est pas encore valide"""
        perm = Permission(
            document_id=test_document.id,
            user_id=second_user.id,
            granted_by=test_user.id,
            start_date=date.today() + timedelta(days=5)
        )
        assert perm.is_valid() is False

    def test_status_permanent(self, test_document, second_user, test_user):
        """Statut permanent"""
        perm = Permission(
            document_id=test_document.id,
            user_id=second_user.id,
            granted_by=test_user.id,
            end_date=None
        )
        assert perm.status == 'permanent'

    def test_status_expired(self, test_document, second_user, test_user):
        """Statut expire"""
        perm = Permission(
            document_id=test_document.id,
            user_id=second_user.id,
            granted_by=test_user.id,
            end_date=date.today() - timedelta(days=1)
        )
        assert perm.status == 'expired'

    def test_status_active(self, test_document, second_user, test_user):
        """Statut actif"""
        perm = Permission(
            document_id=test_document.id,
            user_id=second_user.id,
            granted_by=test_user.id,
            end_date=date.today() + timedelta(days=30)
        )
        assert perm.status == 'active'

    def test_is_expiring_soon(self, test_document, second_user, test_user):
        """Expire bientot"""
        perm = Permission(
            document_id=test_document.id,
            user_id=second_user.id,
            granted_by=test_user.id,
            end_date=date.today() + timedelta(days=3)
        )
        assert perm.is_expiring_soon() is True

    def test_grant_access_new(self, test_document, second_user, test_user):
        """Accorder un nouvel acces"""
        perm = Permission.grant_access(
            document_id=test_document.id,
            user_id=second_user.id,
            granted_by=test_user.id,
            can_edit=True
        )
        assert perm.can_edit is True

    def test_grant_access_update(self, test_document, second_user, test_user):
        """Mettre a jour une permission existante"""
        perm1 = Permission.grant_access(
            document_id=test_document.id,
            user_id=second_user.id,
            granted_by=test_user.id,
            can_edit=False
        )
        db.session.add(perm1)
        db.session.flush()

        perm2 = Permission.grant_access(
            document_id=test_document.id,
            user_id=second_user.id,
            granted_by=test_user.id,
            can_edit=True
        )
        assert perm2.can_edit is True

    def test_revoke_access(self, test_document, second_user, test_user):
        """Revoquer un acces"""
        perm = Permission(
            document_id=test_document.id,
            user_id=second_user.id,
            granted_by=test_user.id
        )
        db.session.add(perm)
        db.session.flush()

        result = Permission.revoke_access(test_document.id, second_user.id)
        assert result is True

    def test_revoke_access_not_found(self, test_document, second_user):
        """Revoquer un acces inexistant"""
        result = Permission.revoke_access(test_document.id, second_user.id)
        assert result is False


# ============================================================
# Tests Notification
# ============================================================
class TestNotificationModel:
    """Tests pour le modele Notification"""

    def test_create_notification(self, test_user):
        """Creation d'une notification"""
        notif = Notification.create_notification(
            user_id=test_user.id,
            type='system',
            title='Test',
            message='Message test'
        )
        db.session.flush()
        assert notif.id is not None
        assert notif.is_read is False

    def test_mark_as_read(self, test_user):
        """Marquer comme lue"""
        notif = Notification.create_notification(
            user_id=test_user.id,
            type='system',
            title='Test',
            message='Message'
        )
        db.session.flush()

        notif.mark_as_read()
        assert notif.is_read is True
        assert notif.read_at is not None

    def test_mark_as_unread(self, test_user):
        """Marquer comme non lue"""
        notif = Notification.create_notification(
            user_id=test_user.id,
            type='system',
            title='Test',
            message='Message'
        )
        db.session.flush()
        notif.mark_as_read()
        notif.mark_as_unread()
        assert notif.is_read is False
        assert notif.read_at is None

    def test_unread_count(self, test_user):
        """Compteur de non lues"""
        for i in range(3):
            Notification.create_notification(
                user_id=test_user.id,
                type='system',
                title=f'Test {i}',
                message='Message'
            )
        db.session.flush()

        count = Notification.get_unread_count(test_user.id)
        assert count == 3

    def test_type_label(self, test_user):
        """Libelle du type"""
        notif = Notification(user_id=test_user.id, type='task_due',
                             title='T', message='M')
        assert notif.type_label == 'Tache a echeance'

    def test_priority_color(self, test_user):
        """Couleur de priorite"""
        notif = Notification(user_id=test_user.id, type='system',
                             title='T', message='M', priority='urgent')
        assert notif.priority_color == 'danger'

    def test_icon(self, test_user):
        """Icone du type"""
        notif = Notification(user_id=test_user.id, type='document_shared',
                             title='T', message='M')
        assert notif.icon == 'bi-share'

    def test_is_expired(self, test_user):
        """Notification expiree"""
        notif = Notification(
            user_id=test_user.id, type='system',
            title='T', message='M',
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        assert notif.is_expired is True

    def test_not_expired(self, test_user):
        """Notification non expiree"""
        notif = Notification(
            user_id=test_user.id, type='system',
            title='T', message='M',
            expires_at=datetime.utcnow() + timedelta(days=1)
        )
        assert notif.is_expired is False

    def test_time_ago_just_now(self, test_user):
        """Temps ecoule : a l'instant"""
        notif = Notification(
            user_id=test_user.id, type='system',
            title='T', message='M',
            created_at=datetime.utcnow()
        )
        assert "l'instant" in notif.time_ago

    def test_get_user_notifications(self, test_user):
        """Recuperation des notifications"""
        for i in range(5):
            Notification.create_notification(
                user_id=test_user.id,
                type='system',
                title=f'Test {i}',
                message='Message'
            )
        db.session.flush()

        notifs = Notification.get_user_notifications(test_user.id, limit=3)
        assert len(notifs) == 3

    def test_mark_all_as_read(self, test_user):
        """Marquer toutes comme lues"""
        for i in range(3):
            Notification.create_notification(
                user_id=test_user.id,
                type='system',
                title=f'Test {i}',
                message='Message'
            )
        db.session.flush()

        Notification.mark_all_as_read(test_user.id)
        count = Notification.get_unread_count(test_user.id)
        assert count == 0


# ============================================================
# Tests Log
# ============================================================
class TestLogModel:
    """Tests pour le modele Log"""

    def test_create_log(self, test_user):
        """Creation d'un log"""
        log = Log.create_log(
            user_id=test_user.id,
            action='login',
            details='Connexion de test'
        )
        db.session.flush()
        assert log.id is not None
        assert log.action == 'login'

    def test_action_label(self, test_user):
        """Libelle de l'action"""
        log = Log(user_id=test_user.id, action='document_upload')
        assert log.action_label == 'Ajout document'

    def test_action_label_unknown(self, test_user):
        """Libelle inconnu retourne l'action brute"""
        log = Log(user_id=test_user.id, action='custom_action')
        assert log.action_label == 'custom_action'

    def test_get_user_logs(self, test_user):
        """Recuperation des logs utilisateur"""
        for action in ['login', 'logout', 'document_view']:
            Log.create_log(user_id=test_user.id, action=action)
        db.session.flush()

        logs = Log.get_user_logs(test_user.id)
        assert len(logs) >= 3

    def test_get_document_logs(self, test_user, test_document):
        """Recuperation des logs document"""
        Log.create_log(
            user_id=test_user.id,
            action='document_view',
            document_id=test_document.id
        )
        db.session.flush()

        logs = Log.get_document_logs(test_document.id)
        assert len(logs) >= 1

    def test_log_repr(self, test_user):
        """Representation string"""
        log = Log(user_id=test_user.id, action='login')
        assert 'login' in repr(log)
