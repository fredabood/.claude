"""
Unit tests for activity log signing.

Tests:
- Canonical serialization
- Signing and verification
- Graceful degradation
"""

import pytest
from unittest.mock import patch, MagicMock
import base64

from vibey.operations.auth.signing import (
    ActivitySigner,
    SigningResult,
    VerifyResult,
    sign_activity_entry,
    verify_activity_signature,
    signing_enabled,
)


class TestSigningResult:
    """Tests for SigningResult dataclass."""

    def test_unsigned_result(self):
        """Test unsigned result."""
        result = SigningResult(signed=False, error="No keypair")
        assert not result.signed
        assert result.signature is None
        assert result.error == "No keypair"

    def test_signed_result(self):
        """Test signed result."""
        result = SigningResult(
            signed=True,
            signature="dGVzdHNpZ25hdHVyZQ==",
            signer="test@example.com"
        )
        assert result.signed
        assert result.signature is not None
        assert result.signer == "test@example.com"


class TestVerifyResult:
    """Tests for VerifyResult dataclass."""

    def test_valid_result(self):
        """Test valid verification result."""
        result = VerifyResult(valid=True, signer="test@example.com")
        assert result.valid
        assert result.error is None

    def test_invalid_result(self):
        """Test invalid verification result."""
        result = VerifyResult(valid=False, error="Invalid signature")
        assert not result.valid
        assert result.error is not None


class TestActivitySignerCanonical:
    """Tests for canonical serialization."""

    @pytest.fixture
    def signer(self):
        """Create ActivitySigner with mocked crypto."""
        with patch("vibey.operations.auth.signing.CRYPTO_AVAILABLE", True):
            s = ActivitySigner.__new__(ActivitySigner)
            s.key_manager = MagicMock()
            return s

    def test_canonicalize_basic_entry(self, signer):
        """Test canonical serialization of basic entry."""
        entry = {
            "id": "evt_123",
            "timestamp": "2025-01-01T00:00:00Z",
            "command": "vibey roadmap start task-001",
            "object_type": "task",
            "object_id": "task-001",
            "changes": [],
            "file_path": ".vibey/roadmap/tasks/task-001.yaml",
            "file_hash_after": "abc123",
        }

        canonical = signer._canonicalize(entry)

        # Should be deterministic JSON bytes
        assert isinstance(canonical, bytes)
        assert b"evt_123" in canonical
        assert b"task-001" in canonical

    def test_canonicalize_sorts_changes(self, signer):
        """Test that changes are sorted by field name."""
        entry = {
            "id": "evt_123",
            "timestamp": "2025-01-01T00:00:00Z",
            "command": "vibey roadmap update",
            "object_type": "task",
            "object_id": "task-001",
            "changes": [
                {"field": "status", "old": "pending", "new": "completed"},
                {"field": "assigned", "old": None, "new": "alice"},
            ],
            "file_path": ".vibey/roadmap/tasks/task-001.yaml",
            "file_hash_after": "abc123",
        }

        canonical = signer._canonicalize(entry)

        # "assigned" should come before "status" alphabetically
        assigned_idx = canonical.find(b"assigned")
        status_idx = canonical.find(b"status")
        assert assigned_idx < status_idx

    def test_canonicalize_is_deterministic(self, signer):
        """Test that same entry always produces same canonical form."""
        entry = {
            "id": "evt_123",
            "timestamp": "2025-01-01T00:00:00Z",
            "command": "test",
            "object_type": "task",
            "object_id": "task-001",
            "changes": [],
            "file_path": "test.yaml",
            "file_hash_after": "abc",
        }

        canonical1 = signer._canonicalize(entry)
        canonical2 = signer._canonicalize(entry)

        assert canonical1 == canonical2


class TestSignActivityEntry:
    """Tests for sign_activity_entry function."""

    def test_returns_unsigned_when_crypto_unavailable(self):
        """Test graceful degradation without crypto."""
        with patch("vibey.operations.auth.signing.CRYPTO_AVAILABLE", False):
            result = sign_activity_entry({"id": "test"})
            assert not result.signed
            assert "not available" in result.error.lower()

    def test_returns_unsigned_on_exception(self):
        """Test graceful handling of exceptions."""
        with patch("vibey.operations.auth.signing.CRYPTO_AVAILABLE", True):
            with patch("vibey.operations.auth.signing.ActivitySigner") as mock:
                mock.side_effect = Exception("Test error")
                result = sign_activity_entry({"id": "test"})
                assert not result.signed


class TestVerifyActivitySignature:
    """Tests for verify_activity_signature function."""

    def test_returns_invalid_when_crypto_unavailable(self):
        """Test graceful degradation without crypto."""
        with patch("vibey.operations.auth.signing.CRYPTO_AVAILABLE", False):
            result = verify_activity_signature(
                {"id": "test"},
                "dGVzdA==",
                b"x" * 32
            )
            assert not result.valid
            assert "not available" in result.error.lower()


class TestSigningEnabled:
    """Tests for signing_enabled function."""

    def test_returns_false_without_crypto(self):
        """Test returns False when crypto unavailable."""
        with patch("vibey.operations.auth.signing.CRYPTO_AVAILABLE", False):
            assert not signing_enabled()

    def test_returns_false_without_keypair(self):
        """Test returns False when no keypair configured."""
        with patch("vibey.operations.auth.signing.CRYPTO_AVAILABLE", True):
            with patch("vibey.operations.auth.signing.KeyManager") as mock:
                mock.return_value.has_keypair.return_value = False
                assert not signing_enabled()
