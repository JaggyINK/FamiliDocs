# modele tags docs
from datetime import datetime
from . import db


# table asso docs <-> tags (N:N)
document_tags = db.Table('document_tags',
    db.Column('document_id', db.Integer, db.ForeignKey('documents.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)


class Tag(db.Model):
    """tag/etiquette"""

    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, index=True)
    color = db.Column(db.String(7), default='#6c757d')
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship('User', backref=db.backref('tags', lazy='dynamic'))
    documents = db.relationship('Document', secondary=document_tags,
                                 backref=db.backref('tags', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('name', 'owner_id', name='uq_tag_name_owner'),
    )

    def __repr__(self):
        return f'<Tag {self.name}>'

    @property
    def document_count(self):
        """nb docs avec ce tag"""
        return len(self.documents)

    @staticmethod
    def get_user_tags(user_id):
        """recup tags user"""
        return Tag.query.filter_by(owner_id=user_id).order_by(Tag.name).all()

    @staticmethod
    def get_or_create(name, owner_id, color='#6c757d'):
        """recup ou cree tag"""
        tag = Tag.query.filter_by(name=name.strip().lower(), owner_id=owner_id).first()
        if not tag:
            tag = Tag(name=name.strip().lower(), owner_id=owner_id, color=color)
            db.session.add(tag)
        return tag

    @staticmethod
    def search_by_name(query, owner_id):
        """recherche tags par nom"""
        return Tag.query.filter(
            Tag.owner_id == owner_id,
            Tag.name.ilike(f'%{query}%')
        ).all()
