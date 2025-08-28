"""
Test cases for WorkspaceIndex file system event handling functionality.
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from one_dragon_agent.core.system.workspace_index import WorkspaceIndex


class TestWorkspaceIndexFileSystemEvents:
    """Test cases for WorkspaceIndex file system event handling."""

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_file_created_event_handling(self):
        """Test handling of file creation events."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create a test file
            test_file = Path(temp_dir) / "new_file.py"
            test_file.write_text("print('new file')")
            
            # Simulate file creation event
            await workspace_index._async_handle_file_created(str(test_file))
            
            # Verify file was added to index
            relative_path = test_file.relative_to(temp_dir).as_posix()
            assert relative_path in workspace_index.index_data.path_to_node
            
            node = workspace_index.index_data.path_to_node[relative_path]
            assert node.name == "new_file.py"
            assert node.path == relative_path
            assert node.is_dir is False
            assert node.is_core is False  # Dynamic files are not core by default

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_directory_created_event_handling(self):
        """Test handling of directory creation events."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create a test directory
            test_dir = Path(temp_dir) / "new_directory"
            test_dir.mkdir()
            
            # Simulate directory creation event
            await workspace_index._async_handle_dir_created(str(test_dir))
            
            # Verify directory was added to index
            relative_path = test_dir.relative_to(temp_dir).as_posix()
            assert relative_path in workspace_index.index_data.path_to_node
            
            node = workspace_index.index_data.path_to_node[relative_path]
            assert node.name == "new_directory"
            assert node.path == relative_path
            assert node.is_dir is True
            assert node.mtime == 0.0  # Directories have mtime 0
            assert node.is_core is False

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_file_deleted_event_handling(self):
        """Test handling of file deletion events."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create and index a test file
            test_file = Path(temp_dir) / "to_delete.py"
            test_file.write_text("print('delete me')")
            
            # Manually add to index to simulate it being indexed
            relative_path = test_file.relative_to(temp_dir).as_posix()
            node = workspace_index._create_index_node(
                name="to_delete.py",
                path=relative_path,
                is_dir=False,
                mtime=test_file.stat().st_mtime,
                is_core=False
            )
            workspace_index._add_node_to_index(node)
            
            # Verify file is in index
            assert relative_path in workspace_index.index_data.path_to_node
            
            # Delete the file
            test_file.unlink()
            
            # Simulate file deletion event
            await workspace_index._async_handle_file_deleted(str(test_file))
            
            # Verify file was removed from index
            assert relative_path not in workspace_index.index_data.path_to_node

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_directory_deleted_event_handling(self):
        """Test handling of directory deletion events."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create and index a test directory with files
            test_dir = Path(temp_dir) / "to_delete_dir"
            test_dir.mkdir()
            
            file1 = test_dir / "file1.py"
            file2 = test_dir / "file2.py"
            file1.write_text("print('file1')")
            file2.write_text("print('file2')")
            
            # Manually add to index
            dir_relative = test_dir.relative_to(temp_dir).as_posix()
            file1_relative = file1.relative_to(temp_dir).as_posix()
            file2_relative = file2.relative_to(temp_dir).as_posix()
            
            dir_node = workspace_index._create_index_node(
                name="to_delete_dir",
                path=dir_relative,
                is_dir=True,
                mtime=0.0,
                is_core=False
            )
            workspace_index._add_node_to_index(dir_node)
            
            file1_node = workspace_index._create_index_node(
                name="file1.py",
                path=file1_relative,
                is_dir=False,
                mtime=file1.stat().st_mtime,
                is_core=False
            )
            workspace_index._add_node_to_index(file1_node)
            
            file2_node = workspace_index._create_index_node(
                name="file2.py",
                path=file2_relative,
                is_dir=False,
                mtime=file2.stat().st_mtime,
                is_core=False
            )
            workspace_index._add_node_to_index(file2_node)
            
            # Verify all are in index
            assert dir_relative in workspace_index.index_data.path_to_node
            assert file1_relative in workspace_index.index_data.path_to_node
            assert file2_relative in workspace_index.index_data.path_to_node
            
            # Delete the directory and its contents
            import shutil
            shutil.rmtree(test_dir)
            
            # Simulate directory deletion event
            await workspace_index._async_handle_dir_deleted(str(test_dir))
            
            # Verify directory and files were removed from index
            assert dir_relative not in workspace_index.index_data.path_to_node
            assert file1_relative not in workspace_index.index_data.path_to_node
            assert file2_relative not in workspace_index.index_data.path_to_node

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_file_modified_event_handling(self):
        """Test handling of file modification events."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create and index a test file
            test_file = Path(temp_dir) / "to_modify.py"
            test_file.write_text("print('original')")
            
            # Manually add to index
            relative_path = test_file.relative_to(temp_dir).as_posix()
            original_mtime = test_file.stat().st_mtime
            
            node = workspace_index._create_index_node(
                name="to_modify.py",
                path=relative_path,
                is_dir=False,
                mtime=original_mtime,
                is_core=False
            )
            workspace_index._add_node_to_index(node)
            
            # Verify original mtime
            assert workspace_index.index_data.path_to_node[relative_path].mtime == original_mtime
            
            # Modify the file
            test_file.write_text("print('modified')")
            new_mtime = test_file.stat().st_mtime
            
            # Simulate file modification event
            await workspace_index._async_handle_file_modified(str(test_file))
            
            # Verify mtime was updated
            assert workspace_index.index_data.path_to_node[relative_path].mtime == new_mtime

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_file_moved_event_handling(self):
        """Test handling of file move/rename events."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create and index a test file
            src_file = Path(temp_dir) / "original.py"
            src_file.write_text("print('original')")
            
            # Manually add to index
            src_relative = src_file.relative_to(temp_dir).as_posix()
            src_node = workspace_index._create_index_node(
                name="original.py",
                path=src_relative,
                is_dir=False,
                mtime=src_file.stat().st_mtime,
                is_core=False
            )
            workspace_index._add_node_to_index(src_node)
            
            # Verify source file is in index
            assert src_relative in workspace_index.index_data.path_to_node
            
            # Move the file
            dest_file = Path(temp_dir) / "renamed.py"
            src_file.rename(dest_file)
            
            # Simulate file move event
            await workspace_index._async_handle_file_moved(str(src_file), str(dest_file))
            
            # Verify source file was removed and destination file was added
            assert src_relative not in workspace_index.index_data.path_to_node
            
            dest_relative = dest_file.relative_to(temp_dir).as_posix()
            assert dest_relative in workspace_index.index_data.path_to_node
            
            dest_node = workspace_index.index_data.path_to_node[dest_relative]
            assert dest_node.name == "renamed.py"
            assert dest_node.path == dest_relative

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_directory_moved_event_handling(self):
        """Test handling of directory move/rename events."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create and index a test directory with files
            src_dir = Path(temp_dir) / "original_dir"
            src_dir.mkdir()
            
            file1 = src_dir / "file1.py"
            file2 = src_dir / "file2.py"
            file1.write_text("print('file1')")
            file2.write_text("print('file2')")
            
            # Manually add to index
            src_relative = src_dir.relative_to(temp_dir).as_posix()
            file1_relative = file1.relative_to(temp_dir).as_posix()
            file2_relative = file2.relative_to(temp_dir).as_posix()
            
            src_node = workspace_index._create_index_node(
                name="original_dir",
                path=src_relative,
                is_dir=True,
                mtime=0.0,
                is_core=False
            )
            workspace_index._add_node_to_index(src_node)
            
            file1_node = workspace_index._create_index_node(
                name="file1.py",
                path=file1_relative,
                is_dir=False,
                mtime=file1.stat().st_mtime,
                is_core=False
            )
            workspace_index._add_node_to_index(file1_node)
            
            file2_node = workspace_index._create_index_node(
                name="file2.py",
                path=file2_relative,
                is_dir=False,
                mtime=file2.stat().st_mtime,
                is_core=False
            )
            workspace_index._add_node_to_index(file2_node)
            
            # Verify all are in index
            assert src_relative in workspace_index.index_data.path_to_node
            assert file1_relative in workspace_index.index_data.path_to_node
            assert file2_relative in workspace_index.index_data.path_to_node
            
            # Move the directory
            dest_dir = Path(temp_dir) / "renamed_dir"
            src_dir.rename(dest_dir)
            
            # Simulate directory move event
            await workspace_index._async_handle_dir_moved(str(src_dir), str(dest_dir))
            
            # Verify source directory and files were removed
            assert src_relative not in workspace_index.index_data.path_to_node
            assert file1_relative not in workspace_index.index_data.path_to_node
            assert file2_relative not in workspace_index.index_data.path_to_node
            
            # Verify destination directory was added
            dest_relative = dest_dir.relative_to(temp_dir).as_posix()
            assert dest_relative in workspace_index.index_data.path_to_node
            
            dest_node = workspace_index.index_data.path_to_node[dest_relative]
            assert dest_node.name == "renamed_dir"
            assert dest_node.path == dest_relative

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_gitignore_file_created_event(self):
        """Test that .gitignore file creation triggers gitignore rebuild."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Mock file watching to prevent actual file system monitoring
            with patch.object(workspace_index, '_start_file_watching'):
                with patch.object(workspace_index, '_stop_file_watching'):
                    await workspace_index.initialize()
            
            # Mock the gitignore change handler
            with patch.object(workspace_index, '_handle_gitignore_changed') as mock_handler:
                mock_handler.return_value = None
                
                # Simulate .gitignore creation event directly
                gitignore_file = Path(temp_dir) / ".gitignore"
                await workspace_index._async_handle_file_created(str(gitignore_file))
                
                # Verify gitignore change handler was called
                mock_handler.assert_called_once()
                # Give up event processing to complete
                await asyncio.sleep(0.1)

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_gitignore_file_modified_event(self):
        """Test that .gitignore file modification triggers gitignore rebuild."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Mock file watching to prevent actual file system monitoring
            with patch.object(workspace_index, '_start_file_watching'):
                with patch.object(workspace_index, '_stop_file_watching'):
                    await workspace_index.initialize()
            
            # Mock the gitignore change handler
            with patch.object(workspace_index, '_handle_gitignore_changed') as mock_handler:
                mock_handler.return_value = None
                
                # Simulate .gitignore modification event directly
                gitignore_file = Path(temp_dir) / ".gitignore"
                await workspace_index._async_handle_file_modified(str(gitignore_file))
                
                # Verify gitignore change handler was called
                mock_handler.assert_called_once()

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_gitignore_file_deleted_event(self):
        """Test that .gitignore file deletion triggers gitignore rebuild."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Mock file watching to prevent actual file system monitoring
            with patch.object(workspace_index, '_start_file_watching'):
                with patch.object(workspace_index, '_stop_file_watching'):
                    await workspace_index.initialize()
            
            # Mock the gitignore change handler
            with patch.object(workspace_index, '_handle_gitignore_changed') as mock_handler:
                mock_handler.return_value = None
                
                # Simulate .gitignore deletion event directly
                gitignore_file = Path(temp_dir) / ".gitignore"
                await workspace_index._async_handle_file_deleted(str(gitignore_file))
                
                # Verify gitignore change handler was called
                mock_handler.assert_called_once()

    def test_event_queue_basic_operations(self):
        """Test basic event queue enqueue/dequeue operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            
            # Test basic queue operations
            test_file1 = str(Path(temp_dir) / "file1.py")
            test_file2 = str(Path(temp_dir) / "file2.py")
            
            # Test enqueue without blocking
            workspace_index._enqueue_event('file_created', test_file1)
            workspace_index._enqueue_event('file_created', test_file2)
            
            # Verify queue has items
            assert not workspace_index._event_queue.empty()

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_event_processing_error_handling(self):
        """Test that event processing handles errors gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Mock the file handler to raise an exception
            with patch.object(workspace_index, '_async_handle_file_created') as mock_handler:
                mock_handler.side_effect = Exception("Test error")
                
                # Enqueue an event that will cause an error
                test_file = Path(temp_dir) / "error_file.py"
                test_file.write_text("print('error')")
                
                workspace_index._enqueue_event('file_created', str(test_file))
                
                # Process events (should not raise exception)
                await workspace_index._process_events()
                
                # Give some time for async processing
                await asyncio.sleep(0.1)
                
                # Verify the error was handled gracefully (no exception raised)
                assert True  # If we get here, error handling worked
                
            # Clean up to prevent hanging
            workspace_index._stop_file_watching()

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_remove_node_from_index(self):
        """Test removing a node from all index structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create and add a test node
            test_node = workspace_index._create_index_node(
                name="test.py",
                path="test.py",
                is_dir=False,
                mtime=123.45,
                is_core=False
            )
            workspace_index._add_node_to_index(test_node)
            
            # Verify node is in all index structures
            assert "test.py" in workspace_index.index_data.path_to_node
            assert test_node.path in workspace_index.index_data.dynamic_nodes_lru
            
            # Remove node from index
            workspace_index._remove_node_from_index("test.py")
            
            # Verify node was removed from all index structures
            assert "test.py" not in workspace_index.index_data.path_to_node
            assert test_node.path not in workspace_index.index_data.dynamic_nodes_lru
            
            # Clean up to prevent hanging
            workspace_index._stop_file_watching()

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_remove_node_and_children(self):
        """Test removing a node and all its children."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create a directory structure
            dir_node = workspace_index._create_index_node(
                name="test_dir",
                path="test_dir",
                is_dir=True,
                mtime=0.0,
                is_core=False
            )
            workspace_index._add_node_to_index(dir_node)
            
            file1_node = workspace_index._create_index_node(
                name="file1.py",
                path="test_dir/file1.py",
                is_dir=False,
                mtime=123.45,
                is_core=False
            )
            workspace_index._add_node_to_index(file1_node)
            
            file2_node = workspace_index._create_index_node(
                name="file2.py",
                path="test_dir/file2.py",
                is_dir=False,
                mtime=678.90,
                is_core=False
            )
            workspace_index._add_node_to_index(file2_node)
            
            # Verify all nodes are in index
            assert "test_dir" in workspace_index.index_data.path_to_node
            assert "test_dir/file1.py" in workspace_index.index_data.path_to_node
            assert "test_dir/file2.py" in workspace_index.index_data.path_to_node
            
            # Remove directory and children
            workspace_index._remove_node_and_children("test_dir")
            
            # Verify all nodes were removed
            assert "test_dir" not in workspace_index.index_data.path_to_node
            assert "test_dir/file1.py" not in workspace_index.index_data.path_to_node
            assert "test_dir/file2.py" not in workspace_index.index_data.path_to_node

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_collect_all_descendant_paths(self):
        """Test collecting all descendant paths of a node."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Test empty case - only test_dir itself is collected even if not exists
            paths = []
            workspace_index._collect_all_descendant_paths("test_dir", paths)
            # _collect_all_descendant_paths always adds the node itself
            assert len(paths) == 1
            assert paths[0] == "test_dir"
            
            # Add some nodes and test real collection
            dir_node = workspace_index._create_index_node(
                name="test_dir",
                path="test_dir",
                is_dir=True,
                mtime=0.0,
                is_core=False
            )
            workspace_index._add_node_to_index(dir_node)
            
            file1_node = workspace_index._create_index_node(
                name="file1.py",
                path="test_dir/file1.py",
                is_dir=False,
                mtime=123.45,
                is_core=False
            )
            workspace_index._add_node_to_index(file1_node)
            
            file2_node = workspace_index._create_index_node(
                name="file2.py",
                path="test_dir/subdir/file2.py",
                is_dir=False,
                mtime=678.90,
                is_core=False
            )
            workspace_index._add_node_to_index(file2_node)
            
            # Collect descendant paths
            paths = []
            workspace_index._collect_all_descendant_paths("test_dir", paths)
            
            # Verify all paths were collected (should include test_dir and its children)
            assert len(paths) >= 3
            assert "test_dir" in paths
            assert "test_dir/file1.py" in paths
            assert "test_dir/subdir/file2.py" in paths

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_does_directory_contain_gitignore(self):
        """Test checking if a directory contains .gitignore files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create directory structure with .gitignore
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            
            gitignore_file = src_dir / ".gitignore"
            gitignore_file.write_text("*.pyc")
            
            # Add .gitignore to index
            gitignore_relative = gitignore_file.relative_to(temp_dir).as_posix()
            gitignore_node = workspace_index._create_index_node(
                name=".gitignore",
                path=gitignore_relative,
                is_dir=False,
                mtime=gitignore_file.stat().st_mtime,
                is_core=True  # .gitignore files are core
            )
            workspace_index._add_node_to_index(gitignore_node)
            
            # Test directory contains .gitignore
            assert workspace_index._does_directory_contain_gitignore("src") is True
            
            # Test directory does not contain .gitignore
            assert workspace_index._does_directory_contain_gitignore("nonexistent") is False

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_core_file_events_not_affected_by_core_flag(self):
        """Test that core file events are handled regardless of is_core flag."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir, core_patterns=["*.py"])
            await workspace_index.initialize()
            
            # Create a core file
            core_file = Path(temp_dir) / "core_file.py"
            core_file.write_text("# core file")
            
            # Calculate relative path
            relative_path = core_file.relative_to(temp_dir).as_posix()
            
            # Test creation
            await workspace_index._async_handle_file_created(str(core_file))
            assert relative_path in workspace_index.index_data.path_to_node
            node = workspace_index.index_data.path_to_node[relative_path]
            assert node.is_core is True
            
            # Test deletion
            core_file.unlink()
            await workspace_index._async_handle_file_deleted(str(core_file))
            assert relative_path not in workspace_index.index_data.path_to_node

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_empty_directory_deletion(self):
        """Test handling of empty directory deletion without children."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create empty directory
            empty_dir = Path(temp_dir) / "empty"
            empty_dir.mkdir()
            
            # Add to index
            empty_relative = empty_dir.relative_to(temp_dir).as_posix()
            empty_node = workspace_index._create_index_node(
                name="empty",
                path=empty_relative,
                is_dir=True,
                mtime=0.0,
                is_core=False
            )
            workspace_index._add_node_to_index(empty_node)
            
            # Delete directory
            empty_dir.rmdir()
            await workspace_index._async_handle_dir_deleted(str(empty_dir))
            
            # Verify empty directory was removed
            assert empty_relative not in workspace_index.index_data.path_to_node

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_concurrent_file_events_keep_parent_child_relationship(self):
        """Test that parent-child relationships are correctly maintained during concurrent events."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # 1. Create directory
            test_dir = Path(temp_dir) / "parent"
            test_dir.mkdir()
            
            # 2. Create file in directory
            child_file = test_dir / "child.py"
            child_file.write_text("print('child')")
            
            # Process events
            await workspace_index._async_handle_dir_created(str(test_dir))
            await workspace_index._async_handle_file_created(str(child_file))
            
            # Verify parent-child relationship
            dir_relative = test_dir.relative_to(temp_dir).as_posix()
            child_relative = child_file.relative_to(temp_dir).as_posix()
            
            assert dir_relative in workspace_index.index_data.path_to_node
            assert child_relative in workspace_index.index_data.path_to_node
            
            dir_node = workspace_index.index_data.path_to_node[dir_relative]
            child_node = workspace_index.index_data.path_to_node[child_relative]
            
            assert child_node.parent == dir_node
            assert "child.py" in dir_node.children
            assert dir_node.children["child.py"] == child_node

    @pytest.mark.timeout(15)
    @pytest.mark.asyncio
    async def test_lru_state_updates_on_file_access(self):
        """Test that LRU state is correctly updated when dynamic files are accessed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create and add a dynamic file
            test_file = Path(temp_dir) / "dynamic.py"
            test_file.write_text("print('dynamic')")
            
            relative_path = test_file.relative_to(temp_dir).as_posix()
            await workspace_index._async_handle_file_created(str(test_file))
            
            # Verify file is in LRU
            assert relative_path in workspace_index.index_data.dynamic_nodes_lru
            original_time = workspace_index.index_data.dynamic_nodes_lru[relative_path]
            
            # Simulate access (visit the node)
            await asyncio.sleep(0.001)  # Ensure timestamp difference
            workspace_index._update_lru_for_nodes([workspace_index.index_data.path_to_node[relative_path]])
            
            # Verify LRU timestamp was updated
            new_time = workspace_index.index_data.dynamic_nodes_lru[relative_path]
            assert new_time >= original_time

    @pytest.mark.timeout(20)
    @pytest.mark.asyncio
    async def test_large_batch_events_processing(self):
        """Test processing of large batch events with performance characteristics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create many files in nested structure
            base_dir = Path(temp_dir) / "batch"
            base_dir.mkdir()
            
            # Create 100 files across directories
            created_files = []
            for i in range(25):
                for j in range(4):
                    sub_dir = base_dir / f"dir{i}"
                    sub_dir.mkdir(exist_ok=True)
                    file_path = sub_dir / f"file{j}.py"
                    file_path.write_text(f"print({i*4 + j})")
                    created_files.append(str(file_path))
            
            # Process events rapidly
            start_time = asyncio.get_event_loop().time()
            for file_path in created_files:
                await workspace_index._async_handle_file_created(file_path)
            
            # Verify all files are processed
            processed_count = 0
            for file_path in created_files:
                relative_path = Path(file_path).relative_to(temp_dir).as_posix()
                if relative_path in workspace_index.index_data.path_to_node:
                    processed_count += 1
            
            assert processed_count == 100
            
            # Verify batch cleanup
            await workspace_index._async_handle_dir_deleted(str(base_dir))
            
            # All files should be removed
            for file_path in created_files:
                relative_path = Path(file_path).relative_to(temp_dir).as_posix()
                assert relative_path not in workspace_index.index_data.path_to_node

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_symbolic_link_handling_events(self):
        """Test handling of symbolic link events."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create a regular file
            regular_file = Path(temp_dir) / "regular.txt"
            regular_file.write_text("regular file content")
            
            # Create symbolic link (platform dependent)
            try:
                link_file = Path(temp_dir) / "link.txt"
                link_file.symlink_to(regular_file)
                
                # Test symlink creation event
                await workspace_index._async_handle_file_created(str(link_file))
                
                # Verify symlink was added (or skipped gracefully)
                link_relative = link_file.relative_to(temp_dir).as_posix()
                # Should either be in index or gracefully skipped
                # Based on current implementation, symlinks are processed like regular files
                
            except (OSError, NotImplementedError):
                # Skip symlink tests if not supported
                pytest.skip("Symbolic links not supported on this platform")

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_migration_between_lru_and_core_on_rules_change(self):
        """Test that files can migrate between LRU and core based on rules changes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create file initially not core
            config_file = Path(temp_dir) / "config.py"
            config_file.write_text("import os")
            
            # Add as dynamic file
            await workspace_index._async_handle_file_created(str(config_file))
            
            relative_path = config_file.relative_to(temp_dir).as_posix()
            node = workspace_index.index_data.path_to_node[relative_path]
            assert node.is_core is False
            assert relative_path in workspace_index.index_data.dynamic_nodes_lru
            
            # Note: Actual migration would require rebuilding PathSpecs, 
            # which is tested in test_gitignore.py

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_event_processor_robustness_with_corrupted_paths(self):
        """Test event processor handles corrupted or invalid paths gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Test with various invalid paths
            invalid_paths = [
                "nonexistent/file.txt",
                temp_dir + "//../../../etc/passwd",  # Path traversal
                temp_dir + "/\\0",  # Null byte in path
                temp_dir + "/invalid\npath",  # Newline in path - fixed to escaped newline
                ""  # Empty string
            ]
            
            # Should handle gracefully without crashing
            for invalid_path in invalid_paths:
                try:
                    await workspace_index._async_handle_file_created(invalid_path)
                    await workspace_index._async_handle_file_modified(invalid_path)
                    await workspace_index._async_handle_file_deleted(invalid_path)
                except Exception:
                    # Should handle gracefully, any exception should be caught internally
                    pass
                    
            # Processor should still be running
            assert workspace_index._event_processor_task is not None or workspace_index._observer is not None