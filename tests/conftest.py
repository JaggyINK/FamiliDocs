"""
Configuration pytest pour FamiliDocs
"""
import pytest
import tempfile
import os

from app import create_app
from app.models import db


@pytest.fixture(scope='session')
def app():
    """Crée une instance de l'application pour la session de test"""
    app = create_app('testing')

    # Configuration spécifique aux tests
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()

    with app.app_context():
        db.create_all()

    yield app

    # Nettoyage
    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    """Crée un client de test"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Crée un runner CLI pour les tests"""
    return app.test_cli_runner()


@pytest.fixture
def auth_client(client, app):
    """Crée un client authentifié pour les tests"""
    from app.models.user import User
    from app.services.auth_service import AuthService

    with app.app_context():
        # Créer un utilisateur de test
        user = User.query.filter_by(email='testauth@familidocs.local').first()
        if not user:
            user = User(
                email='testauth@familidocs.local',
                username='testauthuser',
                password_hash=AuthService.hash_password('Test123!'),
                first_name='Auth',
                last_name='User',
                role='user'
            )
            db.session.add(user)
            db.session.commit()

        # Connexion
        client.post('/login', data={
            'email': 'testauth@familidocs.local',
            'password': 'Test123!'
        })

    return client
