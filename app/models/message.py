# modele message chat familial
from datetime import datetime
from . import db


class Message(db.Model):
    """msg chat famille"""

    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey('families.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_announcement = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    family = db.relationship('Family', backref=db.backref('messages', lazy='dynamic',
                                                           order_by='Message.created_at.desc()'))
    sender = db.relationship('User', backref=db.backref('messages_sent', lazy='dynamic'))

    def __repr__(self):
        return f'<Message {self.id} by user {self.sender_id}>'

    @property
    def is_edited(self):
        """check si msg modifie"""
        if self.updated_at and self.created_at:
            # + de 1s de diff = edite
            return (self.updated_at - self.created_at).total_seconds() > 1
        return False

    def can_edit(self, user_id):
        """check si user peut edit msg"""
        return self.sender_id == user_id and not self.is_deleted

    def can_delete(self, user_id, is_admin=False):
        """check suppresion msg"""
        if self.sender_id == user_id:
            return True
        if is_admin:
            return True
        # verif si admin de la famille
        from app.models.family import FamilyMember
        member = FamilyMember.query.filter_by(
            family_id=self.family_id, user_id=user_id
        ).first()
        return member and member.role in ('admin', 'responsable')

    @staticmethod
    def get_family_messages(family_id, limit=50, offset=0):
        """recup msgs famille"""
        return Message.query.filter_by(
            family_id=family_id,
            is_deleted=False
        ).order_by(Message.created_at.desc())\
         .offset(offset)\
         .limit(limit)\
         .all()

    @staticmethod
    def get_announcements(family_id, limit=5):
        """recup annonces"""
        return Message.query.filter_by(
            family_id=family_id,
            is_announcement=True,
            is_deleted=False
        ).order_by(Message.created_at.desc())\
         .limit(limit)\
         .all()

    @staticmethod
    def create_message(family_id, sender_id, content, is_announcement=False):
        """cree msg"""
        message = Message(
            family_id=family_id,
            sender_id=sender_id,
            content=content.strip(),
            is_announcement=is_announcement
        )
        db.session.add(message)
        return message

    def soft_delete(self):
        """suppresion douce"""
        self.is_deleted = True
        self.content = "[Message supprime]"
