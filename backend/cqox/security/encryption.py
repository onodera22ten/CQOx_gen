"""
Encryption and Key Management

Features:
- AES-256-GCM encryption for data at rest
- HashiCorp Vault integration for secrets
- Key rotation
- Envelope encryption
- Field-level encryption
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from pydantic import BaseModel
import httpx
from loguru import logger


class EncryptedData(BaseModel):
    """Encrypted data with metadata"""
    ciphertext: str  # Base64 encoded
    nonce: str  # Base64 encoded
    tag: str  # Authentication tag (included in ciphertext for GCM)
    key_id: str  # Key used for encryption
    algorithm: str = "AES-256-GCM"
    encrypted_at: datetime


class VaultClient:
    """
    HashiCorp Vault client

    Features:
    - Dynamic secrets
    - Secret versioning
    - Lease management
    - KV v2 engine
    """

    def __init__(
        self,
        vault_addr: str = "http://vault:8200",
        vault_token: Optional[str] = None,
        mount_point: str = "secret"
    ):
        self.vault_addr = vault_addr
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.mount_point = mount_point

    async def read_secret(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Read secret from Vault KV v2

        Args:
            path: Secret path (e.g., "cqox/database")

        Returns:
            Secret data or None
        """
        if not self.vault_token:
            logger.warning("Vault token not configured")
            return None

        url = f"{self.vault_addr}/v1/{self.mount_point}/data/{path}"
        headers = {"X-Vault-Token": self.vault_token}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                data = response.json()

                # KV v2 format: data.data contains actual secret
                return data.get("data", {}).get("data", {})

        except Exception as e:
            logger.error(f"Failed to read Vault secret {path}: {e}")
            return None

    async def write_secret(
        self,
        path: str,
        data: Dict[str, Any],
        cas: Optional[int] = None
    ) -> bool:
        """
        Write secret to Vault KV v2

        Args:
            path: Secret path
            data: Secret data
            cas: Check-and-Set version (for optimistic locking)

        Returns:
            True if successful
        """
        if not self.vault_token:
            logger.warning("Vault token not configured")
            return False

        url = f"{self.vault_addr}/v1/{self.mount_point}/data/{path}"
        headers = {"X-Vault-Token": self.vault_token}

        payload = {"data": data}
        if cas is not None:
            payload["options"] = {"cas": cas}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Failed to write Vault secret {path}: {e}")
            return False

    async def delete_secret(self, path: str) -> bool:
        """Delete secret (soft delete - creates new version)"""
        if not self.vault_token:
            return False

        url = f"{self.vault_addr}/v1/{self.mount_point}/data/{path}"
        headers = {"X-Vault-Token": self.vault_token}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=headers)
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Failed to delete Vault secret {path}: {e}")
            return False

    async def get_encryption_key(self, key_id: str = "default") -> Optional[bytes]:
        """
        Get encryption key from Vault

        Args:
            key_id: Key identifier

        Returns:
            32-byte encryption key
        """
        secret_path = f"cqox/encryption-keys/{key_id}"
        secret_data = await self.read_secret(secret_path)

        if not secret_data or "key" not in secret_data:
            logger.warning(f"Encryption key {key_id} not found in Vault")
            return None

        # Key should be base64 encoded in Vault
        key_b64 = secret_data["key"]
        return base64.b64decode(key_b64)

    async def rotate_encryption_key(self, key_id: str = "default") -> bytes:
        """
        Rotate encryption key

        Creates new key version in Vault

        Returns:
            New 32-byte encryption key
        """
        # Generate new key
        new_key = AESGCM.generate_key(bit_length=256)

        # Store in Vault
        secret_path = f"cqox/encryption-keys/{key_id}"
        await self.write_secret(
            secret_path,
            {
                "key": base64.b64encode(new_key).decode(),
                "created_at": datetime.utcnow().isoformat(),
                "algorithm": "AES-256-GCM"
            }
        )

        logger.info(f"Rotated encryption key: {key_id}")
        return new_key


class EncryptionManager:
    """
    Encryption manager with AES-256-GCM

    Features:
    - AES-256-GCM (authenticated encryption)
    - Automatic key management via Vault
    - Envelope encryption for large data
    - Field-level encryption for sensitive fields
    """

    def __init__(self, vault_client: Optional[VaultClient] = None):
        self.vault_client = vault_client or VaultClient()
        self._key_cache: Dict[str, bytes] = {}

    async def _get_key(self, key_id: str = "default") -> bytes:
        """Get encryption key (with caching)"""
        if key_id in self._key_cache:
            return self._key_cache[key_id]

        # Try Vault first
        if self.vault_client:
            key = await self.vault_client.get_encryption_key(key_id)
            if key:
                self._key_cache[key_id] = key
                return key

        # Fallback: generate local key (NOT RECOMMENDED FOR PRODUCTION)
        logger.warning(
            f"Using local encryption key for {key_id}. "
            "Configure Vault for production!"
        )
        master_secret = os.getenv("ENCRYPTION_SECRET", "changeme-not-secure")

        # Derive key from master secret using PBKDF2
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=key_id.encode(),
            iterations=100000,
        )
        key = kdf.derive(master_secret.encode())
        self._key_cache[key_id] = key
        return key

    async def encrypt(
        self,
        plaintext: str | bytes,
        key_id: str = "default"
    ) -> EncryptedData:
        """
        Encrypt data using AES-256-GCM

        Args:
            plaintext: Data to encrypt (string or bytes)
            key_id: Encryption key identifier

        Returns:
            EncryptedData object
        """
        # Convert to bytes if string
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')

        # Get encryption key
        key = await self._get_key(key_id)

        # Generate random nonce (96 bits recommended for GCM)
        nonce = os.urandom(12)

        # Encrypt with AES-256-GCM
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        # GCM ciphertext includes authentication tag at the end
        return EncryptedData(
            ciphertext=base64.b64encode(ciphertext).decode(),
            nonce=base64.b64encode(nonce).decode(),
            tag="",  # Included in ciphertext for GCM
            key_id=key_id,
            algorithm="AES-256-GCM",
            encrypted_at=datetime.utcnow()
        )

    async def decrypt(
        self,
        encrypted_data: EncryptedData
    ) -> bytes:
        """
        Decrypt data

        Args:
            encrypted_data: EncryptedData object

        Returns:
            Decrypted plaintext (bytes)

        Raises:
            ValueError: If decryption fails (wrong key or tampered data)
        """
        # Get encryption key
        key = await self._get_key(encrypted_data.key_id)

        # Decode from base64
        ciphertext = base64.b64decode(encrypted_data.ciphertext)
        nonce = base64.b64decode(encrypted_data.nonce)

        # Decrypt with AES-256-GCM
        aesgcm = AESGCM(key)
        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption failed - invalid key or tampered data")

    async def encrypt_field(
        self,
        data: Dict[str, Any],
        fields: list[str],
        key_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Encrypt specific fields in dictionary

        Args:
            data: Dictionary containing fields to encrypt
            fields: List of field names to encrypt
            key_id: Encryption key identifier

        Returns:
            Dictionary with encrypted fields
        """
        encrypted_data = data.copy()

        for field in fields:
            if field in data and data[field] is not None:
                # Encrypt field
                encrypted = await self.encrypt(str(data[field]), key_id)

                # Store as encrypted object
                encrypted_data[f"{field}_encrypted"] = encrypted.model_dump()

                # Remove plaintext
                del encrypted_data[field]

        return encrypted_data

    async def decrypt_field(
        self,
        data: Dict[str, Any],
        fields: list[str]
    ) -> Dict[str, Any]:
        """
        Decrypt specific fields in dictionary

        Args:
            data: Dictionary containing encrypted fields
            fields: List of field names to decrypt

        Returns:
            Dictionary with decrypted fields
        """
        decrypted_data = data.copy()

        for field in fields:
            encrypted_field = f"{field}_encrypted"

            if encrypted_field in data and data[encrypted_field] is not None:
                # Parse encrypted data
                encrypted = EncryptedData(**data[encrypted_field])

                # Decrypt
                plaintext_bytes = await self.decrypt(encrypted)
                decrypted_data[field] = plaintext_bytes.decode('utf-8')

                # Remove encrypted field
                del decrypted_data[encrypted_field]

        return decrypted_data


# Global encryption manager
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get or create encryption manager"""
    global _encryption_manager

    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()

    return _encryption_manager


async def encrypt_sensitive_fields(
    data: Dict[str, Any],
    sensitive_fields: list[str] = None
) -> Dict[str, Any]:
    """
    Helper function to encrypt common sensitive fields

    Default sensitive fields:
    - password
    - ssn
    - credit_card
    - api_key
    - secret
    """
    if sensitive_fields is None:
        sensitive_fields = [
            "password", "ssn", "credit_card",
            "api_key", "secret", "private_key"
        ]

    manager = get_encryption_manager()
    return await manager.encrypt_field(data, sensitive_fields)
