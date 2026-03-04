import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

from app.models import db
from app.models.document import Document
from app.models.folder import Folder
from app.models.log import Log
from app.models.task import Task


class DocumentService:
    """gest doc"""
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """check extension fichier si autorisé"""
        if '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in current_app.config.get('ALLOWED_EXTENSIONS', set())
    @staticmethod
    def generate_stored_filename(original_filename: str) -> str:
        """nom fichier unique pr archive bdd"""
        ext = ''
        if '.' in original_filename:
            ext = '.' + original_filename.rsplit('.', 1)[1].lower()
        return f"{uuid.uuid4().hex}{ext}"
    @staticmethod
    def get_file_type(filename: str) -> str:
        """type de fichier : extension"""
        if '.' not in filename:
            return 'other'

        ext = filename.rsplit('.', 1)[1].lower()
        type_mapping = {
            'pdf': 'pdf',
            'doc': 'word', 'docx': 'word',
            'xls': 'excel', 'xlsx': 'excel',
            'png': 'image', 'jpg': 'image', 'jpeg': 'image', 'gif': 'image',
            'txt': 'text',
        }
        return type_mapping.get(ext, 'other')

    @staticmethod
    def upload_document(file, name: str, owner_id: int, folder_id: int = None,
                        description: str = None, confidentiality: str = 'private',
                        expiry_date=None, user=None) -> tuple:
        """ Upload doc : msg (success, document_or_error_message)"""
        # Vérif fichier
        if not file or file.filename == '':
            return False, "Aucun fichier sélectionné"

        original_filename = secure_filename(file.filename)

        if not DocumentService.allowed_file(original_filename):
            return False, "Type de fichier non autorisé"

        # Validation du content-type
        allowed_mimes = {
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'image/jpeg', 'image/png', 'image/gif',
            'text/plain', 'application/octet-stream'
        }
        if file.content_type and file.content_type not in allowed_mimes:
            return False, "Type de contenu non autorisé"

        # Gen nom stockage
        stored_filename = DocumentService.generate_stored_filename(original_filename)

        # Chemin de sauvegarde
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        file_path = os.path.join(upload_folder, stored_filename)

        try:
            # Sauvegarde
            file.save(file_path)
            file_size = os.path.getsize(file_path)

            # Creation document en base
            document = Document(
                name=name,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_type=DocumentService.get_file_type(original_filename),
                file_size=file_size,
                description=description,
                confidentiality=confidentiality,
                expiry_date=expiry_date,
                owner_id=owner_id,
                folder_id=folder_id
            )

            db.session.add(document)
            db.session.commit()

            # T8 - Chiffrement AES si confidentialite 'private'
            if confidentiality == 'private':
                try:
                    from app.services.encryption_service import EncryptionService
                    enc_success, enc_result = EncryptionService.encrypt_file(file_path)
                    if enc_success:
                        document.stored_filename = os.path.basename(enc_result)
                        document.is_encrypted = True
                        db.session.commit()
                    else:
                        current_app.logger.warning(f"Echec chiffrement document {document.id}: {enc_result}")
                except Exception as e:
                    current_app.logger.warning(f"Erreur chiffrement document {document.id}: {e}")

            # Log action
            if user:
                Log.create_log(
                    user_id=user.id,
                    action='document_upload',
                    document_id=document.id,
                    details=f"Document '{name}' uploade" + (" (chiffre)" if document.is_encrypted else "")
                )
                db.session.commit()

            # Création tâche si date echéance
            if expiry_date:
                task = Task.create_from_document(document)
                db.session.add(task)
                db.session.commit()

            return True, document

        except Exception as e:
            # Nettoyage si erreur
            if os.path.exists(file_path):
                os.remove(file_path)
            db.session.rollback()
            return False, f"Erreur lors de l'upload: {str(e)}"

    @staticmethod
    def get_document_path(document: Document) -> str:
        """chemin complet du fichier"""
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        return os.path.join(upload_folder, document.stored_filename)

    @staticmethod
    def delete_document(document: Document, user=None) -> tuple:
        """ Supprime un document : msg (success / error )
        """
        try:
            # Suppression fichier
            file_path = DocumentService.get_document_path(document)
            if os.path.exists(file_path):
                os.remove(file_path)

            document_name = document.name
            document_id = document.id

            # Suppression en base
            db.session.delete(document)
            db.session.commit()

            # Log action
            if user:
                Log.create_log(
                    user_id=user.id,
                    action='document_delete',
                    details=f"Document '{document_name}' (ID: {document_id}) supprimé"
                )
                db.session.commit()

            return True, "Document supprimé avec succès"

        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de la suppression: {str(e)}"

    @staticmethod
    def update_document(document: Document, name: str = None,
                        description: str = None, confidentiality: str = None,
                        folder_id: int = None, expiry_date=None, next_review_date=None,
                        user=None) -> tuple:
        """ Met à jour un document : Retourne (success, message) """
        try:
            changes = []

            if name and name != document.name:
                document.name = name
                changes.append(f"nom: {name}")

            if description is not None and description != document.description:
                document.description = description
                changes.append("description mise à jour")

            if confidentiality and confidentiality != document.confidentiality:
                document.confidentiality = confidentiality
                changes.append(f"confidentialité: {confidentiality}")

            if folder_id is not None and folder_id != document.folder_id:
                document.folder_id = folder_id if folder_id > 0 else None
                changes.append("dossier modifié")

            if expiry_date != document.expiry_date:
                document.expiry_date = expiry_date
                changes.append(f"échéance: {expiry_date}")

            # N2 - Date de revision
            if next_review_date != document.next_review_date:
                document.next_review_date = next_review_date
                changes.append(f"prochaine révision: {next_review_date}")

            if changes:
                document.updated_at = datetime.utcnow()
                db.session.commit()

                # Log action
                if user:
                    Log.create_log(
                        user_id=user.id,
                        action='document_edit',
                        document_id=document.id,
                        details=f"Modifications: {', '.join(changes)}"
                    )
                    db.session.commit()

            return True, "Document mis à jour avec succès"

        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de la mise à jour: {str(e)}"

    @staticmethod
    def get_user_documents_query(user_id: int, folder_id: int = None,
                                 search: str = None, file_type: str = None):
        """Retourne la query filtree (pour pagination)"""
        query = Document.query.filter_by(owner_id=user_id)

        if folder_id:
            query = query.filter_by(folder_id=folder_id)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                db.or_(
                    Document.name.ilike(search_pattern),
                    Document.description.ilike(search_pattern)
                )
            )

        if file_type:
            query = query.filter_by(file_type=file_type)

        return query.order_by(Document.updated_at.desc())

    @staticmethod
    def get_user_documents(user_id: int, folder_id: int = None,
                           search: str = None, file_type: str = None):
        """Récupère documents filtres"""
        return DocumentService.get_user_documents_query(
            user_id, folder_id, search, file_type
        ).all()

    @staticmethod
    def get_shared_documents(user_id: int):
        """Récupère les documents partagés avec un utilisateur"""
        from app.models.permission import Permission

        permissions = Permission.query.filter_by(user_id=user_id).all()
        documents = []

        for perm in permissions:
            if perm.is_valid() and perm.document:
                documents.append(perm.document)

        return documents

    @staticmethod
    def get_expiring_documents(user_id: int, days: int = 30):
        """Récupère les documents qui expirent bientôt"""
        from datetime import date, timedelta

        end_date = date.today() + timedelta(days=days)
        return Document.query.filter(
            Document.owner_id == user_id,
            Document.expiry_date <= end_date,
            Document.expiry_date >= date.today()
        ).order_by(Document.expiry_date).all()
