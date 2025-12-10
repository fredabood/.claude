"""
Ed25519 key management for Vibey signing.

This module handles:
- Keypair generation
- Key storage and loading
- User identity management

Keys are stored in ~/.vibey/ (never in repository).
"""

import os
import base64
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple
from datetime import datetime, timezone

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    from cryptography.hazmat.primitives import serialization
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# Constants
VIBEY_HOME = Path.home() / ".vibey"
PRIVATE_KEY_FILE = VIBEY_HOME / "private.key"
PUBLIC_KEY_FILE = VIBEY_HOME / "public.key"
IDENTITY_FILE = VIBEY_HOME / "identity.txt"


@dataclass
class UserIdentity:
    """User identity for signing."""
    email: str
    name: str

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"


@dataclass
class KeyPair:
    """Ed25519 keypair."""
    private_key: bytes  # Raw 32-byte seed
    public_key: bytes   # Raw 32-byte public key
    identity: Optional[UserIdentity] = None

    def public_key_string(self) -> str:
        """Format public key for sharing."""
        encoded = base64.b64encode(self.public_key).decode('utf-8')
        identity = self.identity.email if self.identity else "unknown"
        return f"vibey-ed25519 {encoded} {identity}"


class KeyManager:
    """
    Manages Ed25519 keys for signing activity log entries.

    Keys are stored in ~/.vibey/:
    - private.key: Ed25519 private key (never shared)
    - public.key: Ed25519 public key
    - identity.txt: User identity (email, name)
    """

    def __init__(self):
        if not CRYPTO_AVAILABLE:
            raise RuntimeError(
                "Cryptography library not installed. "
                "Run: pip install cryptography"
            )

    def ensure_vibey_home(self) -> Path:
        """Create ~/.vibey/ directory if it doesn't exist."""
        VIBEY_HOME.mkdir(mode=0o700, parents=True, exist_ok=True)
        return VIBEY_HOME

    def has_keypair(self) -> bool:
        """Check if user has a keypair configured."""
        return PRIVATE_KEY_FILE.exists() and PUBLIC_KEY_FILE.exists()

    def has_identity(self) -> bool:
        """Check if user has identity configured."""
        return IDENTITY_FILE.exists()

    def generate_keypair(self) -> KeyPair:
        """
        Generate a new Ed25519 keypair.

        Returns:
            KeyPair with raw key bytes
        """
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        # Get raw bytes
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        return KeyPair(private_key=private_bytes, public_key=public_bytes)

    def save_keypair(self, keypair: KeyPair) -> Tuple[Path, Path]:
        """
        Save keypair to ~/.vibey/.

        Args:
            keypair: KeyPair to save

        Returns:
            Tuple of (private_key_path, public_key_path)
        """
        self.ensure_vibey_home()

        # Save private key with restricted permissions
        self._write_private_key(keypair.private_key, keypair.identity)

        # Save public key
        self._write_public_key(keypair.public_key, keypair.identity)

        return PRIVATE_KEY_FILE, PUBLIC_KEY_FILE

    def _write_private_key(self, private_bytes: bytes, identity: Optional[UserIdentity]) -> None:
        """Write private key file with proper permissions."""
        identity_str = identity.email if identity else "unknown"
        timestamp = datetime.now(timezone.utc).isoformat()

        content = f"""# Vibey Ed25519 Private Key
# DO NOT SHARE THIS FILE
# Generated: {timestamp}
# Identity: {identity_str}
#
# This key is used to sign roadmap changes.
# Keep it secure and never commit to version control.

-----BEGIN VIBEY PRIVATE KEY-----
{base64.b64encode(private_bytes).decode('utf-8')}
-----END VIBEY PRIVATE KEY-----
"""
        # Write with restricted permissions (user read/write only)
        PRIVATE_KEY_FILE.touch(mode=0o600)
        PRIVATE_KEY_FILE.write_text(content)
        os.chmod(PRIVATE_KEY_FILE, 0o600)

    def _write_public_key(self, public_bytes: bytes, identity: Optional[UserIdentity]) -> None:
        """Write public key file."""
        identity_str = identity.email if identity else "unknown"
        name_str = identity.name if identity else "Unknown"
        timestamp = datetime.now(timezone.utc).isoformat()

        encoded = base64.b64encode(public_bytes).decode('utf-8')
        content = f"""# Vibey Ed25519 Public Key
# Identity: {name_str} <{identity_str}>
# Generated: {timestamp}
#
# Share this key with project owners to be authorized.

vibey-ed25519 {encoded} {identity_str}
"""
        PUBLIC_KEY_FILE.write_text(content)

    def save_identity(self, identity: UserIdentity) -> Path:
        """
        Save user identity to ~/.vibey/identity.txt.

        Args:
            identity: UserIdentity to save

        Returns:
            Path to identity file
        """
        self.ensure_vibey_home()

        content = f"""# Vibey User Identity
# Used for signing roadmap changes

email={identity.email}
name={identity.name}
"""
        IDENTITY_FILE.write_text(content)
        return IDENTITY_FILE

    def load_identity(self) -> Optional[UserIdentity]:
        """
        Load user identity from ~/.vibey/identity.txt.

        Returns:
            UserIdentity or None if not configured
        """
        if not IDENTITY_FILE.exists():
            return None

        email = None
        name = None

        for line in IDENTITY_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            if line.startswith('email='):
                email = line[6:]
            elif line.startswith('name='):
                name = line[5:]

        if email and name:
            return UserIdentity(email=email, name=name)
        return None

    def load_private_key(self) -> Optional[bytes]:
        """
        Load private key from ~/.vibey/private.key.

        Returns:
            Raw private key bytes or None if not found
        """
        if not PRIVATE_KEY_FILE.exists():
            return None

        # Check permissions
        mode = PRIVATE_KEY_FILE.stat().st_mode & 0o777
        if mode != 0o600:
            # Warn but continue
            pass

        content = PRIVATE_KEY_FILE.read_text()

        # Extract base64 content between markers
        in_key = False
        key_lines = []
        for line in content.splitlines():
            if '-----BEGIN VIBEY PRIVATE KEY-----' in line:
                in_key = True
                continue
            if '-----END VIBEY PRIVATE KEY-----' in line:
                break
            if in_key:
                key_lines.append(line.strip())

        if not key_lines:
            return None

        try:
            return base64.b64decode(''.join(key_lines))
        except Exception:
            return None

    def load_public_key(self) -> Optional[bytes]:
        """
        Load public key from ~/.vibey/public.key.

        Returns:
            Raw public key bytes or None if not found
        """
        if not PUBLIC_KEY_FILE.exists():
            return None

        content = PUBLIC_KEY_FILE.read_text()

        for line in content.splitlines():
            line = line.strip()
            if line.startswith('vibey-ed25519 '):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        return base64.b64decode(parts[1])
                    except Exception:
                        return None

        return None

    def get_public_key_string(self) -> Optional[str]:
        """Get formatted public key string for sharing."""
        public_key = self.load_public_key()
        identity = self.load_identity()

        if not public_key:
            return None

        encoded = base64.b64encode(public_key).decode('utf-8')
        email = identity.email if identity else "unknown"
        return f"vibey-ed25519 {encoded} {email}"


# Module-level convenience functions

def generate_keypair() -> KeyPair:
    """Generate a new Ed25519 keypair."""
    manager = KeyManager()
    return manager.generate_keypair()


def load_private_key() -> Optional[bytes]:
    """Load private key from ~/.vibey/private.key."""
    manager = KeyManager()
    return manager.load_private_key()


def load_public_key() -> Optional[bytes]:
    """Load public key from ~/.vibey/public.key."""
    manager = KeyManager()
    return manager.load_public_key()


def get_user_identity() -> Optional[UserIdentity]:
    """Load user identity from ~/.vibey/identity.txt."""
    manager = KeyManager()
    return manager.load_identity()


def setup_user_keys(email: str, name: str) -> Tuple[str, Path, Path]:
    """
    Set up user keys and identity.

    Args:
        email: User email address
        name: User's full name

    Returns:
        Tuple of (public_key_string, private_key_path, public_key_path)
    """
    manager = KeyManager()

    # Create identity
    identity = UserIdentity(email=email, name=name)

    # Generate keypair
    keypair = manager.generate_keypair()
    keypair.identity = identity

    # Save everything
    private_path, public_path = manager.save_keypair(keypair)
    manager.save_identity(identity)

    return keypair.public_key_string(), private_path, public_path
