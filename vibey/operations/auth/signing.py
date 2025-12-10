"""
Activity log signing for Vibey.

Signs and verifies activity log entries using Ed25519.
"""

import json
import base64
from typing import Optional, Dict, Any
from dataclasses import dataclass

from .keys import KeyManager, load_private_key, get_user_identity

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


@dataclass
class SigningResult:
    """Result of signing an activity log entry."""
    signed: bool
    signature: Optional[str] = None  # Base64-encoded
    signer: Optional[str] = None  # Email
    error: Optional[str] = None


@dataclass
class VerifyResult:
    """Result of verifying a signature."""
    valid: bool
    signer: Optional[str] = None
    error: Optional[str] = None


class ActivitySigner:
    """
    Signs and verifies activity log entries.

    Uses Ed25519 signatures for non-repudiation.
    """

    def __init__(self):
        if not CRYPTO_AVAILABLE:
            raise RuntimeError(
                "Cryptography library not installed. "
                "Run: pip install cryptography"
            )
        self.key_manager = KeyManager()

    def can_sign(self) -> bool:
        """Check if signing is available (user has keys configured)."""
        return self.key_manager.has_keypair()

    def sign_entry(self, entry: Dict[str, Any]) -> SigningResult:
        """
        Sign an activity log entry.

        Args:
            entry: Activity log entry dict

        Returns:
            SigningResult with signature if successful
        """
        if not self.can_sign():
            return SigningResult(
                signed=False,
                error="No keypair configured"
            )

        try:
            # Load private key
            private_bytes = self.key_manager.load_private_key()
            if not private_bytes:
                return SigningResult(
                    signed=False,
                    error="Could not load private key"
                )

            # Get identity
            identity = self.key_manager.load_identity()
            if not identity:
                return SigningResult(
                    signed=False,
                    error="No identity configured"
                )

            # Create canonical representation
            canonical = self._canonicalize(entry)

            # Sign
            private_key = Ed25519PrivateKey.from_private_bytes(private_bytes)
            signature = private_key.sign(canonical)

            return SigningResult(
                signed=True,
                signature=base64.b64encode(signature).decode('utf-8'),
                signer=identity.email,
            )

        except Exception as e:
            return SigningResult(
                signed=False,
                error=str(e)
            )

    def verify_entry(
        self,
        entry: Dict[str, Any],
        signature: str,
        public_key: bytes
    ) -> VerifyResult:
        """
        Verify an activity log entry's signature.

        Args:
            entry: Activity log entry dict (without signature/signer fields)
            signature: Base64-encoded signature
            public_key: Raw Ed25519 public key bytes

        Returns:
            VerifyResult indicating if signature is valid
        """
        try:
            # Decode signature
            sig_bytes = base64.b64decode(signature)

            # Create canonical representation
            canonical = self._canonicalize(entry)

            # Verify
            public = Ed25519PublicKey.from_public_bytes(public_key)
            public.verify(sig_bytes, canonical)

            return VerifyResult(valid=True)

        except InvalidSignature:
            return VerifyResult(
                valid=False,
                error="Invalid signature"
            )
        except Exception as e:
            return VerifyResult(
                valid=False,
                error=str(e)
            )

    def _canonicalize(self, entry: Dict[str, Any]) -> bytes:
        """
        Create canonical (deterministic) serialization for signing.

        Only includes fields that matter for verification:
        - id, timestamp, command
        - object_type, object_id
        - changes (sorted by field name)
        - file_path, file_hash_after

        Args:
            entry: Activity log entry dict

        Returns:
            Canonical bytes representation
        """
        # Extract and normalize changes
        changes = entry.get('changes', [])
        if changes:
            # Sort by field name for determinism
            changes = sorted(changes, key=lambda c: c.get('field', ''))

        # Build canonical dict with only signed fields
        signed_data = {
            'id': entry.get('id', ''),
            'timestamp': entry.get('timestamp', ''),
            'command': entry.get('command', ''),
            'object_type': entry.get('object_type', ''),
            'object_id': entry.get('object_id', ''),
            'changes': changes,
            'file_path': entry.get('file_path', ''),
            'file_hash_after': entry.get('file_hash_after', ''),
        }

        # JSON with sorted keys, no whitespace (deterministic)
        return json.dumps(
            signed_data,
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=True
        ).encode('utf-8')


def sign_activity_entry(entry: Dict[str, Any]) -> SigningResult:
    """
    Sign an activity log entry.

    Convenience function that handles missing crypto gracefully.

    Args:
        entry: Activity log entry dict

    Returns:
        SigningResult - if crypto unavailable or no keys, returns unsigned result
    """
    if not CRYPTO_AVAILABLE:
        return SigningResult(signed=False, error="Cryptography not available")

    try:
        signer = ActivitySigner()
        return signer.sign_entry(entry)
    except Exception as e:
        return SigningResult(signed=False, error=str(e))


def verify_activity_signature(
    entry: Dict[str, Any],
    signature: str,
    public_key: bytes
) -> VerifyResult:
    """
    Verify an activity log entry's signature.

    Args:
        entry: Activity log entry dict
        signature: Base64-encoded signature
        public_key: Raw public key bytes

    Returns:
        VerifyResult
    """
    if not CRYPTO_AVAILABLE:
        return VerifyResult(valid=False, error="Cryptography not available")

    try:
        signer = ActivitySigner()
        return signer.verify_entry(entry, signature, public_key)
    except Exception as e:
        return VerifyResult(valid=False, error=str(e))


def signing_enabled() -> bool:
    """Check if signing is enabled (crypto available + keys configured)."""
    if not CRYPTO_AVAILABLE:
        return False

    try:
        manager = KeyManager()
        return manager.has_keypair()
    except Exception:
        return False
