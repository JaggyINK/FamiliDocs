"""
T22 - Tests du chat : envoi, edition, suppression messages, annonces
"""
import pytest
from app.models import db
from app.models.message import Message
from app.models.family import Family, FamilyMember


class TestMessageCRUD:
    """Tests CRUD des messages"""

    def test_send_message(self, app, test_user, test_family):
        """Test envoi d'un message"""
        msg = Message(
            content='Bonjour tout le monde',
            sender_id=test_user.id,
            family_id=test_family.id
        )
        db.session.add(msg)
        db.session.commit()
        assert msg.id is not None
        assert msg.content == 'Bonjour tout le monde'

    def test_edit_message(self, app, test_user, test_family):
        """Test edition d'un message"""
        msg = Message(
            content='Message original',
            sender_id=test_user.id,
            family_id=test_family.id
        )
        db.session.add(msg)
        db.session.commit()

        msg.content = 'Message modifie'
        db.session.commit()

        updated = db.session.get(Message, msg.id)
        assert updated.content == 'Message modifie'

    def test_delete_message(self, app, test_user, test_family):
        """Test suppression d'un message"""
        msg = Message(
            content='A supprimer',
            sender_id=test_user.id,
            family_id=test_family.id
        )
        db.session.add(msg)
        db.session.commit()
        msg_id = msg.id

        db.session.delete(msg)
        db.session.commit()

        deleted = db.session.get(Message, msg_id)
        assert deleted is None

    def test_announcement_message(self, app, test_user, test_family):
        """Test message de type annonce"""
        msg = Message(
            content='Annonce importante',
            sender_id=test_user.id,
            family_id=test_family.id,
            is_announcement=True
        )
        db.session.add(msg)
        db.session.commit()
        assert msg.is_announcement is True


class TestChatRoute:
    """Tests des routes chat"""

    def test_chat_page_requires_auth(self, client):
        """Test que le chat necessite l'authentification"""
        response = client.get('/families/1/chat')
        assert response.status_code in [302, 308]

    def test_chat_page_loads(self, auth_client, test_family):
        """Test chargement de la page chat"""
        response = auth_client.get(f'/families/{test_family.id}/chat')
        assert response.status_code == 200
