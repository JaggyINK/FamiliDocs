"""
Service de gestion des permissions
"""
from datetime import date
from flask import request, has_request_context

from app.models import db
from app.models.permission import Permission
from app.models.document import Document
from app.models.user import User
from app.models.log import Log


class PermissionService:
    """Service pour la gestion des permissions d'accès aux documents"""

    @staticmethod
    def grant_permission(document_id: int, user_id: int, granted_by: int,
                         can_edit: bool = False, can_download: bool = True,
                         can_share: bool = False, end_date: date = None,
                         notes: str = None) -> tuple:
        """
        Accorde une permission d'accès à un document
        Retourne (success, permission_or_error_message)
        """
        # Vérifications
        document = Document.query.get(document_id)
        if not document:
            return False, "Document introuvable"

        user = User.query.get(user_id)
        if not user:
            return False, "Utilisateur introuvable"

        granter = User.query.get(granted_by)
        if not granter:
            return False, "Utilisateur accordant la permission introuvable"

        # Vérifier que l'utilisateur qui accorde est propriétaire ou admin
        if document.owner_id != granted_by and not granter.is_admin():
            # Vérifier si l'utilisateur a le droit de partager
            existing_perm = Permission.query.filter_by(
                document_id=document_id,
                user_id=granted_by
            ).first()
            if not existing_perm or not existing_perm.can_share:
                return False, "Vous n'avez pas le droit de partager ce document"

        try:
            permission = Permission.grant_access(
                document_id=document_id,
                user_id=user_id,
                granted_by=granted_by,
                can_edit=can_edit,
                can_download=can_download,
                can_share=can_share,
                end_date=end_date,
                notes=notes
            )

            db.session.add(permission)
            db.session.commit()

            # Log de l'action
            Log.create_log(
                user_id=granted_by,
                action='permission_grant',
                document_id=document_id,
                details=f"Permission accordée à {user.username} pour le document '{document.name}'",
                ip_address=request.remote_addr if has_request_context() else None
            )
            db.session.commit()

            return True, permission

        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de l'attribution de la permission: {str(e)}"

    @staticmethod
    def revoke_permission(document_id: int, user_id: int, revoked_by: int) -> tuple:
        """
        Révoque une permission d'accès
        Retourne (success, message)
        """
        document = Document.query.get(document_id)
        if not document:
            return False, "Document introuvable"

        user = User.query.get(user_id)
        if not user:
            return False, "Utilisateur introuvable"

        revoker = User.query.get(revoked_by)
        if not revoker:
            return False, "Utilisateur révoquant la permission introuvable"

        # Vérifier les droits de révocation
        if document.owner_id != revoked_by and not revoker.is_admin():
            return False, "Vous n'avez pas le droit de révoquer cette permission"

        try:
            success = Permission.revoke_access(document_id, user_id)

            if success:
                Log.create_log(
                    user_id=revoked_by,
                    action='permission_revoke',
                    document_id=document_id,
                    details=f"Permission révoquée pour {user.username}",
                    ip_address=request.remote_addr if has_request_context() else None
                )
                db.session.commit()
                return True, "Permission révoquée avec succès"
            else:
                return False, "Permission introuvable"

        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de la révocation: {str(e)}"

    @staticmethod
    def update_permission(permission_id: int, updated_by: int,
                          can_edit: bool = None, can_download: bool = None,
                          can_share: bool = None, end_date: date = None) -> tuple:
        """
        Met à jour une permission
        Retourne (success, message)
        """
        permission = Permission.query.get(permission_id)
        if not permission:
            return False, "Permission introuvable"

        document = permission.document
        updater = User.query.get(updated_by)

        if document.owner_id != updated_by and not updater.is_admin():
            return False, "Vous n'avez pas le droit de modifier cette permission"

        try:
            if can_edit is not None:
                permission.can_edit = can_edit
            if can_download is not None:
                permission.can_download = can_download
            if can_share is not None:
                permission.can_share = can_share
            if end_date is not None:
                permission.end_date = end_date

            db.session.commit()
            return True, "Permission mise à jour avec succès"

        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de la mise à jour: {str(e)}"

    @staticmethod
    def get_document_permissions(document_id: int):
        """Récupère toutes les permissions d'un document"""
        return Permission.query.filter_by(document_id=document_id).all()

    @staticmethod
    def get_user_permissions(user_id: int):
        """Récupère toutes les permissions accordées à un utilisateur"""
        return Permission.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_granted_permissions(user_id: int):
        """Récupère toutes les permissions accordées par un utilisateur"""
        return Permission.query.filter_by(granted_by=user_id).all()

    @staticmethod
    def check_permission(document_id: int, user_id: int, permission_type: str = 'view') -> bool:
        """
        Vérifie si un utilisateur a une permission spécifique sur un document
        permission_type: 'view', 'edit', 'download', 'share'
        """
        document = Document.query.get(document_id)
        if not document:
            return False

        user = User.query.get(user_id)
        if not user:
            return False

        # Propriétaire a tous les droits
        if document.owner_id == user_id:
            return True

        # Admin a tous les droits
        if user.is_admin():
            return True

        # Vérifier la permission explicite
        permission = Permission.query.filter_by(
            document_id=document_id,
            user_id=user_id
        ).first()

        if not permission or not permission.is_valid():
            return False

        # Verifier le type de permission demande
        if permission_type == 'view':
            return permission.can_view
        elif permission_type == 'edit':
            return permission.can_edit
        elif permission_type == 'download':
            return permission.can_download
        elif permission_type == 'share':
            return permission.can_share
        else:
            return False

    @staticmethod
    def get_accessible_users_for_sharing(owner_id: int, document_id: int = None):
        """Récupère les utilisateurs avec qui on peut partager (exclut soi-même et ceux qui ont déjà accès)"""
        from app.models.family import FamilyMember

        # Récupérer les IDs des utilisateurs à exclure
        excluded_ids = [owner_id]

        # Exclure ceux qui ont déjà accès au document
        if document_id:
            existing_perms = Permission.query.filter_by(document_id=document_id).all()
            for perm in existing_perms:
                excluded_ids.append(perm.user_id)

        return User.query.filter(
            User.id.notin_(excluded_ids),
            User.is_active == True
        ).order_by(User.last_name, User.first_name).all()

    @staticmethod
    def get_family_members_for_sharing(owner_id: int, document_id: int = None):
        """Récupère les membres de famille avec qui on peut partager"""
        from app.models.family import FamilyMember, Family

        # Trouver les familles de l'utilisateur
        memberships = FamilyMember.query.filter_by(user_id=owner_id).all()
        family_ids = []
        for m in memberships:
            family_ids.append(m.family_id)

        if not family_ids:
            return []

        # Récupérer tous les membres de ces familles
        all_members = FamilyMember.query.filter(
            FamilyMember.family_id.in_(family_ids),
            FamilyMember.user_id != owner_id
        ).all()

        # Exclure ceux qui ont déjà accès
        excluded_ids = []
        if document_id:
            existing_perms = Permission.query.filter_by(document_id=document_id).all()
            excluded_ids = []
            for p in existing_perms:
                excluded_ids.append(p.user_id)

        members_with_family = []
        for m in all_members:
            if m.user_id not in excluded_ids:
                members_with_family.append({
                    'user': m.user,
                    'family': m.family,
                    'role': m.role
                })

        return members_with_family

    @staticmethod
    def grant_multiple_permissions(document_id: int, user_ids: list, granted_by: int,
                                   can_edit: bool = False, can_download: bool = True,
                                   can_share: bool = False, end_date: date = None,
                                   notes: str = None) -> tuple:
        """Accorde une permission à plusieurs utilisateurs en une fois"""
        from datetime import timedelta

        document = Document.query.get(document_id)
        if not document:
            return False, "Document introuvable"

        # Limite max 90 jours si date spécifiée
        if end_date:
            max_date = date.today() + timedelta(days=90)
            if end_date > max_date:
                end_date = max_date

        granted_count = 0
        errors = []

        for user_id in user_ids:
            if user_id == granted_by:  # Ne pas se partager à soi-même
                continue

            success, result = PermissionService.grant_permission(
                document_id=document_id,
                user_id=user_id,
                granted_by=granted_by,
                can_edit=can_edit,
                can_download=can_download,
                can_share=can_share,
                end_date=end_date,
                notes=notes
            )
            if success:
                granted_count += 1
            else:
                errors.append(f"User {user_id}: {result}")

        if granted_count > 0:
            return True, f"Document partagé avec {granted_count} personne(s)"
        else:
            return False, "Aucun partage effectué"

    @staticmethod
    def share_folder(folder_id: int, user_ids: list, granted_by: int,
                     can_edit: bool = False, can_download: bool = True,
                     can_share: bool = False, end_date: date = None) -> tuple:
        """Partage tous les documents d'un dossier avec plusieurs utilisateurs"""
        from app.models.folder import Folder

        folder = Folder.query.get(folder_id)
        if not folder:
            return False, "Dossier introuvable"

        if folder.owner_id != granted_by:
            granter = User.query.get(granted_by)
            if not granter or not granter.is_admin():
                return False, "Vous n'êtes pas propriétaire de ce dossier"

        documents = folder.documents.all()
        if not documents:
            return False, "Le dossier est vide"

        shared_count = 0
        for doc in documents:
            success, _ = PermissionService.grant_multiple_permissions(
                document_id=doc.id,
                user_ids=user_ids,
                granted_by=granted_by,
                can_edit=can_edit,
                can_download=can_download,
                can_share=can_share,
                end_date=end_date
            )
            if success:
                shared_count += 1

        return True, f"{shared_count} document(s) partagé(s)"

    @staticmethod
    def revoke_all_permissions_for_user(user_id: int, revoked_by: int = None) -> int:
        """Révoque toutes les permissions d'un utilisateur (utilisé quand il quitte une famille)"""
        permissions = Permission.query.filter_by(user_id=user_id).all()
        count = 0
        for perm in permissions:
            db.session.delete(perm)
            count += 1
        db.session.commit()
        return count

    @staticmethod
    def get_documents_shared_by_user(user_id: int):
        """Récupère les documents que l'utilisateur a partagés avec d'autres"""
        # Recuperer tous les documents de l'utilisateur
        my_documents = Document.query.filter_by(owner_id=user_id).all()

        # Garder uniquement ceux qui ont des permissions pour d'autres utilisateurs
        shared_docs = []
        for doc in my_documents:
            permissions = Permission.query.filter_by(document_id=doc.id).all()
            for perm in permissions:
                if perm.user_id != user_id:
                    shared_docs.append(doc)
                    break  # Ne pas ajouter le meme document plusieurs fois

        return shared_docs

    @staticmethod
    def cleanup_expired_permissions():
        """Nettoie les permissions expirées (tâche de maintenance)"""
        today = date.today()
        expired = Permission.query.filter(
            Permission.end_date < today
        ).all()

        for permission in expired:
            db.session.delete(permission)

        db.session.commit()
        return len(expired)
