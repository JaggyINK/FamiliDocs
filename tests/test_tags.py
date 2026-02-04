"""
Tests pour le module Tags de FamiliDocs
"""
import pytest
import tempfile

from app import create_app
from app.models import db
from app.models.user import User
from app.models.document import Document
from app.models.tag import Tag
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
            email='tag_test@familidocs.local',
            username='taguser',
            password_hash=AuthService.hash_password('Test123!'),
            first_name='Tag',
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
            name='Document Tag Test',
            original_filename='test.pdf',
            stored_filename='tag_abc123.pdf',
            file_type='pdf',
            file_size=1024,
            owner_id=test_user
        )
        db.session.add(doc)
        db.session.commit()
        return doc.id


class TestTagModel:
    """Tests pour le modele Tag"""

    def test_create_tag(self, app, test_user):
        """Test de creation d'un tag"""
        with app.app_context():
            tag = Tag(name='urgent', color='#dc3545', owner_id=test_user)
            db.session.add(tag)
            db.session.commit()

            assert tag.id is not None
            assert tag.name == 'urgent'
            assert tag.color == '#dc3545'

    def test_get_user_tags(self, app, test_user):
        """Test de recuperation des tags d'un utilisateur"""
        with app.app_context():
            for name in ['important', 'sante', 'banque']:
                tag = Tag(name=name, owner_id=test_user)
                db.session.add(tag)
            db.session.commit()

            tags = Tag.get_user_tags(test_user)
            assert len(tags) == 3

    def test_get_or_create_existing(self, app, test_user):
        """Test de get_or_create avec tag existant"""
        with app.app_context():
            tag1 = Tag(name='test', owner_id=test_user)
            db.session.add(tag1)
            db.session.commit()
            tag1_id = tag1.id

            tag2 = Tag.get_or_create('test', test_user)
            assert tag2.id == tag1_id

    def test_get_or_create_new(self, app, test_user):
        """Test de get_or_create avec nouveau tag"""
        with app.app_context():
            tag = Tag.get_or_create('nouveau', test_user)
            db.session.commit()

            assert tag.id is not None
            assert tag.name == 'nouveau'

    def test_tag_document_association(self, app, test_user, test_document):
        """Test de l'association tag-document"""
        with app.app_context():
            tag = Tag(name='associe', owner_id=test_user)
            db.session.add(tag)
            db.session.commit()

            doc = Document.query.get(test_document)
            doc.tags.append(tag)
            db.session.commit()

            # Verifier l'association
            assert tag in doc.tags.all()
            assert doc in tag.documents

    def test_unique_constraint(self, app, test_user):
        """Test de la contrainte d'unicite nom+owner"""
        with app.app_context():
            tag1 = Tag(name='unique', owner_id=test_user)
            db.session.add(tag1)
            db.session.commit()

            tag2 = Tag(name='unique', owner_id=test_user)
            db.session.add(tag2)

            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()

    def test_search_by_name(self, app, test_user):
        """Test de recherche de tags par nom"""
        with app.app_context():
            for name in ['admin', 'administratif', 'sante']:
                db.session.add(Tag(name=name, owner_id=test_user))
            db.session.commit()

            results = Tag.search_by_name('admin', test_user)
            assert len(results) == 2


class TestSearchService:
    """Tests pour le service de recherche"""

    def test_global_search_empty(self, app, test_user):
        """Test de recherche globale vide"""
        from app.services.search_service import SearchService
        with app.app_context():
            results = SearchService.global_search(test_user, '')
            assert results['documents'] == []
            assert results['tasks'] == []

    def test_statistics(self, app, test_user, test_document):
        """Test des statistiques"""
        from app.services.search_service import SearchService
        with app.app_context():
            stats = SearchService.get_statistics(test_user)
            assert stats['total_documents'] == 1
            assert 'total_size_formatted' in stats
            assert 'docs_by_month' in stats


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
