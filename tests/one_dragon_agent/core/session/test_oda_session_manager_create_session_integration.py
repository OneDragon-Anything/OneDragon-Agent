"""Integration tests for OdaSessionManager create_session method.

Tests create_session functionality with real dependencies, verifying that OdaSessionManager
can properly create OdaSession instances and manage them in the session pool.

This test file focuses on integration testing with real ADK services and components,
validating the complete session creation workflow and basic session management features.
"""

import os

import pytest
import pytest_asyncio
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService

from one_dragon_agent.core.agent.config.in_memory_oda_agent_config_storage import (
    InMemoryOdaAgentConfigStorage,
)
from one_dragon_agent.core.agent.config.oda_agent_config import (
    create_default_agent_config,
)
from one_dragon_agent.core.agent.config.oda_agent_config_manager import (
    OdaAgentConfigManager,
)
from one_dragon_agent.core.agent.oda_agent_manager import OdaAgentManager
from one_dragon_agent.core.context.oda_context_config import OdaContextConfig
from one_dragon_agent.core.model.in_memory_oda_model_config_storage import (
    InMemoryOdaModelConfigStorage,
)
from one_dragon_agent.core.model.oda_model_config_manager import OdaModelConfigManager
from one_dragon_agent.core.session.oda_session import OdaSession
from one_dragon_agent.core.session.oda_session_manager import OdaSessionManager
from one_dragon_agent.core.tool.mcp.oda_mcp_config_storage import InMemoryOdaMcpStorage
from one_dragon_agent.core.tool.mcp.oda_mcp_manager import OdaMcpManager
from one_dragon_agent.core.tool.oda_tool_manager import OdaToolManager


class TestOdaSessionManagerCreateSessionIntegration:
    """Test OdaSessionManager create_session integration.
    
    This test class validates that OdaSessionManager can successfully create
    OdaSession instances and manage them properly.
    """

    @pytest.fixture(scope="class")
    def required_env_vars(self):
        """Check if required environment variables are set.
        
        Returns:
            dict: Configuration dictionary containing base_url, api_key, and model
        """
        base_url = os.getenv("ODA_DEFAULT_LLM_BASE_URL")
        api_key = os.getenv("ODA_DEFAULT_LLM_API_KEY")
        if not base_url or not api_key:
            pytest.skip("ODA_DEFAULT_LLM_BASE_URL and ODA_DEFAULT_LLM_API_KEY environment variables are required")
        return {
            "base_url": base_url,
            "api_key": api_key,
            "model": os.getenv("ODA_DEFAULT_LLM_MODEL"),
        }

    @pytest_asyncio.fixture
    async def test_setup(self, required_env_vars):
        """Create complete test setup with all required services and managers.
        
        Args:
            required_env_vars: Environment configuration for LLM
            
        Returns:
            dict: Complete test setup including all required services and managers
        """
        # Create ADK native services
        session_service = InMemorySessionService()
        artifact_service = InMemoryArtifactService()
        memory_service = InMemoryMemoryService()
        
        # Create OdaToolManager
        tool_manager = OdaToolManager()
        
        # Create OdaMcpManager with in-memory storage
        mcp_storage = InMemoryOdaMcpStorage()
        mcp_manager = OdaMcpManager(custom_config_storage=mcp_storage)
        
        # Create model config manager
        model_config_service = InMemoryOdaModelConfigStorage()
        context_config = OdaContextConfig(
            default_llm_base_url=required_env_vars["base_url"],
            default_llm_api_key=required_env_vars["api_key"],
            default_llm_model=required_env_vars["model"],
        )
        model_config_manager = OdaModelConfigManager(
            config_service=model_config_service,
            context_config=context_config
        )
        
        # Create agent config manager with in-memory storage
        agent_config_storage = InMemoryOdaAgentConfigStorage(model_config_manager)
        agent_config_manager = OdaAgentConfigManager(
            config_service=agent_config_storage,
            model_config_manager=model_config_manager,
            mcp_manager=mcp_manager
        )
        
        # Create OdaAgentManager
        agent_manager = OdaAgentManager(
            session_service=session_service,
            artifact_service=artifact_service,
            memory_service=memory_service,
            tool_manager=tool_manager,
            mcp_manager=mcp_manager,
            model_config_manager=model_config_manager,
            agent_config_manager=agent_config_manager
        )
        
        # Create OdaSessionManager
        session_manager = OdaSessionManager(session_service, agent_manager)
        
        # Create test agent configuration
        app_name = "test_session_manager_app"
        default_agent_config = create_default_agent_config(app_name)
        default_agent_config.agent_name = "test_default_agent"
        await agent_config_manager.create_config(default_agent_config)
        
        yield {
            "session_manager": session_manager,
            "agent_manager": agent_manager,
            "app_name": app_name,
            "session_service": session_service,
            "tool_manager": tool_manager,
            "mcp_manager": mcp_manager,
            "agent_config_manager": agent_config_manager
        }

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_create_session_basic(self, test_setup):
        """Test basic session creation functionality.
        
        This test validates that OdaSessionManager can successfully create
        OdaSession instances with valid parameters.
        """
        session_manager = test_setup["session_manager"]
        app_name = test_setup["app_name"]
        
        # Test creating session with auto-generated session_id
        user_id = "test_user_1"
        oda_session = await session_manager.create_session(
            app_name=app_name,
            user_id=user_id
        )
        
        # Validate session creation
        assert isinstance(oda_session, OdaSession), \
            f"Created session should be OdaSession instance, got {type(oda_session)}"
        assert oda_session.app_name == app_name, \
            f"Session app_name should match, expected {app_name}, got {oda_session.app_name}"
        assert oda_session.user_id == user_id, \
            f"Session user_id should match, expected {user_id}, got {oda_session.user_id}"
        assert oda_session.session_id is not None and oda_session.session_id != "", \
            "Session should have a valid session_id"
        assert oda_session.agent_manager is not None, \
            "Session should have agent_manager assigned"
        
        # Validate session is in pool
        session_key = f"{app_name}:{user_id}:{oda_session.session_id}"
        assert session_key in session_manager._session_pool, \
            "Created session should be in session pool"
        assert session_manager._session_pool[session_key] is oda_session, \
            "Session in pool should be the same instance"
        
        # Validate session access time tracking
        assert session_key in session_manager._session_last_access, \
            "Session should be tracked for last access time"
        
        print("Successfully tested basic OdaSessionManager create_session functionality")

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_create_session_with_custom_id(self, test_setup):
        """Test session creation with custom session_id.
        
        This test validates that OdaSessionManager can successfully create
        OdaSession instances with a specified session_id.
        """
        session_manager = test_setup["session_manager"]
        app_name = test_setup["app_name"]
        
        # Test creating session with custom session_id
        user_id = "test_user_2"
        custom_session_id = "custom_test_session_123"
        oda_session = await session_manager.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=custom_session_id
        )
        
        # Validate session creation
        assert isinstance(oda_session, OdaSession), \
            f"Created session should be OdaSession instance, got {type(oda_session)}"
        assert oda_session.app_name == app_name, \
            f"Session app_name should match, expected {app_name}, got {oda_session.app_name}"
        assert oda_session.user_id == user_id, \
            f"Session user_id should match, expected {user_id}, got {oda_session.user_id}"
        assert oda_session.session_id == custom_session_id, \
            f"Session session_id should match custom ID, expected {custom_session_id}, got {oda_session.session_id}"
        assert oda_session.agent_manager is not None, \
            "Session should have agent_manager assigned"
        
        # Validate session is in pool
        session_key = f"{app_name}:{user_id}:{custom_session_id}"
        assert session_key in session_manager._session_pool, \
            "Created session should be in session pool"
        assert session_manager._session_pool[session_key] is oda_session, \
            "Session in pool should be the same instance"
        
        # Validate session access time tracking
        assert session_key in session_manager._session_last_access, \
            "Session should be tracked for last access time"
        
        print("Successfully tested OdaSessionManager create_session with custom session_id")

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_create_multiple_sessions(self, test_setup):
        """Test creating multiple sessions for the same user.
        
        This test validates that OdaSessionManager can successfully create
        multiple OdaSession instances for the same user.
        """
        session_manager = test_setup["session_manager"]
        app_name = test_setup["app_name"]
        user_id = "test_user_3"
        
        # Create multiple sessions
        session_ids = []
        sessions = []
        for i in range(3):
            oda_session = await session_manager.create_session(
                app_name=app_name,
                user_id=user_id
            )
            session_ids.append(oda_session.session_id)
            sessions.append(oda_session)
            
            # Validate each session
            assert isinstance(oda_session, OdaSession), \
                f"Created session should be OdaSession instance, got {type(oda_session)}"
            assert oda_session.app_name == app_name
            assert oda_session.user_id == user_id
            assert oda_session.session_id is not None and oda_session.session_id != ""
            assert oda_session.agent_manager is not None
            
            # Validate session is in pool
            session_key = f"{app_name}:{user_id}:{oda_session.session_id}"
            assert session_key in session_manager._session_pool
            assert session_manager._session_pool[session_key] is oda_session
            
            # Validate session access time tracking
            assert session_key in session_manager._session_last_access
        
        # Validate all sessions are unique
        assert len(set(session_ids)) == len(session_ids), \
            "All created sessions should have unique session_ids"
        
        # Validate session pool size
        user_sessions = [key for key in session_manager._session_pool.keys() 
                        if key.startswith(f"{app_name}:{user_id}:")]
        assert len(user_sessions) == 3, \
            "Session pool should contain all created sessions for the user"
        
        print("Successfully tested OdaSessionManager create_session with multiple sessions")

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_session_pool_management(self, test_setup):
        """Test session pool management functionality.
        
        This test validates that OdaSessionManager properly manages
        OdaSession instances in the session pool.
        """
        session_manager = test_setup["session_manager"]
        app_name = test_setup["app_name"]
        
        # Create sessions
        user_id_1 = "test_user_4"
        user_id_2 = "test_user_5"
        
        # Create sessions for user 1
        session_1 = await session_manager.create_session(
            app_name=app_name,
            user_id=user_id_1
        )
        
        session_2 = await session_manager.create_session(
            app_name=app_name,
            user_id=user_id_1
        )
        
        # Create session for user 2
        session_3 = await session_manager.create_session(
            app_name=app_name,
            user_id=user_id_2
        )
        
        # Validate session pool state
        assert len(session_manager._session_pool) == 3, \
            "Session pool should contain all created sessions"
        
        # Test get_session functionality
        retrieved_session = await session_manager.get_session(
            app_name=app_name,
            user_id=user_id_1,
            session_id=session_1.session_id
        )
        assert retrieved_session is session_1, \
            "get_session should return the correct session instance"
        
        # Test list_sessions functionality
        user_1_sessions = await session_manager.list_sessions(
            app_name=app_name,
            user_id=user_id_1
        )
        assert len(user_1_sessions) == 2, \
            "list_sessions should return correct number of sessions for user"
        assert session_1 in user_1_sessions, \
            "list_sessions should include all sessions for user"
        assert session_2 in user_1_sessions, \
            "list_sessions should include all sessions for user"
        
        user_2_sessions = await session_manager.list_sessions(
            app_name=app_name,
            user_id=user_id_2
        )
        assert len(user_2_sessions) == 1, \
            "list_sessions should return correct number of sessions for user"
        assert session_3 in user_2_sessions, \
            "list_sessions should include all sessions for user"
        
        print("Successfully tested OdaSessionManager session pool management")

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_concurrent_session_limit(self, test_setup):
        """Test concurrent session limit functionality.
        
        This test validates that OdaSessionManager properly enforces
        concurrent session limits.
        """
        session_manager = test_setup["session_manager"]
        app_name = test_setup["app_name"]
        
        # Set concurrent session limit
        max_sessions = 2
        await session_manager.set_concurrent_limit(max_sessions)
        
        # Create sessions up to the limit
        user_id = "test_user_6"
        sessions = []
        for i in range(max_sessions):
            session = await session_manager.create_session(
                app_name=app_name,
                user_id=user_id
            )
            sessions.append(session)
        
        # Validate session pool size
        assert len(session_manager._session_pool) == max_sessions, \
            "Session pool should contain maximum allowed sessions"
        
        # Attempt to create one more session, should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            await session_manager.create_session(
                app_name=app_name,
                user_id=user_id
            )
        
        assert f"Maximum concurrent sessions limit ({max_sessions}) reached" in str(exc_info.value), \
            "Should raise RuntimeError with correct message when limit is exceeded"
        
        # Increase limit and try again
        new_max_sessions = 3
        await session_manager.set_concurrent_limit(new_max_sessions)
        
        # Now creation should succeed
        additional_session = await session_manager.create_session(
            app_name=app_name,
            user_id=user_id
        )
        
        assert isinstance(additional_session, OdaSession), \
            "Session creation should succeed after increasing limit"
        assert len(session_manager._session_pool) == new_max_sessions, \
            "Session pool should contain sessions up to new limit"
        
        print("Successfully tested OdaSessionManager concurrent session limit functionality")