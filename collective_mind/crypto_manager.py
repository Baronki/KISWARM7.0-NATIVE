#!/usr/bin/env python3
"""
KISWARM Collective Mind - Crypto Manager
AES-256-GCM encryption for secure memory storage
"""

import os
import base64
import hashlib
import json
from datetime import datetime
from typing import Optional, Union, Dict, Any

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class CryptoManager:
    """
    AES-256-GCM encryption manager for Collective Mind.
    
    Features:
    - AES-256-GCM for authenticated encryption
    - PBKDF2 key derivation from master secret
    - Per-file subkeys for additional security
    - Nonce reuse prevention
    """
    
    KEY_LENGTH = 32  # 256 bits
    NONCE_LENGTH = 12  # 96 bits (recommended for GCM)
    TAG_LENGTH = 16  # 128 bits
    SALT_LENGTH = 16
    ITERATIONS = 100000
    
    def __init__(self, master_secret: str, session_id: str):
        """
        Initialize crypto manager.
        
        Args:
            master_secret: User-provided master secret
            session_id: Unique session identifier
        """
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography package not installed. Run: pip install cryptography")
        
        self.master_secret = master_secret
        self.session_id = session_id
        self._master_key: Optional[bytes] = None
        self._used_nonces: set = set()
        
    def _derive_master_key(self, salt: bytes = None) -> bytes:
        """Derive master key from secret using PBKDF2."""
        if salt is None:
            # Use consistent salt derived from session_id
            salt = hashlib.sha256(f"kiswarm_salt_{self.session_id}".encode()).digest()[:self.SALT_LENGTH]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEY_LENGTH,
            salt=salt,
            iterations=self.ITERATIONS,
        )
        return kdf.derive(self.master_secret.encode())
    
    def _derive_subkey(self, purpose: str) -> bytes:
        """Derive a subkey for specific purpose (file encryption)."""
        if self._master_key is None:
            self._master_key = self._derive_master_key()
        
        # Derive subkey from master key + purpose
        subkey_input = self._master_key + purpose.encode()
        return hashlib.sha256(subkey_input).digest()
    
    def _generate_nonce(self) -> bytes:
        """Generate a unique nonce, preventing reuse."""
        while True:
            nonce = os.urandom(self.NONCE_LENGTH)
            nonce_str = base64.b64encode(nonce).decode()
            if nonce_str not in self._used_nonces:
                self._used_nonces.add(nonce_str)
                # Keep set bounded
                if len(self._used_nonces) > 10000:
                    self._used_nonces = set(list(self._used_nonces)[-5000:])
                return nonce
    
    def encrypt(self, plaintext: Union[str, bytes, Dict, list], purpose: str = "default") -> str:
        """
        Encrypt data with AES-256-GCM.
        
        Args:
            plaintext: Data to encrypt (string, bytes, or JSON-serializable object)
            purpose: Purpose identifier for subkey derivation
            
        Returns:
            Base64 encoded: nonce || ciphertext || tag
        """
        # Convert to bytes
        if isinstance(plaintext, (dict, list)):
            plaintext = json.dumps(plaintext, ensure_ascii=False)
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        # Get subkey for this purpose
        key = self._derive_subkey(purpose)
        
        # Generate nonce
        nonce = self._generate_nonce()
        
        # Encrypt
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        # Return base64 encoded result
        result = nonce + ciphertext  # nonce || ciphertext || tag (tag is last 16 bytes of ciphertext)
        return base64.b64encode(result).decode('ascii')
    
    def decrypt(self, ciphertext_b64: str, purpose: str = "default") -> Union[str, Dict, list]:
        """
        Decrypt data encrypted with AES-256-GCM.
        
        Args:
            ciphertext_b64: Base64 encoded encrypted data
            purpose: Purpose identifier (must match encryption)
            
        Returns:
            Decrypted data (string or parsed JSON object)
        """
        # Decode base64
        try:
            data = base64.b64decode(ciphertext_b64)
        except Exception as e:
            raise ValueError(f"Invalid base64: {e}")
        
        if len(data) < self.NONCE_LENGTH + self.TAG_LENGTH:
            raise ValueError("Ciphertext too short")
        
        # Extract nonce and ciphertext
        nonce = data[:self.NONCE_LENGTH]
        ciphertext = data[self.NONCE_LENGTH:]
        
        # Get subkey for this purpose
        key = self._derive_subkey(purpose)
        
        # Decrypt
        aesgcm = AESGCM(key)
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        except Exception as e:
            raise ValueError(f"Decryption failed (wrong key or corrupted data): {e}")
        
        # Try to parse as JSON
        plaintext_str = plaintext.decode('utf-8')
        try:
            return json.loads(plaintext_str)
        except json.JSONDecodeError:
            return plaintext_str
    
    def encrypt_file_content(self, content: Dict[str, Any], filename: str) -> str:
        """Encrypt file content with filename as purpose."""
        # Add metadata
        envelope = {
            "_meta": {
                "encrypted_at": datetime.utcnow().isoformat(),
                "session_id": self.session_id,
                "filename": filename
            },
            "data": content
        }
        return self.encrypt(envelope, purpose=filename)
    
    def decrypt_file_content(self, ciphertext_b64: str, filename: str) -> Dict[str, Any]:
        """Decrypt file content and return data (strip metadata)."""
        envelope = self.decrypt(ciphertext_b64, purpose=filename)
        if isinstance(envelope, dict) and "data" in envelope:
            return envelope["data"]
        return envelope
    
    def verify_integrity(self, ciphertext_b64: str, purpose: str = "default") -> bool:
        """Verify ciphertext integrity without full decryption."""
        try:
            self.decrypt(ciphertext_b64, purpose)
            return True
        except:
            return False


class CredentialStore:
    """
    Secure credential storage using CryptoManager.
    """
    
    def __init__(self, crypto: CryptoManager):
        self.crypto = crypto
        self._credentials: Dict[str, Any] = {}
    
    def store(self, key: str, value: Any):
        """Store a credential value."""
        self._credentials[key] = value
    
    def store_all(self, credentials: Dict[str, Any]):
        """Store multiple credentials."""
        self._credentials.update(credentials)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a credential value."""
        return self._credentials.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all credentials."""
        return self._credentials.copy()
    
    def export_encrypted(self) -> str:
        """Export all credentials as encrypted string."""
        return self.crypto.encrypt(self._credentials, purpose="credentials")
    
    def import_encrypted(self, ciphertext_b64: str):
        """Import credentials from encrypted string."""
        decrypted = self.crypto.decrypt(ciphertext_b64, purpose="credentials")
        if isinstance(decrypted, dict):
            self._credentials.update(decrypted)


# Test/demo
if __name__ == "__main__":
    import sys
    
    print("Testing CryptoManager...")
    
    # Initialize with test values
    master_secret = "kiswarm_master_secret_2026"
    session_id = "test-session-001"
    
    try:
        crypto = CryptoManager(master_secret, session_id)
        
        # Test 1: Simple string encryption
        test_string = "Hello, KISWARM Collective Mind!"
        encrypted = crypto.encrypt(test_string, purpose="test")
        decrypted = crypto.decrypt(encrypted, purpose="test")
        assert decrypted == test_string, "String encryption failed"
        print("✅ String encryption: OK")
        
        # Test 2: JSON object encryption
        test_json = {
            "session_id": "session-001",
            "credentials": {
                "token": "secret_token_123",
                "api_key": "api_key_456"
            },
            "history": ["event1", "event2", "event3"]
        }
        encrypted = crypto.encrypt(test_json, purpose="json_test")
        decrypted = crypto.decrypt(encrypted, purpose="json_test")
        assert decrypted == test_json, "JSON encryption failed"
        print("✅ JSON encryption: OK")
        
        # Test 3: File content encryption
        file_content = {
            "sessions": {
                "session_1": {"status": "active"},
                "session_2": {"status": "standby"}
            }
        }
        encrypted = crypto.encrypt_file_content(file_content, "registry.json")
        decrypted = crypto.decrypt_file_content(encrypted, "registry.json")
        assert decrypted == file_content, "File encryption failed"
        print("✅ File content encryption: OK")
        
        # Test 4: Credential store
        cred_store = CredentialStore(crypto)
        cred_store.store("github_token", "ghp_test123")
        cred_store.store("api_key", "key_456")
        encrypted_creds = cred_store.export_encrypted()
        
        new_store = CredentialStore(crypto)
        new_store.import_encrypted(encrypted_creds)
        assert new_store.get("github_token") == "ghp_test123", "Credential store failed"
        print("✅ Credential store: OK")
        
        print("\n🎉 All crypto tests passed!")
        print(f"\nEncrypted sample (truncated): {encrypted_creds[:50]}...")
        
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("Install with: pip install cryptography")
        sys.exit(1)
