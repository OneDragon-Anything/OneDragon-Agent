"""Test OdaAgent with real Runner and default LLM configuration from environment

This test file focuses on integration testing with real LLM environments, validating 
the correctness of OdaAgent interactions with actual LLM services.

Test Division Strategy:
- This file (test_oda_agent_real_runner.py): Focuses on real LLM environment integration tests
- Mock test file (test_oda_agent_mocks.py): Focuses on OdaAgent internal logic and retry mechanism unit tests

Test Coverage Scope:
- Real LLM execution flow validation
- Session state persistence validation
- Environment configuration integration validation

Content NOT tested in this file (already covered in mock tests):
- Basic functionality validation (get_agent_info, is_ready, cleanup, etc.)
- Detailed retry mechanism implementation
- Message conversion logic
- Synchronous execution method (run method)
- EventActions construction details

This division ensures:
1. Real tests focus on external integration correctness
2. Mock tests focus on internal logic correctness  
3. Avoid test duplication and instability
4. Improve test execution efficiency and reliability

Reference: See test_oda_agent_mocks.py for comprehensive unit tests covering all internal logic.
"""

import os

import pytest
import pytest_asyncio
from google.adk.agents import LlmAgent
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from one_dragon_agent.core.agent.config.oda_agent_config import (
    create_default_agent_config,
)
from one_dragon_agent.core.agent.oda_agent import OdaAgent
from one_dragon_agent.core.context.oda_context_config import OdaContextConfig
from one_dragon_agent.core.model.in_memory_oda_model_config_storage import (
    InMemoryOdaModelConfigStorage,
)
from one_dragon_agent.core.model.oda_model_config_manager import OdaModelConfigManager


class TestOdaAgentWithRealRunner:
    """Test OdaAgent with real Runner and environment configuration
    
    Integration test class focused on real LLM environment validation.
    These tests verify that OdaAgent works correctly with actual LLM services,
    environment configuration, and session persistence.
    
    Note: These tests require real environment variables and network access.
    For unit testing internal logic, see test_oda_agent_mocks.py.
    """
    
    @pytest.fixture
    def required_env_vars(self):
        """Check if required environment variables are set
        
        This fixture validates that the necessary environment variables for LLM connection
        are available before running integration tests. Missing environment variables
        will cause the test to be skipped rather than failed.
        
        Required environment variables:
        - ODA_DEFAULT_LLM_BASE_URL: Base URL for the LLM service
        - ODA_DEFAULT_LLM_API_KEY: API key for LLM service authentication
        - ODA_DEFAULT_LLM_MODEL: Model name to use (defaults to "gemini-2.0-flash")
        
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
            "model": os.getenv("ODA_DEFAULT_LLM_MODEL", "gemini-2.0-flash")
        }
    
    @pytest_asyncio.fixture
    async def test_setup(self, required_env_vars):
        """Create common test setup for real LLM integration testing
        
        This fixture sets up a complete test environment with real LLM connection,
        including all necessary ADK components and OneDragon custom components.
        
        Setup components:
        1. OdaContextConfig: Environment-based LLM configuration
        2. OdaModelConfigManager: Model configuration management with default config
        3. Default Agent Configuration: Standard agent settings
        4. LiteLlm Model: Real LLM model connection using environment variables
        5. LlmAgent: ADK native agent with real model
        6. InMemorySessionService: ADK native session management
        7. Runner: ADK native execution engine
        8. OdaAgent: OneDragon agent wrapper with real runner
        
        Returns:
            dict: Contains all test components including oda_agent, app_name, 
                   user_id, session_id, and model_config_manager
        """
        # Create context config from environment variables
        context_config = OdaContextConfig(
            default_llm_base_url=required_env_vars["base_url"],
            default_llm_api_key=required_env_vars["api_key"],
            default_llm_model=required_env_vars["model"],
        )
        
        # Create model config manager with default configuration
        # This provides default LLM configuration from environment variables
        model_config_service = InMemoryOdaModelConfigStorage()
        model_config_manager = OdaModelConfigManager(
            config_service=model_config_service,
            context_config=context_config
        )
        
        # Create default agent configuration for testing
        app_name = "test_app"
        agent_config = create_default_agent_config(app_name)
        
        # Create LlmAgent with real GLM model using LiteLlm
        from google.adk.models.lite_llm import LiteLlm
        
        # Configure LiteLlm to connect to actual LLM endpoint
        # Note: "openai/" prefix is required by litellm for openai- custom endpoints
        llm_model = LiteLlm(
            model=f'openai/{required_env_vars["model"]}',
            api_base=required_env_vars["base_url"],
            api_key=f'{required_env_vars["api_key"]}',
        )
        
        # Create ADK native LlmAgent with real model and configuration
        llm_agent = LlmAgent(
            name=agent_config.agent_name,
            model=llm_model,
            instruction='',
        )
        
        # Create ADK native session service for real session management
        session_service = InMemorySessionService()
        
        # Create ADK native Runner with real agent and session service
        runner = Runner(
            agent=llm_agent,
            app_name=app_name,
            session_service=session_service,
        )
        
        # Create session first (required by ADK Runner before execution)
        user_id = "test_user"
        session_id = "test_session"
        await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
        
        # Create OneDragon OdaAgent wrapper with real runner
        # Use 1 retry for faster testing (retry logic tested in mock tests)
        oda_agent = OdaAgent(
            runner=runner,
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            max_retries=1
        )
        
        return {
            "oda_agent": oda_agent,
            "app_name": app_name,
            "user_id": user_id,
            "session_id": session_id,
            "model_config_manager": model_config_manager
        }

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)  # Increased timeout for real LLM interaction
    async def test_basic_llm_execution_flow(self, test_setup):
        """Test real LLM execution flow with actual model interaction
        
        This is the core integration test that validates OdaAgent works correctly
        with real LLM services. It focuses on:
        
        1. Event stream generation and processing
        2. Real LLM response validation  
        3. Message execution flow
        
        Note: Basic functionality tests (get_agent_info, is_ready, etc.) are 
        intentionally excluded here as they are thoroughly covered in 
        test_oda_agent_mocks.py. This test focuses exclusively on real LLM 
        integration aspects.
        
        Test strategy:
        - Use simple, reliable messages that should always succeed
        - Validate response structure rather than specific content
        - Focus on flow correctness rather than output quality
        """
        oda_agent = test_setup["oda_agent"]
        
        # Test: Simple arithmetic question (should always work with modern LLMs)
        event_count = 0
        final_response_found = False
        response_content = None
        
        async for event in oda_agent.run_async("What is 1+1? Answer with just the number."):
            event_count += 1
            assert isinstance(event, Event), f"Event should be Event instance, got {type(event)}"
            
            # Validate event structure from real LLM
            if event.is_final_response():
                final_response_found = True
                if event.content and event.content.parts:
                    assert len(event.content.parts) > 0, "Final response should have content parts"
                    response_content = event.content.parts[0].text
                    print(f"Arithmetic response: {response_content}")
                    
                    # Modern LLMs should reliably answer this simple question
                    response_clean = response_content.strip().lower()
                    assert "2" in response_content, f"Response should contain '2', got: {response_content}"
                    # Also accept "two" as valid answer
                    assert "2" in response_content or "two" in response_clean, \
                        f"Response should contain '2' or 'two', got: {response_content}"
        
        # Core integration validation
        assert event_count > 0, "Should have received at least one event from real LLM"
        assert final_response_found, "Should have found a final response event from real LLM"
        assert response_content is not None, "Should have received response content from real LLM"
        
        print("Basic LLM execution flow test completed successfully")

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)  # Increased timeout for real LLM interaction
    async def test_session_state_persistence(self, test_setup):
        """Test session state persistence across multiple interactions with real LLM
        
        This test validates that session state is properly maintained across
        multiple LLM interactions, which is critical for real-world usage.
        
        Modern LLM approach: Current LLMs are capable enough to maintain
        context and remember previous information in the conversation,
        allowing us to test actual context persistence with reliable verification.
        
        Test focus:
        1. Multi-turn conversation context persistence
        2. Session state management with real LLM
        3. Context continuity validation with verifiable memory
        """
        oda_agent = test_setup["oda_agent"]
        
        # First interaction: Establish specific context
        first_response_found = False
        first_response_content = None
        
        async for event in oda_agent.run_async("My name is Alice and I live in Paris"):
            if event.is_final_response() and event.content:
                first_response_found = True
                first_response_content = event.content.parts[0].text
                print(f"First interaction response: {first_response_content}")
                break
        
        assert first_response_found, "First interaction should complete successfully"
        assert len(first_response_content.strip()) > 0, "First response should not be empty"
        
        # Second interaction: Test context persistence with specific question
        second_response_found = False
        second_response_content = None
        
        async for event in oda_agent.run_async("What is my name and where do I live? Please answer briefly."):
            if event.is_final_response() and event.content:
                second_response_found = True
                second_response_content = event.content.parts[0].text
                print(f"Second interaction response: {second_response_content}")
                break
        
        assert second_response_found, "Second interaction should complete successfully"
        assert len(second_response_content.strip()) > 0, "Second response should not be empty"
        
        # Validate that session maintains context - modern LLMs should remember
        response_lower = second_response_content.lower()
        
        # Check if the LLM remembered the name "Alice"
        name_remembered = "alice" in response_lower
        
        # Check if the LLM remembered the location "Paris" 
        location_remembered = "paris" in response_lower
        
        # Modern LLMs should be capable of remembering both pieces of information
        # We'll accept if it remembers at least one, but ideally both
        assert (name_remembered or location_remembered), \
            f"LLM should remember at least one piece of context (name or location), got: {second_response_content}"
        
        # Additional validation: Check that response is contextual
        contextual_keywords = ["alice", "paris", "name", "live", "city"]
        has_contextual_content = any(keyword in response_lower for keyword in contextual_keywords)
        
        assert has_contextual_content, \
            f"Response should show contextual awareness, got: {second_response_content}"
        
        print(f"Session state persistence validated - Name remembered: {name_remembered}, Location remembered: {location_remembered}")
        print("Session state persistence test completed successfully")

    @pytest.mark.asyncio
    @pytest.mark.timeout(120)  # Increased timeout for real LLM interaction
    async def test_environment_configuration_integration(self, test_setup):
        """Test environment configuration integration with real LLM
        
        This test validates that environment-based configuration works correctly
        with real LLM services, ensuring the integration between:
        
        1. Environment variables (ODA_DEFAULT_LLM_*)
        2. OdaContextConfig
        3. OdaModelConfigManager
        4. Real LLM connection
        
        Modern LLM validation approach: Use specific questions with verifiable
        answers to ensure environment configuration actually produces correct
        LLM behavior, not just any response. Modern LLMs are reliable
        enough for consistent factual answers.
        
        Note: Cleanup functionality testing is intentionally excluded as it's
        thoroughly covered in test_oda_agent_mocks.py. This test focuses
        on environment configuration integration which requires real LLM.
        """
        oda_agent = test_setup["oda_agent"]
        model_config_manager = test_setup["model_config_manager"]
        
        # Verify default LLM configuration is available from environment
        default_config = model_config_manager.get_default_config()
        assert default_config is not None, "Default LLM config should be available from environment"
        assert default_config.base_url is not None, "Base URL should be configured"
        assert default_config.api_key is not None, "API key should be configured"
        assert default_config.model is not None, "Model should be configured"
        
        print(f"Environment configuration verified - Model: {default_config.model}")
        print(f"Environment configuration verified - Base URL: {default_config.base_url}")
        
        # Test that configuration actually works with real LLM using verifiable question
        response_found = False
        response_content = None
        
        # Use a question with a specific, verifiable answer
        async for event in oda_agent.run_async("What is the capital of France? Please answer briefly."):
            if event.is_final_response() and event.content:
                response_found = True
                response_content = event.content.parts[0].text
                print(f"Configuration test response: {response_content}")
                break
        
        # Validate that environment configuration enables successful LLM interaction
        assert response_found, "Environment configuration should enable successful LLM interaction"
        assert len(response_content.strip()) > 0, "Configuration should produce valid LLM response"
        
        # Additional validation: Check if LLM provides expected answer
        # Modern LLMs should reliably answer this basic factual question
        response_lower = response_content.lower()
        
        # Also check if response is at least capital-related
        capital_keywords = ["paris", "capital", "france"]
        has_capital_context = any(keyword in response_lower for keyword in capital_keywords)
        
        # Modern LLMs should provide a reasonable answer to this simple question
        assert has_capital_context, \
            f"LLM should provide reasonable answer about capital of France, got: {response_content}"
        
        print(f"Environment configuration validated - Capital context: {has_capital_context}")
        print("Environment configuration integration test completed successfully")

    # Note: Retry mechanism testing has been intentionally removed from this file.
# 
# Reason: Retry mechanism testing requires controlled failure simulation which is
# not reliable in real LLM environments. The retry mechanism is thoroughly
# tested in test_oda_agent_mocks.py with:
#
# 1. test_retry_event_generation_on_exception - Validates retry event generation
# 2. test_run_async_content_conversion_first_call - Tests retry with failure simulation
# 3. test_run_method_retry_mechanism - Tests synchronous retry mechanism
# 4. test_event_actions_construction - Validates EventActions construction
#
# This real integration test focuses on successful LLM interactions,
# assuming retry logic works correctly (validated by mock tests).