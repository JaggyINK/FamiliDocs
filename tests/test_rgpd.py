"""
T26 - Tests RGPD : export donnees, completude
"""
import json
import pytest
from app.models import db
from app.models.user import User
from app.models.document import Document
from app.models.folder import Folder
from app.models.task import Task
from app.services.backup_service import BackupService


class TestRGPDExportService:
    """Tests de l'export RGPD via le service"""

    def test_export_user_data_success(self, app, test_user):
        """Test export des donnees utilisateur"""
        success, data = BackupService.export_user_data(test_user.id)
        assert success
        assert 'user' in data
        assert data['user']['email'] == 'test@familidocs.local'
        assert data['user']['username'] == 'testuser'

    def test_export_includes_folders(self, app, test_user, test_folder):
        """Test que l'export contient les dossiers"""
        success, data = BackupService.export_user_data(test_user.id)
        assert success
        assert 'folders' in data
        assert len(data['folders']) >= 1
        assert data['folders'][0]['name'] == 'Test Folder'

    def test_export_includes_documents(self, app, test_user, test_document):
        """Test que l'export contient les documents"""
        success, data = BackupService.export_user_data(test_user.id)
        assert success
        assert 'documents' in data
        assert len(data['documents']) >= 1
        assert data['documents'][0]['name'] == 'Test Document'

    def test_export_includes_tasks(self, app, test_user, test_task):
        """Test que l'export contient les taches"""
        success, data = BackupService.export_user_data(test_user.id)
        assert success
        assert 'tasks' in data
        assert len(data['tasks']) >= 1
        assert data['tasks'][0]['title'] == 'Tache de test'

    def test_export_invalid_user(self, app):
        """Test export pour un utilisateur inexistant"""
        success, result = BackupService.export_user_data(99999)
        assert not success

    def test_export_completeness(self, app, test_user, test_folder, test_document, test_task):
        """Test completude de l'export (toutes les sections presentes)"""
        success, data = BackupService.export_user_data(test_user.id)
        assert success
        required_keys = ['user', 'folders', 'documents', 'tasks']
        for key in required_keys:
            assert key in data, f"Cle manquante dans l'export: {key}"

    def test_export_user_fields(self, app, test_user):
        """Test que les champs utilisateur sont complets"""
        success, data = BackupService.export_user_data(test_user.id)
        assert success
        user_data = data['user']
        required_fields = ['email', 'username', 'first_name', 'last_name', 'created_at']
        for field in required_fields:
            assert field in user_data, f"Champ manquant: {field}"


class TestRGPDExportRoute:
    """Tests de la route d'export RGPD"""

    def test_export_route_requires_auth(self, client):
        """Test que la route necessite l'authentification"""
        response = client.get('/profile/export-data')
        assert response.status_code in [302, 308]

    def test_export_route_returns_json(self, auth_client):
        """Test que la route retourne du JSON telechargeabl"""
        response = auth_client.get('/profile/export-data')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        assert 'Content-Disposition' in response.headers
        assert 'attachment' in response.headers['Content-Disposition']

    def test_export_route_json_valid(self, auth_client):
        """Test que le JSON retourne est valide"""
        response = auth_client.get('/profile/export-data')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'user' in data
        assert data['user']['email'] == 'test@familidocs.local'


class TestRGPDDataMinimization:
    """Tests de minimisation des donnees (RGPD art. 5.1.c)"""

    def test_export_does_not_contain_password_hash(self, app, test_user):
        """L'export RGPD ne doit jamais contenir le hash du mot de passe"""
        success, data = BackupService.export_user_data(test_user.id)
        assert success
        assert 'password_hash' not in data['user']
        # check tout le JSON serialise
        json_str = json.dumps(data, default=str)
        assert 'password_hash' not in json_str

    def test_export_does_not_contain_totp_secret(self, app, test_user):
        """L'export RGPD ne doit jamais contenir le secret TOTP (2FA)"""
        success, data = BackupService.export_user_data(test_user.id)
        assert success
        json_str = json.dumps(data, default=str)
        assert 'totp_secret' not in json_str


class TestRGPDLogRetention:
    """Tests de la retention des logs (180 jours par defaut)"""

    def test_cleanup_old_logs_removes_old_entries(self, app, test_user):
        """Les logs anterieurs a la duree de retention sont supprimes"""
        from datetime import datetime, timedelta
        from app.models.log import Log
        from app.models import db

        # cree un vieux log (200 jours)
        old_log = Log(
            user_id=test_user.id,
            action='login',
            details='vieux log',
            created_at=datetime.utcnow() - timedelta(days=200)
        )
        db.session.add(old_log)
        # cree un log recent (10 jours)
        recent_log = Log(
            user_id=test_user.id,
            action='login',
            details='log recent',
            created_at=datetime.utcnow() - timedelta(days=10)
        )
        db.session.add(recent_log)
        db.session.commit()

        # capture des ids avant cleanup (apres delete les objets ne sont plus accessibles)
        old_id = old_log.id
        recent_id = recent_log.id

        # nettoyage avec retention 180j
        deleted = Log.cleanup_old_logs(retention_days=180)

        assert deleted >= 1
        # le log recent doit toujours etre la
        assert db.session.get(Log, recent_id) is not None
        # le vieux doit avoir disparu
        assert db.session.get(Log, old_id) is None


class TestRGPDRightToErasure:
    """Tests du droit a l'oubli (RGPD art. 17)"""

    def test_user_deletion_cascades_to_documents(self, app, test_user, test_document):
        """La suppression d'un user supprime ses documents (cascade)"""
        from app.models import db
        from app.models.document import Document
        from app.models.user import User

        user_id = test_user.id
        doc_id = test_document.id

        # verif que le doc existe
        assert Document.query.get(doc_id) is not None

        # suppression user
        user = User.query.get(user_id)
        db.session.delete(user)
        db.session.commit()

        # le user n'existe plus
        assert User.query.get(user_id) is None
        # le document non plus (cascade)
        assert Document.query.get(doc_id) is None

    def test_user_deletion_cascades_to_folders(self, app, test_user, test_folder):
        """La suppression d'un user supprime ses dossiers (cascade)"""
        from app.models import db
        from app.models.folder import Folder
        from app.models.user import User

        user_id = test_user.id
        folder_id = test_folder.id

        user = User.query.get(user_id)
        db.session.delete(user)
        db.session.commit()

        assert User.query.get(user_id) is None
        assert Folder.query.get(folder_id) is None


class TestFamilyMemberRoleValidation:
    """Tests du validator de role pour FamilyMember (correction phase 2.2)"""

    def test_invalid_role_raises_value_error(self, app, test_user, test_family):
        """Un role hors liste doit lever ValueError"""
        from app.models.family import FamilyMember

        with pytest.raises(ValueError):
            FamilyMember(
                family_id=test_family.id,
                user_id=test_user.id,
                role='superadmin'  # role inexistant
            )

    def test_valid_role_accepted(self, app, test_user, test_family):
        """Tous les roles definis dans ROLES sont acceptes"""
        from app.models.family import FamilyMember

        for role in FamilyMember.ROLES.keys():
            # ne doit pas lever
            member = FamilyMember(
                family_id=test_family.id,
                user_id=test_user.id,
                role=role
            )
            assert member.role == role


class TestLogActionTypes:
    """Tests que tous les ACTION_TYPES attendus sont definis"""

    def test_log_has_required_action_types(self):
        """Verifie la presence des 23 types d'actions documentes"""
        from app.models.log import Log

        required = {
            'login', 'logout', 'login_failed',
            'document_view', 'document_download', 'document_upload',
            'document_edit', 'document_delete', 'document_share', 'document_review',
            'permission_grant', 'permission_revoke', 'permission_update',
            'user_create', 'user_edit', 'user_delete',
            'profile_update', 'avatar_upload', 'avatar_delete',
            'folder_create', 'folder_edit', 'folder_delete',
            'task_create', 'task_edit', 'task_complete',
            'backup_create', 'backup_restore'
        }
        for action in required:
            assert action in Log.ACTION_TYPES, f"ACTION_TYPES manquant: {action}"
