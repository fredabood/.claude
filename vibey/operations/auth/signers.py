"""
Authorized signer management for Vibey.

Manages the list of authorized signers for a project.
Signers are stored in .vibey/authorized-signers/.
"""

import base64
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime, timezone

import yaml

from .keys import KeyManager, UserIdentity


@dataclass
class AuthorizedSigner:
    """An authorized signer for a project."""
    identity: str  # email
    name: str
    public_key: str  # Base64-encoded
    added: str  # ISO8601 timestamp
    added_by: str  # email of who added, or "self" for bootstrap
    role: str = "developer"  # owner, admin, developer
    active: bool = True


@dataclass
class SignerManifest:
    """Manifest of all authorized signers."""
    version: str = "1.0"
    created: str = ""
    updated: str = ""
    signers: List[AuthorizedSigner] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        return {
            "version": self.version,
            "created": self.created,
            "updated": self.updated,
            "signers": [
                {
                    "identity": s.identity,
                    "name": s.name,
                    "added": s.added,
                    "added_by": s.added_by,
                    "role": s.role,
                    "active": s.active,
                }
                for s in self.signers
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SignerManifest":
        """Create from dictionary."""
        signers = []
        for s in data.get("signers", []):
            signers.append(AuthorizedSigner(
                identity=s["identity"],
                name=s["name"],
                public_key="",  # Loaded separately from .pub file
                added=s.get("added", ""),
                added_by=s.get("added_by", "unknown"),
                role=s.get("role", "developer"),
                active=s.get("active", True),
            ))
        return cls(
            version=data.get("version", "1.0"),
            created=data.get("created", ""),
            updated=data.get("updated", ""),
            signers=signers,
        )


class SignerManager:
    """
    Manages authorized signers for a project.

    Signers are stored in .vibey/authorized-signers/:
    - manifest.yaml: Signer metadata
    - {email}.pub: Public key files
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.signers_dir = self.project_root / ".vibey" / "authorized-signers"
        self.manifest_path = self.signers_dir / "manifest.yaml"
        self.key_manager = KeyManager()

    def is_initialized(self) -> bool:
        """Check if signing is initialized for this project."""
        return self.manifest_path.exists()

    def initialize_project(self) -> AuthorizedSigner:
        """
        Initialize signing for a project.

        The current user becomes the first authorized signer (owner).
        Requires the user to have a keypair configured.

        Returns:
            AuthorizedSigner for the owner
        """
        if not self.key_manager.has_keypair():
            raise RuntimeError(
                "No keypair configured.\n\n"
                "To fix, run:\n"
                "    vibey auth setup\n\n"
                "This will generate your Ed25519 keypair.\n"
                "See: docs/guides/KEY_MANAGEMENT.md"
            )

        identity = self.key_manager.load_identity()
        if not identity:
            raise RuntimeError(
                "No identity configured.\n\n"
                "To fix, run:\n"
                "    vibey auth setup\n\n"
                "This will set up your email and name.\n"
                "See: docs/guides/KEY_MANAGEMENT.md"
            )

        public_key = self.key_manager.load_public_key()
        if not public_key:
            raise RuntimeError("Could not load public key")

        # Create signers directory
        self.signers_dir.mkdir(parents=True, exist_ok=True)

        # Create owner signer
        now = datetime.now(timezone.utc).isoformat()
        owner = AuthorizedSigner(
            identity=identity.email,
            name=identity.name,
            public_key=base64.b64encode(public_key).decode('utf-8'),
            added=now,
            added_by="self",
            role="owner",
            active=True,
        )

        # Create manifest
        manifest = SignerManifest(
            version="1.0",
            created=now,
            updated=now,
            signers=[owner],
        )

        # Write manifest
        self._write_manifest(manifest)

        # Write public key file
        self._write_public_key_file(owner)

        return owner

    def add_signer(
        self,
        email: str,
        name: str,
        public_key_str: str,
        role: str = "developer"
    ) -> AuthorizedSigner:
        """
        Add an authorized signer.

        Args:
            email: Signer's email
            name: Signer's full name
            public_key_str: Public key in "vibey-ed25519 <base64> <email>" format
            role: Signer role (developer, admin, owner)

        Returns:
            The added AuthorizedSigner

        Raises:
            RuntimeError if project not initialized or signer already exists
        """
        if not self.is_initialized():
            raise RuntimeError(
                "Project signing not initialized.\n\n"
                "To fix, run:\n"
                "    vibey auth init-project\n\n"
                "This will set you up as the first authorized signer.\n"
                "See: docs/guides/KEY_MANAGEMENT.md"
            )

        manifest = self._load_manifest()

        # Check if signer already exists
        for s in manifest.signers:
            if s.identity == email:
                raise RuntimeError(
                    f"Signer already exists: {email}\n\n"
                    "Each email can only be authorized once.\n"
                    "To update their key, first revoke the old one:\n"
                    f"    vibey auth revoke {email}"
                )

        # Parse public key
        public_key_b64 = self._parse_public_key_string(public_key_str)
        if not public_key_b64:
            raise RuntimeError(
                "Invalid public key format.\n\n"
                "Expected format:\n"
                "    vibey-ed25519 <base64-key> <email>\n\n"
                "The new team member should run:\n"
                "    vibey auth export\n\n"
                "And send you the output.\n"
                "See: docs/guides/TEAM_ONBOARDING.md"
            )

        # Get current user identity for added_by
        current_identity = self.key_manager.load_identity()
        added_by = current_identity.email if current_identity else "unknown"

        # Create signer
        now = datetime.now(timezone.utc).isoformat()
        signer = AuthorizedSigner(
            identity=email,
            name=name,
            public_key=public_key_b64,
            added=now,
            added_by=added_by,
            role=role,
            active=True,
        )

        # Update manifest
        manifest.signers.append(signer)
        manifest.updated = now
        self._write_manifest(manifest)

        # Write public key file
        self._write_public_key_file(signer)

        return signer

    def list_signers(self) -> List[AuthorizedSigner]:
        """List all authorized signers."""
        if not self.is_initialized():
            return []

        manifest = self._load_manifest()

        # Load public keys from .pub files
        for signer in manifest.signers:
            pub_file = self.signers_dir / f"{signer.identity}.pub"
            if pub_file.exists():
                signer.public_key = self._load_public_key_from_file(pub_file)

        return manifest.signers

    def get_signer(self, email: str) -> Optional[AuthorizedSigner]:
        """Get a specific signer by email."""
        for signer in self.list_signers():
            if signer.identity == email:
                return signer
        return None

    def revoke_signer(self, email: str) -> bool:
        """
        Revoke a signer (soft delete - mark as inactive).

        Args:
            email: Signer's email

        Returns:
            True if revoked, False if not found
        """
        if not self.is_initialized():
            return False

        manifest = self._load_manifest()

        for signer in manifest.signers:
            if signer.identity == email:
                signer.active = False
                manifest.updated = datetime.now(timezone.utc).isoformat()
                self._write_manifest(manifest)
                return True

        return False

    def get_authorized_public_keys(self) -> Dict[str, bytes]:
        """
        Get all authorized public keys.

        Returns:
            Dict mapping email to raw public key bytes
        """
        result = {}
        for signer in self.list_signers():
            if signer.active and signer.public_key:
                try:
                    result[signer.identity] = base64.b64decode(signer.public_key)
                except Exception:
                    pass
        return result

    def _write_manifest(self, manifest: SignerManifest) -> None:
        """Write manifest to YAML file."""
        with open(self.manifest_path, 'w') as f:
            yaml.safe_dump(manifest.to_dict(), f, default_flow_style=False, sort_keys=False)

    def _load_manifest(self) -> SignerManifest:
        """Load manifest from YAML file."""
        with open(self.manifest_path, 'r') as f:
            data = yaml.safe_load(f) or {}
        return SignerManifest.from_dict(data)

    def _write_public_key_file(self, signer: AuthorizedSigner) -> None:
        """Write public key to .pub file."""
        pub_file = self.signers_dir / f"{signer.identity}.pub"
        content = f"""# Authorized Signer: {signer.name}
# Added: {signer.added}
# Added by: {signer.added_by}
# Role: {signer.role}

vibey-ed25519 {signer.public_key} {signer.identity}
"""
        pub_file.write_text(content)

    def _load_public_key_from_file(self, pub_file: Path) -> str:
        """Load public key from .pub file."""
        for line in pub_file.read_text().splitlines():
            line = line.strip()
            if line.startswith('vibey-ed25519 '):
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1]
        return ""

    def _parse_public_key_string(self, key_str: str) -> Optional[str]:
        """Parse public key string to extract base64 portion."""
        key_str = key_str.strip()
        if key_str.startswith('vibey-ed25519 '):
            parts = key_str.split()
            if len(parts) >= 2:
                return parts[1]
        return None


# Module-level convenience functions

def init_project_signing(project_root: Optional[Path] = None) -> AuthorizedSigner:
    """Initialize signing for a project."""
    manager = SignerManager(project_root)
    return manager.initialize_project()


def add_authorized_signer(
    email: str,
    name: str,
    public_key: str,
    role: str = "developer",
    project_root: Optional[Path] = None
) -> AuthorizedSigner:
    """Add an authorized signer to a project."""
    manager = SignerManager(project_root)
    return manager.add_signer(email, name, public_key, role)


def list_authorized_signers(project_root: Optional[Path] = None) -> List[AuthorizedSigner]:
    """List all authorized signers for a project."""
    manager = SignerManager(project_root)
    return manager.list_signers()


def is_signing_enabled(project_root: Optional[Path] = None) -> bool:
    """Check if signing is enabled for a project."""
    manager = SignerManager(project_root)
    return manager.is_initialized()
