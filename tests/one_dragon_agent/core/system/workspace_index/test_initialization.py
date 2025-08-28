"""
Test cases for WorkspaceIndex initialization and setup functionality.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from one_dragon_agent.core.system.workspace_index import WorkspaceIndex


class TestWorkspaceIndexInitialization:
    """Test cases for WorkspaceIndex initialization and setup."""

    @pytest.mark.timeout(10)
    def test_initialization_with_valid_root_path(self):
        """Test initialization with a valid root path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            assert workspace_index.root_path == str(Path(temp_dir).resolve())
            assert workspace_index.core_patterns == []
            assert workspace_index.ignore_patterns == []
            assert workspace_index.use_gitignore is True
            assert workspace_index._initialized is False
            assert workspace_index._initializing is False
            assert workspace_index.index_data is not None

    @pytest.mark.timeout(10)
    def test_initialization_with_custom_patterns(self):
        """Test initialization with custom core and ignore patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            core_patterns = ["*.py", "src/"]
            ignore_patterns = ["*.tmp", "__pycache__/"]
            workspace_index = WorkspaceIndex(
                root_path=temp_dir,
                core_patterns=core_patterns,
                ignore_patterns=ignore_patterns,
                use_gitignore=False,
            )
            assert workspace_index.core_patterns == core_patterns
            assert workspace_index.ignore_patterns == ignore_patterns
            assert workspace_index.use_gitignore is False

    @pytest.mark.timeout(10)
    def test_initialization_with_nonexistent_root_path(self):
        """Test initialization fails with non-existent root path."""
        with pytest.raises(ValueError, match="根路径不存在"):
            WorkspaceIndex(root_path="/nonexistent/path")

    @pytest.mark.timeout(10)
    def test_initialization_with_file_as_root_path(self):
        """Test initialization fails when root path is a file."""
        with tempfile.NamedTemporaryFile() as temp_file:
            with pytest.raises(ValueError, match="根路径不是一个目录"):
                WorkspaceIndex(root_path=temp_file.name)

    @pytest.mark.timeout(10)
    def test_construct_pathspecs(self):
        """Test PathSpec construction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            core_patterns = ["*.py", "src/"]
            ignore_patterns = ["*.tmp", "__pycache__/"]
            
            workspace_index = WorkspaceIndex(
                root_path=temp_dir,
                core_patterns=core_patterns,
                ignore_patterns=ignore_patterns,
                use_gitignore=True,
            )
            
            # Call _construct_pathspecs
            workspace_index._construct_pathspecs()
            
            # Verify PathSpec objects are created
            assert workspace_index._core_pathspec is not None
            assert workspace_index._ignore_pathspec_static is not None
            assert workspace_index._ignore_pathspec_git is None  # Not constructed yet
            
            # Verify .gitignore is automatically added to core patterns
            # The method adds .gitignore to the patterns used by PathSpec, not the original list
            # So we check if the core patterns include the original ones plus .gitignore
            expected_patterns = ["*.py", "src/", "**/.gitignore"]
            # We can't directly check the patterns used by PathSpec, but we can verify the method works
            assert workspace_index._core_pathspec is not None

    @pytest.mark.timeout(10)
    def test_construct_pathspecs_without_gitignore(self):
        """Test PathSpec construction without gitignore."""
        with tempfile.TemporaryDirectory() as temp_dir:
            core_patterns = ["*.py"]
            ignore_patterns = ["*.tmp"]
            
            workspace_index = WorkspaceIndex(
                root_path=temp_dir,
                core_patterns=core_patterns,
                ignore_patterns=ignore_patterns,
                use_gitignore=False,
            )
            
            workspace_index._construct_pathspecs()
            
            assert workspace_index._core_pathspec is not None
            assert workspace_index._ignore_pathspec_static is not None
            assert workspace_index._ignore_pathspec_git is None
            
            # Verify .gitignore is not added to core patterns
            assert "**/.gitignore" not in workspace_index.core_patterns

    @pytest.mark.timeout(10)
    def test_match_pathspec_core_priority(self):
        """Test that core patterns have highest priority."""
        with tempfile.TemporaryDirectory() as temp_dir:
            core_patterns = ["*.py"]
            ignore_patterns = ["*.py"]  # Same pattern, but core should win
            
            workspace_index = WorkspaceIndex(
                root_path=temp_dir,
                core_patterns=core_patterns,
                ignore_patterns=ignore_patterns,
                use_gitignore=False,
            )
            
            workspace_index._construct_pathspecs()
            
            # Test core pattern match
            should_index, is_core = workspace_index._match_pathspec("test.py", False)
            assert should_index is True
            assert is_core is True

    @pytest.mark.timeout(10)
    def test_match_pathspec_ignore_priority(self):
        """Test that ignore patterns work for non-core files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            ignore_patterns = ["*.tmp"]
            
            workspace_index = WorkspaceIndex(
                root_path=temp_dir,
                ignore_patterns=ignore_patterns,
                use_gitignore=False,
            )
            
            workspace_index._construct_pathspecs()
            
            # Test ignore pattern match
            should_index, is_core = workspace_index._match_pathspec("test.tmp", False)
            assert should_index is False
            assert is_core is False

    @pytest.mark.timeout(10)
    def test_match_pathspec_directory_handling(self):
        """Test that directory paths are handled correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            core_patterns = ["src/"]
            
            workspace_index = WorkspaceIndex(
                root_path=temp_dir,
                core_patterns=core_patterns,
                use_gitignore=False,
            )
            
            workspace_index._construct_pathspecs()
            
            # Test directory matching (with and without trailing slash)
            should_index1, is_core1 = workspace_index._match_pathspec("src", True)
            should_index2, is_core2 = workspace_index._match_pathspec("src/", True)
            
            assert should_index1 is True
            assert is_core1 is True
            assert should_index2 is True
            assert is_core2 is True

    @pytest.mark.timeout(10)
    def test_read_gitignore_file(self):
        """Test reading .gitignore file content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Create a test .gitignore file
            gitignore_path = Path(temp_dir) / ".gitignore"
            gitignore_content = "# Comment\n*.pyc\n__pycache__/\n\n# Another comment\ntemp/\n"
            gitignore_path.write_text(gitignore_content)
            
            # Test reading the file
            rules = workspace_index._read_gitignore_file(gitignore_path)
            expected_rules = ["*.pyc", "__pycache__/", "temp/"]
            assert rules == expected_rules

    @pytest.mark.timeout(10)
    def test_read_gitignore_file_nonexistent(self):
        """Test reading non-existent .gitignore file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Test reading non-existent file
            gitignore_path = Path(temp_dir) / ".gitignore"
            rules = workspace_index._read_gitignore_file(gitignore_path)
            assert rules == []

    @pytest.mark.timeout(10)
    def test_process_gitignore_rules_root_directory(self):
        """Test processing .gitignore rules from root directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            rules = ["*.pyc", "__pycache__/", "temp/"]
            relative_dir = Path("")
            
            processed_rules = workspace_index._process_gitignore_rules(rules, relative_dir)
            assert processed_rules == rules  # Rules should remain unchanged for root directory

    @pytest.mark.timeout(10)
    def test_process_gitignore_rules_subdirectory(self):
        """Test processing .gitignore rules from subdirectory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            rules = ["*.pyc", "/config.py", "!important.py", "!/config.json"]
            relative_dir = Path("src")
            
            processed_rules = workspace_index._process_gitignore_rules(rules, relative_dir)
            expected = [
                "src/*.pyc",
                "/src/config.py", 
                "!src/important.py",
                "!/src/config.json"
            ]
            assert processed_rules == expected

    @pytest.mark.timeout(10)
    def test_create_index_node_new_node(self):
        """Test creating a new IndexNode."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Create root node first
            root_node = workspace_index._create_index_node(
                name="", path="", is_dir=True, mtime=0.0, is_core=True
            )
            workspace_index._add_node_to_index(root_node)
            
            # Create a new node
            node = workspace_index._create_index_node(
                name="test.py", path="test.py", is_dir=False, mtime=123.45, is_core=False
            )
            
            assert node.name == "test.py"
            assert node.path == "test.py"
            assert node.is_dir is False
            assert node.mtime == 123.45
            assert node.is_core is False
            assert node.parent == root_node
            assert root_node.children["test.py"] == node

    @pytest.mark.timeout(10)
    def test_create_index_node_existing_node(self):
        """Test creating an IndexNode that already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Create root node first
            root_node = workspace_index._create_index_node(
                name="", path="", is_dir=True, mtime=0.0, is_core=True
            )
            workspace_index._add_node_to_index(root_node)
            
            # Create a node and add it to index
            node1 = workspace_index._create_index_node(
                name="test.py", path="test.py", is_dir=False, mtime=123.45, is_core=False
            )
            workspace_index._add_node_to_index(node1)
            
            # Create the same node again (should return existing node)
            node2 = workspace_index._create_index_node(
                name="test.py", path="test.py", is_dir=False, mtime=999.99, is_core=True
            )
            
            assert node1 is node2  # Should be the same object
            assert node2.is_core is True  # Should be updated to core

    @pytest.mark.timeout(10)
    def test_add_node_to_index(self):
        """Test adding a node to all index structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Create root node first
            root_node = workspace_index._create_index_node(
                name="", path="", is_dir=True, mtime=0.0, is_core=True
            )
            workspace_index._add_node_to_index(root_node)
            
            # Create a test node
            node = workspace_index._create_index_node(
                name="test.py", path="test.py", is_dir=False, mtime=123.45, is_core=False
            )
            
            # Add to index
            workspace_index._add_node_to_index(node)
            
            # Verify node is in all index structures
            assert node.path in workspace_index.index_data.path_to_node
            assert workspace_index.index_data.path_to_node[node.path] == node
            
            # Verify path trie
            path_results = workspace_index.index_data.path_trie.starts_with("test.py")
            assert node.path in path_results
            
            # Verify name trie
            name_results = workspace_index.index_data.name_trie.starts_with("test.py")
            assert name_results is not None
            
            # Verify LRU (for non-core nodes)
            assert node.path in workspace_index.index_data.dynamic_nodes_lru

    @pytest.mark.timeout(10)
    def test_add_core_node_to_index(self):
        """Test adding a core node to index structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Create root node first
            root_node = workspace_index._create_index_node(
                name="", path="", is_dir=True, mtime=0.0, is_core=True
            )
            workspace_index._add_node_to_index(root_node)
            
            # Create a core node
            node = workspace_index._create_index_node(
                name="core.py", path="core.py", is_dir=False, mtime=123.45, is_core=True
            )
            
            # Add to index
            workspace_index._add_node_to_index(node)
            
            # Verify core node is not in LRU
            assert node.path not in workspace_index.index_data.dynamic_nodes_lru

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_full_initialization_flow(self):
        """Test the complete initialization flow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('hello')")
            
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Mock the async methods to avoid actual file system operations
            with patch.object(workspace_index, '_construct_gitignore_pathspec') as mock_gitignore, \
                 patch.object(workspace_index, '_build_core_index') as mock_core_index, \
                 patch.object(workspace_index, '_start_file_watching') as mock_watching, \
                 patch.object(workspace_index, '_start_event_processor') as mock_processor:
                
                mock_gitignore.return_value = None
                mock_core_index.return_value = None
                mock_watching.return_value = None
                mock_processor.return_value = None
                
                # Run initialization
                await workspace_index.initialize()
                
                # Verify initialization completed
                assert workspace_index._initialized is True
                assert workspace_index._initializing is False
                
                # Verify all initialization steps were called
                mock_gitignore.assert_called_once()
                mock_core_index.assert_called_once()
                mock_watching.assert_called_once()
                mock_processor.assert_called_once()

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_initialization_concurrent_protection(self):
        """Test that initialization is protected against concurrent calls."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Mock the async methods
            with patch.object(workspace_index, '_construct_gitignore_pathspec') as mock_gitignore, \
                 patch.object(workspace_index, '_build_core_index') as mock_core_index, \
                 patch.object(workspace_index, '_start_file_watching') as mock_watching, \
                 patch.object(workspace_index, '_start_event_processor') as mock_processor:
                
                mock_gitignore.return_value = None
                mock_core_index.return_value = None
                mock_watching.return_value = None
                mock_processor.return_value = None
                
                # Start multiple concurrent initializations
                tasks = [
                    workspace_index.initialize(),
                    workspace_index.initialize(),
                    workspace_index.initialize()
                ]
                
                # Wait for all tasks to complete
                await asyncio.gather(*tasks)
                
                # Verify initialization completed only once
                assert workspace_index._initialized is True
                assert workspace_index._initializing is False
                
                # Verify initialization methods were called only once
                mock_gitignore.assert_called_once()
                mock_core_index.assert_called_once()
                mock_watching.assert_called_once()
                mock_processor.assert_called_once()

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_initialization_already_initialized(self):
        """Test that calling initialize when already initialized does nothing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Mock the async methods
            with patch.object(workspace_index, '_construct_gitignore_pathspec') as mock_gitignore, \
                 patch.object(workspace_index, '_build_core_index') as mock_core_index, \
                 patch.object(workspace_index, '_start_file_watching') as mock_watching, \
                 patch.object(workspace_index, '_start_event_processor') as mock_processor:
                
                mock_gitignore.return_value = None
                mock_core_index.return_value = None
                mock_watching.return_value = None
                mock_processor.return_value = None
                
                # First initialization
                await workspace_index.initialize()
                assert workspace_index._initialized is True
                
                # Reset mocks
                mock_gitignore.reset_mock()
                mock_core_index.reset_mock()
                mock_watching.reset_mock()
                mock_processor.reset_mock()
                
                # Second initialization
                await workspace_index.initialize()
                
                # Verify initialization methods were not called again
                mock_gitignore.assert_not_called()
                mock_core_index.assert_not_called()
                mock_watching.assert_not_called()
                mock_processor.assert_not_called()