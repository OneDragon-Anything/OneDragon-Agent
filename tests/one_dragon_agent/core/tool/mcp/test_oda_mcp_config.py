import pytest

from one_dragon_agent.core.tool.mcp.oda_mcp_config import OdaMcpConfig


class TestOdaMcpConfig:
    """Tests for OdaMcpConfig class."""

    def test_init_with_valid_sse_config(self):
        """Test initializing with valid SSE configuration."""
        config = OdaMcpConfig(
            app_name="test_app",
            mcp_id="sse_mcp",
            name="SSE MCP",
            description="Test SSE MCP",
            server_type="sse",
            url="http://localhost:8090/sse",
            headers={"Authorization": "Bearer token"},
            tool_filter=["read_file", "list_directory"],
            timeout=30,
            retry_count=3
        )

        assert config.app_name == "test_app"
        assert config.mcp_id == "sse_mcp"
        assert config.name == "SSE MCP"
        assert config.description == "Test SSE MCP"
        assert config.server_type == "sse"
        assert config.url == "http://localhost:8090/sse"
        assert config.headers == {"Authorization": "Bearer token"}
        assert config.tool_filter == ["read_file", "list_directory"]
        assert config.timeout == 30
        assert config.retry_count == 3

    def test_init_with_valid_stdio_config(self):
        """Test initializing with valid Stdio configuration."""
        config = OdaMcpConfig(
            app_name="test_app",
            mcp_id="stdio_mcp",
            name="Stdio MCP",
            description="Test Stdio MCP",
            server_type="stdio",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem"],
            env={"TARGET_FOLDER": "/path/to/folder"},
            tool_filter=["read_file", "list_directory"],
            timeout=30,
            retry_count=3
        )

        assert config.app_name == "test_app"
        assert config.mcp_id == "stdio_mcp"
        assert config.name == "Stdio MCP"
        assert config.description == "Test Stdio MCP"
        assert config.server_type == "stdio"
        assert config.command == "npx"
        assert config.args == ["-y", "@modelcontextprotocol/server-filesystem"]
        assert config.env == {"TARGET_FOLDER": "/path/to/folder"}
        assert config.tool_filter == ["read_file", "list_directory"]
        assert config.timeout == 30
        assert config.retry_count == 3

    def test_init_with_valid_http_config(self):
        """Test initializing with valid HTTP configuration."""
        config = OdaMcpConfig(
            app_name="test_app",
            mcp_id="http_mcp",
            name="HTTP MCP",
            description="Test HTTP MCP",
            server_type="http",
            url="http://localhost:8080/mcp",
            headers={"Authorization": "Bearer token", "Content-Type": "application/json"},
            tool_filter=["get_data", "post_data"],
            timeout=30,
            retry_count=3
        )

        assert config.app_name == "test_app"
        assert config.mcp_id == "http_mcp"
        assert config.name == "HTTP MCP"
        assert config.description == "Test HTTP MCP"
        assert config.server_type == "http"
        assert config.url == "http://localhost:8080/mcp"
        assert config.headers == {"Authorization": "Bearer token", "Content-Type": "application/json"}
        assert config.tool_filter == ["get_data", "post_data"]
        assert config.timeout == 30
        assert config.retry_count == 3

    def test_validation_empty_app_name(self):
        """Test validation for empty app_name."""
        with pytest.raises(ValueError, match="app_name cannot be empty"):
            OdaMcpConfig(
                app_name="",
                mcp_id="test_mcp",
                name="Test MCP",
                description="Test Description",
                server_type="sse",
                url="http://localhost:8090/sse"
            )

    def test_validation_empty_mcp_id(self):
        """Test validation for empty mcp_id."""
        with pytest.raises(ValueError, match="mcp_id cannot be empty"):
            OdaMcpConfig(
                app_name="test_app",
                mcp_id="",
                name="Test MCP",
                description="Test Description",
                server_type="sse",
                url="http://localhost:8090/sse"
            )

    def test_validation_empty_name(self):
        """Test validation for empty name."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            OdaMcpConfig(
                app_name="test_app",
                mcp_id="test_mcp",
                name="",
                description="Test Description",
                server_type="sse",
                url="http://localhost:8090/sse"
            )

    def test_validation_empty_description(self):
        """Test validation for empty description."""
        with pytest.raises(ValueError, match="description cannot be empty"):
            OdaMcpConfig(
                app_name="test_app",
                mcp_id="test_mcp",
                name="Test MCP",
                description="",
                server_type="sse",
                url="http://localhost:8090/sse"
            )

    def test_validation_invalid_server_type(self):
        """Test validation for invalid server_type."""
        with pytest.raises(ValueError, match="server_type must be 'sse', 'stdio' or 'http'"):
            OdaMcpConfig(
                app_name="test_app",
                mcp_id="test_mcp",
                name="Test MCP",
                description="Test Description",
                server_type="invalid",
                url="http://localhost:8090/sse"
            )

    def test_validation_sse_without_url(self):
        """Test validation for SSE server without url."""
        with pytest.raises(ValueError, match="url cannot be empty when server_type is 'sse' or 'http'"):
            OdaMcpConfig(
                app_name="test_app",
                mcp_id="test_mcp",
                name="Test MCP",
                description="Test Description",
                server_type="sse"
            )

    def test_validation_http_without_url(self):
        """Test validation for HTTP server without url."""
        with pytest.raises(ValueError, match="url cannot be empty when server_type is 'sse' or 'http'"):
            OdaMcpConfig(
                app_name="test_app",
                mcp_id="test_mcp",
                name="Test MCP",
                description="Test Description",
                server_type="http"
            )

    def test_validation_stdio_without_command(self):
        """Test validation for Stdio server without command."""
        with pytest.raises(ValueError, match="command cannot be empty when server_type is 'stdio'"):
            OdaMcpConfig(
                app_name="test_app",
                mcp_id="test_mcp",
                name="Test MCP",
                description="Test Description",
                server_type="stdio"
            )

    def test_validation_invalid_timeout(self):
        """Test validation for invalid timeout."""
        with pytest.raises(ValueError, match="timeout must be greater than 0"):
            OdaMcpConfig(
                app_name="test_app",
                mcp_id="test_mcp",
                name="Test MCP",
                description="Test Description",
                server_type="sse",
                url="http://localhost:8090/sse",
                timeout=0
            )

    def test_validation_invalid_retry_count(self):
        """Test validation for invalid retry_count."""
        with pytest.raises(ValueError, match="retry_count cannot be less than 0"):
            OdaMcpConfig(
                app_name="test_app",
                mcp_id="test_mcp",
                name="Test MCP",
                description="Test Description",
                server_type="sse",
                url="http://localhost:8090/sse",
                retry_count=-1
            )

    def test_get_global_id(self):
        """Test get_global_id method."""
        config = OdaMcpConfig(
            app_name="test_app",
            mcp_id="test_mcp",
            name="Test MCP",
            description="Test Description",
            server_type="sse",
            url="http://localhost:8090/sse"
        )

        assert config.get_global_id() == "test_app:test_mcp"

    def test_to_dict(self):
        """Test to_dict method."""
        config = OdaMcpConfig(
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

        config_dict = config.to_dict()
        expected_dict = {
            "app_name": "test_app",
            "mcp_id": "test_mcp",
            "name": "Test MCP",
            "description": "Test Description",
            "server_type": "sse",
            "command": None,
            "args": [],
            "url": "http://localhost:8090/sse",
            "env": {},
            "headers": {"Authorization": "Bearer token"},
            "tool_filter": ["read_file", "list_directory"],
            "timeout": 30,
            "retry_count": 3,
        }

        assert config_dict == expected_dict

    def test_from_dict(self):
        """Test from_dict class method."""
        config_dict = {
            "app_name": "test_app",
            "mcp_id": "test_mcp",
            "name": "Test MCP",
            "description": "Test Description",
            "server_type": "sse",
            "url": "http://localhost:8090/sse",
            "headers": {"Authorization": "Bearer token"},
            "tool_filter": ["read_file", "list_directory"],
            "timeout": 30,
            "retry_count": 3
        }

        config = OdaMcpConfig.from_dict(config_dict)

        assert config.app_name == "test_app"
        assert config.mcp_id == "test_mcp"
        assert config.name == "Test MCP"
        assert config.description == "Test Description"
        assert config.server_type == "sse"
        assert config.url == "http://localhost:8090/sse"
        assert config.headers == {"Authorization": "Bearer token"}
        assert config.tool_filter == ["read_file", "list_directory"]
        assert config.timeout == 30
        assert config.retry_count == 3

    def test_repr(self):
        """Test __repr__ method."""
        config = OdaMcpConfig(
            app_name="test_app",
            mcp_id="test_mcp",
            name="Test MCP",
            description="Test Description",
            server_type="sse",
            url="http://localhost:8090/sse"
        )

        expected_repr = "OdaMcpConfig(app_name='test_app', mcp_id='test_mcp', name='Test MCP')"
        assert repr(config) == expected_repr

    def test_eq(self):
        """Test __eq__ method."""
        config1 = OdaMcpConfig(
            app_name="test_app",
            mcp_id="test_mcp",
            name="Test MCP",
            description="Test Description",
            server_type="sse",
            url="http://localhost:8090/sse"
        )

        config2 = OdaMcpConfig(
            app_name="test_app",
            mcp_id="test_mcp",
            name="Test MCP",
            description="Test Description",
            server_type="sse",
            url="http://localhost:8090/sse"
        )

        config3 = OdaMcpConfig(
            app_name="test_app",
            mcp_id="different_mcp",
            name="Different MCP",
            description="Different Description",
            server_type="sse",
            url="http://localhost:8090/sse"
        )

        assert config1 == config2
        assert config1 != config3
        assert config1 != "not_a_config_object"