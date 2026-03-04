"""
Tests pour les routes de FamiliDocs
Couverture : Auth, Documents, Tasks, User, Admin, Erreurs
"""
import pytest
from datetime import date, timedelta

from app.models import db as _db
from app.models.user import User
from app.models.document import Document
from app.models.task import Task
from app.models.notification import Notification
from app.services.auth_service import AuthService

db = _db


# ============================================================
# Tests Routes Auth
# ============================================================
class TestAuthRoutes:
    """Tests pour les routes d'authentification"""

    def test_login_page(self, client):
        """Page de connexion accessible"""
        response = client.get('/login')
        assert response.status_code == 200

    def test_register_page(self, client):
        """Page d'inscription accessible"""
        response = client.get('/register')
        assert response.status_code == 200

    def test_index_redirects_to_login(self, client):
        """L'index redirige vers login si non connecte"""
        response = client.get('/')
        assert response.status_code == 302

    def test_login_with_empty_fields(self, client):
        """Connexion avec champs vides"""
        response = client.post('/login', data={
            'email': '',
            'password': ''
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'remplir' in response.data

    def test_login_with_wrong_credentials(self, client, test_user):
        """Connexion avec mauvais identifiants"""
        response = client.post('/login', data={
            'email': 'test@familidocs.local',
            'password': 'WrongPassword123!'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'incorrect' in response.data

    def test_register_password_mismatch(self, client):
        """Inscription avec mots de passe differents"""
        response = client.post('/register', data={
            'email': 'new@test.local',
            'username': 'newuser',
            'password': 'Test123!',
            'password_confirm': 'Different123!',
            'first_name': 'New',
            'last_name': 'User'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'correspondent pas' in response.data

    def test_register_empty_fields(self, client):
        """Inscription avec champs vides"""
        response = client.post('/register', data={
            'email': '',
            'username': '',
            'password': '',
            'password_confirm': '',
            'first_name': '',
            'last_name': ''
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'remplir' in response.data

    def test_change_password_page_requires_auth(self, client):
        """Page changement mdp necessite auth"""
        response = client.get('/change-password')
        assert response.status_code == 302

    def test_logout_requires_auth(self, client):
        """Deconnexion necessite auth"""
        response = client.get('/logout')
        assert response.status_code == 302


# ============================================================
# Tests Routes Documents
# ============================================================
class TestDocumentRoutes:
    """Tests pour les routes de documents"""

    def test_list_documents_requires_auth(self, client):
        """Liste documents necessite auth"""
        response = client.get('/documents/')
        assert response.status_code == 302

    def test_upload_page_requires_auth(self, client):
        """Page upload necessite auth"""
        response = client.get('/documents/upload')
        assert response.status_code == 302

    def test_shared_documents_requires_auth(self, client):
        """Documents partages necessite auth"""
        response = client.get('/documents/shared')
        assert response.status_code == 302

    def test_list_documents_authenticated(self, auth_client):
        """Liste documents pour utilisateur connecte"""
        response = auth_client.get('/documents/')
        assert response.status_code == 200

    def test_upload_page_authenticated(self, auth_client):
        """Page upload pour utilisateur connecte"""
        response = auth_client.get('/documents/upload')
        assert response.status_code == 200

    def test_view_nonexistent_document(self, auth_client):
        """Vue document inexistant = 404"""
        response = auth_client.get('/documents/99999')
        assert response.status_code == 404

    def test_view_document_no_access(self, auth_client, second_user):
        """Vue document sans acces"""
        doc = Document(
            name='Secret Doc', original_filename='secret.pdf',
            stored_filename='secret_xyz.pdf', file_type='pdf',
            owner_id=second_user.id
        )
        db.session.add(doc)
        db.session.flush()

        response = auth_client.get(f'/documents/{doc.id}', follow_redirects=True)
        assert response.status_code == 200
        # Devrait etre redirige avec message d'acces refuse


# ============================================================
# Tests Routes Tasks
# ============================================================
class TestTaskRoutes:
    """Tests pour les routes de taches"""

    def test_list_tasks_requires_auth(self, client):
        """Liste taches necessite auth"""
        response = client.get('/tasks/')
        assert response.status_code == 302

    def test_create_task_requires_auth(self, client):
        """Creation tache necessite auth"""
        response = client.get('/tasks/create')
        assert response.status_code == 302

    def test_list_tasks_authenticated(self, auth_client):
        """Liste taches pour utilisateur connecte"""
        response = auth_client.get('/tasks/')
        assert response.status_code == 200

    def test_create_task_page(self, auth_client):
        """Page de creation de tache"""
        response = auth_client.get('/tasks/create')
        assert response.status_code == 200

    def test_create_task_post_empty_title(self, auth_client):
        """Creation tache sans titre"""
        response = auth_client.post('/tasks/create', data={
            'title': '',
            'due_date': '2026-12-31'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'obligatoire' in response.data

    def test_create_task_post_empty_date(self, auth_client):
        """Creation tache sans date"""
        response = auth_client.post('/tasks/create', data={
            'title': 'Test Task',
            'due_date': ''
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'obligatoire' in response.data

    def test_create_task_post_invalid_date(self, auth_client):
        """Creation tache avec date invalide"""
        response = auth_client.post('/tasks/create', data={
            'title': 'Test Task',
            'due_date': 'not-a-date'
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b'invalide' in response.data

    def test_view_task_nonexistent(self, auth_client):
        """Vue tache inexistante = 404"""
        response = auth_client.get('/tasks/99999')
        assert response.status_code == 404

    def test_calendar_page(self, auth_client):
        """Page calendrier"""
        response = auth_client.get('/tasks/calendar')
        assert response.status_code == 200

    def test_overdue_page(self, auth_client):
        """Page taches en retard"""
        response = auth_client.get('/tasks/overdue')
        assert response.status_code == 200

    def test_upcoming_page(self, auth_client):
        """Page taches a venir"""
        response = auth_client.get('/tasks/upcoming')
        assert response.status_code == 200


# ============================================================
# Tests Routes User
# ============================================================
class TestUserRoutes:
    """Tests pour les routes utilisateur"""

    def test_dashboard_requires_auth(self, client):
        """Dashboard necessite auth"""
        response = client.get('/dashboard')
        assert response.status_code == 302

    def test_profile_requires_auth(self, client):
        """Profil necessite auth"""
        response = client.get('/profile')
        assert response.status_code == 302

    def test_dashboard_authenticated(self, auth_client):
        """Dashboard pour utilisateur connecte"""
        response = auth_client.get('/dashboard')
        assert response.status_code == 200

    def test_profile_authenticated(self, auth_client):
        """Profil pour utilisateur connecte"""
        response = auth_client.get('/profile')
        assert response.status_code == 200

    def test_folders_page(self, auth_client):
        """Page dossiers"""
        response = auth_client.get('/folders')
        assert response.status_code == 200

    def test_activity_page(self, auth_client):
        """Page activite"""
        response = auth_client.get('/activity')
        assert response.status_code == 200


# ============================================================
# Tests Routes Admin
# ============================================================
class TestAdminRoutes:
    """Tests pour les routes admin"""

    def test_admin_dashboard_requires_auth(self, client):
        """Dashboard admin necessite auth"""
        response = client.get('/admin/')
        assert response.status_code == 302

    def test_admin_dashboard_requires_admin_role(self, auth_client):
        """Dashboard admin necessite role admin"""
        response = auth_client.get('/admin/')
        # Un user normal devrait etre refuse (302 redirect ou 403)
        assert response.status_code in [302, 403]

    def test_admin_dashboard_admin_user(self, admin_client):
        """Dashboard admin pour admin"""
        response = admin_client.get('/admin/')
        assert response.status_code == 200

    def test_admin_users_page(self, admin_client):
        """Page gestion utilisateurs"""
        response = admin_client.get('/admin/users')
        assert response.status_code == 200

    def test_admin_logs_page(self, admin_client):
        """Page des logs"""
        response = admin_client.get('/admin/logs')
        assert response.status_code == 200


# ============================================================
# Tests Error Pages
# ============================================================
class TestErrorPages:
    """Tests pour les pages d'erreur"""

    def test_404_page(self, client):
        """Page 404 personnalisee"""
        response = client.get('/page-inexistante-xyz')
        assert response.status_code == 404
        assert b'404' in response.data

    def test_404_contains_navigation(self, client):
        """Page 404 contient un lien de retour"""
        response = client.get('/url-totalement-bidon')
        assert response.status_code == 404
        assert b'Retour' in response.data or b'Connexion' in response.data


# ============================================================
# Tests Security Headers
# ============================================================
class TestSecurityHeaders:
    """Tests pour les en-tetes de securite HTTP"""

    def test_x_content_type_options(self, client):
        """X-Content-Type-Options present"""
        response = client.get('/login')
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'

    def test_x_frame_options(self, client):
        """X-Frame-Options present"""
        response = client.get('/login')
        assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'

    def test_x_xss_protection(self, client):
        """X-XSS-Protection present"""
        response = client.get('/login')
        assert response.headers.get('X-XSS-Protection') == '1; mode=block'

    def test_cache_control(self, client):
        """Cache-Control present"""
        response = client.get('/login')
        assert 'no-cache' in response.headers.get('Cache-Control', '')

    def test_referrer_policy(self, client):
        """Referrer-Policy present"""
        response = client.get('/login')
        assert response.headers.get('Referrer-Policy') == 'strict-origin-when-cross-origin'
