"""Unit tests for OdaSessionManager with mocks.

Tests OdaSessionManager functionality using mocks, verifying core logic
such as session cleanup, key generation, and error handling.

This test file focuses on unit testing with mocks to validate specific logic
that is difficult to test with integration tests, such as timeout cleanup
and edge cases in session management.
"""

import time
import unittest.mock
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from google.adk.sessions import InMemorySessionService

from one_dragon_agent.core.agent.oda_agent_manager import OdaAgentManager
from one_dragon_agent.core.session.oda_session import OdaSession
from one_dragon_agent.core.session.oda_session_manager import OdaSessionManager


class TestOdaSessionManagerWithMocks:
    """Test OdaSessionManager with mocks.
    
    This test class validates OdaSessionManager logic using mocks to isolate
    specific functionality that is difficult to test with integration tests.
    """

    @pytest_asyncio.fixture
    async def mock_setup(self):
        """Create test setup with mocks.
        
        Returns:
            dict: Test setup with mocked services and managers
        """
        # Create mocked services
        session_service = AsyncMock(spec=InMemorySessionService)
        agent_manager = AsyncMock(spec=OdaAgentManager)
        
        # Create OdaSessionManager with mocks
        session_manager = OdaSessionManager(session_service, agent_manager)
        
        yield {
            "session_manager": session_manager,
            "session_service": session_service,
            "agent_manager": agent_manager
        }

    @pytest.mark.asyncio
    async def test_get_session_key(self, mock_setup):
        """Test _get_session_key method.
        
        This test validates that _get_session_key generates correct session keys.
        """
        session_manager = mock_setup["session_manager"]
        
        # Test with valid parameters
        app_name = "test_app"
        user_id = "test_user"
        session_id = "test_session"
        
        expected_key = f"{app_name}:{user_id}:{session_id}"
        actual_key = session_manager._get_session_key(app_name, user_id, session_id)
        
        assert actual_key == expected_key, \
            f"Session key should match expected format, got {actual_key}"
        
        # Test with special characters
        app_name_special = "test_app_123"
        user_id_special = "test_user@example.com"
        session_id_special = "test_session-abc_def"
        
        expected_key_special = f"{app_name_special}:{user_id_special}:{session_id_special}"
        actual_key_special = session_manager._get_session_key(
            app_name_special, user_id_special, session_id_special
        )
        
        assert actual_key_special == expected_key_special, \
            f"Session key should handle special characters, got {actual_key_special}"
        
        print("Successfully tested OdaSessionManager _get_session_key method")

    @pytest.mark.asyncio
    async def test_cleanup_inactive_sessions(self, mock_setup):
        """Test cleanup_inactive_sessions method.
        
        This test validates that cleanup_inactive_sessions properly identifies
        and cleans up expired sessions.
        """
        session_manager = mock_setup["session_manager"]
        
        # Create mock sessions
        app_name = "test_app"
        user_id = "test_user"
        
        # Create session keys and mock sessions
        session_keys = [
            f"{app_name}:{user_id}:session_1",
            f"{app_name}:{user_id}:session_2",
            f"{app_name}:{user_id}:session_3"
        ]
        
        mock_sessions = {}
        for key in session_keys:
            _, _, session_id = key.split(":")
            mock_session = AsyncMock(spec=OdaSession)
            mock_session.cleanup = AsyncMock()
            mock_sessions[key] = mock_session
        
        # Set up session pool and access times
        session_manager._session_pool = mock_sessions.copy()
        current_time = time.time()
        
        # Set access times - session_1 and session_3 expired, session_2 active
        session_manager._session_last_access = {
            session_keys[0]: current_time - 120,  # Expired (2 minutes ago)
            session_keys[1]: current_time - 30,   # Active (30 seconds ago)
            session_keys[2]: current_time - 150   # Expired (2.5 minutes ago)
        }
        
        # Mock session service delete_session method
        session_service = mock_setup["session_service"]
        session_service.delete_session = AsyncMock()
        
        # Call cleanup with 60 second timeout
        timeout_seconds = 60
        await session_manager.cleanup_inactive_sessions(timeout_seconds)
        
        # Validate cleanup was called on expired sessions
        mock_sessions[session_keys[0]].cleanup.assert_awaited_once(), \
            "Expired session should have cleanup called"
        mock_sessions[session_keys[2]].cleanup.assert_awaited_once(), \
            "Expired session should have cleanup called"
        
        # Validate active session was not cleaned up
        mock_sessions[session_keys[1]].cleanup.assert_not_awaited(), \
            "Active session should not have cleanup called"
        
        # Validate session service delete_session was called for expired sessions
        expected_calls = [
            unittest.mock.call(app_name=app_name, user_id=user_id, session_id="session_1"),
            unittest.mock.call(app_name=app_name, user_id=user_id, session_id="session_3")
        ]
        session_service.delete_session.assert_has_awaits(expected_calls, any_order=True)
        
        # Validate expired sessions were removed from pool and access tracking
        assert session_keys[0] not in session_manager._session_pool, \
            "Expired session should be removed from pool"
        assert session_keys[2] not in session_manager._session_pool, \
            "Expired session should be removed from pool"
        assert session_keys[0] not in session_manager._session_last_access, \
            "Expired session should be removed from access tracking"
        assert session_keys[2] not in session_manager._session_last_access, \
            "Expired session should be removed from access tracking"
        
        # Validate active session remains in pool and access tracking
        assert session_keys[1] in session_manager._session_pool, \
            "Active session should remain in pool"
        assert session_keys[1] in session_manager._session_last_access, \
            "Active session should remain in access tracking"
        
        print("Successfully tested OdaSessionManager cleanup_inactive_sessions method")

    @pytest.mark.asyncio
    async def test_cleanup_inactive_sessions_with_session_cleanup_error(self, mock_setup):
        """Test cleanup_inactive_sessions error handling during session cleanup.
        
        This test validates that cleanup_inactive_sessions propagates exceptions
        that occur during session cleanup.
        """
        session_manager = mock_setup["session_manager"]
        
        # Create mock sessions
        app_name = "test_app"
        user_id = "test_user"
        session_id = "session_with_cleanup_error"
        session_key = f"{app_name}:{user_id}:{session_id}"
        
        # Create mock session that raises an exception during cleanup
        mock_session = AsyncMock(spec=OdaSession)
        mock_session.cleanup = AsyncMock(side_effect=RuntimeError("Cleanup failed"))
        
        session_manager._session_pool = {session_key: mock_session}
        session_manager._session_last_access = {session_key: time.time() - 120}
        
        # Mock session service delete_session method
        session_service = mock_setup["session_service"]
        session_service.delete_session = AsyncMock()
        
        # Call cleanup with 60 second timeout
        timeout_seconds = 60
        # The method should propagate the exception
        with pytest.raises(RuntimeError) as exc_info:
            await session_manager.cleanup_inactive_sessions(timeout_seconds)
        
        assert "Cleanup failed" in str(exc_info.value), \
            "Should propagate the exception from session cleanup"
        
        # Validate cleanup was attempted
        mock_session.cleanup.assert_awaited_once()
        
        # Validate session service delete_session was not attempted
        # (Because the method should have exited early due to the exception)
        session_service.delete_session.assert_not_awaited()
        
        # Validate session is still in pool and access tracking
        # (Because the method should have exited early due to the exception)
        assert session_key in session_manager._session_pool, \
            "Session should still be in pool when cleanup fails"
        assert session_key in session_manager._session_last_access, \
            "Session should still be in access tracking when cleanup fails"
        
        print("Successfully tested OdaSessionManager cleanup_inactive_sessions error handling")

    @pytest.mark.asyncio
    async def test_create_session_service_error(self, mock_setup):
        """Test create_session error handling.
        
        This test validates that create_session handles errors from
        the session service gracefully.
        """
        session_manager = mock_setup["session_manager"]
        session_service = mock_setup["session_service"]
        
        # Mock session service to raise an exception
        session_service.create_session = AsyncMock(
            side_effect=RuntimeError("Session service unavailable")
        )
        
        # Attempt to create session
        app_name = "test_app"
        user_id = "test_user"
        
        with pytest.raises(RuntimeError) as exc_info:
            await session_manager.create_session(app_name, user_id)
        
        assert "Session service unavailable" in str(exc_info.value), \
            "Should propagate exception from session service"
        
        # Validate session was not added to pool
        assert len(session_manager._session_pool) == 0, \
            "No sessions should be in pool when creation fails"
        assert len(session_manager._session_last_access) == 0, \
            "No sessions should be in access tracking when creation fails"
        
        print("Successfully tested OdaSessionManager create_session error handling")

    @pytest.mark.asyncio
    async def test_delete_session_service_error(self, mock_setup):
        """Test delete_session error handling.
        
        This test validates that delete_session handles errors from
        the session service gracefully.
        """
        session_manager = mock_setup["session_manager"]
        session_service = mock_setup["session_service"]
        
        # Create a mock session in the pool
        app_name = "test_app"
        user_id = "test_user"
        session_id = "test_session"
        session_key = f"{app_name}:{user_id}:{session_id}"
        
        mock_session = AsyncMock(spec=OdaSession)
        mock_session.cleanup = AsyncMock()
        session_manager._session_pool = {session_key: mock_session}
        session_manager._session_last_access = {session_key: time.time()}
        
        # Mock session service to raise an exception
        session_service.delete_session = AsyncMock(
            side_effect=RuntimeError("Session service unavailable")
        )
        
        # Attempt to delete session
        with pytest.raises(RuntimeError) as exc_info:
            await session_manager.delete_session(app_name, user_id, session_id)
        
        assert "Session service unavailable" in str(exc_info.value), \
            "Should propagate exception from session service"
        
        # Validate session cleanup was still attempted
        mock_session.cleanup.assert_awaited_once()
        
        # Validate session is still removed from pool and access tracking
        # (Even if service call fails, we still remove it from our tracking)
        assert session_key not in session_manager._session_pool, \
            "Session should be removed from pool even if service call fails"
        assert session_key not in session_manager._session_last_access, \
            "Session should be removed from access tracking even if service call fails"
        
        print("Successfully tested OdaSessionManager delete_session error handling")