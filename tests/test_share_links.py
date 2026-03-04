"""
T23 - Tests des liens de partage : creation, expiration, utilisation
"""
import pytest
from datetime import datetime, timedelta
from app.models import db
from app.models.family import ShareLink, Family, FamilyMember


class TestShareLinkCreation:
    """Tests creation de liens de partage"""

    def test_create_share_link(self, app, test_user, test_family):
        """Test creation d'un lien de partage"""
        link = ShareLink.create_share_link(
            family_id=test_family.id,
            created_by=test_user.id,
            granted_role='member'
        )
        db.session.commit()
        assert link.token is not None
        assert len(link.token) > 10

    def test_link_has_default_expiry(self, app, test_user, test_family):
        """Test que le lien a une expiration par defaut"""
        link = ShareLink.create_share_link(
            family_id=test_family.id,
            created_by=test_user.id,
            granted_role='member'
        )
        db.session.commit()
        assert link.is_valid


class TestShareLinkExpiration:
    """Tests d'expiration des liens"""

    def test_expired_link_invalid(self, app, test_user, test_family):
        """Test qu'un lien expire est invalide"""
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

    def test_future_link_valid(self, app, test_user, test_family):
        """Test qu'un lien non expire est valide"""
        link = ShareLink(
            token=ShareLink.generate_token(),
            family_id=test_family.id,
            created_by=test_user.id,
            granted_role='member',
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(link)
        db.session.commit()
        assert link.is_valid


class TestShareLinkUsage:
    """Tests d'utilisation des liens"""

    def test_max_uses_reached(self, app, test_user, test_family):
        """Test limite d'utilisation"""
        link = ShareLink(
            token=ShareLink.generate_token(),
            family_id=test_family.id,
            created_by=test_user.id,
            granted_role='member',
            expires_at=datetime.utcnow() + timedelta(days=1),
            max_uses=1,
            use_count=1
        )
        db.session.add(link)
        db.session.commit()
        assert not link.is_valid

    def test_link_use_count_increment(self, app, test_user, test_family):
        """Test increment du compteur d'utilisation"""
        link = ShareLink.create_share_link(
            family_id=test_family.id,
            created_by=test_user.id,
            granted_role='member',
            max_uses=5
        )
        db.session.commit()

        link.use_count += 1
        db.session.commit()
        assert link.use_count == 1
        assert link.is_valid

    def test_active_links_for_family(self, app, test_user, test_family):
        """Test recuperation des liens actifs"""
        link = ShareLink.create_share_link(
            family_id=test_family.id,
            created_by=test_user.id,
            granted_role='member',
            expires_hours=168
        )
        db.session.commit()

        links = ShareLink.query.filter_by(family_id=test_family.id).all()
        assert len(links) >= 1
