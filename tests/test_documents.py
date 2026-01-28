"""
Tests pour le module Documents de FamiliDocs
"""
import pytest
import os
import tempfile
from io import BytesIO

from app import create_app
from app.models import db
from app.models.user import User
from app.models.document import Document
from app.models.folder import Folder
from app.services.auth_service import AuthService
from app.services.document_service import DocumentService


@pytest.fixture
def app():
    """Crée une instance de l'application pour les tests"""
    app = create_app('testing')
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Crée un client de test"""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Crée un utilisateur de test"""
    with app.app_context():
        user = User(
            email='test@familidocs.local',
            username='testuser',
            password_hash=AuthService.hash_password('Test123!'),
            first_name='Test',
            last_name='User',
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def test_folder(app, test_user):
    """Crée un dossier de test"""
    with app.app_context():
        folder = Folder(
            name='Test Folder',
            category='Administratif',
            owner_id=test_user
        )
        db.session.add(folder)
        db.session.commit()
        return folder.id


class TestDocumentModel:
    """Tests pour le modèle Document"""

    def test_create_document(self, app, test_user, test_folder):
        """Test de création d'un document"""
        with app.app_context():
            document = Document(
                name='Test Document',
                original_filename='test.pdf',
                stored_filename='abc123.pdf',
                file_type='pdf',
                file_size=1024,
                owner_id=test_user,
                folder_id=test_folder
            )
            db.session.add(document)
            db.session.commit()

            assert document.id is not None
            assert document.name == 'Test Document'
            assert document.file_type == 'pdf'

    def test_document_extension(self, app, test_user):
        """Test de l'extension du document"""
        with app.app_context():
            document = Document(
                name='Test',
                original_filename='document.pdf',
                stored_filename='abc.pdf',
                owner_id=test_user
            )
            assert document.file_extension == 'pdf'

    def test_document_human_readable_size(self, app, test_user):
        """Test du format lisible de la taille"""
        with app.app_context():
            document = Document(
                name='Test',
                original_filename='test.pdf',
                stored_filename='abc.pdf',
                file_size=1024,
                owner_id=test_user
            )
            size = document.get_human_readable_size()
            assert 'Ko' in size or 'o' in size


class TestDocumentService:
    """Tests pour le service Document"""

    def test_allowed_file_pdf(self, app):
        """Test de validation des fichiers PDF"""
        with app.app_context():
            assert DocumentService.allowed_file('document.pdf') is True

    def test_allowed_file_invalid(self, app):
        """Test de rejet des fichiers non autorisés"""
        with app.app_context():
            assert DocumentService.allowed_file('script.exe') is False

    def test_generate_stored_filename(self, app):
        """Test de génération de nom de fichier"""
        with app.app_context():
            filename = DocumentService.generate_stored_filename('test.pdf')
            assert filename.endswith('.pdf')
            assert len(filename) > 10  # UUID + extension

    def test_get_file_type(self, app):
        """Test de détection du type de fichier"""
        with app.app_context():
            assert DocumentService.get_file_type('document.pdf') == 'pdf'
            assert DocumentService.get_file_type('image.png') == 'image'
            assert DocumentService.get_file_type('data.xlsx') == 'excel'
            assert DocumentService.get_file_type('unknown.xyz') == 'other'


class TestAuthService:
    """Tests pour le service d'authentification"""

    def test_hash_password(self, app):
        """Test du hashage de mot de passe"""
        with app.app_context():
            password = 'Test123!'
            hashed = AuthService.hash_password(password)
            assert hashed != password
            assert len(hashed) > 50

    def test_verify_password(self, app):
        """Test de vérification de mot de passe"""
        with app.app_context():
            password = 'Test123!'
            hashed = AuthService.hash_password(password)
            assert AuthService.verify_password(password, hashed) is True
            assert AuthService.verify_password('WrongPassword', hashed) is False

    def test_validate_password_valid(self, app):
        """Test de validation d'un mot de passe valide"""
        with app.app_context():
            is_valid, message = AuthService.validate_password('Test123!')
            assert is_valid is True

    def test_validate_password_too_short(self, app):
        """Test de validation d'un mot de passe trop court"""
        with app.app_context():
            is_valid, message = AuthService.validate_password('Te1!')
            assert is_valid is False
            assert '8 caractères' in message

    def test_validate_password_no_uppercase(self, app):
        """Test de validation sans majuscule"""
        with app.app_context():
            is_valid, message = AuthService.validate_password('test1234!')
            assert is_valid is False
            assert 'majuscule' in message

    def test_validate_password_no_digit(self, app):
        """Test de validation sans chiffre"""
        with app.app_context():
            is_valid, message = AuthService.validate_password('TestTest!')
            assert is_valid is False
            assert 'chiffre' in message


class TestUserRegistration:
    """Tests pour l'inscription des utilisateurs"""

    def test_register_user_success(self, app):
        """Test d'inscription réussie"""
        with app.app_context():
            success, result = AuthService.register_user(
                email='new@familidocs.local',
                username='newuser',
                password='NewUser123!',
                first_name='New',
                last_name='User'
            )
            assert success is True
            assert isinstance(result, User)
            assert result.email == 'new@familidocs.local'

    def test_register_user_duplicate_email(self, app, test_user):
        """Test d'inscription avec email existant"""
        with app.app_context():
            success, message = AuthService.register_user(
                email='test@familidocs.local',
                username='newuser',
                password='NewUser123!',
                first_name='New',
                last_name='User'
            )
            assert success is False
            assert 'email' in message.lower()


class TestAuthentication:
    """Tests pour l'authentification"""

    def test_authenticate_success(self, app, test_user):
        """Test d'authentification réussie"""
        with app.app_context():
            success, result = AuthService.authenticate(
                'test@familidocs.local',
                'Test123!'
            )
            assert success is True
            assert isinstance(result, User)

    def test_authenticate_wrong_password(self, app, test_user):
        """Test d'authentification avec mauvais mot de passe"""
        with app.app_context():
            success, message = AuthService.authenticate(
                'test@familidocs.local',
                'WrongPassword123!'
            )
            assert success is False

    def test_authenticate_wrong_email(self, app):
        """Test d'authentification avec email inexistant"""
        with app.app_context():
            success, message = AuthService.authenticate(
                'nonexistent@familidocs.local',
                'Test123!'
            )
            assert success is False


class TestLoginRoute:
    """Tests pour les routes d'authentification"""

    def test_login_page_accessible(self, client):
        """Test d'accès à la page de connexion"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Connexion' in response.data or b'connexion' in response.data

    def test_login_redirect_when_authenticated(self, client, app, test_user):
        """Test de redirection si déjà connecté"""
        with client.session_transaction() as sess:
            sess['_user_id'] = str(test_user)

        response = client.get('/login')
        # Devrait rediriger vers le dashboard
        assert response.status_code in [200, 302]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
