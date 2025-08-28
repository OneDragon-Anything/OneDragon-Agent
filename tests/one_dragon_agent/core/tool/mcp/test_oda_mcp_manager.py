from unittest.mock import AsyncMock, patch

import pytest

from one_dragon_agent.core.tool.mcp.oda_mcp_config import OdaMcpConfig
from one_dragon_agent.core.tool.mcp.oda_mcp_manager import OdaMcpManager


class TestOdaMcpManager:
    """Tests for OdaMcpManager class."""

    @pytest.fixture
    def manager(self):
        """Fixture to create a new OdaMcpManager instance for each test."""
        # Create a mock storage for testing
        from unittest.mock import Mock
        from one_dragon_agent.core.tool.mcp.oda_mcp_config_storage import BaseOdaMcpStorage
        mock_storage = Mock(spec=BaseOdaMcpStorage)
        mock_storage.create_config = AsyncMock()
        mock_storage.get_config = AsyncMock(return_value=None)
        mock_storage.update_config = AsyncMock()
        mock_storage.delete_config = AsyncMock()
        mock_storage.list_configs = AsyncMock(return_value=[])
        return OdaMcpManager(custom_config_storage=mock_storage)

    @pytest.fixture
    def sample_builtin_config(self):
        """Fixture to create a sample built-in OdaMcpConfig."""
        return OdaMcpConfig(
            app_name="test_app",
            mcp_id="builtin_mcp",
            name="Built-in MCP",
            description="Built-in Description",
            server_type="sse",
            url="http://localhost:8090/sse",
            headers={"Authorization": "Bearer token"},
            tool_filter=["read_file", "list_directory"],
            timeout=30,
            retry_count=3
        )

    @pytest.fixture
    def sample_custom_config(self):
        """Fixture to create a sample custom OdaMcpConfig."""
        return OdaMcpConfig(
            app_name="test_app",
            mcp_id="custom_mcp",
            name="Custom MCP",
            description="Custom Description",
            server_type="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
            timeout=30,
            retry_count=3
        )

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_build_in_config(self, manager, sample_builtin_config):
        """Test registering a built-in configuration."""
        await manager.register_build_in_config(sample_builtin_config)

        # Verify the config was stored in built-in configs
        global_id = sample_builtin_config.get_global_id()
        assert global_id in manager._build_in_configs
        assert manager._build_in_configs[global_id] == sample_builtin_config

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_build_in_config_duplicate(self, manager, sample_builtin_config):
        """Test registering a duplicate built-in configuration."""
        # Register the config once
        await manager.register_build_in_config(sample_builtin_config)

        # Try to register the same config again - should raise ValueError
        with pytest.raises(ValueError, match="Built-in config with ID .* already exists"):
            await manager.register_build_in_config(sample_builtin_config)

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_register_custom_config(self, manager, sample_custom_config):
        """Test registering a custom configuration."""
        with patch.object(manager._custom_config_storage, 'create_config', new_callable=AsyncMock) as mock_create:
            await manager.register_custom_config(sample_custom_config)

            # Verify the storage method was called
            mock_create.assert_called_once_with(sample_custom_config)

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_unregister_build_in_config(self, manager, sample_builtin_config):
        """Test unregistering a built-in configuration."""
        # First register the config
        await manager.register_build_in_config(sample_builtin_config)

        # Try to unregister it - should raise PermissionError
        with pytest.raises(PermissionError, match="Built-in configurations cannot be unregistered"):
            await manager.unregister_build_in_config("test_app", "builtin_mcp")

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_unregister_custom_config(self, manager, sample_custom_config):
        """Test unregistering a custom configuration."""
        with patch.object(manager._custom_config_storage, 'delete_config', new_callable=AsyncMock) as mock_delete:
            await manager.unregister_custom_config("test_app", "custom_mcp")

            # Verify the storage method was called
            mock_delete.assert_called_once_with("test_app:custom_mcp")

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_mcp_config_from_builtin(self, manager, sample_builtin_config):
        """Test getting a configuration from built-in configs."""
        # First register the config
        await manager.register_build_in_config(sample_builtin_config)

        # Retrieve it
        config = await manager.get_mcp_config("test_app", "builtin_mcp")
        assert config is not None
        assert config == sample_builtin_config

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_mcp_config_from_custom(self, manager, sample_custom_config):
        """Test getting a configuration from custom configs."""
        # Mock the storage to return the custom config
        with patch.object(manager._custom_config_storage, 'get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = sample_custom_config
            config = await manager.get_mcp_config("test_app", "custom_mcp")

            # Verify the storage method was called
            mock_get.assert_called_once_with("test_app:custom_mcp")
            assert config is not None
            assert config == sample_custom_config

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_mcp_config_not_found(self, manager):
        """Test getting a non-existent configuration."""
        # Mock the storage to return None
        with patch.object(manager._custom_config_storage, 'get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            config = await manager.get_mcp_config("test_app", "non_existent_mcp")

            # Verify the storage method was called
            mock_get.assert_called_once_with("test_app:non_existent_mcp")
            assert config is None

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_mcp_configs(self, manager, sample_builtin_config):
        """Test listing all configurations."""
        # Register a built-in config
        await manager.register_build_in_config(sample_builtin_config)

        # Mock the storage to return custom configs
        custom_config = OdaMcpConfig(
            app_name="test_app",
            mcp_id="custom_mcp",
            name="Custom MCP",
            description="Custom Description",
            server_type="stdio",
            command="npx",
            timeout=30,
            retry_count=3
        )

        with patch.object(manager._custom_config_storage, 'list_configs', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [custom_config]
            configs = await manager.list_mcp_configs("test_app")

            # Verify the storage method was called
            mock_list.assert_called_once()

            # Verify both built-in and custom configs are returned
            assert len(configs) == 2
            assert sample_builtin_config.get_global_id() in configs
            assert custom_config.get_global_id() in configs
            assert configs[sample_builtin_config.get_global_id()] == sample_builtin_config
            assert configs[custom_config.get_global_id()] == custom_config

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_update_custom_config(self, manager, sample_custom_config):
        """Test updating a custom configuration."""
        # Mock the storage methods
        with patch.object(manager._custom_config_storage, 'get_config', new_callable=AsyncMock) as mock_get, \
             patch.object(manager._custom_config_storage, 'update_config', new_callable=AsyncMock) as mock_update:

            # Mock get_config to return an existing config
            mock_get.return_value = sample_custom_config

            # Update the config
            await manager.update_custom_config("test_app", "custom_mcp", sample_custom_config)

            # Verify the storage methods were called
            mock_get.assert_called_once_with("test_app:custom_mcp")
            mock_update.assert_called_once_with(sample_custom_config)

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_update_custom_config_not_found(self, manager, sample_custom_config):
        """Test updating a non-existent custom configuration."""
        # Mock the storage methods
        with patch.object(manager._custom_config_storage, 'get_config', new_callable=AsyncMock) as mock_get:
            # Mock get_config to return None (config not found)
            mock_get.return_value = None

            # Try to update the config - should raise ValueError
            with pytest.raises(ValueError, match="Custom config with ID .* does not exist"):
                await manager.update_custom_config("test_app", "non_existent_mcp", sample_custom_config)

            # Verify the storage method was called
            mock_get.assert_called_once_with("test_app:non_existent_mcp")

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_update_builtin_config_should_fail(self, manager, sample_builtin_config):
        """Test that updating a built-in configuration should fail."""
        # First register the built-in config
        await manager.register_build_in_config(sample_builtin_config)

        # Mock the storage to return None for custom config check
        with patch.object(manager._custom_config_storage, 'get_config', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            # Try to update the built-in config - should raise PermissionError
            with pytest.raises(PermissionError, match="Cannot update built-in configurations"):
                await manager.update_custom_config("test_app", "builtin_mcp", sample_builtin_config)