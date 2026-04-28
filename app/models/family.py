# modele famille + liens partage : espace famille, droits de chacuns, lien de partage temporaire + sécu
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import validates
from . import db


class Family(db.Model):
    __tablename__ = 'families'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    #1 createur par famille
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator = db.relationship('User', backref=db.backref('created_families', lazy='dynamic'),
                               foreign_keys=[creator_id])
    members = db.relationship('FamilyMember', backref='family', lazy='dynamic',
                               cascade='all, delete-orphan')
    #famille actuelle
    def __repr__(self):
        return f'<Family {self.name}>'

    #membres de la famille
    @property
    def member_count(self):
        return self.members.count()
    #check si membre de la famille
    def is_member(self, user_id):
        return self.members.filter_by(user_id=user_id).first() is not None

    #recup le role du membre
    def get_member_role(self, user_id):
        member = self.members.filter_by(user_id=user_id).first()
        return member.role if member else None

    #check perm du membre pour gerer famille
    def can_manage(self, user_id):
        if self.creator_id == user_id:
            return True
        member = self.members.filter_by(user_id=user_id).first()
        return member and member.role in FamilyMember.MANAGER_ROLES

#relier user à une famille, avec role et droits : qui , depis quand , quel role , qui la invité?
class FamilyMember(db.Model):
    __tablename__ = 'family_members'

    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    role = db.Column(db.String(30), nullable=False, default='lecteur')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    invited_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    user = db.relationship('User', backref=db.backref('family_memberships', lazy='dynamic'),
                            foreign_keys=[user_id])
    inviter = db.relationship('User', foreign_keys=[invited_by])

    __table_args__ = (
        db.UniqueConstraint('family_id', 'user_id', name='uq_family_member'),
    )

    ROLES = {
        'responsable': 'Responsable - Administration complete (max 2)',
        'admin': 'Administrateur - Gestion complete',
        'parent': 'Parent - Gestion documents et taches',
        'gestionnaire': 'Gestionnaire - Ajout/suppresion de documents',
        'enfant': 'Enfant - Acces limite supervise',
        'editeur': 'Editeur - Modification des documents partages',
        'lecteur': 'Lecteur - Consultation uniquement',
        'invite': 'Invite - Acces temporaire limite'
    }

    # roles qui peuvent gerer la fam
    MANAGER_ROLES = ('responsable', 'admin', 'parent', 'gestionnaire')

    # validation : refuse les roles hors de la liste ROLES
    @validates('role')
    def validate_role(self, key, value):
        if value not in self.ROLES:
            raise ValueError(f"Role invalide: {value}. Roles autorises : {list(self.ROLES.keys())}")
        return value

    def __repr__(self):
        return f'<FamilyMember family={self.family_id} user={self.user_id} role={self.role}>'

#lien partage
class ShareLink(db.Model):
    __tablename__ = 'share_links'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    max_uses = db.Column(db.Integer, default=1)
    use_count = db.Column(db.Integer, default=0)
    is_revoked = db.Column(db.Boolean, default=False)
    granted_role = db.Column(db.String(30), default='lecteur')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    creator = db.relationship('User', backref=db.backref('share_links', lazy='dynamic'))
    document = db.relationship('Document', backref=db.backref('share_links', lazy='dynamic'))

    def __repr__(self):
        return f'<ShareLink {self.token[:8]}...>'

    #check si lien tjrs valide
    @property
    def is_valid(self):
        if self.is_revoked:
            return False
        if self.expires_at < datetime.utcnow():
            return False
        if self.use_count >= self.max_uses:
            return False
        return True

    #check nb d'utilisation
    @property
    def remaining_uses(self):
        return max(0, self.max_uses - self.use_count)

    #limite de 1 utilisation
    def use(self):
        self.use_count += 1

    #anuler lien
    def revoke(self):
        """revoque lien"""
        self.is_revoked = True

    #token unique por l'invité
    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(48)
    #creation du lien controlé
    @staticmethod
    def create_share_link(document_id=None, family_id=None, created_by=None,
                           expires_hours=24, max_uses=1, granted_role='lecteur'):
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
    def get_active_links_for_document(document_id, limit=50):
        now = datetime.utcnow()
        return ShareLink.query.filter(
            ShareLink.document_id == document_id,
            ShareLink.expires_at > now,
            ShareLink.is_revoked == False
        ).order_by(ShareLink.created_at.desc()).limit(limit).all()

    @staticmethod
    def cleanup_expired():
        """supprime liens expires"""
        expired = ShareLink.query.filter(
            ShareLink.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()
        return expired
