"""
T21 - Tests des familles : creation, invitation, roles, exclusion
"""
import pytest
from app.models import db
from app.models.family import Family, FamilyMember, ShareLink
from app.models.user import User
from app.services.auth_service import AuthService


class TestFamilyCreation:
    """Tests de creation de familles"""

    def test_create_family(self, app, test_user):
        """Test creation d'une famille"""
        family = Family(
            name='Ma Famille',
            description='Test',
            creator_id=test_user.id
        )
        db.session.add(family)
        db.session.commit()
        assert family.id is not None
        assert family.name == 'Ma Famille'
        assert family.creator_id == test_user.id

    def test_create_family_route(self, auth_client, test_user):
        """Test creation via route"""
        response = auth_client.post('/families/create', data={
            'name': 'Nouvelle Famille',
            'description': 'Description test'
        }, follow_redirects=True)
        assert response.status_code == 200
        family = Family.query.filter_by(name='Nouvelle Famille').first()
        assert family is not None

    def test_list_families(self, auth_client, test_family):
        """Test liste des familles"""
        response = auth_client.get('/families')
        assert response.status_code == 200
        assert b'Famille Test' in response.data


class TestFamilyMembers:
    """Tests des membres de famille"""

    def test_add_member(self, app, test_user, second_user, test_family):
        """Test ajout d'un membre"""
        member = FamilyMember(
            family_id=test_family.id,
            user_id=second_user.id,
            role='member'
        )
        db.session.add(member)
        db.session.commit()
        assert member.id is not None

    def test_family_member_roles(self, app, test_user, test_family):
        """Test des roles de membre"""
        member = FamilyMember.query.filter_by(
            family_id=test_family.id,
            user_id=test_user.id
        ).first()
        assert member is not None
        assert member.role == 'chef_famille'

    def test_exclude_member(self, app, test_user, second_user, test_family):
        """Test exclusion d'un membre"""
        member = FamilyMember(
            family_id=test_family.id,
            user_id=second_user.id,
            role='member'
        )
        db.session.add(member)
        db.session.commit()

        db.session.delete(member)
        db.session.commit()

        removed = FamilyMember.query.filter_by(
            family_id=test_family.id,
            user_id=second_user.id
        ).first()
        assert removed is None


class TestFamilyInvitation:
    """Tests des invitations"""

    def test_create_invite_link(self, app, test_user, test_family):
        """Test creation d'un lien d'invitation"""
        link = ShareLink.create_share_link(
            family_id=test_family.id,
            created_by=test_user.id,
            granted_role='member',
            max_uses=5
        )
        db.session.commit()
        assert link.token is not None
        assert link.is_valid

    def test_invite_link_expiration(self, app, test_user, test_family):
        """Test expiration du lien"""
        from datetime import datetime, timedelta
        link = ShareLink(
            token=ShareLink.generate_token(),
            family_id=test_family.id,
            created_by=test_user.id,
            granted_role='member',
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        db.session.add(link)
        db.session.commit()
        assert not link.is_valid
