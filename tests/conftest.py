"""
Configuration pytest pour FamiliDocs
Fixtures partagees pour tous les tests
"""
import pytest
import tempfile

from app import create_app
from app.models import db as _db
from app.models.user import User
from app.models.document import Document
from app.models.folder import Folder
from app.models.task import Task
from app.models.family import Family, FamilyMember
from app.services.auth_service import AuthService


@pytest.fixture
def app():
    """Instance de l'application pour les tests"""
    _app = create_app('testing')
    _app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    _app.config['BACKUP_FOLDER'] = tempfile.mkdtemp()

    with _app.app_context():
        _db.create_all()
        yield _app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Client de test HTTP"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner pour les tests"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Cree un utilisateur de test standard"""
    user = User(
        email='test@familidocs.local',
        username='testuser',
        password_hash=AuthService.hash_password('Test123!'),
        first_name='Test',
        last_name='User',
        role='user',
        is_active=True
    )
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture
def admin_user(app):
    """Cree un utilisateur admin de test"""
    user = User(
        email='admin_test@familidocs.local',
        username='admintest',
        password_hash=AuthService.hash_password('Admin123!'),
        first_name='Admin',
        last_name='Test',
        role='admin',
        is_active=True
    )
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture
def second_user(app):
    """Cree un deuxieme utilisateur pour les tests de partage"""
    user = User(
        email='other@familidocs.local',
        username='otheruser',
        password_hash=AuthService.hash_password('Other123!'),
        first_name='Other',
        last_name='User',
        role='user',
        is_active=True
    )
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture
def test_folder(app, test_user):
    """Cree un dossier de test"""
    folder = Folder(
        name='Test Folder',
        category='Administratif',
        owner_id=test_user.id
    )
    _db.session.add(folder)
    _db.session.commit()
    return folder


@pytest.fixture
def test_document(app, test_user, test_folder):
    """Cree un document de test"""
    doc = Document(
        name='Test Document',
        original_filename='test.pdf',
        stored_filename='abc123_test.pdf',
        file_type='pdf',
        file_size=2048,
        owner_id=test_user.id,
        folder_id=test_folder.id,
        confidentiality='private'
    )
    _db.session.add(doc)
    _db.session.commit()
    return doc


@pytest.fixture
def test_task(app, test_user):
    """Cree une tache de test"""
    from datetime import date, timedelta
    task = Task(
        title='Tache de test',
        description='Description de test',
        due_date=date.today() + timedelta(days=7),
        priority='normal',
        status='pending',
        owner_id=test_user.id,
        reminder_days=3
    )
    _db.session.add(task)
    _db.session.commit()
    return task


@pytest.fixture
def test_family(app, test_user):
    """Cree une famille de test avec le createur comme admin"""
    family = Family(
        name='Famille Test',
        description='Famille pour les tests',
        creator_id=test_user.id
    )
    _db.session.add(family)
    _db.session.commit()

    member = FamilyMember(
        family_id=family.id,
        user_id=test_user.id,
        role='chef_famille'
    )
    _db.session.add(member)
    _db.session.commit()
    return family


@pytest.fixture
def auth_client(client, app, test_user):
    """Client authentifie en tant qu'utilisateur standard"""
    client.post('/login', data={
        'email': 'test@familidocs.local',
        'password': 'Test123!'
    })
    return client


@pytest.fixture
def admin_client(client, app, admin_user):
    """Client authentifie en tant qu'admin"""
    client.post('/login', data={
        'email': 'admin_test@familidocs.local',
        'password': 'Admin123!'
    })
    return client
