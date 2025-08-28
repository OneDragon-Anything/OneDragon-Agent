"""
Test cases for WorkspaceIndex gitignore processing functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from one_dragon_agent.core.system.workspace_index import WorkspaceIndex


class TestWorkspaceIndexGitignore:
    """Test cases for WorkspaceIndex gitignore processing functionality."""

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_read_gitignore_file_basic(self):
        """Test reading basic .gitignore file content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Create a test .gitignore file
            gitignore_path = Path(temp_dir) / ".gitignore"
            gitignore_content = """# Comment line
*.pyc
__pycache__/

# Another comment
temp/
*.log
"""
            gitignore_path.write_text(gitignore_content)
            
            # Test reading the file
            rules = workspace_index._read_gitignore_file(gitignore_path)
            
            expected_rules = ["*.pyc", "__pycache__/", "temp/", "*.log"]
            assert rules == expected_rules

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_read_gitignore_file_empty(self):
        """Test reading empty .gitignore file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Create an empty .gitignore file
            gitignore_path = Path(temp_dir) / ".gitignore"
            gitignore_path.write_text("")
            
            # Test reading the file
            rules = workspace_index._read_gitignore_file(gitignore_path)
            assert rules == []

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_read_gitignore_file_nonexistent(self):
        """Test reading non-existent .gitignore file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Test reading non-existent file
            gitignore_path = Path(temp_dir) / ".gitignore"
            rules = workspace_index._read_gitignore_file(gitignore_path)
            assert rules == []

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_read_gitignore_file_with_encoding_issues(self):
        """Test reading .gitignore file with encoding issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Create a .gitignore file with encoding issues
            gitignore_path = Path(temp_dir) / ".gitignore"
            with open(gitignore_path, 'wb') as f:
                f.write(b"*.pyc\n\xff\xfe invalid bytes\n*.log\n")
            
            # Test reading the file (should handle encoding errors gracefully)
            rules = workspace_index._read_gitignore_file(gitignore_path)
            
            # Should return valid rules and skip invalid ones
            assert "*.pyc" in rules
            assert "*.log" in rules

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_process_gitignore_rules_root_directory(self):
        """Test processing .gitignore rules from root directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            rules = ["*.pyc", "__pycache__/", "temp/", "!important.py"]
            relative_dir = Path("")
            
            processed_rules = workspace_index._process_gitignore_rules(rules, relative_dir)
            
            # Rules should remain unchanged for root directory
            assert processed_rules == rules

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_process_gitignore_rules_subdirectory(self):
        """Test processing .gitignore rules from subdirectory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            rules = [
                "*.pyc",           # Relative pattern
                "/config.py",      # Absolute pattern
                "!important.py",   # Negated relative pattern
                "!/config.json",   # Negated absolute pattern
                "temp/"            # Directory pattern
            ]
            relative_dir = Path("src")
            
            processed_rules = workspace_index._process_gitignore_rules(rules, relative_dir)
            
            expected = [
                "src/*.pyc",
                "/src/config.py",
                "!src/important.py",
                "!/src/config.json",
                "src/temp/"
            ]
            assert processed_rules == expected

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_process_gitignore_rules_nested_subdirectory(self):
        """Test processing .gitignore rules from nested subdirectory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            rules = ["*.pyc", "/config.py", "!important.py"]
            relative_dir = Path("src/core")
            
            processed_rules = workspace_index._process_gitignore_rules(rules, relative_dir)
            
            expected = [
                "src/core/*.pyc",
                "/src/core/config.py",
                "!src/core/important.py"
            ]
            assert processed_rules == expected

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_scan_and_process_gitignore_files_single(self):
        """Test scanning and processing a single .gitignore file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Create a .gitignore file
            gitignore_path = Path(temp_dir) / ".gitignore"
            gitignore_content = "*.pyc\n__pycache__/\ntemp/"
            gitignore_path.write_text(gitignore_content)
            
            # Test scanning and processing
            all_lines = workspace_index._scan_and_process_gitignore_files()
            
            expected_lines = ["*.pyc", "__pycache__/", "temp/"]
            assert all_lines == expected_lines

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_scan_and_process_gitignore_files_multiple(self):
        """Test scanning and processing multiple .gitignore files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Create directory structure
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            
            test_dir = Path(temp_dir) / "test"
            test_dir.mkdir()
            
            # Create .gitignore files
            root_gitignore = Path(temp_dir) / ".gitignore"
            root_gitignore.write_text("*.pyc\n__pycache__/")
            
            src_gitignore = src_dir / ".gitignore"
            src_gitignore.write_text("*.tmp\n!important.tmp")
            
            test_gitignore = test_dir / ".gitignore"
            test_gitignore.write_text("*.log\n/debug.log")
            
            # Test scanning and processing
            all_lines = workspace_index._scan_and_process_gitignore_files()
            
            # Verify all rules are included and properly prefixed
            assert "*.pyc" in all_lines
            assert "__pycache__/" in all_lines
            assert "src/*.tmp" in all_lines
            assert "!src/important.tmp" in all_lines
            assert "test/*.log" in all_lines
            assert "/test/debug.log" in all_lines  # Absolute path gets leading slash

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_scan_and_process_gitignore_files_empty(self):
        """Test scanning when no .gitignore files exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Test scanning and processing
            all_lines = workspace_index._scan_and_process_gitignore_files()
            assert all_lines == []

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_construct_gitignore_pathspec_basic(self):
        """Test basic gitignore PathSpec construction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Create a .gitignore file
            gitignore_path = Path(temp_dir) / ".gitignore"
            gitignore_content = "*.pyc\n__pycache__/\ntemp/"
            gitignore_path.write_text(gitignore_content)
            
            # Test PathSpec construction
            await workspace_index._construct_gitignore_pathspec()
            
            # Verify PathSpec was created
            assert workspace_index._ignore_pathspec_git is not None
            
            # Test matching
            assert workspace_index._ignore_pathspec_git.match_file("test.pyc") is True
            assert workspace_index._ignore_pathspec_git.match_file("test.py") is False
            assert workspace_index._ignore_pathspec_git.match_file("__pycache__/test.py") is True

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_construct_gitignore_pathspec_with_subdirectories(self):
        """Test gitignore PathSpec construction with subdirectory rules."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Create directory structure
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            
            # Create .gitignore files
            root_gitignore = Path(temp_dir) / ".gitignore"
            root_gitignore.write_text("*.pyc")
            
            src_gitignore = src_dir / ".gitignore"
            src_gitignore.write_text("*.tmp")
            
            # Test PathSpec construction
            await workspace_index._construct_gitignore_pathspec()
            
            # Verify PathSpec was created
            assert workspace_index._ignore_pathspec_git is not None
            
            # Test matching
            assert workspace_index._ignore_pathspec_git.match_file("test.pyc") is True
            assert workspace_index._ignore_pathspec_git.match_file("src/test.tmp") is True
            assert workspace_index._ignore_pathspec_git.match_file("src/test.py") is False

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_handle_gitignore_changed(self):
        """Test handling .gitignore file changes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create a .gitignore file
            gitignore_path = Path(temp_dir) / ".gitignore"
            gitignore_content = "*.pyc\n__pycache__/"
            gitignore_path.write_text(gitignore_content)
            
            # Mock the rescan method
            with patch.object(workspace_index, '_rescan_index_for_ignore_rules') as mock_rescan:
                mock_rescan.return_value = None
                
                # Test handling gitignore change
                await workspace_index._handle_gitignore_changed()
                
                # Verify rescan was called
                mock_rescan.assert_called_once()

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_rescan_index_for_ignore_rules(self):
        """Test rescanning index when ignore rules change."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create test files
            test_pyc = Path(temp_dir) / "test.pyc"
            test_py = Path(temp_dir) / "test.py"
            test_pyc.write_text("compiled")
            test_py.write_text("source")
            
            # Add files to index
            pyc_relative = test_pyc.relative_to(temp_dir).as_posix()
            py_relative = test_py.relative_to(temp_dir).as_posix()
            
            pyc_node = workspace_index._create_index_node(
                name="test.pyc",
                path=pyc_relative,
                is_dir=False,
                mtime=test_pyc.stat().st_mtime,
                is_core=False
            )
            workspace_index._add_node_to_index(pyc_node)
            
            py_node = workspace_index._create_index_node(
                name="test.py",
                path=py_relative,
                is_dir=False,
                mtime=test_py.stat().st_mtime,
                is_core=False
            )
            workspace_index._add_node_to_index(py_node)
            
            # Verify both files are in index
            assert pyc_relative in workspace_index.index_data.path_to_node
            assert py_relative in workspace_index.index_data.path_to_node
            
            # Set up ignore rules to ignore .pyc files but not .py files
            workspace_index._ignore_pathspec_static = MagicMock()
            def mock_match_file_1(path):
                return path.endswith('.pyc')
            workspace_index._ignore_pathspec_static.match_file = mock_match_file_1
            
            # Test rescan
            workspace_index._rescan_index_for_ignore_rules()
            
            # Verify .pyc file was removed, .py file remains
            assert pyc_relative not in workspace_index.index_data.path_to_node
            assert py_relative in workspace_index.index_data.path_to_node

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_rescan_index_preserves_core_files(self):
        """Test that rescan preserves core files even if they match ignore rules."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create test files
            test_pyc = Path(temp_dir) / "test.pyc"
            test_pyc.write_text("compiled")
            
            # Add file to index as core
            pyc_relative = test_pyc.relative_to(temp_dir).as_posix()
            pyc_node = workspace_index._create_index_node(
                name="test.pyc",
                path=pyc_relative,
                is_dir=False,
                mtime=test_pyc.stat().st_mtime,
                is_core=True  # Mark as core
            )
            workspace_index._add_node_to_index(pyc_node)
            
            # Verify file is in index
            assert pyc_relative in workspace_index.index_data.path_to_node
            
            # Set up ignore rules to ignore .pyc files
            workspace_index._ignore_pathspec_static = MagicMock()
            def mock_match_file_2(path):
                return path.endswith('.pyc')
            workspace_index._ignore_pathspec_static.match_file = mock_match_file_2
            
            # Test rescan
            workspace_index._rescan_index_for_ignore_rules()
            
            # Verify core file is preserved
            assert pyc_relative in workspace_index.index_data.path_to_node

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_rescan_index_handles_missing_pathspec(self):
        """Test that rescan handles missing PathSpec objects gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create test file
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('test')")
            
            # Add file to index
            file_relative = test_file.relative_to(temp_dir).as_posix()
            file_node = workspace_index._create_index_node(
                name="test.py",
                path=file_relative,
                is_dir=False,
                mtime=test_file.stat().st_mtime,
                is_core=False
            )
            workspace_index._add_node_to_index(file_node)
            
            # Verify file is in index
            assert file_relative in workspace_index.index_data.path_to_node
            
            # Set PathSpec objects to None
            workspace_index._ignore_pathspec_static = None
            workspace_index._ignore_pathspec_git = None
            
            # Test rescan (should not raise exception)
            workspace_index._rescan_index_for_ignore_rules()
            
            # Verify file is still in index (no matching occurred)
            assert file_relative in workspace_index.index_data.path_to_node

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_gitignore_rules_with_negation(self):
        """Test gitignore rules with negation patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Create a .gitignore file with negation
            gitignore_path = Path(temp_dir) / ".gitignore"
            gitignore_content = """*.pyc
!important.pyc
__pycache__/
!__pycache__/important/
"""
            gitignore_path.write_text(gitignore_content)
            
            # Test PathSpec construction
            await workspace_index._construct_gitignore_pathspec()
            
            # Verify PathSpec was created
            assert workspace_index._ignore_pathspec_git is not None
            
            # Test matching
            assert workspace_index._ignore_pathspec_git.match_file("test.pyc") is True
            assert workspace_index._ignore_pathspec_git.match_file("important.pyc") is False
            assert workspace_index._ignore_pathspec_git.match_file("__pycache__/test.py") is True
            assert workspace_index._ignore_pathspec_git.match_file("__pycache__/important/test.py") is False

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_gitignore_rules_with_directory_patterns(self):
        """Test gitignore rules with directory patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Create a .gitignore file with directory patterns
            gitignore_path = Path(temp_dir) / ".gitignore"
            gitignore_content = """temp/
logs/
/build/
"""
            gitignore_path.write_text(gitignore_content)
            
            # Test PathSpec construction
            await workspace_index._construct_gitignore_pathspec()
            
            # Verify PathSpec was created
            assert workspace_index._ignore_pathspec_git is not None
            
            # Test matching
            assert workspace_index._ignore_pathspec_git.match_file("temp/test.py") is True
            assert workspace_index._ignore_pathspec_git.match_file("logs/app.log") is True
            assert workspace_index._ignore_pathspec_git.match_file("build/output.o") is True
            assert workspace_index._ignore_pathspec_git.match_file("src/main.py") is False

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_gitignore_rules_with_complex_patterns(self):
        """Test gitignore rules with complex patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Create a .gitignore file with complex patterns
            gitignore_path = Path(temp_dir) / ".gitignore"
            gitignore_content = """*.py[co]
__pycache__/
*.so
.DS_Store
.env
.venv
"""
            gitignore_path.write_text(gitignore_content)
            
            # Test PathSpec construction
            await workspace_index._construct_gitignore_pathspec()
            
            # Verify PathSpec was created
            assert workspace_index._ignore_pathspec_git is not None
            
            # Test matching
            assert workspace_index._ignore_pathspec_git.match_file("test.pyc") is True
            assert workspace_index._ignore_pathspec_git.match_file("test.pyo") is True
            assert workspace_index._ignore_pathspec_git.match_file("test.py") is False
            assert workspace_index._ignore_pathspec_git.match_file("__pycache__/test.py") is True
            assert workspace_index._ignore_pathspec_git.match_file("libtest.so") is True
            assert workspace_index._ignore_pathspec_git.match_file(".DS_Store") is True
            assert workspace_index._ignore_pathspec_git.match_file(".env") is True
            assert workspace_index._ignore_pathspec_git.match_file(".venv/bin/python") is True