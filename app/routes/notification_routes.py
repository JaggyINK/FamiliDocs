# routes notifs
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user

from app.models import db
from app.models.notification import Notification
from app.services.notification_service import NotificationService

notification_bp = Blueprint('notification', __name__, url_prefix='/notifications')


@notification_bp.route('/')
@login_required
def list_notifications():
    """liste notifs user"""
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('type', '')
    unread_only = request.args.get('unread', '') == '1'

    query = Notification.query.filter_by(user_id=current_user.id)

    if filter_type:
        query = query.filter_by(type=filter_type)

    if unread_only:
        query = query.filter_by(is_read=False)

    # exclure expirees
    from datetime import datetime
    query = query.filter(
        db.or_(
            Notification.expires_at.is_(None),
            Notification.expires_at > datetime.utcnow()
        )
    )

    notifications = query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    # stats
    stats = {
        'total': Notification.query.filter_by(user_id=current_user.id).count(),
        'unread': Notification.get_unread_count(current_user.id)
    }

    return render_template(
        'notifications.html',
        notifications=notifications,
        stats=stats,
        filter_type=filter_type,
        unread_only=unread_only,
        notification_types=Notification.NOTIFICATION_TYPES
    )


@notification_bp.route('/count')
@login_required
def get_count():
    """API nb notifs non lues"""
    count = Notification.get_unread_count(current_user.id)
    return jsonify({'count': count})


@notification_bp.route('/summary')
@login_required
def get_summary():
    """API resume notifs"""
    summary = NotificationService.get_notification_summary(current_user.id)

    # convert dict pr JSON
    summary['recent'] = [{
        'id': n.id,
        'type': n.type,
        'title': n.title,
        'message': n.message,
        'icon': n.icon,
        'priority_color': n.priority_color,
        'time_ago': n.time_ago,
        'is_read': n.is_read
    } for n in summary['recent']]

    return jsonify(summary)


@notification_bp.route('/recent')
@login_required
def get_recent():
    """API notifs recentes dropdown"""
    notifications = Notification.get_user_notifications(
        current_user.id,
        unread_only=False,
        limit=10
    )

    result = [{
        'id': n.id,
        'type': n.type,
        'title': n.title,
        'message': n.message[:100] + '...' if len(n.message) > 100 else n.message,
        'icon': n.icon,
        'priority_color': n.priority_color,
        'time_ago': n.time_ago,
        'is_read': n.is_read,
        'url': _get_notification_url(n)
    } for n in notifications]

    return jsonify({
        'notifications': result,
        'unread_count': Notification.get_unread_count(current_user.id)
    })


def _get_notification_url(notification):
    """url notif"""
    if notification.task_id:
        return url_for('task.view', task_id=notification.task_id)
    elif notification.document_id:
        return url_for('document.view', document_id=notification.document_id)
    return url_for('notification.list_notifications')


@notification_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """marque notif lue"""
    notification = Notification.query.get_or_404(notification_id)

    if notification.user_id != current_user.id:
        return jsonify({'error': 'Non autorise'}), 403

    notification.mark_as_read()
    db.session.commit()

    if request.is_json:
        return jsonify({'success': True})

    # redir element lie
    redirect_url = _get_notification_url(notification)
    return redirect(redirect_url)


@notification_bp.route('/<int:notification_id>/unread', methods=['POST'])
@login_required
def mark_as_unread(notification_id):
    """marque notif non lue"""
    notification = Notification.query.get_or_404(notification_id)

    if notification.user_id != current_user.id:
        return jsonify({'error': 'Non autorise'}), 403

    notification.mark_as_unread()
    db.session.commit()

    if request.is_json:
        return jsonify({'success': True})

    return redirect(url_for('notification.list_notifications'))


@notification_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_as_read():
    """tout marquer lu"""
    Notification.mark_all_as_read(current_user.id)

    if request.is_json:
        return jsonify({'success': True})

    flash('Toutes les notifications ont ete marquees comme lues.', 'success')
    return redirect(url_for('notification.list_notifications'))


@notification_bp.route('/<int:notification_id>/delete', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """suppr notif"""
    notification = Notification.query.get_or_404(notification_id)

    if notification.user_id != current_user.id:
        if request.is_json:
            return jsonify({'error': 'Non autorise'}), 403
        flash('Non autorise.', 'danger')
        return redirect(url_for('notification.list_notifications'))

    db.session.delete(notification)
    db.session.commit()

    if request.is_json:
        return jsonify({'success': True})

    flash('Notification supprimee.', 'success')
    return redirect(url_for('notification.list_notifications'))


@notification_bp.route('/delete-read', methods=['POST'])
@login_required
def delete_read_notifications():
    """suppr notifs lues"""
    deleted = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=True
    ).delete()

    db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'deleted': deleted})

    flash(f'{deleted} notification(s) supprimee(s).', 'success')
    return redirect(url_for('notification.list_notifications'))


@notification_bp.route('/check-due', methods=['POST'])
@login_required
def check_due_notifications():
    """check echeances cree notifs"""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin requis'}), 403

    count = NotificationService.check_and_create_due_notifications()

    if request.is_json:
        return jsonify({'success': True, 'notifications_created': count})

    flash(f'{count} notification(s) creee(s) pour les echeances.', 'success')
    return redirect(url_for('admin.dashboard'))


@notification_bp.route('/cleanup', methods=['POST'])
@login_required
def cleanup_notifications():
    """cleanup notifs (admin)"""
    if not current_user.is_admin():
        return jsonify({'error': 'Admin requis'}), 403

    result = NotificationService.cleanup()

    if request.is_json:
        return jsonify({'success': True, **result})

    flash(f"Nettoyage effectue: {result['expired_deleted']} expirees, {result['old_deleted']} anciennes.", 'success')
    return redirect(url_for('admin.dashboard'))
