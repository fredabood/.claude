"""
Authentication and signing module for Vibey.

Provides Ed25519 key management and activity log signing.
"""

from .keys import (
    KeyManager,
    generate_keypair,
    load_private_key,
    load_public_key,
    get_user_identity,
    setup_user_keys,
)

from .signers import (
    SignerManager,
    AuthorizedSigner,
    init_project_signing,
    add_authorized_signer,
    list_authorized_signers,
    is_signing_enabled,
)

from .signing import (
    ActivitySigner,
    SigningResult,
    VerifyResult,
    sign_activity_entry,
    verify_activity_signature,
    signing_enabled,
)

__all__ = [
    # Keys
    "KeyManager",
    "generate_keypair",
    "load_private_key",
    "load_public_key",
    "get_user_identity",
    "setup_user_keys",
    # Signers
    "SignerManager",
    "AuthorizedSigner",
    "init_project_signing",
    "add_authorized_signer",
    "list_authorized_signers",
    "is_signing_enabled",
    # Signing
    "ActivitySigner",
    "SigningResult",
    "VerifyResult",
    "sign_activity_entry",
    "verify_activity_signature",
    "signing_enabled",
]
