import pytest

from one_dragon_agent.core.tool.mcp.oda_mcp_config import OdaMcpConfig
from one_dragon_agent.core.tool.mcp.oda_mcp_config_storage import InMemoryOdaMcpStorage


class TestInMemoryOdaMcpStorage:
    """Tests for InMemoryOdaMcpStorage class."""

    @pytest.fixture
    def storage(self):
        """Fixture to create a new InMemoryOdaMcpStorage instance for each test."""
        return InMemoryOdaMcpStorage()

    @pytest.fixture
    def sample_config(self):
        """Fixture to create a sample OdaMcpConfig."""
        return OdaMcpConfig(
            app_name="test_app",
            mcp_id="test_mcp",
            name="Test MCP",
            description="Test Description",
            server_type="sse",
            url="http://localhost:8090/sse",
            headers={"Authorization": "Bearer token"},
            tool_filter=["read_file", "list_directory"],
            timeout=30,
            retry_count=3
        )

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_create_config(self, storage, sample_config):
        """Test creating a configuration."""
        await storage.create_config(sample_config)

        # Verify the config was stored
        stored_config = storage._configs.get(sample_config.get_global_id())
        assert stored_config is not None
        assert stored_config == sample_config

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_config(self, storage, sample_config):
        """Test getting a configuration."""
        # First create a config
        await storage.create_config(sample_config)

        # Then retrieve it
        retrieved_config = await storage.get_config(sample_config.get_global_id())
        assert retrieved_config is not None
        assert retrieved_config == sample_config

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_get_config_not_found(self, storage):
        """Test getting a non-existent configuration."""
        config = await storage.get_config("non_existent_app:non_existent_mcp")
        assert config is None

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_update_config(self, storage, sample_config):
        """Test updating a configuration."""
        # First create a config
        await storage.create_config(sample_config)

        # Update the config with new values
        updated_config = OdaMcpConfig(
            app_name="test_app",
            mcp_id="test_mcp",
            name="Updated MCP",
            description="Updated Description",
            server_type="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
            timeout=60,
            retry_count=5
        )

        await storage.update_config(updated_config)

        # Verify the config was updated
        retrieved_config = await storage.get_config(sample_config.get_global_id())
        assert retrieved_config is not None
        assert retrieved_config == updated_config
        assert retrieved_config.name == "Updated MCP"
        assert retrieved_config.description == "Updated Description"
        assert retrieved_config.server_type == "stdio"
        assert retrieved_config.timeout == 60

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_delete_config(self, storage, sample_config):
        """Test deleting a configuration."""
        # First create a config
        await storage.create_config(sample_config)

        # Verify it exists
        retrieved_config = await storage.get_config(sample_config.get_global_id())
        assert retrieved_config is not None

        # Delete the config
        await storage.delete_config(sample_config.get_global_id())

        # Verify it was deleted
        retrieved_config = await storage.get_config(sample_config.get_global_id())
        assert retrieved_config is None

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_delete_config_not_found(self, storage):
        """Test deleting a non-existent configuration."""
        # This should not raise an exception
        await storage.delete_config("non_existent_app:non_existent_mcp")

    @pytest.mark.asyncio
    @pytest.mark.timeout(5)
    async def test_list_configs(self, storage):
        """Test listing all configurations."""
        # Create multiple configs
        config1 = OdaMcpConfig(
            app_name="test_app",
            mcp_id="test_mcp_1",
            name="Test MCP 1",
            description="Test Description 1",
            server_type="sse",
            url="http://localhost:8090/sse",
            timeout=30,
            retry_count=3
        )

        config2 = OdaMcpConfig(
            app_name="test_app",
            mcp_id="test_mcp_2",
            name="Test MCP 2",
            description="Test Description 2",
            server_type="stdio",
            command="npx",
            timeout=30,
            retry_count=3
        )

        config3 = OdaMcpConfig(
            app_name="another_app",
            mcp_id="test_mcp_3",
            name="Test MCP 3",
            description="Test Description 3",
            server_type="http",
            url="http://localhost:8080/mcp",
            timeout=30,
            retry_count=3
        )

        # Store all configs
        await storage.create_config(config1)
        await storage.create_config(config2)
        await storage.create_config(config3)

        # List all configs
        configs = await storage.list_configs()

        # Verify all configs are returned
        assert len(configs) == 3
        assert config1 in configs
        assert config2 in configs
        assert config3 in configs