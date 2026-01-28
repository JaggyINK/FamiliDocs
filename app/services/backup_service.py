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
            db_path = os.path.join(
                current_app.config.get('UPLOAD_FOLDER', ''),
                '..',
                'familidocs.db'
            )
            # Normalisation du chemin
            db_path = os.path.normpath(
                os.path.join(
                    os.path.dirname(current_app.config.get('UPLOAD_FOLDER', '')),
                    'familidocs.db'
                )
            )

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
    def restore_backup(backup_path: str, user_id: int = None) -> tuple:
        """
        Restaure une sauvegarde
        Retourne (success, message)
        """
        if not os.path.exists(backup_path):
            return False, "Fichier de sauvegarde introuvable"

        if not backup_path.endswith('.zip'):
            return False, "Format de sauvegarde invalide"

        try:
            # Dossier temporaire d'extraction
            extract_path = backup_path.replace('.zip', '_extract')
            os.makedirs(extract_path, exist_ok=True)

            # Extraction de l'archive
            with ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(extract_path)

            # Vérification des métadonnées
            metadata_path = os.path.join(extract_path, 'metadata.json')
            if not os.path.exists(metadata_path):
                shutil.rmtree(extract_path)
                return False, "Sauvegarde invalide: métadonnées manquantes"

            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            # Restauration de la base de données
            db_backup = os.path.join(extract_path, 'familidocs.db')
            if os.path.exists(db_backup):
                db_dest = os.path.normpath(
                    os.path.join(
                        os.path.dirname(current_app.config.get('UPLOAD_FOLDER', '')),
                        'familidocs.db'
                    )
                )
                # Sauvegarde de l'ancienne base avant restauration
                if os.path.exists(db_dest):
                    shutil.copy2(db_dest, db_dest + '.before_restore')
                shutil.copy2(db_backup, db_dest)

            # Restauration des fichiers
            uploads_backup = os.path.join(extract_path, 'uploads')
            if os.path.exists(uploads_backup):
                upload_folder = current_app.config.get('UPLOAD_FOLDER')
                # Sauvegarde des anciens fichiers
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
