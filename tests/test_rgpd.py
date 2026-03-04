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
