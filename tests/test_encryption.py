"""
T25 - Tests du chiffrement : chiffrement/dechiffrement round-trip
"""
import os
import pytest
import tempfile
from cryptography.fernet import Fernet


class TestEncryptionService:
    """Tests du service de chiffrement"""

    def test_generate_key(self, app):
        """Test generation de cle"""
        from app.services.encryption_service import EncryptionService
        key = EncryptionService.generate_key()
        assert key is not None
        assert len(key) > 0

    def test_encrypt_decrypt_data(self, app):
        """Test chiffrement/dechiffrement en memoire"""
        from app.services.encryption_service import EncryptionService
        key = Fernet.generate_key()
        original = b'Donnees sensibles de test'

        success, encrypted = EncryptionService.encrypt_data(original, key)
        assert success
        assert encrypted != original

        success, decrypted = EncryptionService.decrypt_data(encrypted, key)
        assert success
        assert decrypted == original

    def test_encrypt_decrypt_string(self, app):
        """Test chiffrement/dechiffrement de chaine"""
        from app.services.encryption_service import EncryptionService
        key = Fernet.generate_key()
        original = 'Texte secret a chiffrer'

        encrypted = EncryptionService.encrypt_string(original, key)
        assert encrypted != original

        decrypted = EncryptionService.decrypt_string(encrypted, key)
        assert decrypted == original

    def test_encrypt_decrypt_file(self, app):
        """Test chiffrement/dechiffrement de fichier"""
        from app.services.encryption_service import EncryptionService
        key = Fernet.generate_key()

        # Creer un fichier temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            f.write(b'Contenu du fichier de test')
            temp_path = f.name

        try:
            # Chiffrer
            success, enc_path = EncryptionService.encrypt_file(temp_path, key)
            assert success
            assert enc_path.endswith('.enc')
            assert os.path.exists(enc_path)
            assert not os.path.exists(temp_path)  # original supprime

            # Dechiffrer
            success, dec_path = EncryptionService.decrypt_file(enc_path, key)
            assert success
            assert os.path.exists(dec_path)

            with open(dec_path, 'rb') as f:
                content = f.read()
            assert content == b'Contenu du fichier de test'
        finally:
            for p in [temp_path, temp_path + '.enc', temp_path]:
                if os.path.exists(p):
                    os.remove(p)

    def test_decrypt_to_memory(self, app):
        """Test dechiffrement en memoire"""
        from app.services.encryption_service import EncryptionService
        key = Fernet.generate_key()
        original = b'Donnees pour dechiffrement memoire'

        with tempfile.NamedTemporaryFile(delete=False, suffix='.enc') as f:
            fernet = Fernet(key)
            f.write(fernet.encrypt(original))
            enc_path = f.name

        try:
            success, data = EncryptionService.decrypt_to_memory(enc_path, key)
            assert success
            assert data == original
        finally:
            os.remove(enc_path)

    def test_wrong_key_fails(self, app):
        """Test qu'une mauvaise cle echoue"""
        from app.services.encryption_service import EncryptionService
        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()

        success, encrypted = EncryptionService.encrypt_data(b'secret', key1)
        assert success

        success, result = EncryptionService.decrypt_data(encrypted, key2)
        assert not success

    def test_derive_key_from_password(self, app):
        """Test derivation de cle depuis mot de passe"""
        from app.services.encryption_service import EncryptionService
        key1, salt = EncryptionService.derive_key_from_password('MonMotDePasse')
        key2, _ = EncryptionService.derive_key_from_password('MonMotDePasse', salt)
        assert key1 == key2

        key3, _ = EncryptionService.derive_key_from_password('AutreMotDePasse', salt)
        assert key1 != key3
