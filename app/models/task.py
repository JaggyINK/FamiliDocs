"""
Modèle Task - Gestion des tâches et échéances
"""
from datetime import datetime, date, timedelta
from . import db


class Task(db.Model):
    """Modèle représentant une tâche ou échéance"""

    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=False)
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, urgent
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    reminder_days = db.Column(db.Integer, default=7)  # Jours avant l'échéance pour le rappel

    # Relations
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)

    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Task {self.title}>'

    @property
    def is_overdue(self):
        """Vérifie si la tâche est en retard"""
        if self.status in ['completed', 'cancelled']:
            return False
        return self.due_date < date.today()

    @property
    def is_due_soon(self):
        """Vérifie si la tâche arrive à échéance bientôt"""
        if self.status in ['completed', 'cancelled']:
            return False
        return date.today() <= self.due_date <= date.today() + timedelta(days=self.reminder_days)

    @property
    def days_until_due(self):
        """Retourne le nombre de jours avant l'échéance"""
        delta = self.due_date - date.today()
        return delta.days

    @property
    def priority_color(self):
        """Retourne la couleur associée à la priorité"""
        colors = {
            'low': 'secondary',
            'normal': 'primary',
            'high': 'warning',
            'urgent': 'danger'
        }
        return colors.get(self.priority, 'primary')

    @property
    def status_color(self):
        """Retourne la couleur associée au statut"""
        colors = {
            'pending': 'secondary',
            'in_progress': 'info',
            'completed': 'success',
            'cancelled': 'dark'
        }
        return colors.get(self.status, 'secondary')

    def mark_completed(self):
        """Marque la tâche comme terminée"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()

    def mark_in_progress(self):
        """Marque la tâche comme en cours"""
        self.status = 'in_progress'

    def mark_cancelled(self):
        """Marque la tâche comme annulée"""
        self.status = 'cancelled'

    @staticmethod
    def get_upcoming_tasks(user_id, days=30):
        """Récupère les tâches à venir pour un utilisateur"""
        from sqlalchemy import and_
        end_date = date.today() + timedelta(days=days)
        return Task.query.filter(
            and_(
                Task.owner_id == user_id,
                Task.due_date <= end_date,
                Task.status.notin_(['completed', 'cancelled'])
            )
        ).order_by(Task.due_date).all()

    @staticmethod
    def get_overdue_tasks(user_id):
        """Récupère les tâches en retard pour un utilisateur"""
        return Task.query.filter(
            Task.owner_id == user_id,
            Task.due_date < date.today(),
            Task.status.notin_(['completed', 'cancelled'])
        ).order_by(Task.due_date).all()

    @staticmethod
    def create_from_document(document, title=None, due_date=None, owner_id=None):
        """Crée une tâche à partir d'un document"""
        if not due_date and document.expiry_date:
            due_date = document.expiry_date

        if not due_date:
            raise ValueError("Une date d'échéance est requise")

        task = Task(
            title=title or f"Renouveler: {document.name}",
            description=f"Document lié: {document.name}",
            due_date=due_date,
            owner_id=owner_id or document.owner_id,
            document_id=document.id
        )
        return task
