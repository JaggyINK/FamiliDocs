"""
Service de sauvegarde et restauration
"""
import os
import shutil
import json
from datetime import datetime
from zipfile import ZipFile
from flask import current_app

from app.models import db
from app.models.log import Log


class BackupService:
    """Service pour la sauvegarde et restauration des données"""

    @staticmethod
    def get_backup_folder() -> str:
        """Récupère le dossier de sauvegarde"""
        backup_folder = current_app.config.get('BACKUP_FOLDER')
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder)
        return backup_folder

    @staticmethod
    def _is_postgresql():
        """Detecte si la BDD est PostgreSQL"""
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        return db_uri.startswith('postgresql')

    @staticmethod
    def _export_table(model):
        """Exporte une table SQLAlchemy en liste de dictionnaires"""
        from sqlalchemy import inspect

        table_name = model.__tablename__
        mapper = inspect(model)

        # Recuperer les noms des colonnes
        columns = []
        for col in mapper.column_attrs:
            columns.append(col.key)

        # Exporter chaque ligne
        rows = []
        for obj in model.query.all():
            row = {}
            for col_name in columns:
                val = getattr(obj, col_name)
                # Convertir les dates en texte
                if isinstance(val, datetime):
                    val = val.isoformat()
                # Convertir les bytes en hexadecimal
                elif isinstance(val, bytes):
                    val = val.hex()
                row[col_name] = val
            rows.append(row)

        return table_name, rows

    @staticmethod
    def _export_db_to_json(backup_path):
        """Exporte toutes les tables via SQLAlchemy en JSON (pour PostgreSQL)"""
        from app.models import (User, Folder, Document, Permission, Task,
                                Log, Notification, DocumentVersion, Tag,
                                Family, FamilyMember, ShareLink, Message)

        # Liste des modeles a exporter
        models_to_export = [
            User, Folder, Document, Permission, Task, Log,
            Notification, DocumentVersion, Tag, Family,
            FamilyMember, ShareLink, Message
        ]

        tables_data = {}
        for model in models_to_export:
            table_name, rows = BackupService._export_table(model)
            tables_data[table_name] = rows

        # Exporter aussi la table d'association document_tags
        from app.models.tag import document_tags
        result = db.session.execute(document_tags.select()).fetchall()
        tags_rows = []
        for r in result:
            tags_rows.append({'document_id': r[0], 'tag_id': r[1]})
        tables_data['document_tags'] = tags_rows

        with open(os.path.join(backup_path, 'database.json'), 'w', encoding='utf-8') as f:
            json.dump(tables_data, f, indent=2, ensure_ascii=False, default=str)

    @staticmethod
    def create_backup(user_id: int = None, include_files: bool = True) -> tuple:
        """
        Crée une sauvegarde complète
        Retourne (success, backup_path_or_error)
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_folder = BackupService.get_backup_folder()
            backup_name = f"familidocs_backup_{timestamp}"
            backup_path = os.path.join(backup_folder, backup_name)

            # Création du dossier temporaire de sauvegarde
            os.makedirs(backup_path, exist_ok=True)

            # Sauvegarde de la base de données
            if BackupService._is_postgresql():
                # PostgreSQL : export JSON via SQLAlchemy
                BackupService._export_db_to_json(backup_path)
            else:
                # SQLite : copie du fichier .db
                db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
                db_path = db_uri.replace('sqlite:///', '') if db_uri.startswith('sqlite:///') else ''
                if os.path.exists(db_path):
                    shutil.copy2(db_path, os.path.join(backup_path, 'familidocs.db'))

            # Sauvegarde des fichiers uploadés
            if include_files:
                upload_folder = current_app.config.get('UPLOAD_FOLDER')
                if os.path.exists(upload_folder):
                    files_backup = os.path.join(backup_path, 'uploads')
                    shutil.copytree(upload_folder, files_backup)

            # Métadonnées de la sauvegarde
            metadata = {
                'created_at': datetime.now().isoformat(),
                'created_by': user_id,
                'include_files': include_files,
                'db_type': 'postgresql' if BackupService._is_postgresql() else 'sqlite',
                'version': '1.0'
            }
            with open(os.path.join(backup_path, 'metadata.json'), 'w') as f:
                json.dump(metadata, f, indent=2)

            # Création de l'archive ZIP
            zip_path = f"{backup_path}.zip"
            with ZipFile(zip_path, 'w') as zipf:
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, backup_path)
                        zipf.write(file_path, arcname)

            # Nettoyage du dossier temporaire
            shutil.rmtree(backup_path)

            # Log de l'action
            if user_id:
                Log.create_log(
                    user_id=user_id,
                    action='backup_create',
                    details=f"Sauvegarde créée: {os.path.basename(zip_path)}"
                )
                db.session.commit()

            return True, zip_path

        except Exception as e:
            return False, f"Erreur lors de la sauvegarde: {str(e)}"

    @staticmethod
    def _restore_db_from_json(extract_path):
        """Restaure la BDD PostgreSQL depuis un export JSON"""
        from app.models import (User, Folder, Document, Permission, Task,
                                Log, Notification, DocumentVersion, Tag,
                                Family, FamilyMember, ShareLink, Message)
        from app.models.tag import document_tags

        json_path = os.path.join(extract_path, 'database.json')
        if not os.path.exists(json_path):
            return False, "Fichier database.json manquant dans la sauvegarde"

        with open(json_path, 'r', encoding='utf-8') as f:
            tables_data = json.load(f)

        # Ordre de suppression (respecte les FK)
        delete_order = [Message, document_tags, DocumentVersion, Notification,
                        Log, Permission, Task, Document, Folder,
                        ShareLink, FamilyMember, Family, Tag, User]

        for model in delete_order:
            if hasattr(model, '__tablename__'):
                db.session.execute(model.__table__.delete())
            else:
                db.session.execute(model.delete())
        db.session.commit()

        # Ordre d'insertion (respecte les FK)
        insert_order = [
            (User, 'users'), (Tag, 'tags'), (Family, 'families'),
            (FamilyMember, 'family_members'), (ShareLink, 'share_links'),
            (Folder, 'folders'), (Document, 'documents'),
            (Task, 'tasks'), (Permission, 'permissions'),
            (Log, 'logs'), (Notification, 'notifications'),
            (DocumentVersion, 'document_versions'), (Message, 'messages'),
        ]

        for model, table_name in insert_order:
            if table_name in tables_data:
                for row in tables_data[table_name]:
                    db.session.execute(model.__table__.insert().values(**row))

        # Table d'association document_tags
        if 'document_tags' in tables_data:
            for row in tables_data['document_tags']:
                db.session.execute(document_tags.insert().values(**row))

        db.session.commit()
        return True, "OK"

    @staticmethod
    def restore_backup(backup_path: str, user_id: int = None) -> tuple:
        """
        Restaure une sauvegarde
        Retourne (success, message)
        """
        if not os.path.exists(backup_path):
            return False, "Fichier de sauvegarde introuvable"

        if not backup_path.endswith('.zip'):
            return False, "Format de sauvegarde invalide"

        # Validation : le fichier doit etre dans le dossier de backups
        backup_folder = BackupService.get_backup_folder()
        real_backup = os.path.realpath(backup_path)
        real_folder = os.path.realpath(backup_folder)
        if not real_backup.startswith(real_folder + os.sep):
            return False, "Chemin de sauvegarde invalide"

        try:
            # Dossier temporaire d'extraction
            extract_path = backup_path.replace('.zip', '_extract')
            os.makedirs(extract_path, exist_ok=True)

            # Validation et extraction securisee de l'archive (protection Zip Slip)
            with ZipFile(backup_path, 'r') as zipf:
                for member in zipf.namelist():
                    member_path = os.path.realpath(os.path.join(extract_path, member))
                    if not member_path.startswith(os.path.realpath(extract_path) + os.sep):
                        shutil.rmtree(extract_path, ignore_errors=True)
                        return False, "Archive invalide : chemin suspect detecte"
                zipf.extractall(extract_path)

            # Vérification des métadonnées
            metadata_path = os.path.join(extract_path, 'metadata.json')
            if not os.path.exists(metadata_path):
                shutil.rmtree(extract_path)
                return False, "Sauvegarde invalide: métadonnées manquantes"

            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            # Restauration de la base de données
            if BackupService._is_postgresql():
                # PostgreSQL : import depuis JSON
                success, msg = BackupService._restore_db_from_json(extract_path)
                if not success:
                    shutil.rmtree(extract_path)
                    return False, msg
            else:
                # SQLite : copie du fichier .db
                db_backup = os.path.join(extract_path, 'familidocs.db')
                if os.path.exists(db_backup):
                    db_dest = os.path.normpath(
                        os.path.join(
                            os.path.dirname(current_app.config.get('UPLOAD_FOLDER', '')),
                            'familidocs.db'
                        )
                    )
                    if os.path.exists(db_dest):
                        shutil.copy2(db_dest, db_dest + '.before_restore')
                    shutil.copy2(db_backup, db_dest)

            # Restauration des fichiers
            uploads_backup = os.path.join(extract_path, 'uploads')
            if os.path.exists(uploads_backup):
                upload_folder = current_app.config.get('UPLOAD_FOLDER')
                if os.path.exists(upload_folder):
                    shutil.move(upload_folder, upload_folder + '.before_restore')
                shutil.copytree(uploads_backup, upload_folder)

            # Nettoyage
            shutil.rmtree(extract_path)

            # Log de l'action
            if user_id:
                Log.create_log(
                    user_id=user_id,
                    action='backup_restore',
                    details=f"Restauration depuis: {os.path.basename(backup_path)}"
                )
                db.session.commit()

            return True, "Restauration effectuée avec succès"

        except Exception as e:
            # Nettoyage en cas d'erreur
            if 'extract_path' in locals() and os.path.exists(extract_path):
                shutil.rmtree(extract_path, ignore_errors=True)
            return False, f"Erreur lors de la restauration: {str(e)}"

    @staticmethod
    def list_backups() -> list:
        """Liste toutes les sauvegardes disponibles"""
        backup_folder = BackupService.get_backup_folder()
        backups = []

        for filename in os.listdir(backup_folder):
            if filename.endswith('.zip') and filename.startswith('familidocs_backup_'):
                file_path = os.path.join(backup_folder, filename)
                stat = os.stat(file_path)
                backups.append({
                    'filename': filename,
                    'path': file_path,
                    'size': stat.st_size,
                    'created_at': datetime.fromtimestamp(stat.st_mtime)
                })

        # Tri par date décroissante
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups

    @staticmethod
    def delete_backup(backup_path: str) -> tuple:
        """
        Supprime une sauvegarde
        Retourne (success, message)
        """
        if not os.path.exists(backup_path):
            return False, "Sauvegarde introuvable"

        # Validation : le fichier doit etre dans le dossier de backups
        backup_folder = BackupService.get_backup_folder()
        real_backup = os.path.realpath(backup_path)
        real_folder = os.path.realpath(backup_folder)
        if not real_backup.startswith(real_folder + os.sep):
            return False, "Chemin de sauvegarde invalide"

        try:
            os.remove(backup_path)
            return True, "Sauvegarde supprimée"
        except Exception as e:
            return False, f"Erreur lors de la suppression: {str(e)}"

    @staticmethod
    def get_backup_size(backup_path: str) -> str:
        """Retourne la taille d'une sauvegarde en format lisible"""
        if not os.path.exists(backup_path):
            return "Inconnu"

        size = os.path.getsize(backup_path)
        for unit in ['o', 'Ko', 'Mo', 'Go']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} To"

    @staticmethod
    def cleanup_old_backups(keep_count: int = 10) -> int:
        """
        Supprime les anciennes sauvegardes en gardant les plus récentes
        Retourne le nombre de sauvegardes supprimées
        """
        backups = BackupService.list_backups()

        if len(backups) <= keep_count:
            return 0

        deleted = 0
        for backup in backups[keep_count:]:
            success, _ = BackupService.delete_backup(backup['path'])
            if success:
                deleted += 1

        return deleted

    @staticmethod
    def export_user_data(user_id: int) -> tuple:
        """
        Exporte les données d'un utilisateur (RGPD)
        Retourne (success, data_or_error)
        """
        from app.models.user import User
        from app.models.document import Document
        from app.models.folder import Folder
        from app.models.task import Task

        try:
            user = User.query.get(user_id)
            if not user:
                return False, "Utilisateur introuvable"

            # Collecte des données
            data = {
                'user': {
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                },
                'folders': [],
                'documents': [],
                'tasks': []
            }

            # Dossiers
            for folder in Folder.query.filter_by(owner_id=user_id).all():
                data['folders'].append({
                    'name': folder.name,
                    'category': folder.category,
                    'created_at': folder.created_at.isoformat() if folder.created_at else None
                })

            # Documents
            for doc in Document.query.filter_by(owner_id=user_id).all():
                data['documents'].append({
                    'name': doc.name,
                    'original_filename': doc.original_filename,
                    'file_type': doc.file_type,
                    'created_at': doc.created_at.isoformat() if doc.created_at else None
                })

            # Tâches
            for task in Task.query.filter_by(owner_id=user_id).all():
                data['tasks'].append({
                    'title': task.title,
                    'description': task.description,
                    'due_date': task.due_date.isoformat() if task.due_date else None,
                    'status': task.status
                })

            return True, data

        except Exception as e:
            return False, f"Erreur lors de l'export: {str(e)}"
