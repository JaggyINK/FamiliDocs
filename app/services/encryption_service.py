"""
Service de chiffrement des documents sensibles
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from flask import current_app


class EncryptionService:
    """Service pour le chiffrement et déchiffrement des documents"""

    @staticmethod
    def generate_key() -> bytes:
        """Génère une nouvelle clé de chiffrement"""
        return Fernet.generate_key()

    @staticmethod
    def derive_key_from_password(password: str, salt: bytes = None) -> tuple:
        """
        Dérive une clé de chiffrement à partir d'un mot de passe
        Retourne (key, salt)
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

    @staticmethod
    def get_encryption_key() -> bytes:
        """Récupère la clé de chiffrement depuis la configuration"""
        key = current_app.config.get('ENCRYPTION_KEY')
        if key:
            return key.encode() if isinstance(key, str) else key
        # Génère une clé par défaut si aucune n'est configurée
        return EncryptionService.generate_key()

    @staticmethod
    def encrypt_file(file_path: str, key: bytes = None) -> tuple:
        """
        Chiffre un fichier
        Retourne (success, encrypted_path_or_error)
        """
        if key is None:
            key = EncryptionService.get_encryption_key()

        try:
            fernet = Fernet(key)

            # Lecture du fichier original
            with open(file_path, 'rb') as f:
                data = f.read()

            # Chiffrement
            encrypted_data = fernet.encrypt(data)

            # Écriture du fichier chiffré
            encrypted_path = file_path + '.enc'
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)

            # Suppression du fichier original
            os.remove(file_path)

            return True, encrypted_path

        except Exception as e:
            return False, f"Erreur lors du chiffrement: {str(e)}"

    @staticmethod
    def decrypt_file(encrypted_path: str, key: bytes = None) -> tuple:
        """
        Déchiffre un fichier
        Retourne (success, decrypted_path_or_error)
        """
        if key is None:
            key = EncryptionService.get_encryption_key()

        try:
            fernet = Fernet(key)

            # Lecture du fichier chiffré
            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()

            # Déchiffrement
            decrypted_data = fernet.decrypt(encrypted_data)

            # Écriture du fichier déchiffré
            decrypted_path = encrypted_path.replace('.enc', '')
            with open(decrypted_path, 'wb') as f:
                f.write(decrypted_data)

            return True, decrypted_path

        except Exception as e:
            return False, f"Erreur lors du déchiffrement: {str(e)}"

    @staticmethod
    def decrypt_to_memory(encrypted_path: str, key: bytes = None) -> tuple:
        """
        Déchiffre un fichier en mémoire sans l'écrire sur disque
        Retourne (success, data_or_error)
        """
        if key is None:
            key = EncryptionService.get_encryption_key()

        try:
            fernet = Fernet(key)

            with open(encrypted_path, 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = fernet.decrypt(encrypted_data)
            return True, decrypted_data

        except Exception as e:
            return False, f"Erreur lors du déchiffrement: {str(e)}"

    @staticmethod
    def encrypt_data(data: bytes, key: bytes = None) -> tuple:
        """
        Chiffre des données en mémoire
        Retourne (success, encrypted_data_or_error)
        """
        if key is None:
            key = EncryptionService.get_encryption_key()

        try:
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(data)
            return True, encrypted_data

        except Exception as e:
            return False, f"Erreur lors du chiffrement: {str(e)}"

    @staticmethod
    def decrypt_data(encrypted_data: bytes, key: bytes = None) -> tuple:
        """
        Déchiffre des données en mémoire
        Retourne (success, decrypted_data_or_error)
        """
        if key is None:
            key = EncryptionService.get_encryption_key()

        try:
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_data)
            return True, decrypted_data

        except Exception as e:
            return False, f"Erreur lors du déchiffrement: {str(e)}"

    @staticmethod
    def encrypt_string(text: str, key: bytes = None) -> str:
        """Chiffre une chaîne de caractères et retourne le résultat en base64"""
        success, result = EncryptionService.encrypt_data(text.encode(), key)
        if success:
            return base64.urlsafe_b64encode(result).decode()
        raise ValueError(result)

    @staticmethod
    def decrypt_string(encrypted_text: str, key: bytes = None) -> str:
        """Déchiffre une chaîne de caractères encodée en base64"""
        encrypted_data = base64.urlsafe_b64decode(encrypted_text.encode())
        success, result = EncryptionService.decrypt_data(encrypted_data, key)
        if success:
            return result.decode()
        raise ValueError(result)
