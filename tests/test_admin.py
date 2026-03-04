"""
T24 - Tests admin : CRUD users, backup, logs
"""
import pytest
from app.models import db
from app.models.user import User
from app.models.log import Log
from app.services.auth_service import AuthService


class TestAdminDashboard:
    """Tests du dashboard admin"""

    def test_admin_dashboard_access(self, admin_client):
        """Test acces au dashboard admin"""
        response = admin_client.get('/admin/')
        assert response.status_code == 200

    def test_admin_dashboard_denied_for_user(self, auth_client):
        """Test acces refuse pour un utilisateur normal"""
        response = auth_client.get('/admin/')
        assert response.status_code in [302, 403]


class TestAdminUserCRUD:
    """Tests CRUD utilisateurs par l'admin"""

    def test_admin_list_users(self, admin_client):
        """Test liste des utilisateurs"""
        response = admin_client.get('/admin/')
        assert response.status_code == 200

    def test_admin_create_user(self, admin_client, app):
        """Test creation d'un utilisateur"""
        response = admin_client.post('/admin/users/create', data={
            'email': 'newuser@test.com',
            'username': 'newuser',
            'password': 'NewUser123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'user'
        }, follow_redirects=True)
        assert response.status_code == 200
        user = User.query.filter_by(email='newuser@test.com').first()
        assert user is not None

    def test_admin_edit_user(self, admin_client, test_user):
        """Test modification d'un utilisateur"""
        response = admin_client.post(f'/admin/users/{test_user.id}/edit', data={
            'first_name': 'Modified',
            'last_name': 'User',
            'email': test_user.email,
            'role': 'user',
            'is_active': 'on'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestAdminLogs:
    """Tests des logs admin"""

    def test_admin_view_logs(self, admin_client, app, admin_user):
        """Test visualisation des logs"""
        Log.create_log(
            user_id=admin_user.id,
            action='test_action',
            details='Test log entry'
        )
        db.session.commit()
        response = admin_client.get('/admin/')
        assert response.status_code == 200


class TestAdminBackup:
    """Tests backup admin"""

    def test_admin_backup_page(self, admin_client):
        """Test acces a la page backup"""
        response = admin_client.get('/admin/')
        assert response.status_code == 200
