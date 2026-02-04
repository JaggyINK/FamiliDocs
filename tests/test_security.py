"""
Tests pour la securite de FamiliDocs
"""
import pytest
import tempfile

from app import create_app
from app.models import db
from app.models.user import User
from app.services.auth_service import AuthService


@pytest.fixture
def app():
    """Instance de l'application pour les tests"""
    app = create_app('testing')
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Client de test"""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Utilisateur de test"""
    with app.app_context():
        user = User(
            email='security_test@familidocs.local',
            username='securityuser',
            password_hash=AuthService.hash_password('Test123!'),
            first_name='Security',
            last_name='Tester',
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        return user.id


class TestSecurityHeaders:
    """Tests pour les en-tetes de securite HTTP"""

    def test_x_content_type_options(self, client):
        """Verifie l'en-tete X-Content-Type-Options"""
        response = client.get('/login')
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'

    def test_x_frame_options(self, client):
        """Verifie l'en-tete X-Frame-Options"""
        response = client.get('/login')
        assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'

    def test_x_xss_protection(self, client):
        """Verifie l'en-tete X-XSS-Protection"""
        response = client.get('/login')
        assert response.headers.get('X-XSS-Protection') == '1; mode=block'

    def test_cache_control(self, client):
        """Verifie l'en-tete Cache-Control"""
        response = client.get('/login')
        assert 'no-cache' in response.headers.get('Cache-Control', '')


class TestPasswordPolicy:
    """Tests pour la politique de mots de passe"""

    def test_password_min_length(self, app):
        """Mot de passe trop court"""
        with app.app_context():
            valid, msg = AuthService.validate_password('Ab1!')
            assert valid is False

    def test_password_needs_uppercase(self, app):
        """Mot de passe sans majuscule"""
        with app.app_context():
            valid, msg = AuthService.validate_password('abcdef1!')
            assert valid is False

    def test_password_needs_lowercase(self, app):
        """Mot de passe sans minuscule"""
        with app.app_context():
            valid, msg = AuthService.validate_password('ABCDEF1!')
            assert valid is False

    def test_password_needs_digit(self, app):
        """Mot de passe sans chiffre"""
        with app.app_context():
            valid, msg = AuthService.validate_password('Abcdefgh!')
            assert valid is False

    def test_password_needs_special(self, app):
        """Mot de passe sans caractere special"""
        with app.app_context():
            valid, msg = AuthService.validate_password('Abcdefg1')
            assert valid is False

    def test_valid_password(self, app):
        """Mot de passe valide"""
        with app.app_context():
            valid, msg = AuthService.validate_password('Test123!')
            assert valid is True


class TestRateLimiting:
    """Tests pour la limitation de tentatives"""

    def test_rate_limit_allows_first_attempts(self, app):
        """Les premieres tentatives sont autorisees"""
        with app.app_context():
            # Reinitialiser
            AuthService._failed_attempts.clear()

            allowed, msg = AuthService._check_rate_limit('192.168.1.1')
            assert allowed is True

    def test_rate_limit_blocks_after_max(self, app):
        """Blocage apres le nombre max de tentatives"""
        with app.app_context():
            AuthService._failed_attempts.clear()
            ip = '10.0.0.1'

            for i in range(AuthService.MAX_LOGIN_ATTEMPTS):
                AuthService._record_failed_attempt(ip)

            allowed, msg = AuthService._check_rate_limit(ip)
            assert allowed is False
            assert 'Trop de tentatives' in msg

    def test_rate_limit_clears_on_success(self, app):
        """Les tentatives sont reinitialises apres succes"""
        with app.app_context():
            AuthService._failed_attempts.clear()
            ip = '10.0.0.2'

            AuthService._record_failed_attempt(ip)
            AuthService._record_failed_attempt(ip)
            assert ip in AuthService._failed_attempts

            AuthService._clear_failed_attempts(ip)
            assert ip not in AuthService._failed_attempts


class TestAccessControl:
    """Tests pour le controle d'acces"""

    def test_dashboard_requires_auth(self, client):
        """Le dashboard necessite une authentification"""
        response = client.get('/dashboard')
        assert response.status_code in [302, 401]

    def test_documents_requires_auth(self, client):
        """La liste des documents necessite une authentification"""
        response = client.get('/documents/')
        assert response.status_code in [302, 401]

    def test_admin_requires_auth(self, client):
        """L'admin necessite une authentification"""
        response = client.get('/admin/')
        assert response.status_code in [302, 401]

    def test_login_page_accessible(self, client):
        """La page de connexion est accessible sans auth"""
        response = client.get('/login')
        assert response.status_code == 200


class TestNotificationModel:
    """Tests pour le modele Notification"""

    def test_create_notification(self, app, test_user):
        """Test de creation d'une notification"""
        from app.models.notification import Notification
        with app.app_context():
            notif = Notification.create_notification(
                user_id=test_user,
                type='system',
                title='Test',
                message='Message de test',
                priority='normal'
            )
            db.session.commit()

            assert notif.id is not None
            assert notif.is_read is False

    def test_mark_as_read(self, app, test_user):
        """Test de marquage comme lu"""
        from app.models.notification import Notification
        with app.app_context():
            notif = Notification.create_notification(
                user_id=test_user,
                type='system',
                title='Test',
                message='Message',
            )
            db.session.commit()

            notif.mark_as_read()
            db.session.commit()

            assert notif.is_read is True
            assert notif.read_at is not None

    def test_unread_count(self, app, test_user):
        """Test du compteur de non lus"""
        from app.models.notification import Notification
        with app.app_context():
            for i in range(3):
                Notification.create_notification(
                    user_id=test_user,
                    type='system',
                    title=f'Test {i}',
                    message='Message',
                )
            db.session.commit()

            count = Notification.get_unread_count(test_user)
            assert count == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
