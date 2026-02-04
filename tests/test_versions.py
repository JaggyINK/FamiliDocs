"""
Tests pour le module Versioning de FamiliDocs
"""
import pytest
import tempfile

from app import create_app
from app.models import db
from app.models.user import User
from app.models.document import Document
from app.models.document_version import DocumentVersion
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
def test_user(app):
    """Utilisateur de test"""
    with app.app_context():
        user = User(
            email='version_test@familidocs.local',
            username='versionuser',
            password_hash=AuthService.hash_password('Test123!'),
            first_name='Version',
            last_name='Tester',
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        return user.id


@pytest.fixture
def test_document(app, test_user):
    """Document de test"""
    with app.app_context():
        doc = Document(
            name='Document Versionne',
            original_filename='test.pdf',
            stored_filename='original_abc123.pdf',
            file_type='pdf',
            file_size=2048,
            owner_id=test_user
        )
        db.session.add(doc)
        db.session.commit()
        return doc.id


class TestDocumentVersionModel:
    """Tests pour le modele DocumentVersion"""

    def test_create_version(self, app, test_user, test_document):
        """Test de creation d'une version"""
        with app.app_context():
            version = DocumentVersion(
                document_id=test_document,
                version_number=1,
                stored_filename='v1_abc123.pdf',
                original_filename='test.pdf',
                file_size=2048,
                file_type='pdf',
                comment='Version initiale',
                uploaded_by=test_user
            )
            db.session.add(version)
            db.session.commit()

            assert version.id is not None
            assert version.version_number == 1
            assert version.comment == 'Version initiale'

    def test_get_latest_version_number(self, app, test_user, test_document):
        """Test de recuperation du dernier numero de version"""
        with app.app_context():
            # Pas de versions encore
            assert DocumentVersion.get_latest_version_number(test_document) == 0

            # Ajouter une version
            v1 = DocumentVersion(
                document_id=test_document,
                version_number=1,
                stored_filename='v1_file.pdf',
                original_filename='test.pdf',
                file_size=1024,
                file_type='pdf',
                uploaded_by=test_user
            )
            db.session.add(v1)
            db.session.commit()

            assert DocumentVersion.get_latest_version_number(test_document) == 1

    def test_get_versions_ordered(self, app, test_user, test_document):
        """Test que les versions sont triees par numero decroissant"""
        with app.app_context():
            for i in range(1, 4):
                v = DocumentVersion(
                    document_id=test_document,
                    version_number=i,
                    stored_filename=f'v{i}_file.pdf',
                    original_filename='test.pdf',
                    file_size=1024 * i,
                    file_type='pdf',
                    uploaded_by=test_user
                )
                db.session.add(v)
            db.session.commit()

            versions = DocumentVersion.get_versions(test_document)
            assert len(versions) == 3
            assert versions[0].version_number == 3
            assert versions[2].version_number == 1

    def test_human_readable_size(self, app, test_user, test_document):
        """Test du formatage de la taille"""
        with app.app_context():
            version = DocumentVersion(
                document_id=test_document,
                version_number=1,
                stored_filename='v1.pdf',
                original_filename='test.pdf',
                file_size=2048,
                file_type='pdf',
                uploaded_by=test_user
            )
            size = version.get_human_readable_size()
            assert 'Ko' in size or 'o' in size


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
