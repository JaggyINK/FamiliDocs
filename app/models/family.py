"""
Modele Family - Groupes familiaux et liens de partage securises
"""
import secrets
from datetime import datetime, timedelta
from . import db


class Family(db.Model):
    """Modele representant un groupe familial"""

    __tablename__ = 'families'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    creator = db.relationship('User', backref=db.backref('created_families', lazy='dynamic'),
                               foreign_keys=[creator_id])
    members = db.relationship('FamilyMember', backref='family', lazy='dynamic',
                               cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Family {self.name}>'

    @property
    def member_count(self):
        return self.members.count()

    def is_member(self, user_id):
        """Verifie si un utilisateur est membre"""
        return self.members.filter_by(user_id=user_id).first() is not None

    def get_member_role(self, user_id):
        """Retourne le role d'un membre"""
        member = self.members.filter_by(user_id=user_id).first()
        return member.role if member else None

    def can_manage(self, user_id):
        """Verifie si un utilisateur peut gerer la famille"""
        if self.creator_id == user_id:
            return True
        member = self.members.filter_by(user_id=user_id).first()
        return member and member.role in FamilyMember.MANAGER_ROLES


class FamilyMember(db.Model):
    """Association utilisateur-famille avec role"""

    __tablename__ = 'family_members'

    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(30), nullable=False, default='lecteur')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    invited_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relations
    user = db.relationship('User', backref=db.backref('family_memberships', lazy='dynamic'),
                            foreign_keys=[user_id])
    inviter = db.relationship('User', foreign_keys=[invited_by])

    # Contrainte unicite
    __table_args__ = (
        db.UniqueConstraint('family_id', 'user_id', name='uq_family_member'),
    )

    # Roles disponibles (etendu avec roles familiaux)
    ROLES = {
        'chef_famille': 'Chef de famille - Administration complete (max 2)',
        'admin': 'Administrateur - Gestion complete',
        'parent': 'Parent - Gestion documents et taches',
        'gestionnaire': 'Gestionnaire - Ajout/suppression de documents',
        'enfant': 'Enfant - Acces limite supervise',
        'editeur': 'Editeur - Modification des documents partages',
        'lecteur': 'Lecteur - Consultation uniquement',
        'invite': 'Invite - Acces temporaire limite'
    }

    # Roles qui peuvent gerer
    MANAGER_ROLES = ('chef_famille', 'admin', 'parent', 'gestionnaire')

    def __repr__(self):
        return f'<FamilyMember family={self.family_id} user={self.user_id} role={self.role}>'


class ShareLink(db.Model):
    """Lien de partage securise a usage limite"""

    __tablename__ = 'share_links'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Securite
    expires_at = db.Column(db.DateTime, nullable=False)
    max_uses = db.Column(db.Integer, default=1)
    use_count = db.Column(db.Integer, default=0)
    is_revoked = db.Column(db.Boolean, default=False)

    # Role attribue au destinataire
    granted_role = db.Column(db.String(30), default='lecteur')

    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    creator = db.relationship('User', backref=db.backref('share_links', lazy='dynamic'))
    document = db.relationship('Document', backref=db.backref('share_links', lazy='dynamic'))

    def __repr__(self):
        return f'<ShareLink {self.token[:8]}...>'

    @property
    def is_valid(self):
        """Verifie si le lien est encore utilisable"""
        if self.is_revoked:
            return False
        if self.expires_at < datetime.utcnow():
            return False
        if self.use_count >= self.max_uses:
            return False
        return True

    @property
    def remaining_uses(self):
        return max(0, self.max_uses - self.use_count)

    def use(self):
        """Incremente le compteur d'utilisation"""
        self.use_count += 1

    def revoke(self):
        """Revoque le lien"""
        self.is_revoked = True

    @staticmethod
    def generate_token():
        """Genere un token securise unique"""
        return secrets.token_urlsafe(48)

    @staticmethod
    def create_share_link(document_id=None, family_id=None, created_by=None,
                           expires_hours=24, max_uses=1, granted_role='lecteur'):
        """Cree un nouveau lien de partage securise"""
        link = ShareLink(
            token=ShareLink.generate_token(),
            document_id=document_id,
            family_id=family_id,
            created_by=created_by,
            expires_at=datetime.utcnow() + timedelta(hours=expires_hours),
            max_uses=max_uses,
            granted_role=granted_role
        )
        db.session.add(link)
        return link

    @staticmethod
    def get_active_links_for_document(document_id):
        """Recupere les liens actifs pour un document"""
        now = datetime.utcnow()
        return ShareLink.query.filter(
            ShareLink.document_id == document_id,
            ShareLink.expires_at > now,
            ShareLink.is_revoked == False
        ).all()

    @staticmethod
    def cleanup_expired():
        """Supprime les liens expires"""
        expired = ShareLink.query.filter(
            ShareLink.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()
        return expired
