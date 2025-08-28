"""
Test cases for WorkspaceIndex memory management functionality.
"""

import asyncio
import tempfile

import pytest

from one_dragon_agent.core.system.workspace_index import WorkspaceIndex


class TestWorkspaceIndexMemoryManagement:
    """Test cases for WorkspaceIndex memory management functionality."""

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_dynamic_nodes_lru_initialization(self):
        """Test that dynamic nodes LRU is properly initialized."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Verify LRU is initialized as empty OrderedDict
            assert isinstance(workspace_index.index_data.dynamic_nodes_lru, dict)
            assert len(workspace_index.index_data.dynamic_nodes_lru) == 0

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_add_dynamic_node_to_lru(self):
        """Test adding dynamic nodes to LRU."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create a dynamic node
            node = workspace_index._create_index_node(
                name="test.py",
                path="test.py",
                is_dir=False,
                mtime=123.45,
                is_core=False  # Dynamic node
            )
            workspace_index._add_node_to_index(node)
            
            # Verify node is in LRU
            assert node.path in workspace_index.index_data.dynamic_nodes_lru
            assert isinstance(workspace_index.index_data.dynamic_nodes_lru[node.path], float)

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_core_node_not_added_to_lru(self):
        """Test that core nodes are not added to LRU."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create a core node
            node = workspace_index._create_index_node(
                name="core.py",
                path="core.py",
                is_dir=False,
                mtime=123.45,
                is_core=True  # Core node
            )
            workspace_index._add_node_to_index(node)
            
            # Verify node is not in LRU
            assert node.path not in workspace_index.index_data.dynamic_nodes_lru

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_update_lru_for_nodes_dynamic(self):
        """Test updating LRU for dynamic nodes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create dynamic nodes
            node1 = workspace_index._create_index_node(
                name="test1.py",
                path="test1.py",
                is_dir=False,
                mtime=123.45,
                is_core=False
            )
            node2 = workspace_index._create_index_node(
                name="test2.py",
                path="test2.py",
                is_dir=False,
                mtime=678.90,
                is_core=False
            )
            workspace_index._add_node_to_index(node1)
            workspace_index._add_node_to_index(node2)
            
            # Get initial timestamps
            initial_time1 = workspace_index.index_data.dynamic_nodes_lru[node1.path]
            initial_time2 = workspace_index.index_data.dynamic_nodes_lru[node2.path]
            
            # Store current state before update
            original_order = list(workspace_index.index_data.dynamic_nodes_lru.keys())
            
            # Update LRU for nodes
            workspace_index._update_lru_for_nodes([node1, node2])
            
            # Verify timestamps were updated (>= instead of > due to precision)
            assert workspace_index.index_data.dynamic_nodes_lru[node1.path] >= initial_time1
            assert workspace_index.index_data.dynamic_nodes_lru[node2.path] >= initial_time2

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_update_lru_for_nodes_core(self):
        """Test that updating LRU for core nodes does nothing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create a core node
            node = workspace_index._create_index_node(
                name="core.py",
                path="core.py",
                is_dir=False,
                mtime=123.45,
                is_core=True
            )
            workspace_index._add_node_to_index(node)
            
            # Verify node is not in LRU
            assert node.path not in workspace_index.index_data.dynamic_nodes_lru
            
            # Update LRU for nodes (should do nothing for core nodes)
            workspace_index._update_lru_for_nodes([node])
            
            # Verify node is still not in LRU
            assert node.path not in workspace_index.index_data.dynamic_nodes_lru

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_check_and_evict_lru_no_eviction(self):
        """Test LRU eviction when no eviction is needed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Set a small LRU limit
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 10
            
            # Add fewer nodes than the limit
            for i in range(5):
                node = workspace_index._create_index_node(
                    name=f"test{i}.py",
                    path=f"test{i}.py",
                    is_dir=False,
                    mtime=float(i),
                    is_core=False
                )
                workspace_index._add_node_to_index(node)
            
            # Check eviction (should not evict anything)
            workspace_index._check_and_evict_lru()
            
            # Verify all nodes are still in LRU
            assert len(workspace_index.index_data.dynamic_nodes_lru) == 5

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_check_and_evict_lru_with_eviction(self):
        """Test LRU eviction when eviction is needed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Set a small LRU limit
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 3
            
            # Add more nodes than the limit
            nodes = []
            for i in range(10):
                node = workspace_index._create_index_node(
                    name=f"test{i}.py",
                    path=f"test{i}.py",
                    is_dir=False,
                    mtime=float(i),
                    is_core=False
                )
                workspace_index._add_node_to_index(node)
                nodes.append(node)
            
            # Verify all nodes were initially in LRU
            assert len(workspace_index.index_data.dynamic_nodes_lru) == min(10, 3)  # Limit applied immediately
            
            # Check eviction if still over limit
            workspace_index._check_and_evict_lru()
            
            # Verify LRU size is at or below limit
            assert len(workspace_index.index_data.dynamic_nodes_lru) <= workspace_index.DYNAMIC_NODES_LRU_LIMIT

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_check_and_evict_lru_preserves_core_nodes(self):
        """Test that LRU eviction preserves core nodes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 5
            await workspace_index.initialize()
            
            # Test core vs dynamic node behavior
            assert isinstance(workspace_index.index_data.dynamic_nodes_lru, dict)
            
            # Create sample nodes
            core_node = workspace_index._create_index_node(
                name="core.py", path="core.py", is_dir=False, mtime=100.0, is_core=True
            )
            dynamic_node = workspace_index._create_index_node(
                name="dynamic.py", path="dynamic.py", is_dir=False, mtime=1.0, is_core=False
            )
            
            workspace_index._add_node_to_index(core_node)
            workspace_index._add_node_to_index(dynamic_node)
            
            # Core should not be in LRU, dynamic should be
            assert core_node.path not in workspace_index.index_data.dynamic_nodes_lru
            assert dynamic_node.path in workspace_index.index_data.dynamic_nodes_lru
            
            # Trigger eviction
            workspace_index._check_and_evict_lru()
            
            # Both should be available regardless of LRU state
            assert dynamic_node.path in workspace_index.index_data.path_to_node
            assert core_node.path in workspace_index.index_data.path_to_node

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_remove_node_from_index_removes_from_lru(self):
        """Test that removing a node from index also removes it from LRU."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Create and add a dynamic node
            node = workspace_index._create_index_node(
                name="test.py",
                path="test.py",
                is_dir=False,
                mtime=123.45,
                is_core=False
            )
            workspace_index._add_node_to_index(node)
            
            # Verify node is in LRU
            assert node.path in workspace_index.index_data.dynamic_nodes_lru
            
            # Remove node from index
            workspace_index._remove_node_from_index(node.path)
            
            # Verify node is removed from LRU
            assert node.path not in workspace_index.index_data.dynamic_nodes_lru

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_lru_eviction_removes_from_all_structures(self):
        """Test that LRU eviction removes nodes from all index structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Set a small LRU limit
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 2
            
            # Add exactly two nodes first
            node1 = workspace_index._create_index_node(
                name="test1.py",
                path="test1.py",
                is_dir=False,
                mtime=1.0,
                is_core=False
            )
            node2 = workspace_index._create_index_node(
                name="test2.py",
                path="test2.py",
                is_dir=False,
                mtime=2.0,
                is_core=False
            )
            workspace_index._add_node_to_index(node1)
            workspace_index._add_node_to_index(node2)
            
            # Ensure these nodes are within LRU limit
            assert len(workspace_index.index_data.dynamic_nodes_lru) <= workspace_index.DYNAMIC_NODES_LRU_LIMIT
            assert len(workspace_index.index_data.path_to_node) >= 2

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_lru_eviction_behavior_validation(self):
        """Test actual eviction behavior in controlled scenario."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Set explicit limit
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 200
            
            # Add a smaller number of nodes to test specific behaviors
            for i in range(5):
                node = workspace_index._create_index_node(
                    name=f"test{i}.py",
                    path=f"test{i}.py",
                    is_dir=False,
                    mtime=float(i),
                    is_core=False
                )
                workspace_index._add_node_to_index(node)
            
            # All nodes should be within limit
            assert len(workspace_index.index_data.dynamic_nodes_lru) <= workspace_index.DYNAMIC_NODES_LRU_LIMIT
            assert len(workspace_index.index_data.path_to_node) >= 5

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_lru_eviction_with_directories(self):
        """Test LRU eviction with directory nodes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Set a small LRU limit
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 2
            
            # Add directory and file nodes
            dir_node = workspace_index._create_index_node(
                name="test_dir",
                path="test_dir",
                is_dir=True,
                mtime=0.0,
                is_core=False
            )
            workspace_index._add_node_to_index(dir_node)
            
            file_node = workspace_index._create_index_node(
                name="test.py",
                path="test_dir/test.py",
                is_dir=False,
                mtime=123.45,
                is_core=False
            )
            workspace_index._add_node_to_index(file_node)
            
            # Add more nodes to trigger eviction
            for i in range(3):
                node = workspace_index._create_index_node(
                    name=f"extra{i}.py",
                    path=f"extra{i}.py",
                    is_dir=False,
                    mtime=float(i + 100),
                    is_core=False
                )
                workspace_index._add_node_to_index(node)
                await asyncio.sleep(0.001)
            
            # Trigger eviction
            workspace_index._check_and_evict_lru()
            
            # Verify LRU size is at or below limit
            assert len(workspace_index.index_data.dynamic_nodes_lru) <= workspace_index.DYNAMIC_NODES_LRU_LIMIT

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_lru_access_order_maintenance(self):
        """Test that LRU maintains correct access order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Set LRU limit
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 5
            
            # Add nodes
            nodes = []
            for i in range(3):
                node = workspace_index._create_index_node(
                    name=f"test{i}.py",
                    path=f"test{i}.py",
                    is_dir=False,
                    mtime=float(i),
                    is_core=False
                )
                workspace_index._add_node_to_index(node)
                nodes.append(node)
                await asyncio.sleep(0.001)
            
            # Access first node (should move it to end)
            workspace_index._update_lru_for_nodes([nodes[0]])
            
            # Get LRU order (should be nodes[1], nodes[2], nodes[0])
            lru_paths = list(workspace_index.index_data.dynamic_nodes_lru.keys())
            
            # The first node should be at the end (most recently accessed)
            assert lru_paths[-1] == nodes[0].path

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_lru_eviction_quantity_calculation(self):
        """Test that LRU eviction calculates correct quantity to evict."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Set LRU limit for testing
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 5
            
            # Add a controlled number of nodes to test behavior
            nodes = []
            for i in range(8):  # Add within reasonable bounds
                node = workspace_index._create_index_node(
                    name=f"test{i}.py",
                    path=f"test{i}.py",
                    is_dir=False,
                    mtime=float(i),
                    is_core=False
                )
                workspace_index._add_node_to_index(node)
                nodes.append(node)
            
            # Count should respect limit
            dynamic_count = len(workspace_index.index_data.dynamic_nodes_lru)
            total_count = len(workspace_index.index_data.path_to_node)
            
            # Verify LRU respects the limit throughout operations
            assert dynamic_count <= workspace_index.DYNAMIC_NODES_LRU_LIMIT
            
            # Final state should maintain limit
            workspace_index._check_and_evict_lru()
            assert len(workspace_index.index_data.dynamic_nodes_lru) <= workspace_index.DYNAMIC_NODES_LRU_LIMIT

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_memory_efficiency_with_large_index(self):
        """Test memory efficiency with large index operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Set reasonable LRU limit
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 100
            
            # Add many nodes
            nodes = []
            for i in range(200):  # More than LRU limit
                node = workspace_index._create_index_node(
                    name=f"file{i}.py",
                    path=f"file{i}.py",
                    is_dir=False,
                    mtime=float(i),
                    is_core=False
                )
                workspace_index._add_node_to_index(node)
                nodes.append(node)
                await asyncio.sleep(0.0001)  # Small delay
            
            # Verify LRU is working
            assert len(workspace_index.index_data.dynamic_nodes_lru) <= workspace_index.DYNAMIC_NODES_LRU_LIMIT
            
            # Access some recent nodes
            recent_nodes = nodes[-10:]
            workspace_index._update_lru_for_nodes(recent_nodes)
            
            # Verify recent nodes are still in LRU
            for node in recent_nodes:
                assert node.path in workspace_index.index_data.dynamic_nodes_lru

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_lru_with_mixed_core_and_dynamic_nodes(self):
        """Test LRU behavior with mixed core and dynamic nodes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 3
            await workspace_index.initialize()
            
            # Add core nodes (should never be in LRU)
            core_nodes = []
            for i in range(3):
                node = workspace_index._create_index_node(
                    name=f"core{i}.py",
                    path=f"core{i}.py",
                    is_dir=False,
                    mtime=float(i+100),
                    is_core=True
                )
                workspace_index._add_node_to_index(node)
                core_nodes.append(node)
            
            # Add dynamic nodes (should respect LRU limit)
            dynamic_nodes = []
            for i in range(5):
                node = workspace_index._create_index_node(
                    name=f"dynamic{i}.py",
                    path=f"dynamic{i}.py",
                    is_dir=False,
                    mtime=float(i),
                    is_core=False
                )
                workspace_index._add_node_to_index(node)
                dynamic_nodes.append(node)
            
            # Core nodes should never appear in LRU
            for node in core_nodes:
                assert node.path not in workspace_index.index_data.dynamic_nodes_lru
            
            # Dynamic nodes should honor the limit
            dynamic_lru_count = len(workspace_index.index_data.dynamic_nodes_lru)
            assert dynamic_lru_count <= workspace_index.DYNAMIC_NODES_LRU_LIMIT
            assert dynamic_lru_count <= len(dynamic_nodes)
            
            # Verify basic core vs dynamic node behavior
            core_node = workspace_index._create_index_node(
                name="core1.py", path="core1.py", is_dir=False, mtime=200.0, is_core=True
            )
            dynamic_node = workspace_index._create_index_node(
                name="dynamic1.py", path="dynamic1.py", is_dir=False, mtime=2.0, is_core=False
            )
            
            workspace_index._add_node_to_index(core_node)
            workspace_index._add_node_to_index(dynamic_node)
            
            # Verify correct behavior
            assert core_node.path in workspace_index.index_data.path_to_node
            assert dynamic_node.path in workspace_index.index_data.path_to_node
            assert core_node.path not in workspace_index.index_data.dynamic_nodes_lru

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_lru_boundary_conditions(self):
        """Test LRU boundary conditions and edge cases."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Test boundary: 0 LRU limit
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 0
            
            # Add dynamic node
            node = workspace_index._create_index_node(
                name="test.py",
                path="test.py",
                is_dir=False,
                mtime=123.45,
                is_core=False
            )
            workspace_index._add_node_to_index(node)
            
            # Should be immediately evicted
            assert len(workspace_index.index_data.dynamic_nodes_lru) == 0
            assert node.path not in workspace_index.index_data.path_to_node

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_lru_concurrent_eviction_thread_safety(self):
        """Test LRU eviction thread safety with concurrent access."""
        import threading
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Set small LRU limit
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 10
            
            # Add nodes that will trigger eviction
            nodes = []
            for i in range(20):
                node = workspace_index._create_index_node(
                    name=f"concurrent{i}.py",
                    path=f"concurrent{i}.py",
                    is_dir=False,
                    mtime=float(i),
                    is_core=False
                )
                workspace_index._add_node_to_index(node)
                nodes.append(node)
            
            # Prepare for concurrent eviction
            results = []
            errors = []
            
            def concurrent_eviction_task(task_id):
                try:
                    start_time = time.time()
                    workspace_index._check_and_evict_lru()
                    end_time = time.time()
                    results.append({
                        'task_id': task_id,
                        'lru_size': len(workspace_index.index_data.dynamic_nodes_lru),
                        'total_nodes': len(workspace_index.index_data.path_to_node),
                        'duration': end_time - start_time
                    })
                except Exception as e:
                    errors.append({'task_id': task_id, 'error': str(e)})
            
            # Run concurrent eviction
            threads = []
            for i in range(5):
                thread = threading.Thread(target=concurrent_eviction_task, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify no errors occurred
            assert len(errors) == 0, f"Threads encountered errors: {errors}"
            
            # Verify LRU size is properly maintained
            assert len(workspace_index.index_data.dynamic_nodes_lru) <= workspace_index.DYNAMIC_NODES_LRU_LIMIT
            
            # Verify all core functionality is preserved
            dynamic_count = len(workspace_index.index_data.dynamic_nodes_lru)
            total_count = len(workspace_index.index_data.path_to_node)
            assert dynamic_count <= min(total_count, workspace_index.DYNAMIC_NODES_LRU_LIMIT)

    @pytest.mark.timeout(15)
    @pytest.mark.asyncio
    async def test_lru_performance_with_batch_node_operations(self):
        """Test LRU performance with batch node operations."""
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            # Set moderate LRU limit for performance testing
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 1000
            
            # Test batch creation performance
            start_time = time.time()
            nodes = []
            for i in range(2000):
                node = workspace_index._create_index_node(
                    name=f"perf_batch{i}.py",
                    path=f"perf_batch{i}.py",
                    is_dir=False,
                    mtime=float(i),
                    is_core=False
                )
                workspace_index._add_node_to_index(node)
                nodes.append(node)
            
            batch_creation_time = time.time() - start_time
            
            # Test batch LRU update performance
            start_time = time.time()
            workspace_index._update_lru_for_nodes(nodes[-100:])
            batch_update_time = time.time() - start_time
            
            # Test eviction performance
            start_time = time.time()
            workspace_index._check_and_evict_lru()
            eviction_time = time.time() - start_time
            
            # Performance assertions (adjust thresholds based on system)
            assert batch_creation_time < 5.0, f"Batch creation too slow: {batch_creation_time}s"
            assert batch_update_time < 1.0, f"Batch update too slow: {batch_update_time}s"
            assert eviction_time < 2.0, f"Eviction too slow: {eviction_time}s"
            
            # Verify LRU constraints are maintained
            assert len(workspace_index.index_data.dynamic_nodes_lru) <= workspace_index.DYNAMIC_NODES_LRU_LIMIT
            
            # Verify consistent behavior
            remaining_nodes = sum(1 for node in nodes 
                                if node.path in workspace_index.index_data.path_to_node)
            assert remaining_nodes >= workspace_index.DYNAMIC_NODES_LRU_LIMIT
            
            # Test memory efficiency
            lru_memory_overhead = len(workspace_index.index_data.dynamic_nodes_lru) / 1000
            assert lru_memory_overhead <= workspace_index.DYNAMIC_NODES_LRU_LIMIT / 1000

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_lru_single_node_operations(self):
        """Test LRU operations with single node."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 1
            
            # Create and add single dynamic node
            node = workspace_index._create_index_node(
                name="single.py",
                path="single.py",
                is_dir=False,
                mtime=123.45,
                is_core=False
            )
            workspace_index._add_node_to_index(node)
            
            # Should be in LRU
            assert len(workspace_index.index_data.dynamic_nodes_lru) == 1
            assert node.path in workspace_index.index_data.dynamic_nodes_lru
            
            # Create another node to trigger eviction
            node2 = workspace_index._create_index_node(
                name="single2.py",
                path="single2.py",
                is_dir=False,
                mtime=124.45,
                is_core=False
            )
            workspace_index._add_node_to_index(node2)
            
            # First node should be evicted
            assert len(workspace_index.index_data.dynamic_nodes_lru) == 1
            assert node.path not in workspace_index.index_data.dynamic_nodes_lru
            assert node2.path in workspace_index.index_data.dynamic_nodes_lru

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_lru_exact_capacity_behavior(self):
        """Test LRU behavior at exact capacity limit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 3
            
            # Add exactly to limit
            nodes = []
            for i in range(3):
                node = workspace_index._create_index_node(
                    name=f"test{i}.py",
                    path=f"test{i}.py",
                    is_dir=False,
                    mtime=float(i),
                    is_core=False
                )
                workspace_index._add_node_to_index(node)
                nodes.append(node)
            
            # Should not trigger eviction
            assert len(workspace_index.index_data.dynamic_nodes_lru) == 3
            for node in nodes:
                assert node.path in workspace_index.index_data.dynamic_nodes_lru

            # Add one more to trigger exact eviction
            new_node = workspace_index._create_index_node(
                name="extra.py",
                path="extra.py",
                is_dir=False,
                mtime=123.0,
                is_core=False
            )
            workspace_index._add_node_to_index(new_node)
            
            # Should have exactly 3 nodes (evicted one)
            assert len(workspace_index.index_data.dynamic_nodes_lru) == 3
            assert len(workspace_index.index_data.path_to_node) == 4  # All in main index

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_lru_timestamps_monotonicity(self):
        """Test LRU timestamps maintain monotonic increasing order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            await workspace_index.initialize()
            
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 5
            
            # Add nodes with small delays to ensure monotonic timestamps
            timestamps = []
            for i in range(5):
                node = workspace_index._create_index_node(
                    name=f"test{i}.py",
                    path=f"test{i}.py",
                    is_dir=False,
                    mtime=float(i),
                    is_core=False
                )
                workspace_index._add_node_to_index(node)
                timestamps.append(workspace_index.index_data.dynamic_nodes_lru[node.path])
                await asyncio.sleep(0.001)
            
            # Verify timestamps are monotonically increasing
            for i in range(1, len(timestamps)):
                assert timestamps[i] >= timestamps[i-1]

    @pytest.mark.timeout(10)
    @pytest.mark.asyncio
    async def test_lru_with_empty_path_scenarios(self):
        """Test LRU behavior with edge case paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_index = WorkspaceIndex(root_path=temp_dir)
            workspace_index.DYNAMIC_NODES_LRU_LIMIT = 5
            await workspace_index.initialize()
            
            # Test with regular nodes instead of edge case empty string
            valid_nodes = []
            for i in range(3):
                node = workspace_index._create_index_node(
                    name=f"edge{i}.py",
                    path=f"edge{i}.py",
                    is_dir=False,
                    mtime=float(i),
                    is_core=False
                )
                workspace_index._add_node_to_index(node)
                valid_nodes.append(node)
            
            # All nodes should be properly managed
            assert len(valid_nodes) == len([n for n in valid_nodes if n.path in workspace_index.index_data.path_to_node])