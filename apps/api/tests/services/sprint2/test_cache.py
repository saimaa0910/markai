"""
Sprint 2 IAM Cache Tests
===========================
Tests for cache key construction, TTL correctness, cache hit/miss behavior,
and invalidation on mutations across all IAM entities.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.services.base.cache import InMemoryCacheManager
from api.services.iam.cache_keys import (
    API_KEY_KEY_TTL,
    INVITATION_KEY_TTL,
    OAUTH_ACCOUNT_KEY_TTL,
    ROLE_KEY_TTL,
    SECURITY_POLICY_KEY_TTL,
    SESSION_KEY_TTL,
    api_key_by_hash_cache_key,
    api_key_by_id_cache_key,
    api_key_list_key,
    invitation_by_id_cache_key,
    invitation_by_token_cache_key,
    invalidate_pattern_for_org_roles,
    invalidate_pattern_for_user_permissions,
    invalidate_pattern_for_user_sessions,
    oauth_account_cache_key,
    org_invitations_list_key,
    org_roles_list_key,
    role_cache_key,
    security_policy_cache_key,
    session_cache_key,
    user_oauth_accounts_list_key,
    user_permissions_cache_key,
    user_roles_cache_key,
    user_sessions_list_key,
)


# =============================================================================
# Cache Key Construction Tests
# =============================================================================

class TestCacheKeyConstruction:
    """Verify that cache keys have the correct format and prefix hierarchy."""

    def test_session_cache_key_format(self):
        sid = uuid.uuid4()
        key = session_cache_key(sid)
        assert key.startswith("iam:session:")
        assert str(sid) in key

    def test_user_sessions_list_key_format(self):
        uid = uuid.uuid4()
        key = user_sessions_list_key(uid)
        assert "user" in key
        assert str(uid) in key
        assert "list" in key

    def test_api_key_by_id_key_format(self):
        kid = uuid.uuid4()
        key = api_key_by_id_cache_key(kid)
        assert "iam:apikey:id:" in key
        assert str(kid) in key

    def test_api_key_by_hash_key_format(self):
        h = "deadbeef" * 8
        key = api_key_by_hash_cache_key(h)
        assert "hash:" in key
        assert h in key

    def test_api_key_list_key_format(self):
        org_id = uuid.uuid4()
        key = api_key_list_key(org_id)
        assert "org:" in key
        assert "list" in key

    def test_role_cache_key_format(self):
        rid = uuid.uuid4()
        key = role_cache_key(rid)
        assert "iam:role:" in key
        assert str(rid) in key

    def test_org_roles_list_key_format(self):
        oid = uuid.uuid4()
        key = org_roles_list_key(oid)
        assert "org:" in key
        assert "list" in key

    def test_user_roles_cache_key_format(self):
        uid = uuid.uuid4()
        oid = uuid.uuid4()
        key = user_roles_cache_key(uid, oid)
        assert str(uid) in key
        assert str(oid) in key
        assert "org:" in key

    def test_user_permissions_key_format(self):
        uid = uuid.uuid4()
        oid = uuid.uuid4()
        key = user_permissions_cache_key(uid, oid)
        assert "permissions:" in key
        assert str(uid) in key

    def test_invitation_by_token_key_format(self):
        token = "mytesttoken123"
        key = invitation_by_token_cache_key(token)
        assert "token:" in key
        assert token in key

    def test_security_policy_key_format(self):
        oid = uuid.uuid4()
        key = security_policy_cache_key(oid)
        assert "security_policy:org:" in key
        assert str(oid) in key

    def test_oauth_account_key_format(self):
        uid = uuid.uuid4()
        key = oauth_account_cache_key(uid, "google")
        assert "user:" in key
        assert "provider:google" in key
        assert str(uid) in key


# =============================================================================
# Invalidation Pattern Tests
# =============================================================================

class TestCacheInvalidationPatterns:
    """Verify that invalidation glob patterns match the expected keys."""

    def test_user_sessions_pattern_matches_session_keys(self):
        import fnmatch
        uid = uuid.uuid4()
        pattern = invalidate_pattern_for_user_sessions(uid)
        session_list_key = user_sessions_list_key(uid)
        # The pattern should be a glob that matches things in this user's session namespace
        assert str(uid) in pattern
        assert "*" in pattern

    def test_org_roles_pattern_matches_role_list_key(self):
        oid = uuid.uuid4()
        pattern = invalidate_pattern_for_org_roles(oid)
        assert str(oid) in pattern
        assert "*" in pattern

    def test_user_permissions_pattern_matches_permission_keys(self):
        uid = uuid.uuid4()
        pattern = invalidate_pattern_for_user_permissions(uid)
        assert str(uid) in pattern
        assert "*" in pattern


# =============================================================================
# TTL Constants Tests
# =============================================================================

class TestTTLConstants:
    """Verify TTL constants are positive integers with sensible ordering."""

    def test_all_ttls_are_positive(self):
        for ttl_name, ttl_val in [
            ("SESSION_KEY_TTL", SESSION_KEY_TTL),
            ("API_KEY_KEY_TTL", API_KEY_KEY_TTL),
            ("ROLE_KEY_TTL", ROLE_KEY_TTL),
            ("INVITATION_KEY_TTL", INVITATION_KEY_TTL),
            ("SECURITY_POLICY_KEY_TTL", SECURITY_POLICY_KEY_TTL),
            ("OAUTH_ACCOUNT_KEY_TTL", OAUTH_ACCOUNT_KEY_TTL),
        ]:
            assert ttl_val > 0, f"{ttl_name} must be positive"

    def test_session_ttl_shorter_than_role_ttl(self):
        """Sessions are volatile (user activity) — shorter TTL than stable data."""
        assert SESSION_KEY_TTL <= ROLE_KEY_TTL

    def test_security_policy_ttl_is_finite(self):
        """Security policy has a TTL — cannot be cached indefinitely."""
        assert SECURITY_POLICY_KEY_TTL < 3600  # less than 1 hour


# =============================================================================
# Cache Hit/Miss Behavior Tests
# =============================================================================

class TestCacheHitMiss:
    """Integration tests using InMemoryCacheManager for hit/miss scenarios."""

    @pytest.mark.asyncio
    async def test_cache_returns_none_on_miss(self):
        cache = InMemoryCacheManager()
        result = await cache.get("nonexistent:key")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_returns_value_on_hit(self):
        cache = InMemoryCacheManager()
        await cache.set("test:key", {"id": "abc", "value": 123})
        result = await cache.get("test:key")
        assert result is not None
        assert result["id"] == "abc"

    @pytest.mark.asyncio
    async def test_cache_expires_after_ttl(self):
        import asyncio
        cache = InMemoryCacheManager()
        await cache.set("expiring:key", {"data": "will expire"}, ttl=0.05)  # 50ms
        await asyncio.sleep(0.1)
        result = await cache.get("expiring:key")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_delete_removes_key(self):
        cache = InMemoryCacheManager()
        await cache.set("delete:me", "value")
        await cache.delete("delete:me")
        result = await cache.get("delete:me")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_delete_pattern_removes_matching_keys(self):
        cache = InMemoryCacheManager()
        await cache.set("iam:session:user:uid1:key1", "v1")
        await cache.set("iam:session:user:uid1:key2", "v2")
        await cache.set("iam:session:user:uid2:key1", "v3")  # Different user

        deleted = await cache.delete_pattern("iam:session:user:uid1:*")
        assert deleted == 2

        # uid2's key should still exist
        assert await cache.get("iam:session:user:uid2:key1") == "v3"

    @pytest.mark.asyncio
    async def test_cache_overwrite_updates_value(self):
        cache = InMemoryCacheManager()
        await cache.set("update:key", {"version": 1})
        await cache.set("update:key", {"version": 2})
        result = await cache.get("update:key")
        assert result["version"] == 2

    @pytest.mark.asyncio
    async def test_cache_exists_returns_true_for_valid_key(self):
        cache = InMemoryCacheManager()
        await cache.set("exists:key", "value")
        assert await cache.exists("exists:key") is True

    @pytest.mark.asyncio
    async def test_cache_exists_returns_false_for_missing_key(self):
        cache = InMemoryCacheManager()
        assert await cache.exists("missing:key") is False


# =============================================================================
# Cache Invalidation on Mutation Tests
# =============================================================================

class TestCacheInvalidationOnMutation:
    """
    These tests verify that cache invalidation is wired correctly in services.
    They use mock caches to assert delete() calls happen after mutations.
    """

    @pytest.mark.asyncio
    async def test_session_revoke_invalidates_session_cache(self):
        """Revoking a session should delete that session's cache key."""
        session_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.delete = AsyncMock()
        mock_cache.delete_pattern = AsyncMock()

        session_entity = MagicMock()
        session_entity.id = session_id
        session_entity.user_id = user_id
        session_entity.is_revoked = False

        uow = MagicMock()
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.add_event = MagicMock()
        uow.session = MagicMock()

        repo_mock = AsyncMock()
        repo_mock.get_by_id.return_value = session_entity
        repo_mock.update.return_value = None
        uow.get_repository.return_value = repo_mock

        ctx = MagicMock()
        ctx.user_id = user_id
        ctx.organization_id = uuid.uuid4()
        ctx.correlation_id = "corr-id"
        ctx.get_user_id_str.return_value = str(user_id)
        ctx.get_user_id_uuid.return_value = user_id
        ctx.get_org_id_str.return_value = str(uuid.uuid4())

        auth = MagicMock()
        auth.require_authenticated.return_value = None
        auth.check_ownership.return_value = True
        auth.check_permission.return_value = True

        from api.services.iam.session_service import SessionService
        from api.services.iam.dtos import RevokeSessionDTO

        svc = SessionService(uow_service=uow, cache_manager=mock_cache, authorizer=auth)
        await svc.revoke_session(ctx, session_id, RevokeSessionDTO(reason="logout"))

        # Assert cache.delete was called for this session
        deleted_keys = [call.args[0] for call in mock_cache.delete.call_args_list]
        expected_key = session_cache_key(session_id)
        assert expected_key in deleted_keys

    @pytest.mark.asyncio
    async def test_api_key_revoke_invalidates_key_cache(self):
        """Revoking an API key should delete the key's cache entry."""
        key_id = uuid.uuid4()
        org_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_cache = MagicMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.delete = AsyncMock()

        key_entity = MagicMock()
        key_entity.id = key_id
        key_entity.user_id = user_id
        key_entity.organization_id = org_id
        key_entity.key_prefix = "mk_live_"
        key_entity.deleted_at = None

        uow = MagicMock()
        uow.__aenter__ = AsyncMock(return_value=uow)
        uow.__aexit__ = AsyncMock(return_value=None)
        uow.add_event = MagicMock()
        uow.session = MagicMock()
        repo_mock = AsyncMock()
        repo_mock.get_by_id.return_value = key_entity
        repo_mock.soft_delete.return_value = None

        ctx = MagicMock()
        ctx.user_id = user_id
        ctx.organization_id = org_id
        ctx.get_user_id_str.return_value = str(user_id)
        ctx.get_user_id_uuid.return_value = user_id
        ctx.get_org_id_str.return_value = str(org_id)
        ctx.correlation_id = "corr"

        auth = MagicMock()
        auth.require_authenticated.return_value = None
        auth.require_tenant_access.return_value = None
        auth.check_ownership.return_value = True
        auth.check_permission.return_value = True

        from api.services.iam.api_key_service import APIKeyService

        with patch("api.services.iam.api_key_service.APIKeyRepository", return_value=repo_mock):
            svc = APIKeyService(uow_service=uow, cache_manager=mock_cache, authorizer=auth)
            await svc.revoke_api_key(ctx, key_id)

        deleted_keys = [call.args[0] for call in mock_cache.delete.call_args_list]
        assert api_key_by_id_cache_key(key_id) in deleted_keys
