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

        # Tri - choisir la colonne selon le parametre
        if sort_by == 'name':
            sort_column = Document.name
        elif sort_by == 'created_at':
            sort_column = Document.created_at
        elif sort_by == 'file_size':
            sort_column = Document.file_size
        else:
            sort_column = Document.updated_at

        if sort_order == 'asc':
            base_query = base_query.order_by(sort_column.asc())
        else:
            base_query = base_query.order_by(sort_column.desc())

        return base_query.all()

    @staticmethod
    def search_documents_query(user_id, query=None, file_type=None, folder_id=None,
                                tags=None, date_from=None, date_to=None,
                                confidentiality=None, expired_only=False,
                                sort_by='updated_at', sort_order='desc'):
        """Retourne la query de recherche (pour pagination)"""
        base_query = Document.query.filter_by(owner_id=user_id)

        if query:
            pattern = f'%{query}%'
            base_query = base_query.filter(
                or_(
                    Document.name.ilike(pattern),
                    Document.description.ilike(pattern),
                    Document.original_filename.ilike(pattern)
                )
            )
        if file_type:
            base_query = base_query.filter_by(file_type=file_type)
        if folder_id:
            if folder_id == -1:
                base_query = base_query.filter(Document.folder_id.is_(None))
            else:
                base_query = base_query.filter_by(folder_id=folder_id)
        if tags:
            for tag_id in tags:
                base_query = base_query.filter(Document.tags.any(Tag.id == tag_id))
        if date_from:
            base_query = base_query.filter(Document.created_at >= date_from)
        if date_to:
            base_query = base_query.filter(Document.created_at <= date_to)
        if confidentiality:
            base_query = base_query.filter_by(confidentiality=confidentiality)
        if expired_only:
            base_query = base_query.filter(Document.expiry_date < date.today())

        # Tri - choisir la colonne selon le parametre
        if sort_by == 'name':
            sort_column = Document.name
        elif sort_by == 'created_at':
            sort_column = Document.created_at
        elif sort_by == 'file_size':
            sort_column = Document.file_size
        else:
            sort_column = Document.updated_at

        if sort_order == 'asc':
            base_query = base_query.order_by(sort_column.asc())
        else:
            base_query = base_query.order_by(sort_column.desc())

        return base_query

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

        # Recuperer tous les documents de l'utilisateur
        all_docs = Document.query.filter_by(owner_id=user_id).all()
        total_docs = len(all_docs)

        # Compter les documents par type de fichier
        docs_by_type = {}
        total_size = 0
        expired_docs = 0
        expiring_soon = 0

        for doc in all_docs:
            # Comptage par type
            file_type = doc.file_type or 'autre'
            if file_type not in docs_by_type:
                docs_by_type[file_type] = 0
            docs_by_type[file_type] = docs_by_type[file_type] + 1

            # Taille totale
            if doc.file_size:
                total_size = total_size + doc.file_size

            # Documents expires ou bientot expires
            if doc.expiry_date:
                if doc.expiry_date < today:
                    expired_docs = expired_docs + 1
                elif doc.expiry_date <= today + timedelta(days=30):
                    expiring_soon = expiring_soon + 1

        # Compter les documents par dossier
        docs_by_folder = {}
        folders = Folder.query.filter_by(owner_id=user_id).all()
        for folder in folders:
            count = Document.query.filter_by(folder_id=folder.id).count()
            if count > 0:
                docs_by_folder[folder.name] = count

        # Recuperer toutes les taches de l'utilisateur
        all_tasks = Task.query.filter_by(owner_id=user_id).all()
        total_tasks = len(all_tasks)

        # Compter les taches par statut et priorite
        tasks_by_status = {}
        tasks_by_priority = {}
        overdue_tasks = 0

        for task in all_tasks:
            # Par statut
            if task.status not in tasks_by_status:
                tasks_by_status[task.status] = 0
            tasks_by_status[task.status] = tasks_by_status[task.status] + 1

            # Par priorite
            if task.priority not in tasks_by_priority:
                tasks_by_priority[task.priority] = 0
            tasks_by_priority[task.priority] = tasks_by_priority[task.priority] + 1

            # Taches en retard
            if task.due_date and task.due_date < today:
                if task.status not in ('completed', 'cancelled'):
                    overdue_tasks = overdue_tasks + 1

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
            'docs_by_type': docs_by_type,
            'docs_by_folder': docs_by_folder,
            'total_size': total_size,
            'total_size_formatted': SearchService._format_size(total_size),
            'expired_documents': expired_docs,
            'expiring_soon': expiring_soon,
            'total_tasks': total_tasks,
            'tasks_by_status': tasks_by_status,
            'tasks_by_priority': tasks_by_priority,
            'overdue_tasks': overdue_tasks,
            'docs_by_month': docs_by_month
        }

    @staticmethod
    def _format_size(size_bytes):
        """Formate une taille en octets en format lisible"""
        if not size_bytes:
            return '0 o'

        # Convertir en unite lisible
        if size_bytes < 1024:
            return f'{size_bytes:.1f} o'
        elif size_bytes < 1024 * 1024:
            return f'{size_bytes / 1024:.1f} Ko'
        elif size_bytes < 1024 * 1024 * 1024:
            return f'{size_bytes / (1024 * 1024):.1f} Mo'
        else:
            return f'{size_bytes / (1024 * 1024 * 1024):.1f} Go'
