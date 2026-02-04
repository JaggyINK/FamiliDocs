"""
Service de recherche avancee - Recherche multi-criteres
"""
from sqlalchemy import or_, and_, func
from datetime import date, timedelta

from app.models import db
from app.models.document import Document
from app.models.folder import Folder
from app.models.tag import Tag, document_tags
from app.models.task import Task


class SearchService:
    """Service pour la recherche avancee dans les documents et taches"""

    @staticmethod
    def search_documents(user_id, query=None, file_type=None, folder_id=None,
                          tags=None, date_from=None, date_to=None,
                          confidentiality=None, expired_only=False,
                          sort_by='updated_at', sort_order='desc'):
        """
        Recherche avancee de documents avec filtres multiples.
        Retourne une liste de documents correspondants.
        """
        base_query = Document.query.filter_by(owner_id=user_id)

        # Recherche textuelle (nom + description)
        if query:
            pattern = f'%{query}%'
            base_query = base_query.filter(
                or_(
                    Document.name.ilike(pattern),
                    Document.description.ilike(pattern),
                    Document.original_filename.ilike(pattern)
                )
            )

        # Filtre par type de fichier
        if file_type:
            base_query = base_query.filter_by(file_type=file_type)

        # Filtre par dossier
        if folder_id:
            if folder_id == -1:  # Documents sans dossier
                base_query = base_query.filter(Document.folder_id.is_(None))
            else:
                base_query = base_query.filter_by(folder_id=folder_id)

        # Filtre par tags
        if tags:
            for tag_id in tags:
                base_query = base_query.filter(
                    Document.tags.any(Tag.id == tag_id)
                )

        # Filtre par date de creation
        if date_from:
            base_query = base_query.filter(Document.created_at >= date_from)
        if date_to:
            base_query = base_query.filter(Document.created_at <= date_to)

        # Filtre par confidentialite
        if confidentiality:
            base_query = base_query.filter_by(confidentiality=confidentiality)

        # Filtre documents expires
        if expired_only:
            base_query = base_query.filter(
                Document.expiry_date < date.today()
            )

        # Tri
        sort_column = getattr(Document, sort_by, Document.updated_at)
        if sort_order == 'asc':
            base_query = base_query.order_by(sort_column.asc())
        else:
            base_query = base_query.order_by(sort_column.desc())

        return base_query.all()

    @staticmethod
    def search_tasks(user_id, query=None, status=None, priority=None,
                      overdue_only=False, date_from=None, date_to=None):
        """Recherche avancee de taches"""
        base_query = Task.query.filter_by(owner_id=user_id)

        if query:
            pattern = f'%{query}%'
            base_query = base_query.filter(
                or_(
                    Task.title.ilike(pattern),
                    Task.description.ilike(pattern)
                )
            )

        if status:
            base_query = base_query.filter_by(status=status)

        if priority:
            base_query = base_query.filter_by(priority=priority)

        if overdue_only:
            base_query = base_query.filter(
                Task.due_date < date.today(),
                Task.status.notin_(['completed', 'cancelled'])
            )

        if date_from:
            base_query = base_query.filter(Task.due_date >= date_from)
        if date_to:
            base_query = base_query.filter(Task.due_date <= date_to)

        return base_query.order_by(Task.due_date).all()

    @staticmethod
    def global_search(user_id, query):
        """
        Recherche globale dans documents et taches.
        Retourne un dictionnaire avec les resultats par categorie.
        """
        if not query or len(query) < 2:
            return {'documents': [], 'tasks': [], 'tags': []}

        pattern = f'%{query}%'

        documents = Document.query.filter(
            Document.owner_id == user_id,
            or_(
                Document.name.ilike(pattern),
                Document.description.ilike(pattern)
            )
        ).order_by(Document.updated_at.desc()).limit(10).all()

        tasks = Task.query.filter(
            Task.owner_id == user_id,
            or_(
                Task.title.ilike(pattern),
                Task.description.ilike(pattern)
            )
        ).order_by(Task.due_date).limit(10).all()

        tags = Tag.query.filter(
            Tag.owner_id == user_id,
            Tag.name.ilike(pattern)
        ).limit(10).all()

        return {
            'documents': documents,
            'tasks': tasks,
            'tags': tags
        }

    @staticmethod
    def get_statistics(user_id):
        """Retourne des statistiques detaillees pour le dashboard"""
        today = date.today()

        # Statistiques documents
        total_docs = Document.query.filter_by(owner_id=user_id).count()

        docs_by_type = db.session.query(
            Document.file_type, func.count(Document.id)
        ).filter_by(owner_id=user_id).group_by(Document.file_type).all()

        docs_by_folder = db.session.query(
            Folder.name, func.count(Document.id)
        ).join(Document, Document.folder_id == Folder.id)\
         .filter(Folder.owner_id == user_id)\
         .group_by(Folder.name).all()

        total_size = db.session.query(
            func.sum(Document.file_size)
        ).filter_by(owner_id=user_id).scalar() or 0

        expired_docs = Document.query.filter(
            Document.owner_id == user_id,
            Document.expiry_date < today
        ).count()

        expiring_soon = Document.query.filter(
            Document.owner_id == user_id,
            Document.expiry_date >= today,
            Document.expiry_date <= today + timedelta(days=30)
        ).count()

        # Statistiques taches
        total_tasks = Task.query.filter_by(owner_id=user_id).count()

        tasks_by_status = db.session.query(
            Task.status, func.count(Task.id)
        ).filter_by(owner_id=user_id).group_by(Task.status).all()

        tasks_by_priority = db.session.query(
            Task.priority, func.count(Task.id)
        ).filter_by(owner_id=user_id).group_by(Task.priority).all()

        overdue_tasks = Task.query.filter(
            Task.owner_id == user_id,
            Task.due_date < today,
            Task.status.notin_(['completed', 'cancelled'])
        ).count()

        # Documents par mois (6 derniers mois)
        docs_by_month = []
        for i in range(5, -1, -1):
            month_start = today.replace(day=1) - timedelta(days=i * 30)
            month_end = month_start + timedelta(days=30)
            count = Document.query.filter(
                Document.owner_id == user_id,
                Document.created_at >= month_start,
                Document.created_at < month_end
            ).count()
            docs_by_month.append({
                'month': month_start.strftime('%b %Y'),
                'count': count
            })

        return {
            'total_documents': total_docs,
            'docs_by_type': dict(docs_by_type),
            'docs_by_folder': dict(docs_by_folder),
            'total_size': total_size,
            'total_size_formatted': SearchService._format_size(total_size),
            'expired_documents': expired_docs,
            'expiring_soon': expiring_soon,
            'total_tasks': total_tasks,
            'tasks_by_status': dict(tasks_by_status),
            'tasks_by_priority': dict(tasks_by_priority),
            'overdue_tasks': overdue_tasks,
            'docs_by_month': docs_by_month
        }

    @staticmethod
    def _format_size(size_bytes):
        """Formate une taille en octets en format lisible"""
        if not size_bytes:
            return '0 o'
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if size_bytes < 1024:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024
        return f'{size_bytes:.1f} To'
