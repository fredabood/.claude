"""
Unit tests for authorized signer management.

Tests:
- SignerManager initialization
- Adding and listing signers
- Revoking signers
- Manifest persistence
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

from vibey.operations.auth.signers import (
    SignerManager,
    AuthorizedSigner,
    SignerManifest,
    init_project_signing,
    add_authorized_signer,
    list_authorized_signers,
    is_signing_enabled,
)


class TestAuthorizedSigner:
    """Tests for AuthorizedSigner dataclass."""

    def test_signer_defaults(self):
        """Test signer default values."""
        signer = AuthorizedSigner(
            identity="test@example.com",
            name="Test User",
            public_key="dGVzdA==",
            added="2025-01-01T00:00:00Z",
            added_by="self",
        )
        assert signer.role == "developer"
        assert signer.active is True

    def test_signer_custom_role(self):
        """Test signer with custom role."""
        signer = AuthorizedSigner(
            identity="admin@example.com",
            name="Admin User",
            public_key="YWRtaW4=",
            added="2025-01-01T00:00:00Z",
            added_by="self",
            role="admin",
        )
        assert signer.role == "admin"


class TestSignerManifest:
    """Tests for SignerManifest dataclass."""

    def test_to_dict(self):
        """Test manifest serialization."""
        manifest = SignerManifest(
            version="1.0",
            created="2025-01-01T00:00:00Z",
            updated="2025-01-01T00:00:00Z",
            signers=[
                AuthorizedSigner(
                    identity="test@example.com",
                    name="Test User",
                    public_key="dGVzdA==",
                    added="2025-01-01T00:00:00Z",
                    added_by="self",
                )
            ]
        )
        data = manifest.to_dict()
        assert data["version"] == "1.0"
        assert len(data["signers"]) == 1
        assert data["signers"][0]["identity"] == "test@example.com"

    def test_from_dict(self):
        """Test manifest deserialization."""
        data = {
            "version": "1.0",
            "created": "2025-01-01T00:00:00Z",
            "updated": "2025-01-01T00:00:00Z",
            "signers": [
                {
                    "identity": "test@example.com",
                    "name": "Test User",
                    "added": "2025-01-01T00:00:00Z",
                    "added_by": "self",
                    "role": "developer",
                    "active": True,
                }
            ]
        }
        manifest = SignerManifest.from_dict(data)
        assert manifest.version == "1.0"
        assert len(manifest.signers) == 1
        assert manifest.signers[0].identity == "test@example.com"


class TestSignerManager:
    """Tests for SignerManager class."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """Create temporary project directory."""
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()
        return tmp_path

    @pytest.fixture
    def manager(self, project_root):
        """Create SignerManager for test project."""
        return SignerManager(project_root)

    def test_is_initialized_false(self, manager):
        """Test is_initialized returns False for new project."""
        assert not manager.is_initialized()

    def test_list_signers_empty(self, manager):
        """Test list_signers returns empty list when not initialized."""
        assert manager.list_signers() == []

    def test_get_signer_not_found(self, manager):
        """Test get_signer returns None when signer not found."""
        assert manager.get_signer("nonexistent@example.com") is None

    def test_revoke_signer_not_initialized(self, manager):
        """Test revoke returns False when not initialized."""
        result = manager.revoke_signer("test@example.com")
        assert result is False

    def test_get_authorized_public_keys_empty(self, manager):
        """Test get_authorized_public_keys returns empty dict when not initialized."""
        result = manager.get_authorized_public_keys()
        assert result == {}


class TestSignerManagerWithMockedKeys:
    """Tests for SignerManager with mocked key manager."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """Create temporary project directory."""
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()
        return tmp_path

    @pytest.fixture
    def mock_key_manager(self):
        """Create mock key manager with proper return types."""
        from vibey.operations.auth.keys import UserIdentity
        mock = MagicMock()
        mock.has_keypair.return_value = True
        mock.load_identity.return_value = UserIdentity(
            email="owner@example.com",
            name="Project Owner"
        )
        mock.load_public_key.return_value = b"x" * 32
        return mock

    @pytest.fixture
    def manager(self, project_root, mock_key_manager):
        """Create SignerManager with mocked key manager."""
        manager = SignerManager(project_root)
        manager.key_manager = mock_key_manager
        return manager

    def test_initialize_project(self, manager):
        """Test project initialization."""
        owner = manager.initialize_project()
        assert owner.identity == "owner@example.com"
        assert owner.role == "owner"
        assert manager.is_initialized()

    def test_add_signer_after_init(self, manager):
        """Test adding signer after initialization."""
        manager.initialize_project()

        new_signer = manager.add_signer(
            email="dev@example.com",
            name="Developer",
            public_key_str="vibey-ed25519 dGVzdHB1YmxpY2tleQ== dev@example.com",
            role="developer"
        )

        assert new_signer.identity == "dev@example.com"
        assert new_signer.role == "developer"
        assert new_signer.added_by == "owner@example.com"

    def test_list_signers_after_add(self, manager):
        """Test listing signers after adding."""
        manager.initialize_project()
        manager.add_signer(
            email="dev@example.com",
            name="Developer",
            public_key_str="vibey-ed25519 dGVzdHB1YmxpY2tleQ== dev@example.com"
        )

        signers = manager.list_signers()
        assert len(signers) == 2
        emails = [s.identity for s in signers]
        assert "owner@example.com" in emails
        assert "dev@example.com" in emails

    def test_revoke_signer(self, manager):
        """Test revoking a signer."""
        manager.initialize_project()
        manager.add_signer(
            email="dev@example.com",
            name="Developer",
            public_key_str="vibey-ed25519 dGVzdHB1YmxpY2tleQ== dev@example.com"
        )

        result = manager.revoke_signer("dev@example.com")
        assert result is True

        signer = manager.get_signer("dev@example.com")
        assert signer.active is False


class TestSignerManagerErrors:
    """Tests for SignerManager error handling."""

    @pytest.fixture
    def project_root(self, tmp_path):
        """Create temporary project directory."""
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()
        return tmp_path

    def test_initialize_without_keypair(self, project_root):
        """Test initialization fails without keypair."""
        manager = SignerManager(project_root)
        mock_key_manager = MagicMock()
        mock_key_manager.has_keypair.return_value = False
        manager.key_manager = mock_key_manager

        with pytest.raises(RuntimeError) as exc_info:
            manager.initialize_project()
        assert "vibey auth setup" in str(exc_info.value)

    def test_add_signer_not_initialized(self, project_root):
        """Test adding signer fails when not initialized."""
        manager = SignerManager(project_root)

        with pytest.raises(RuntimeError) as exc_info:
            manager.add_signer(
                email="dev@example.com",
                name="Developer",
                public_key_str="vibey-ed25519 dGVzdA== dev@example.com"
            )
        assert "init-project" in str(exc_info.value)

    def test_add_signer_invalid_key_format(self, project_root):
        """Test adding signer fails with invalid key format."""
        from vibey.operations.auth.keys import UserIdentity
        manager = SignerManager(project_root)
        mock_key_manager = MagicMock()
        mock_key_manager.has_keypair.return_value = True
        mock_key_manager.load_identity.return_value = UserIdentity(
            email="owner@example.com",
            name="Owner"
        )
        mock_key_manager.load_public_key.return_value = b"x" * 32
        manager.key_manager = mock_key_manager

        manager.initialize_project()

        with pytest.raises(RuntimeError) as exc_info:
            manager.add_signer(
                email="dev@example.com",
                name="Developer",
                public_key_str="invalid-format"
            )
        assert "Invalid public key format" in str(exc_info.value)


class TestModuleFunctions:
    """Tests for module-level convenience functions."""

    def test_is_signing_enabled_false(self, tmp_path):
        """Test is_signing_enabled returns False when not initialized."""
        result = is_signing_enabled(tmp_path)
        assert result is False
