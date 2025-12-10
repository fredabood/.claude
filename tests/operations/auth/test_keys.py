"""
Unit tests for Ed25519 key management.

Tests:
- Keypair generation
- Key storage and loading
- Identity management
- Public key formatting
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import os

from vibey.operations.auth.keys import (
    KeyManager,
    KeyManagerError,
    UserIdentity,
    KeyPair,
    setup_user_keys,
    generate_keypair,
    load_private_key,
    load_public_key,
    get_user_identity,
    VIBEY_HOME,
)


class TestUserIdentity:
    """Tests for UserIdentity dataclass."""

    def test_str_representation(self):
        """Test string representation of identity."""
        identity = UserIdentity(email="alice@example.com", name="Alice Smith")
        assert str(identity) == "Alice Smith <alice@example.com>"

    def test_identity_attributes(self):
        """Test identity attribute access."""
        identity = UserIdentity(email="bob@example.com", name="Bob Jones")
        assert identity.email == "bob@example.com"
        assert identity.name == "Bob Jones"


class TestKeyPair:
    """Tests for KeyPair dataclass."""

    def test_public_key_string_with_identity(self):
        """Test public key string formatting with identity."""
        keypair = KeyPair(
            private_key=b"x" * 32,
            public_key=b"y" * 32,
            identity=UserIdentity(email="test@example.com", name="Test User")
        )
        key_str = keypair.public_key_string()
        assert key_str.startswith("vibey-ed25519 ")
        assert "test@example.com" in key_str

    def test_public_key_string_without_identity(self):
        """Test public key string formatting without identity."""
        keypair = KeyPair(
            private_key=b"x" * 32,
            public_key=b"y" * 32,
            identity=None
        )
        key_str = keypair.public_key_string()
        assert "unknown" in key_str


class TestKeyManager:
    """Tests for KeyManager class."""

    @pytest.fixture
    def temp_home(self, tmp_path):
        """Create temporary home directory for keys."""
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()
        return vibey_dir

    @pytest.fixture
    def manager(self, temp_home):
        """Create KeyManager with patched home directory."""
        with patch("vibey.operations.auth.keys.VIBEY_HOME", temp_home):
            with patch("vibey.operations.auth.keys.PRIVATE_KEY_FILE", temp_home / "private.key"):
                with patch("vibey.operations.auth.keys.PUBLIC_KEY_FILE", temp_home / "public.key"):
                    with patch("vibey.operations.auth.keys.IDENTITY_FILE", temp_home / "identity.txt"):
                        yield KeyManager()

    def test_ensure_vibey_home(self, manager, temp_home):
        """Test directory creation."""
        # Directory already exists in fixture
        result = manager.ensure_vibey_home()
        assert result.exists()

    def test_has_keypair_false(self, manager, temp_home):
        """Test has_keypair returns False when no keys exist."""
        with patch("vibey.operations.auth.keys.PRIVATE_KEY_FILE", temp_home / "private.key"):
            with patch("vibey.operations.auth.keys.PUBLIC_KEY_FILE", temp_home / "public.key"):
                assert not manager.has_keypair()

    def test_generate_keypair(self, manager):
        """Test keypair generation."""
        try:
            keypair = manager.generate_keypair()
            assert len(keypair.private_key) == 32  # Ed25519 private key
            assert len(keypair.public_key) == 32   # Ed25519 public key
        except RuntimeError:
            pytest.skip("Cryptography library not available")

    def test_save_and_load_identity(self, manager, temp_home):
        """Test identity save and load."""
        with patch("vibey.operations.auth.keys.IDENTITY_FILE", temp_home / "identity.txt"):
            identity = UserIdentity(email="test@example.com", name="Test User")
            manager.save_identity(identity)

            loaded = manager.load_identity()
            assert loaded is not None
            assert loaded.email == "test@example.com"
            assert loaded.name == "Test User"

    def test_load_identity_not_found(self, manager, temp_home):
        """Test load_identity returns None when no identity exists."""
        with patch("vibey.operations.auth.keys.IDENTITY_FILE", temp_home / "nonexistent.txt"):
            assert manager.load_identity() is None


class TestKeyManagerCryptoNotAvailable:
    """Tests for when cryptography library is not available."""

    def test_raises_error_without_crypto(self):
        """Test KeyManager raises error if crypto unavailable."""
        with patch("vibey.operations.auth.keys.CRYPTO_AVAILABLE", False):
            with pytest.raises(KeyManagerError) as exc_info:
                KeyManager()
            assert "pip install cryptography" in str(exc_info.value)


class TestModuleFunctions:
    """Tests for module-level convenience functions."""

    @pytest.fixture
    def temp_home(self, tmp_path):
        """Create temporary home directory."""
        vibey_dir = tmp_path / ".vibey"
        vibey_dir.mkdir()
        return vibey_dir

    def test_get_user_identity_not_configured(self, temp_home):
        """Test get_user_identity when not configured."""
        with patch("vibey.operations.auth.keys.IDENTITY_FILE", temp_home / "identity.txt"):
            result = get_user_identity()
            assert result is None

    def test_load_private_key_not_found(self, temp_home):
        """Test load_private_key when file doesn't exist."""
        with patch("vibey.operations.auth.keys.PRIVATE_KEY_FILE", temp_home / "private.key"):
            result = load_private_key()
            assert result is None

    def test_load_public_key_not_found(self, temp_home):
        """Test load_public_key when file doesn't exist."""
        with patch("vibey.operations.auth.keys.PUBLIC_KEY_FILE", temp_home / "public.key"):
            result = load_public_key()
            assert result is None
