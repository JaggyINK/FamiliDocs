# service chiffrement docs
import os
from cryptography.fernet import Fernet, InvalidToken
from flask import current_app


class EncryptionService:
    """chiffrement / dechiffrement docs (AES via Fernet)"""

    @staticmethod
    def generate_key():
        """genere une nouvelle cle Fernet"""
        return Fernet.generate_key()

    @staticmethod
    def get_encryption_key():
        """recup la cle (env ou fichier .encryption_key)

        en prod la cle devrait venir d'un coffre type Vault/KMS,
        ici on fait simple : ENCRYPTION_KEY dans .env, sinon
        on genere et on stocke dans .encryption_key (gitignore).
        """
        key = current_app.config.get('ENCRYPTION_KEY')
        if key:
            return key.encode() if isinstance(key, str) else key

        key_file = os.path.join(
            os.path.dirname(current_app.config.get('UPLOAD_FOLDER', '')),
            '.encryption_key'
        )
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read().strip()

        # premiere utilisation : on genere et on sauvegarde
        new_key = Fernet.generate_key()
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(new_key)
        current_app.logger.info("Cle de chiffrement generee dans .encryption_key")
        return new_key

    @staticmethod
    def encrypt_file(file_path, key=None):
        """chiffre un fichier sur disque, supprime l'original"""
        if key is None:
            key = EncryptionService.get_encryption_key()
        try:
            fernet = Fernet(key)
            with open(file_path, 'rb') as f:
                data = f.read()
            encrypted = fernet.encrypt(data)
            encrypted_path = file_path + '.enc'
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted)
            os.remove(file_path)
            return True, encrypted_path
        except (IOError, OSError, ValueError, InvalidToken) as e:
            return False, f"Erreur chiffrement: {e}"

    @staticmethod
    def decrypt_file(encrypted_path, key=None):
        """dechiffre un fichier vers le disque"""
        if key is None:
            key = EncryptionService.get_encryption_key()
        try:
            fernet = Fernet(key)
            with open(encrypted_path, 'rb') as f:
                encrypted = f.read()
            decrypted = fernet.decrypt(encrypted)
            decrypted_path = encrypted_path.replace('.enc', '')
            with open(decrypted_path, 'wb') as f:
                f.write(decrypted)
            return True, decrypted_path
        except (IOError, OSError, ValueError, InvalidToken) as e:
            return False, f"Erreur dechiffrement: {e}"

    @staticmethod
    def decrypt_to_memory(encrypted_path, key=None):
        """dechiffre directement en memoire (pas d'ecriture disque)"""
        if key is None:
            key = EncryptionService.get_encryption_key()
        try:
            fernet = Fernet(key)
            with open(encrypted_path, 'rb') as f:
                encrypted = f.read()
            return True, fernet.decrypt(encrypted)
        except (IOError, OSError, ValueError, InvalidToken) as e:
            return False, f"Erreur dechiffrement: {e}"
