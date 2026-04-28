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
            for p in [temp_path, temp_path + '.enc']:
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
        """Test qu'une mauvaise cle echoue au dechiffrement"""
        from app.services.encryption_service import EncryptionService
        key1 = Fernet.generate_key()
        key2 = Fernet.generate_key()

        # chiffre avec key1
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as f:
            f.write(b'secret')
            temp_path = f.name

        try:
            success, enc_path = EncryptionService.encrypt_file(temp_path, key1)
            assert success

            # tentative dechiffrement avec key2
            success, _ = EncryptionService.decrypt_to_memory(enc_path, key2)
            assert not success
        finally:
            for p in [temp_path, temp_path + '.enc']:
                if os.path.exists(p):
                    os.remove(p)
