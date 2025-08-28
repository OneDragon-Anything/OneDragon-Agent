"""Test OdaAgent logic with mocks to ensure correct behavior"""

from unittest.mock import AsyncMock, Mock

import pytest
from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.genai.types import Content, Part

from one_dragon_agent.core.agent.config.oda_agent_config import (
    create_default_agent_config,
)
from one_dragon_agent.core.agent.oda_agent import OdaAgent
from one_dragon_agent.core.model.oda_model_config import OdaModelConfig
from one_dragon_agent.core.model.oda_model_config_manager import OdaModelConfigManager

# Test constants
DEFAULT_MAX_RETRIES = 2
EXPECTED_RETRY_EVENTS = 2
EXPECTED_TOTAL_EVENTS = 3
SINGLE_EVENT_COUNT = 1


class TestOdaAgentWithMocks:
    """Test OdaAgent logic with mocked dependencies"""

    @pytest.fixture
    def mock_runner(self):
        """Create a mock Runner instance"""
        mock_runner = Mock(spec=Runner)
        # Create a proper async mock that yields events
        async def mock_run_async(*args, **kwargs):
            # Correct ADK Runner.run_async implementation: AsyncGenerator[Event, None]
            # Mock runner should yield Event objects, not return empty generator
            # For testing, we'll yield a simple final response event
            final_event = Event(
                author="model",
                content=Content(
                    role="model", 
                    parts=[Part(text="Mock response")]
                )
            )
            yield final_event
        
        mock_runner.run_async = AsyncMock(side_effect=mock_run_async)
        mock_runner.run = Mock(return_value=iter([]))
        return mock_runner

    @pytest.fixture
    def mock_model_config(self):
        """Create a mock model config"""
        return OdaModelConfig(
            app_name="test_app",
            model_id="test_model",
            base_url="https://example.com",
            api_key="test_key",
            model="gemini-2.0-flash"
        )

    @pytest.fixture
    def mock_model_config_manager(self, mock_model_config):
        """Create a mock model config manager"""
        mock_manager = Mock(spec=OdaModelConfigManager)
        mock_manager.get_model_config = AsyncMock(return_value=mock_model_config)
        return mock_manager

    @pytest.fixture
    def agent_config(self):
        """Create a default agent config"""
        return create_default_agent_config("test_app")

    @pytest.fixture
    def oda_agent(self, mock_runner, agent_config):
        """Create an OdaAgent instance for testing"""
        return OdaAgent(
            runner=mock_runner,
            app_name="test_app",
            user_id="test_user",
            session_id="test_session",
            max_retries=DEFAULT_MAX_RETRIES
        )

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_oda_agent_initialization(self, oda_agent, mock_runner):
        """Test OdaAgent initialization"""
        assert oda_agent.runner == mock_runner
        assert oda_agent.app_name == "test_app"
        assert oda_agent.user_id == "test_user"
        assert oda_agent.session_id == "test_session"
        assert oda_agent.max_retries == DEFAULT_MAX_RETRIES
        assert oda_agent._retry_count == 0
        assert oda_agent.is_ready()

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_oda_agent_get_agent_info(self, oda_agent):
        """Test get_agent_info method"""
        info = oda_agent.get_agent_info()
        expected_info = {
            "app_name": "test_app",
            "user_id": "test_user",
            "session_id": "test_session",
            "max_retries": 2,
            "retry_count": 0,
        }
        assert info == expected_info

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_run_async_content_conversion_first_call(self, oda_agent, mock_runner):
        """Test that run_async converts string to Content on first execution"""
        test_message = "Hello, world!"
        
        # Mock runner's run_async to capture call arguments and succeed
        call_args_list = []

        # Create a mock that captures arguments and handles retry properly
        call_count = 0

        async def mock_runner_run_async(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            call_args_list.append((args, kwargs))

            # First call fails, second call succeeds with Event generator
            if call_count == 1:
                raise Exception("First call fails to test retry")
            else:
                # Correct ADK Runner.run_async implementation: AsyncGenerator[Event, None]
                # Mock runner should yield Event objects, not return empty generator
                final_event = Event(
                    author="model",
                    content=Content(
                        role="model",
                        parts=[Part(text="Retry success response")]
                    )
                )
                yield final_event

        mock_runner.run_async = mock_runner_run_async

        events = []
        async for event in oda_agent.run_async(test_message):
            events.append(event)

        # Verify that run_async was called twice (first failed, second succeeded)
        assert len(call_args_list) == 2

        # Verify first call (with Content object)
        args, kwargs = call_args_list[0]
        assert kwargs['user_id'] == "test_user"
        assert kwargs['session_id'] == "test_session"
        assert kwargs['new_message'].role == "user"
        assert kwargs['new_message'].parts[0].text == test_message

        # Verify second call (retry with None message)
        args, kwargs = call_args_list[1]
        assert kwargs['user_id'] == "test_user"
        assert kwargs['session_id'] == "test_session"
        assert kwargs['new_message'] is None

    @pytest.mark.asyncio
    async def test_run_content_conversion_first_call(self, oda_agent, mock_runner):
        """Test that run converts string to Content on first execution"""
        test_message = "Hello, world!"

        # Mock runner's run to capture call arguments
        call_args_list = []

        def mock_run(*args, **kwargs):
            call_args_list.append((args, kwargs))
            # Return empty iterator to stop iteration
            return iter([])

        mock_runner.run.side_effect = mock_run

        # Execute method - it should only call once because we return empty iterator
        events = []
        for event in oda_agent.run(test_message):
            events.append(event)

        # Verify that run was called exactly once with Content object
        assert len(call_args_list) == 1
        args, kwargs = call_args_list[0]
        assert kwargs['user_id'] == "test_user"
        assert kwargs['session_id'] == "test_session"
        assert kwargs['new_message'].role == "user"
        assert kwargs['new_message'].parts[0].text == test_message

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_cleanup_resets_retry_count(self, oda_agent):
        """Test that cleanup resets retry count"""
        # Set retry count to non-zero
        oda_agent._retry_count = 5

        # Call cleanup
        await oda_agent.cleanup()

        # Verify retry count was reset
        assert oda_agent._retry_count == 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_retry_event_generation_on_exception(self, oda_agent, mock_runner):
        """Test retry event generation when execution fails"""
        test_message = "Test message that will fail"

        # Mock runner to always raise exception like real Runner
        async def always_fail_async(*args, **kwargs):
            # Correct ADK Runner.run_async implementation: AsyncGenerator[Event, None]
            # Mock runner should be an async generator that raises exception when iterated
            raise Exception("Simulated execution failure")
            yield Event(  # This makes it a generator, but never reached
                author="model",
                content=Content(role="model", parts=[Part(text="This would be the response")])
            )

        def always_fail_sync(*args, **kwargs):
            raise Exception("Simulated execution failure")

        mock_runner.run_async = always_fail_async
        mock_runner.run = Mock(side_effect=always_fail_sync)

        # Execute method and capture events
        events = []
        retry_events = []
        final_error_events = []

        async for event in oda_agent.run_async(test_message):
            events.append(event)
            if hasattr(event, 'error_code'):
                if event.error_code == "RETRY_ATTEMPT":
                    retry_events.append(event)
                elif event.error_code == "MAX_RETRIES_EXCEEDED":
                    final_error_events.append(event)

        # Test retry events
        assert len(retry_events) == oda_agent.max_retries  # Should have 2 retry events
        for i, retry_event in enumerate(retry_events):
            assert retry_event.author == "system"
            assert retry_event.error_code == "RETRY_ATTEMPT"
            assert f"Retry attempt {i+1}/{oda_agent.max_retries}" in retry_event.error_message
            assert retry_event.actions == EventActions()

        # Test final error event
        assert len(final_error_events) == SINGLE_EVENT_COUNT
        final_error = final_error_events[0]
        assert final_error.author == "system"
        assert final_error.error_code == "MAX_RETRIES_EXCEEDED"
        assert "Maximum retries exceeded" in final_error.error_message
        assert final_error.actions.escalate is True

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_runner_cleanup_called_during_oda_cleanup(self, oda_agent):
        """Test that runner cleanup is called during OdaAgent cleanup"""
        # Add cleanup method to mock runner
        oda_agent.runner.cleanup = AsyncMock()

        # Call cleanup
        await oda_agent.cleanup()

        # Verify runner cleanup was called
        oda_agent.runner.cleanup.assert_called_once()

        # Verify retry count was reset
        assert oda_agent._retry_count == 0

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_event_actions_construction(self):
        """Test that retry and error events are constructed with correct EventActions"""
        # Create a new OdaAgent for this specific test to avoid state pollution
        mock_runner = Mock(spec=Runner)
        async def always_fail(*args, **kwargs):
            # Correct ADK Runner.run_async implementation: AsyncGenerator[Event, None]
            # Mock runner should be an async generator that raises exception when iterated
            raise Exception("Test failure")
            yield Event(  # This makes it a generator, but never reached
                author="model",
                content=Content(role="model", parts=[Part(text="This would be response")])
            )
        
        mock_runner.run_async = always_fail
        
        test_agent = OdaAgent(
            runner=mock_runner,
            app_name="test_app",
            user_id="test_user",
            session_id="test_session",
            max_retries=1  # Use 1 retry to make test faster
        )
        
        # Execute and capture events
        retry_events = []
        error_events = []
        
        async for event in test_agent.run_async("Test message"):
            if hasattr(event, 'error_code'):
                if event.error_code == "RETRY_ATTEMPT":
                    retry_events.append(event)
                elif event.error_code == "MAX_RETRIES_EXCEEDED":
                    error_events.append(event)
            # Break after getting the final error to avoid infinite loop
            if error_events:
                break
        
        # Test retry event structure
        assert len(retry_events) == 1
        retry_event = retry_events[0]
        assert retry_event.author == "system"
        assert retry_event.error_code == "RETRY_ATTEMPT"
        assert retry_event.actions == EventActions()
        
        # Test error event structure
        assert len(error_events) == 1
        error_event = error_events[0]
        assert error_event.author == "system"
        assert error_event.error_code == "MAX_RETRIES_EXCEEDED"
        assert error_event.actions.escalate is True
        
        # Verify total events: 1 retry + 1 final error
        assert len(retry_events) + len(error_events) == 2  # 1 retry + 1 final error

    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_run_method_retry_mechanism(self, oda_agent, mock_runner):
        """Test synchronous run method retry mechanism"""
        test_message = "Test message that will fail"
        
        # Mock runner to always raise exception
        def always_fail_sync(*args, **kwargs):
            raise Exception("Simulated execution failure")
        
        mock_runner.run.side_effect = always_fail_sync
        
        # Execute method and capture events
        events = []
        retry_events = []
        final_error_events = []
        
        for event in oda_agent.run(test_message):
            events.append(event)
            if hasattr(event, 'error_code'):
                if event.error_code == "RETRY_ATTEMPT":
                    retry_events.append(event)
                elif event.error_code == "MAX_RETRIES_EXCEEDED":
                    final_error_events.append(event)
        
        # Test retry events
        assert len(retry_events) == oda_agent.max_retries  # Should have 2 retry events
        for i, retry_event in enumerate(retry_events):
            assert retry_event.author == "system"
            assert retry_event.error_code == "RETRY_ATTEMPT"
            assert f"Retry attempt {i+1}/{oda_agent.max_retries}" in retry_event.error_message
            assert retry_event.actions == EventActions()
        
        # Test final error event
        assert len(final_error_events) == SINGLE_EVENT_COUNT
        final_error = final_error_events[0]
        assert final_error.author == "system"
        assert final_error.error_code == "MAX_RETRIES_EXCEEDED"
        assert "Maximum retries exceeded" in final_error.error_message
        assert final_error.actions.escalate is True
        
        # Verify total events: 2 retry + 1 final error
        assert len(events) == EXPECTED_TOTAL_EVENTS