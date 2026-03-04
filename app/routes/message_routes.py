"""
Routes de messagerie/chat familial - N1
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app.models import db
from app.models.family import Family, FamilyMember
from app.models.message import Message
from app.services.notification_service import NotificationService

message_bp = Blueprint('message', __name__)


@message_bp.route('/families/<int:family_id>/chat')
@login_required
def chat(family_id):
    """Page de chat familial"""
    family = Family.query.get_or_404(family_id)

    if not family.is_member(current_user.id):
        flash("Vous n'etes pas membre de ce groupe.", 'danger')
        return redirect(url_for('family.list_families'))

    # Recuperer les messages (les plus recents en premier)
    messages = Message.get_family_messages(family_id, limit=100)
    # Inverser pour affichage chronologique
    messages = list(reversed(messages))

    # Annonces importantes
    announcements = Message.get_announcements(family_id, limit=3)

    # Role de l'utilisateur pour savoir s'il peut faire des annonces
    current_member = FamilyMember.query.filter_by(
        family_id=family_id, user_id=current_user.id
    ).first()
    can_announce = current_member and current_member.role in ('admin', 'chef_famille', 'parent')

    return render_template(
        'chat.html',
        family=family,
        messages=messages,
        announcements=announcements,
        can_announce=can_announce
    )


@message_bp.route('/families/<int:family_id>/chat/send', methods=['POST'])
@login_required
def send_message(family_id):
    """Envoie un message dans le chat"""
    family = Family.query.get_or_404(family_id)

    if not family.is_member(current_user.id):
        flash("Vous n'etes pas membre de ce groupe.", 'danger')
        return redirect(url_for('family.list_families'))

    content = request.form.get('content', '').strip()
    is_announcement = request.form.get('is_announcement') == 'on'

    if not content:
        flash('Le message ne peut pas etre vide.', 'warning')
        return redirect(url_for('message.chat', family_id=family_id))

    if len(content) > 2000:
        flash('Le message est trop long (max 2000 caracteres).', 'warning')
        return redirect(url_for('message.chat', family_id=family_id))

    # Verifier si l'utilisateur peut poster des annonces
    if is_announcement:
        member = FamilyMember.query.filter_by(
            family_id=family_id, user_id=current_user.id
        ).first()
        if not member or member.role not in ('admin', 'chef_famille', 'parent'):
            is_announcement = False

    message = Message.create_message(
        family_id=family_id,
        sender_id=current_user.id,
        content=content,
        is_announcement=is_announcement
    )
    db.session.commit()

    # Notifier les membres pour les annonces
    if is_announcement:
        members = FamilyMember.query.filter(
            FamilyMember.family_id == family_id,
            FamilyMember.user_id != current_user.id
        ).all()
        for member in members:
            NotificationService.notify_system(
                member.user_id,
                f'Annonce de {current_user.first_name}',
                f'{family.name} : {content[:100]}...' if len(content) > 100 else f'{family.name} : {content}'
            )

    return redirect(url_for('message.chat', family_id=family_id))


@message_bp.route('/messages/<int:message_id>/edit', methods=['POST'])
@login_required
def edit_message(message_id):
    """Modifie un message"""
    message = Message.query.get_or_404(message_id)

    if not message.can_edit(current_user.id):
        flash("Vous ne pouvez pas modifier ce message.", 'danger')
        return redirect(url_for('message.chat', family_id=message.family_id))

    content = request.form.get('content', '').strip()
    if not content:
        flash('Le message ne peut pas etre vide.', 'warning')
        return redirect(url_for('message.chat', family_id=message.family_id))

    if len(content) > 2000:
        flash('Le message est trop long (max 2000 caracteres).', 'warning')
        return redirect(url_for('message.chat', family_id=message.family_id))

    message.content = content
    db.session.commit()

    flash('Message modifie.', 'success')
    return redirect(url_for('message.chat', family_id=message.family_id))


@message_bp.route('/messages/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(message_id):
    """Supprime un message (soft delete)"""
    message = Message.query.get_or_404(message_id)

    if not message.can_delete(current_user.id, current_user.is_admin()):
        flash("Vous ne pouvez pas supprimer ce message.", 'danger')
        return redirect(url_for('message.chat', family_id=message.family_id))

    family_id = message.family_id
    message.soft_delete()
    db.session.commit()

    flash('Message supprime.', 'success')
    return redirect(url_for('message.chat', family_id=family_id))


@message_bp.route('/families/<int:family_id>/chat/load-more')
@login_required
def load_more_messages(family_id):
    """Charge plus de messages (AJAX)"""
    family = Family.query.get_or_404(family_id)

    if not family.is_member(current_user.id):
        return jsonify({'error': 'Non autorise'}), 403

    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 50, type=int)

    messages = Message.get_family_messages(family_id, limit=limit, offset=offset)

    return jsonify({
        'messages': [{
            'id': m.id,
            'content': m.content,
            'sender_name': m.sender.full_name,
            'sender_id': m.sender_id,
            'is_announcement': m.is_announcement,
            'is_edited': m.is_edited,
            'created_at': m.created_at.strftime('%d/%m/%Y %H:%M')
        } for m in messages],
        'has_more': len(messages) == limit
    })
