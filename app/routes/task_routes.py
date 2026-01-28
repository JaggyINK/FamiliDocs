"""
Routes de gestion des tâches et échéances
"""
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.models import db
from app.models.task import Task
from app.models.document import Document
from app.models.log import Log

task_bp = Blueprint('task', __name__, url_prefix='/tasks')


@task_bp.route('/')
@login_required
def list_tasks():
    """Liste toutes les tâches de l'utilisateur"""
    # Filtres
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')

    query = Task.query.filter_by(owner_id=current_user.id)

    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)

    tasks = query.order_by(Task.due_date).all()

    # Statistiques
    stats = {
        'total': Task.query.filter_by(owner_id=current_user.id).count(),
        'pending': Task.query.filter_by(owner_id=current_user.id, status='pending').count(),
        'in_progress': Task.query.filter_by(owner_id=current_user.id, status='in_progress').count(),
        'completed': Task.query.filter_by(owner_id=current_user.id, status='completed').count(),
        'overdue': len(Task.get_overdue_tasks(current_user.id))
    }

    return render_template(
        'tasks.html',
        tasks=tasks,
        stats=stats,
        selected_status=status,
        selected_priority=priority
    )


@task_bp.route('/calendar')
@login_required
def calendar():
    """Vue calendrier des tâches"""
    # Récupérer toutes les tâches actives
    tasks = Task.query.filter(
        Task.owner_id == current_user.id,
        Task.status.notin_(['completed', 'cancelled'])
    ).order_by(Task.due_date).all()

    # Formater pour le calendrier
    events = []
    for task in tasks:
        events.append({
            'id': task.id,
            'title': task.title,
            'start': task.due_date.isoformat(),
            'color': _get_task_color(task),
            'url': url_for('task.view', task_id=task.id)
        })

    return render_template('calendar.html', events=events)


def _get_task_color(task):
    """Retourne la couleur pour une tâche dans le calendrier"""
    if task.is_overdue:
        return '#dc3545'  # Rouge
    if task.priority == 'urgent':
        return '#fd7e14'  # Orange
    if task.priority == 'high':
        return '#ffc107'  # Jaune
    return '#0d6efd'  # Bleu


@task_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Création d'une nouvelle tâche"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date_str = request.form.get('due_date', '').strip()
        priority = request.form.get('priority', 'normal')
        document_id = request.form.get('document_id', type=int)
        reminder_days = request.form.get('reminder_days', 7, type=int)

        # Validation
        if not title:
            flash('Le titre est obligatoire.', 'warning')
            return redirect(url_for('task.create'))

        if not due_date_str:
            flash('La date d\'échéance est obligatoire.', 'warning')
            return redirect(url_for('task.create'))

        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Format de date invalide.', 'warning')
            return redirect(url_for('task.create'))

        # Vérifier le document si spécifié
        if document_id:
            document = Document.query.get(document_id)
            if not document or document.owner_id != current_user.id:
                flash('Document invalide.', 'danger')
                return redirect(url_for('task.create'))

        task = Task(
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            owner_id=current_user.id,
            document_id=document_id if document_id else None,
            reminder_days=reminder_days
        )

        db.session.add(task)
        db.session.commit()

        Log.create_log(
            user_id=current_user.id,
            action='task_create',
            details=f"Tâche '{title}' créée"
        )
        db.session.commit()

        flash(f'Tâche "{title}" créée avec succès.', 'success')
        return redirect(url_for('task.view', task_id=task.id))

    # Documents pour lier à la tâche
    documents = Document.query.filter_by(owner_id=current_user.id).order_by(Document.name).all()

    return render_template('create_task.html', documents=documents)


@task_bp.route('/<int:task_id>')
@login_required
def view(task_id):
    """Affiche les détails d'une tâche"""
    task = Task.query.get_or_404(task_id)

    if task.owner_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas accès à cette tâche.', 'danger')
        return redirect(url_for('task.list_tasks'))

    return render_template('view_task.html', task=task)


@task_bp.route('/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(task_id):
    """Modification d'une tâche"""
    task = Task.query.get_or_404(task_id)

    if task.owner_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas le droit de modifier cette tâche.', 'danger')
        return redirect(url_for('task.list_tasks'))

    if request.method == 'POST':
        task.title = request.form.get('title', '').strip()
        task.description = request.form.get('description', '').strip()
        task.priority = request.form.get('priority', 'normal')
        task.reminder_days = request.form.get('reminder_days', 7, type=int)

        due_date_str = request.form.get('due_date', '').strip()
        if due_date_str:
            try:
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Format de date invalide.', 'warning')
                return redirect(url_for('task.edit', task_id=task_id))

        document_id = request.form.get('document_id', type=int)
        task.document_id = document_id if document_id else None

        db.session.commit()

        Log.create_log(
            user_id=current_user.id,
            action='task_edit',
            details=f"Tâche '{task.title}' modifiée"
        )
        db.session.commit()

        flash('Tâche mise à jour avec succès.', 'success')
        return redirect(url_for('task.view', task_id=task_id))

    documents = Document.query.filter_by(owner_id=current_user.id).order_by(Document.name).all()

    return render_template('edit_task.html', task=task, documents=documents)


@task_bp.route('/<int:task_id>/status/<status>', methods=['POST'])
@login_required
def change_status(task_id, status):
    """Change le statut d'une tâche"""
    task = Task.query.get_or_404(task_id)

    if task.owner_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas le droit de modifier cette tâche.', 'danger')
        return redirect(url_for('task.list_tasks'))

    valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
    if status not in valid_statuses:
        flash('Statut invalide.', 'danger')
        return redirect(url_for('task.view', task_id=task_id))

    old_status = task.status

    if status == 'completed':
        task.mark_completed()
    elif status == 'in_progress':
        task.mark_in_progress()
    elif status == 'cancelled':
        task.mark_cancelled()
    else:
        task.status = status

    db.session.commit()

    Log.create_log(
        user_id=current_user.id,
        action='task_edit',
        details=f"Statut de '{task.title}' changé de '{old_status}' à '{status}'"
    )
    db.session.commit()

    flash(f'Statut de la tâche mis à jour.', 'success')

    # Redirection vers la page précédente ou la liste des tâches
    return redirect(request.referrer or url_for('task.list_tasks'))


@task_bp.route('/<int:task_id>/delete', methods=['POST'])
@login_required
def delete(task_id):
    """Suppression d'une tâche"""
    task = Task.query.get_or_404(task_id)

    if task.owner_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas le droit de supprimer cette tâche.', 'danger')
        return redirect(url_for('task.list_tasks'))

    task_title = task.title
    db.session.delete(task)
    db.session.commit()

    flash(f'Tâche "{task_title}" supprimée.', 'success')
    return redirect(url_for('task.list_tasks'))


@task_bp.route('/overdue')
@login_required
def overdue():
    """Liste des tâches en retard"""
    tasks = Task.get_overdue_tasks(current_user.id)
    return render_template('overdue_tasks.html', tasks=tasks)


@task_bp.route('/upcoming')
@login_required
def upcoming():
    """Liste des tâches à venir"""
    days = request.args.get('days', 30, type=int)
    tasks = Task.get_upcoming_tasks(current_user.id, days=days)
    return render_template('upcoming_tasks.html', tasks=tasks, days=days)
