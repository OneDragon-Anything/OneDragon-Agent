import asyncio
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty, Queue
from typing import Optional

from pathspec import PathSpec
from pathspec.gitignore import GitIgnoreSpec
from pathspec.patterns import GitWildMatchPattern
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from one_dragon_agent.core.algo.trie import Trie


class IndexFileSystemEventHandler(FileSystemEventHandler):
    """
    文件系统事件处理器，用于监听文件系统变化并更新索引
    """

    def __init__(self, workspace_index: "WorkspaceIndex") -> None:
        """
        初始化文件系统事件处理器

        Args:
            workspace_index: 关联的WorkspaceIndex实例
        """
        self.workspace_index = workspace_index
        super().__init__()

    def on_created(self, event: FileSystemEvent) -> None:
        """
        处理文件/目录创建事件

        Args:
            event: 文件系统事件
        """
        # 确保路径是字符串类型
        src_path_str = str(event.src_path)

        if not event.is_directory:
            # Check if it's a .gitignore file
            if Path(src_path_str).name == ".gitignore":
                self.workspace_index._enqueue_event('gitignore_changed', None)

            # 文件创建事件 - 放入事件队列
            self.workspace_index._enqueue_event('file_created', src_path_str)
        else:
            # 目录创建事件 - 放入事件队列
            self.workspace_index._enqueue_event('dir_created', src_path_str)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """
        处理文件/目录删除事件

        Args:
            event: 文件系统事件
        """
        # 确保路径是字符串类型
        src_path_str = str(event.src_path)

        # Check if it's a .gitignore file
        is_gitignore = Path(src_path_str).name == ".gitignore"
        
        # Check if gitignore change event needs to be triggered
        need_gitignore_change = is_gitignore
        
        # For directory deletion, also need to check if the directory contains .gitignore files
        if event.is_directory:
            # Check if there are .gitignore files in the directory
            relative_base = Path(src_path_str).relative_to(self.workspace_index.root_path).as_posix()
            if self.workspace_index._does_directory_contain_gitignore(relative_base):
                need_gitignore_change = True

        if need_gitignore_change:
            self.workspace_index._enqueue_event('gitignore_changed', None)

        if not event.is_directory:
            # 文件删除事件 - 放入事件队列
            self.workspace_index._enqueue_event('file_deleted', src_path_str)
        else:
            # 目录删除事件 - 放入事件队列
            self.workspace_index._enqueue_event('dir_deleted', src_path_str)

    def on_modified(self, event: FileSystemEvent) -> None:
        """
        处理文件/目录修改事件

        Args:
            event: 文件系统事件
        """
        # 确保路径是字符串类型
        src_path_str = str(event.src_path)

        if not event.is_directory:
            # Check if it's a .gitignore file
            if Path(src_path_str).name == ".gitignore":
                self.workspace_index._enqueue_event('gitignore_changed', None)

            # 文件修改事件 - 放入事件队列
            self.workspace_index._enqueue_event('file_modified', src_path_str)
        # 目录修改事件通常不需要特殊处理

    def on_moved(self, event: FileSystemEvent) -> None:
        """
        处理文件/目录移动/重命名事件

        Args:
            event: 文件系统事件
        """
        # 确保路径是字符串类型
        src_path_str = str(event.src_path)
        dest_path_str = str(event.dest_path)

        # Check if source path or destination path is a .gitignore file
        src_is_gitignore = Path(src_path_str).name == ".gitignore"
        dest_is_gitignore = (
            not event.is_directory and Path(dest_path_str).name == ".gitignore"
        )

        # Check if gitignore change event needs to be triggered
        need_gitignore_change = src_is_gitignore or dest_is_gitignore
        
        # For directory move, also need to check if the source directory contains .gitignore files
        if event.is_directory:
            # Only check if there are .gitignore files in the source directory
            src_relative_base = Path(src_path_str).relative_to(self.workspace_index.root_path).as_posix()
            if self.workspace_index._does_directory_contain_gitignore(src_relative_base):
                need_gitignore_change = True

        if need_gitignore_change:
            self.workspace_index._enqueue_event('gitignore_changed', None)

        if not event.is_directory:
            # 文件移动/重命名事件 - 放入事件队列
            self.workspace_index._enqueue_event('file_moved', (src_path_str, dest_path_str))
        else:
            # 目录移动/重命名事件 - 放入事件队列
            self.workspace_index._enqueue_event('dir_moved', (src_path_str, dest_path_str))


@dataclass
class IndexNode:
    """
    表示文件系统中一个实体（文件或目录）的核心数据对象
    """

    name: str  # Name of the file or directory
    path: str  # Canonicalized relative path from the project root directory
    is_dir: bool  # Mark whether this node is a directory
    mtime: float = 0.0  # Unix timestamp of last file modification time, 0 for directory nodes
    parent: Optional["IndexNode"] = None  # Direct reference to its parent node
    children: dict[str, "IndexNode"] = field(default_factory=dict)  # Child node mapping
    is_core: bool = False  # Mark whether this node belongs to the "static core area"

    def __post_init__(self) -> None:
        """
        Post-initialization processing
        """
        if self.children is None:
            self.children = {}


class IndexData:
    """
    存放所有索引数据的内部容器
    """

    def __init__(self) -> None:
        """
        初始化IndexData
        """
        # Main index and data owner: Stores all known IndexNode object instances in the project
        self.path_to_node: dict[str, IndexNode] = {}

        # 路径前缀搜索加速器
        self.path_trie: Trie = Trie()

        # 名称前缀搜索加速器
        self.name_trie: Trie = Trie()

        # LRU manager for dynamic discovery area nodes
        self.dynamic_nodes_lru: OrderedDict[str, float] = OrderedDict()


class WorkspaceIndex:
    """
    实时文件索引服务

    为 OneDragon-Agent 提供一个高性能、实时同步的文件和目录索引服务。
    """

    # LRU default size limit
    DYNAMIC_NODES_LRU_LIMIT: int = 10000

    def __init__(
        self,
        root_path: str,
        core_patterns: list[str] | None = None,
        ignore_patterns: list[str] | None = None,
        use_gitignore: bool = True,
    ) -> None:
        """
        初始化WorkspaceIndex

        Args:
            root_path: 项目根目录的绝对路径
            core_patterns: 用户定义的核心文件/目录模式列表
            ignore_patterns: 用户定义的忽略文件/目录模式列表
            use_gitignore: 是否使用.gitignore文件定义忽略规则
        """
        # 验证根路径
        root_path_obj = Path(root_path).resolve()
        if not root_path_obj.exists():
            raise ValueError(f"根路径不存在: {root_path}")
        if not root_path_obj.is_dir():
            raise ValueError(f"根路径不是一个目录: {root_path}")

        self.root_path: str = str(root_path_obj)
        self.core_patterns: list[str] = core_patterns or []
        self.ignore_patterns: list[str] = ignore_patterns or []
        self.use_gitignore: bool = use_gitignore

        # 初始化索引数据容器
        self.index_data: IndexData = IndexData()

        # 初始化状态管理
        self._initialized: bool = False
        self._initializing: bool = False
        self._init_lock: asyncio.Lock = asyncio.Lock()

        # PathSpec object (will be constructed during initialization)
        self._core_pathspec: PathSpec | None = None
        self._ignore_pathspec_static: GitIgnoreSpec | None = None
        self._ignore_pathspec_git: GitIgnoreSpec | None = None

        # 文件系统监听相关
        self._observer: Observer | None = None
        self._event_handler: IndexFileSystemEventHandler | None = None
        self._watching: bool = False

        # 全局扫描锁，防止并发昂贵的磁盘扫描
        self._global_scan_lock: asyncio.Lock = asyncio.Lock()
        self._sync_scan_lock: asyncio.Lock = asyncio.Lock()
        
        # 线程安全的事件队列
        self._event_queue: Queue = Queue()
        self._event_processor_task: asyncio.Task | None = None
        self._event_processing_lock = threading.Lock()

    def _does_directory_contain_gitignore(self, directory_path: str) -> bool:
        """
        检查目录及其子目录下是否包含.gitignore文件

        该方法通过遍历索引中的所有节点，检查是否存在以指定目录路径为前缀
        且以/.gitignore结尾的路径，从而判断该目录及其子目录下是否包含.gitignore文件。
        这种方法避免了直接访问文件系统，提高了检查效率。

        Args:
            directory_path: 目录的相对路径

        Returns:
            如果目录及其子目录下包含.gitignore文件则返回True，否则返回False
        """
        # Check if there are .gitignore file paths in the index with this directory as prefix
        directory_prefix = directory_path + "/" if directory_path else ""
        for path in self.index_data.path_to_node:
            # Check if the path starts with the directory prefix and is a .gitignore file
            if path.startswith(directory_prefix) and path.endswith("/.gitignore"):
                return True
        return False

    async def initialize(self) -> None:
        """
        异步初始化索引服务
        """
        async with self._init_lock:
            if self._initialized or self._initializing:
                return

            self._initializing = True
            try:
                # 1. PathSpec construction
                self._construct_pathspecs()

                # 2. Construct .gitignore PathSpec (needs to be completed before building core index)
                if self.use_gitignore:
                    await self._construct_gitignore_pathspec()

                # 3. Core area index construction
                await self._build_core_index()

                # 4. Start file system monitoring
                await self._start_file_watching()
                
                # 5. Start event processor
                self._start_event_processor()

                # 6. Mark initialization complete
                self._initialized = True
            except Exception as e:
                # 记录错误并清理状态
                self._initialized = False
                raise e
            finally:
                self._initializing = False

    def _construct_pathspecs(self) -> None:
        """
        构造PathSpec对象（同步部分）

        该方法构造三个PathSpec对象，用于路径匹配：
        1. core_pathspec - 核心文件/目录模式
        2. ignore_pathspec_static - 静态忽略模式
        3. ignore_pathspec_git - Git忽略模式（在异步初始化中构造）

        对于core_pathspec，如果启用Git忽略功能，会自动包含**/.gitignore模式，
        确保所有.gitignore文件都被视为核心文件。
        """
        # Construct core_pathspec
        core_patterns = self.core_patterns.copy()
        if self.use_gitignore:
            # Automatically include .gitignore pattern
            core_patterns.append("**/.gitignore")
        self._core_pathspec = PathSpec.from_lines(GitWildMatchPattern, core_patterns)

        # Construct ignore_pathspec_static
        self._ignore_pathspec_static = GitIgnoreSpec.from_lines(self.ignore_patterns)

        # ignore_pathspec_git will be constructed in async initialization

    def _read_gitignore_file(self, gitignore_path: Path) -> list[str]:
        """
        读取并解析.gitignore文件，返回规则列表

        Args:
            gitignore_path: .gitignore文件的路径

        Returns:
            规则列表，每行一个规则
        """
        try:
            # Use utf-8 encoding directly and ignore errors, simplify processing
            with open(gitignore_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            # 处理每一行，去除注释和空行
            rules = []
            for line in lines:
                line = line.rstrip("\n")
                if line and not line.startswith("#"):
                    rules.append(line)

            return rules
        except Exception:
            # 读取失败时返回空列表
            return []

    def _process_gitignore_rules(
        self, rules: list[str], relative_dir: Path
    ) -> list[str]:
        """
        处理.gitignore规则，为子目录的规则添加正确的前缀

        该方法用于处理不同目录下的.gitignore文件规则，确保规则的作用域正确。
        对于非根目录的.gitignore文件，需要为规则添加目录前缀，以确保规则只在
        正确的范围内生效。处理的规则类型包括：
        1. 绝对路径规则（以/开头）
        2. 否定绝对路径规则（以!/开头）
        3. 否定相对路径规则（以!开头）
        4. 相对路径规则（不以/或!开头）

        Args:
            rules: 原始规则列表
            relative_dir: .gitignore文件相对于项目根目录的路径

        Returns:
            处理后的规则列表
        """
        processed_rules = []

        # Add path prefix for .gitignore files in non-root directories
        if relative_dir != Path("../sys"):
            dir_prefix = relative_dir.as_posix()
            for rule in rules:
                if rule.startswith("/"):
                    # Absolute path: /pattern -> /dir/pattern
                    processed_rules.append(f"/{dir_prefix}{rule}")
                elif rule.startswith("!/"):
                    # Negative absolute path: !/pattern -> !/dir/pattern
                    processed_rules.append(f"!/{dir_prefix}{rule[1:]}")
                elif rule.startswith("!"):
                    # Negative relative path: !pattern -> !dir/pattern
                    processed_rules.append(f"!{dir_prefix}/{rule[1:]}")
                else:
                    # Relative path: pattern -> dir/pattern
                    processed_rules.append(f"{dir_prefix}/{rule}")
        else:
            # .gitignore file in root directory, use original rules directly
            processed_rules.extend(rules)

        return processed_rules

    async def _construct_gitignore_pathspec(self) -> None:
        """
        异步构造.gitignore规则的PathSpec对象，正确处理子目录规则的作用域
        """
        # Async scan .gitignore files and process all .gitignore files
        all_lines = await asyncio.to_thread(self._scan_and_process_gitignore_files)
        self._ignore_pathspec_git = GitIgnoreSpec.from_lines(all_lines)

    async def _build_core_index(self) -> None:
        """
        异步构建核心区索引
        """
        # 首先创建根节点
        root_node = self._create_index_node(
            name="",
            path="",
            is_dir=True,
            mtime=0.0,
            is_core=True,  # 根节点始终是核心节点
        )
        self._add_node_to_index(root_node)

        # 在线程池中执行同步扫描
        nodes = await asyncio.to_thread(self._scan_files)
        
        # 批量添加到索引结构中
        for node in nodes:
            self._add_node_to_index(node)

        # File system monitoring will be started asynchronously in the initialize method

    def _match_pathspec(self, relative_path: str, is_dir: bool) -> tuple[bool, bool]:
        """
        使用PathSpec匹配路径

        该方法使用三个PathSpec对象（核心规则、静态忽略规则、Git忽略规则）来确定
        给定路径是否应该被索引以及是否属于核心区域。匹配按优先级顺序进行：
        1. 核心区匹配 - 最高优先级
        2. 静态忽略匹配 - 次高优先级
        3. Git忽略匹配 - 最低优先级

        Args:
            relative_path: 相对于项目根目录的路径
            is_dir: 是否为目录

        Returns:
            (should_index, is_core) 二元组
            - should_index: 是否应该索引该路径
            - is_core: 是否为核心区文件
        """
        # Ensure PathSpec objects are initialized
        if self._core_pathspec is None or self._ignore_pathspec_static is None:
            raise RuntimeError("PathSpec对象尚未初始化")

        # 对于目录，我们也检查带有/后缀的路径
        paths_to_check = [relative_path]
        if is_dir:
            paths_to_check.append(relative_path + "/")

        # 1. Core area matching
        for path in paths_to_check:
            if self._core_pathspec.match_file(path):
                return True, True

        # 2. Static ignore matching
        for path in paths_to_check:
            if self._ignore_pathspec_static.match_file(path):
                return False, False

        # 3. Git ignore matching
        if self._ignore_pathspec_git:
            for path in paths_to_check:
                if self._ignore_pathspec_git.match_file(path):
                    return False, False

        # 默认情况：应该索引，但不是核心区
        return True, False

    async def _start_file_watching(self) -> None:
        """
        启动文件系统监听
        """
        # Start monitoring during initialization (at this time _initialized may still be False)
        # 创建事件处理器
        self._event_handler = IndexFileSystemEventHandler(self)

        # 创建观察者
        self._observer = Observer()

        # 安排观察路径
        self._observer.schedule(self._event_handler, self.root_path, recursive=True)

        # 启动观察者（会自动创建内部线程）
        self._observer.start()

        self._watching = True

    def _stop_file_watching(self) -> None:
        """
        停止文件系统监听
        """
        if self._observer:
            try:
                self._observer.stop()
                self._observer.join(timeout=1.0)  # 等待观察者停止
            except Exception:
                # 忽略停止过程中的错误
                pass
            finally:
                self._observer = None

        self._event_handler = None
        self._watching = False
        
        # 停止事件处理器
        if self._event_processor_task:
            self._event_processor_task.cancel()
            self._event_processor_task = None

    def _start_event_processor(self) -> None:
        """
        启动事件处理器
        """
        self._event_processor_task = asyncio.create_task(self._process_events())

    async def _process_events(self) -> None:
        """
        异步处理文件系统事件

        该方法运行在一个独立的任务中，持续从事件队列中获取文件系统事件并处理。
        支持的事件类型包括：文件/目录的创建、删除、修改、移动，以及.gitignore文件变化。
        事件处理是异步的，确保不会阻塞主线程。
        """
        while True:
            try:
                # 非阻塞获取事件
                try:
                    event_type, file_path = self._event_queue.get_nowait()
                except Empty:
                    await asyncio.sleep(0.01)
                    continue
                
                # 处理事件
                if event_type == 'file_created':
                    await self._async_handle_file_created(file_path)
                elif event_type == 'dir_created':
                    await self._async_handle_dir_created(file_path)
                elif event_type == 'file_deleted':
                    await self._async_handle_file_deleted(file_path)
                elif event_type == 'dir_deleted':
                    await self._async_handle_dir_deleted(file_path)
                elif event_type == 'file_modified':
                    await self._async_handle_file_modified(file_path)
                elif event_type == 'file_moved':
                    await self._async_handle_file_moved(file_path[0], file_path[1])
                elif event_type == 'dir_moved':
                    await self._async_handle_dir_moved(file_path[0], file_path[1])
                elif event_type == 'gitignore_changed':
                    await self._handle_gitignore_changed()
                    
            except asyncio.CancelledError:
                break
            except Exception:
                # 忽略事件处理中的错误
                pass

    def _create_index_node(
        self, name: str, path: str, is_dir: bool, mtime: float, is_core: bool
    ) -> IndexNode:
        """
        创建IndexNode对象并建立父子关系

        该方法用于创建新的索引节点，并建立节点之间的父子关系。如果节点已存在，
        则更新其核心属性。对于新创建的节点，还会递归创建其父节点（如果需要），
        并建立完整的父子关系链。

        Args:
            name: 文件或目录名称
            path: 相对于项目根目录的路径
            is_dir: 是否为目录
            mtime: 修改时间
            is_core: 是否为核心区文件

        Returns:
            创建的IndexNode对象
        """
        # 检查节点是否已存在
        if path in self.index_data.path_to_node:
            # 如果节点已存在，更新其核心属性（如果需要）
            existing_node = self.index_data.path_to_node[path]
            # 如果新节点是核心节点，更新现有节点的核心属性
            if is_core and not existing_node.is_core:
                existing_node.is_core = True
            return existing_node

        # 创建节点
        node = IndexNode(
            name=name, path=path, is_dir=is_dir, mtime=mtime, is_core=is_core
        )

        # 建立父子关系
        if path != "":  # 不是根节点
            # 计算父路径
            parent_path = "/".join(path.split("/")[:-1]) if "/" in path else ""

            # 获取或创建父节点
            if parent_path in self.index_data.path_to_node:
                parent_node = self.index_data.path_to_node[parent_path]
                # 如果当前节点是核心节点，父节点也应该是核心节点
                # 但只有当父节点还没有被标记为核心节点时才需要检查
                if is_core and not parent_node.is_core:
                    # 检查父节点是否应该被标记为核心节点
                    _, parent_should_be_core = self._match_pathspec(parent_path, True)
                    if parent_should_be_core:
                        parent_node.is_core = True
            else:
                # 创建父节点（递归）
                parent_parts = parent_path.split("/") if parent_path else []
                parent_name = parent_parts[-1] if parent_parts else ""
                # 检查父节点是否应该被标记为核心节点
                _, parent_should_be_core = self._match_pathspec(parent_path, True)
                parent_node = self._create_index_node(
                    parent_name,
                    parent_path,
                    True,  # 父节点是目录
                    0.0,  # Directory mtime is 0
                    parent_should_be_core,  # 父节点的核心区属性基于匹配结果
                )
                # 确保父节点被添加到索引中
                self._add_node_to_index(parent_node)

            # 建立父子关系
            node.parent = parent_node
            parent_node.children[name] = node

        return node

    def _enqueue_event(self, event_type: str, file_path: str | None) -> None:
        """
        将文件系统事件加入处理队列
        
        该方法将文件系统事件放入事件队列中，供异步事件处理器处理。
        事件队列是线程安全的，确保在多线程环境中也能正确处理事件。
        如果队列已满，新事件将被忽略，以防止系统过载。

        Args:
            event_type: 事件类型
            file_path: 文件路径或元组（对于移动事件）
        """
        try:
            self._event_queue.put((event_type, file_path), block=False)
        except:
            # 队列满时忽略事件
            pass

    def _add_node_to_index(self, node: IndexNode) -> None:
        """
        将节点添加到所有索引结构中

        该方法将节点添加到所有相关的索引结构中，包括：
        1. path_to_node字典 - 主索引，用于通过路径快速访问节点
        2. path_trie - 路径前缀搜索加速器
        3. name_trie - 名称前缀搜索加速器
        4. dynamic_nodes_lru - 动态节点的LRU管理器（仅对非核心节点）
        同时还会更新节点的父子关系。

        Args:
            node: 要添加的IndexNode对象
        """
        # Add to path_to_node dictionary
        self.index_data.path_to_node[node.path] = node

        # Add path to path_trie
        self.index_data.path_trie.insert(node.path, node.path)

        # Add name to name_trie
        # In name_trie, data is a list of file paths with the same name
        existing_paths = self.index_data.name_trie.search(node.name)
        if existing_paths is None:
            # 如果名称不存在，创建新的路径列表
            self.index_data.name_trie.insert(node.name, [node.path])
        else:
            # 如果名称已存在，添加路径到列表
            existing_paths.append(node.path)

        # Core area nodes are not added to dynamic_nodes_lru
        if not node.is_core:
            self.index_data.dynamic_nodes_lru[node.path] = time.time()

            # Check and execute LRU eviction
            self._check_and_evict_lru()

    async def search(self, query: str, contextual_base_path: str) -> list[IndexNode]:
        """
        搜索文件或目录

        Args:
            query: 用户输入的原始查询字符串（不包含@符号）
            contextual_base_path: 用户发起搜索时所在的上下文目录（相对路径）

        Returns:
            匹配的IndexNode列表
        """
        # 1. Input normalization processing (two-stage security verification)
        normalized_query, normalized_context_path, is_listing_request = (
            self._normalize_input(query, contextual_base_path)
        )

        # 2. Empty query processing
        if not normalized_query:
            return []

        # 3. Handle initialization state
        if not self._initialized:
            if self._initializing:
                # 初始化中状态：先在内存中搜索，如果未命中则等待初始化完成
                results = self._search_in_memory(
                    normalized_query, normalized_context_path, is_listing_request
                )
                if results:
                    # Update LRU status and return
                    self._update_lru_for_nodes(results)
                    return results

                # Wait for initialization to complete (up to 30 seconds)
                try:
                    await asyncio.wait_for(
                        self._wait_for_initialization(), timeout=30.0
                    )
                except TimeoutError:
                    # 超时，进入降级模式
                    pass

                # 初始化完成后，重新搜索
                results = self._search_in_memory(
                    normalized_query, normalized_context_path, is_listing_request
                )
                if results:
                    self._update_lru_for_nodes(results)
                    return results
            else:
                # 初始化失败状态，进入降级模式
                results = self._search_in_memory(
                    normalized_query, normalized_context_path, is_listing_request
                )
                if results:
                    self._update_lru_for_nodes(results)
                    return results

        # 4. Search in memory index
        results = self._search_in_memory(
            normalized_query, normalized_context_path, is_listing_request
        )

        # 5. If results are found, update LRU status and return
        if results:
            self._update_lru_for_nodes(results)
            return results

        # 6. If no results are found, trigger fallback scan
        results = await self._fallback_scan(
            normalized_query, normalized_context_path, is_listing_request
        )

        # 7. Update LRU status again and return
        if results:
            self._update_lru_for_nodes(results)

        return results

    def _search_directory_listing(self, query: str) -> list[IndexNode]:
        """
        处理目录内容列出请求

        Args:
            query: 规范化后的查询字符串（目录路径）

        Returns:
            目录下的子节点列表
        """
        node = self.index_data.path_to_node.get(query)
        if node and node.is_dir:
            return list(node.children.values())
        return []

    def _search_by_name_or_path(
        self, query: str, contextual_base_path: str
    ) -> list[IndexNode]:
        """
        根据查询类型执行路径前缀搜索或名称前缀搜索

        Args:
            query: 规范化后的查询字符串
            contextual_base_path: 规范化后的上下文路径

        Returns:
            匹配的IndexNode列表
        """
        # 路径前缀搜索
        if "/" in query:
            return self._search_path_prefix(query)

        # 名称前缀搜索（上下文感知的两阶段搜索）
        return self._search_name_prefix(query, contextual_base_path)

    def _search_path_prefix(self, query: str) -> list[IndexNode]:
        """
        执行路径前缀搜索

        Args:
            query: 规范化后的查询字符串（包含路径分隔符）

        Returns:
            匹配的IndexNode列表
        """
        # 首先检查是否查询精确匹配一个目录
        exact_match_node = self.index_data.path_to_node.get(query)
        if exact_match_node and exact_match_node.is_dir:
            # 查询完全匹配一个目录，返回其子节点
            nodes = list(exact_match_node.children.values())
            nodes.sort(key=lambda x: x.path)
            return nodes

        # Use path_trie for prefix search
        path_results = self.index_data.path_trie.starts_with(query)
        if path_results:
            # Get corresponding IndexNode objects from path_to_node
            nodes = []
            for path in path_results:
                if path in self.index_data.path_to_node:
                    node = self.index_data.path_to_node[path]
                    # 路径前缀搜索应该返回文件节点，而不是目录节点
                    # 但如果查询完全匹配一个目录，则返回该目录下的所有文件
                    if node.is_dir and node.path == query:
                        # 查询完全匹配一个目录，返回其子节点
                        nodes.extend(node.children.values())
                    elif not node.is_dir:
                        # 这是一个文件节点，且路径匹配前缀
                        nodes.append(node)
            # 按路径排序
            nodes.sort(key=lambda x: x.path)
            if nodes:
                return nodes

        # 如果前缀搜索没有找到结果，尝试查找以查询开头的所有路径
        # This is to handle cases where Trie may not be properly indexed
        nodes = []
        for path, node in self.index_data.path_to_node.items():
            if path.startswith(query) and path != query:
                # 只返回文件节点，不返回目录节点
                if not node.is_dir:
                    nodes.append(node)
        nodes.sort(key=lambda x: x.path)
        return nodes

    def _search_name_prefix(
        self, query: str, contextual_base_path: str
    ) -> list[IndexNode]:
        """
        执行名称前缀搜索（上下文感知的两阶段搜索）

        Args:
            query: 规范化后的查询字符串（不包含路径分隔符）
            contextual_base_path: 规范化后的上下文路径

        Returns:
            匹配的IndexNode列表
        """
        # 阶段一：上下文搜索
        context_node = self.index_data.path_to_node.get(contextual_base_path)
        if context_node and context_node.is_dir:
            matching_nodes = []
            query_lower = query.lower()
            for child in context_node.children.values():
                if child.name.lower().startswith(query_lower):
                    # 如果匹配的节点是目录且名称完全匹配，返回其子节点
                    if child.is_dir and child.name.lower() == query_lower:
                        matching_nodes.extend(list(child.children.values()))
                    else:
                        matching_nodes.append(child)
            if matching_nodes:
                # 按名称排序
                matching_nodes.sort(key=lambda x: x.name)
                return matching_nodes

        # 阶段二：全局搜索
        # 首先检查是否查询精确匹配一个目录名
        exact_match_node = self.index_data.path_to_node.get(query)
        if exact_match_node and exact_match_node.is_dir:
            # 查询完全匹配一个目录，返回其子节点
            nodes = list(exact_match_node.children.values())
            nodes.sort(key=lambda x: x.path)
            return nodes

        # Use name_trie for prefix search
        name_results = self.index_data.name_trie.starts_with(query)
        if name_results:
            # name_trie stores path lists, need to merge and deduplicate
            path_set = set()
            for path_list in name_results:
                if isinstance(path_list, list):
                    path_set.update(path_list)

            # Get corresponding IndexNode objects from path_to_node
            nodes = []
            for path in path_set:
                if path in self.index_data.path_to_node:
                    nodes.append(self.index_data.path_to_node[path])
            # 按路径排序
            nodes.sort(key=lambda x: x.path)
            return nodes

        return []

    def _search_in_memory(
        self, query: str, contextual_base_path: str, is_listing_request: bool
    ) -> list[IndexNode]:
        """
        在内存索引中搜索

        Args:
            query: 规范化后的查询字符串
            contextual_base_path: 规范化后的上下文路径
            is_listing_request: 是否为目录列出请求

        Returns:
            匹配的IndexNode列表
        """
        # 1. Directory content listing
        if is_listing_request:
            return self._search_directory_listing(query)

        # 2. Path prefix search or name prefix search
        return self._search_by_name_or_path(query, contextual_base_path)

    async def _fallback_path_scan(
        self, query: str, contextual_base_path: str, is_listing_request: bool
    ) -> list[IndexNode]:
        """
        路径前缀搜索的回退扫描机制

        Args:
            query: 规范化后的查询字符串（包含路径分隔符）
            contextual_base_path: 规范化后的上下文路径
            is_listing_request: 是否为目录列出请求

        Returns:
            匹配的IndexNode列表
        """
        # 定位父级目录
        parent_path = "/".join(query.split("/")[:-1]) if "/" in query else ""

        # 检查父级目录在磁盘上是否存在
        parent_full_path = Path(self.root_path) / parent_path
        if parent_full_path.exists() and parent_full_path.is_dir():
            # 异步执行单层扫描
            scan_results = await asyncio.to_thread(self._scan_directory, parent_full_path)
            
            # 批量创建节点并添加到索引
            for name, relative_path, is_dir, mtime, is_core in scan_results:
                node = self._create_index_node(
                    name,
                    relative_path,
                    is_dir,
                    mtime,
                    is_core,
                )
                self._add_node_to_index(node)

        # 重新执行搜索，但限制为仅内存搜索，避免递归调用回退扫描
        if is_listing_request:
            # 如果是目录列出请求，使用目录列出逻辑
            return self._search_directory_listing(query)
        elif "/" in query:
            return self._search_path_prefix(query)
        else:
            return self._search_name_prefix(query, contextual_base_path)

    async def _fallback_name_scan(
        self, query: str, contextual_base_path: str, is_listing_request: bool
    ) -> list[IndexNode]:
        """
        名称前缀搜索的回退扫描机制

        Args:
            query: 规范化后的查询字符串（不包含路径分隔符）
            contextual_base_path: 规范化后的上下文路径
            is_listing_request: 是否为目录列出请求

        Returns:
            匹配的IndexNode列表
        """
        # 检查空查询
        if not query:
            return []
            
        # 检查是否已经有其他任务完成了扫描
        # 先尝试搜索，如果已经有结果就直接返回
        temp_results = self._search_in_memory(
            query, contextual_base_path, is_listing_request
        )
        if temp_results:
            return temp_results

        # 使用异步锁防止并发的昂贵磁盘扫描
        async with self._sync_scan_lock:
            # 再次检查，避免在获取锁期间其他任务已完成扫描
            temp_results = self._search_in_memory(
                query, contextual_base_path, is_listing_request
            )
            if temp_results:
                return temp_results

            # 异步执行全局扫描
            scan_results = await asyncio.to_thread(self._scan_global, query)
            
            # 批量创建节点并添加到索引
            for name, relative_path, is_dir, mtime, is_core in scan_results:
                node = self._create_index_node(
                    name,
                    relative_path,
                    is_dir,
                    mtime,
                    is_core,
                )
                self._add_node_to_index(node)

        # 重新执行名称前缀搜索，但限制为仅内存搜索，避免递归调用回退扫描
        if "/" in query:
            return self._search_path_prefix(query)
        else:
            return self._search_name_prefix(query, contextual_base_path)

    async def _fallback_scan(
        self, query: str, contextual_base_path: str, is_listing_request: bool
    ) -> list[IndexNode]:
        """
        回退扫描机制

        Args:
            query: 规范化后的查询字符串
            contextual_base_path: 规范化后的上下文路径
            is_listing_request: 是否为目录列出请求

        Returns:
            匹配的IndexNode列表
        """
        # 路径前缀搜索未命中，执行目录单层扫描
        if "/" in query:
            return await self._fallback_path_scan(
                query, contextual_base_path, is_listing_request
            )

        # 名称前缀搜索未命中，执行文件名全局扫描
        return await self._fallback_name_scan(
            query, contextual_base_path, is_listing_request
        )

    async def _handle_gitignore_changed(self) -> None:
        """
        异步处理.gitignore文件变化事件
        """
        try:
            # Reconstruct gitignore PathSpec
            await self._construct_gitignore_pathspec()
            # 重新扫描索引以应用新的忽略规则
            self._rescan_index_for_ignore_rules()
        except Exception:
            # 忽略重建过程中的错误
            pass

    def _rescan_index_for_ignore_rules(self) -> None:
        """
        重新扫描索引以应用新的忽略规则
        根据新的.gitignore规则，移除被忽略的文件，添加不再被忽略的文件

        该方法在.gitignore文件发生变化时被调用，用于更新索引以反映新的忽略规则。
        它会遍历所有索引节点，检查它们是否应该被新的忽略规则忽略，如果是则从索引中移除。
        注意：对于不再被忽略的文件，我们不主动添加它们，因为它们可能已经被删除了，
        而且添加它们需要磁盘扫描。这些文件会在用户搜索时通过回退扫描机制重新发现。
        """
        # 创建需要移除的节点列表
        nodes_to_remove = []

        # 遍历所有索引节点
        for path, node in self.index_data.path_to_node.items():
            # 跳过根节点和核心节点
            if path == "" or node.is_core:
                continue

            # 检查节点是否应该被忽略
            try:
                # Match paths using new PathSpec
                if (
                    self._ignore_pathspec_static
                    and self._ignore_pathspec_static.match_file(path)
                ):
                    nodes_to_remove.append(path)
                    continue

                if self._ignore_pathspec_git and self._ignore_pathspec_git.match_file(
                    path
                ):
                    nodes_to_remove.append(path)
                    continue
            except Exception:
                # 忽略匹配过程中的错误
                continue

        # 移除被忽略的节点
        for path in nodes_to_remove:
            self._remove_node_from_index(path)

        # 注意：对于不再被忽略的文件，我们不主动添加它们
        # 因为它们可能已经被删除了，而且添加它们需要磁盘扫描
        # 这些文件会在用户搜索时通过回退扫描机制重新发现

    async def _async_handle_file_created(self, file_path: str) -> None:
        """
        异步处理文件创建事件

        Args:
            file_path: 创建的文件路径
        """
        try:
            # 确保路径是字符串类型
            file_path_str = str(file_path)

            # 计算相对于项目根目录的路径
            relative_path = Path(file_path_str).relative_to(self.root_path).as_posix()

            # 检查是否应该索引以及是否为核心区文件
            should_index, is_core = self._match_pathspec(relative_path, False)

            if should_index:
                # 获取文件的修改时间
                mtime = Path(file_path_str).stat().st_mtime

                # Create IndexNode object
                node = self._create_index_node(
                    Path(file_path_str).name,
                    relative_path,
                    False,  # 不是目录
                    mtime,
                    is_core,
                )

                # 添加到索引结构中
                self._add_node_to_index(node)
        except Exception:
            # 忽略无法处理的文件
            pass

    async def _async_handle_dir_created(self, dir_path: str) -> None:
        """
        异步处理目录创建事件

        Args:
            dir_path: 创建的目录路径
        """
        try:
            # 确保路径是字符串类型
            dir_path_str = str(dir_path)

            # 计算相对于项目根目录的路径
            relative_path = Path(dir_path_str).relative_to(self.root_path).as_posix()

            # 检查是否应该索引以及是否为核心区文件
            should_index, is_core = self._match_pathspec(relative_path, True)

            if should_index:
                # Create IndexNode object
                node = self._create_index_node(
                    Path(dir_path_str).name,
                    relative_path,
                    True,  # 是目录
                    0.0,  # Directory mtime is 0
                    is_core,
                )

                # 添加到索引结构中
                self._add_node_to_index(node)
        except Exception:
            # 忽略无法处理的目录
            pass

    async def _async_handle_file_deleted(self, file_path: str) -> None:
        """
        异步处理文件删除事件

        Args:
            file_path: 删除的文件路径
        """
        try:
            # 确保路径是字符串类型
            file_path_str = str(file_path)

            # 计算相对于项目根目录的路径
            relative_path = Path(file_path_str).relative_to(self.root_path).as_posix()

            # 从索引中移除节点
            self._remove_node_from_index(relative_path)
        except Exception:
            # 忽略无法处理的文件
            pass

    async def _async_handle_dir_deleted(self, dir_path: str) -> None:
        """
        异步处理目录删除事件

        Args:
            dir_path: 删除的目录路径
        """
        try:
            # 确保路径是字符串类型
            dir_path_str = str(dir_path)

            # 计算相对于项目根目录的路径
            relative_path = Path(dir_path_str).relative_to(self.root_path).as_posix()

            # 递归删除目录及其所有子节点
            self._remove_node_and_children(relative_path)
        except Exception:
            # 忽略无法处理的目录
            pass

    def _remove_node_and_children(self, path: str) -> None:
        """
        递归删除节点及其所有子节点

        该方法用于在目录被删除或移动时，从索引中移除该目录及其包含的所有文件和子目录。
        它首先收集所有需要删除的节点路径，然后按路径深度倒序排列，确保先删除子节点
        再删除父节点，以维护索引结构的完整性。

        Args:
            path: 要删除的节点路径
        """
        # 检查节点是否存在
        if path not in self.index_data.path_to_node:
            return

        # 首先收集所有需要删除的节点路径（包括当前节点和所有子孙节点）
        paths_to_delete = []
        self._collect_all_descendant_paths(path, paths_to_delete)

        # 按路径深度倒序排列，确保先删除子节点再删除父节点
        paths_to_delete.sort(key=lambda p: p.count('/'), reverse=True)

        # 删除所有收集到的节点
        for node_path in paths_to_delete:
            if node_path in self.index_data.path_to_node:
                self._remove_node_from_index(node_path)

    def _collect_all_descendant_paths(self, path: str, paths_list: list[str]) -> None:
        """
        收集节点及其所有子孙节点的路径

        该方法通过遍历所有索引节点，查找以指定路径为前缀的所有子节点路径，
        并将它们添加到提供的路径列表中。这包括直接子节点和间接子节点（孙节点等）。

        Args:
            path: 当前节点路径
            paths_list: 用于收集路径的列表
        """
        # 添加当前节点路径
        paths_list.append(path)

        # 遍历所有节点，查找以当前路径为前缀的子节点
        path_prefix = path + "/" if path else ""
        for node_path in list(self.index_data.path_to_node.keys()):
            # 检查是否是直接或间接子节点
            if node_path.startswith(path_prefix) and node_path != path:
                # 确保这是一个子孙节点，而不是其他路径的一部分
                node_path[len(path_prefix):]
                # 如果相对路径不包含额外的斜杠，说明是直接子节点
                # 如果包含斜杠，说明是间接子节点，也需要包含
                if node_path not in paths_list:
                    paths_list.append(node_path)

    async def _async_handle_file_modified(self, file_path: str) -> None:
        """
        异步处理文件修改事件

        Args:
            file_path: 修改的文件路径
        """
        try:
            # 确保路径是字符串类型
            file_path_str = str(file_path)

            # 计算相对于项目根目录的路径
            relative_path = Path(file_path_str).relative_to(self.root_path).as_posix()

            # 检查文件是否在索引中
            if relative_path in self.index_data.path_to_node:
                node = self.index_data.path_to_node[relative_path]
                # 更新文件的修改时间
                node.mtime = Path(file_path_str).stat().st_mtime
        except Exception:
            # 忽略无法处理的文件
            pass

    async def _async_handle_file_moved(self, src_path: str, dest_path: str) -> None:
        """
        异步处理文件移动/重命名事件

        Args:
            src_path: 源文件路径
            dest_path: 目标文件路径
        """
        try:
            # 确保路径是字符串类型
            src_path_str = str(src_path)
            dest_path_str = str(dest_path)

            # 计算相对于项目根目录的路径
            src_relative_path = (
                Path(src_path_str).relative_to(self.root_path).as_posix()
            )
            dest_relative_path = (
                Path(dest_path_str).relative_to(self.root_path).as_posix()
            )

            # 检查源文件是否在索引中
            if src_relative_path in self.index_data.path_to_node:
                # 移除旧节点
                self._remove_node_from_index(src_relative_path)

                # 检查目标文件是否应该索引
                should_index, is_core = self._match_pathspec(dest_relative_path, False)

                if should_index:
                    # 获取文件的修改时间
                    mtime = Path(dest_path_str).stat().st_mtime

                    # 创建新节点
                    node = self._create_index_node(
                        Path(dest_path_str).name,
                        dest_relative_path,
                        False,  # 不是目录
                        mtime,
                        is_core,
                    )

                    # 添加到索引结构中
                    self._add_node_to_index(node)
        except Exception:
            # 忽略无法处理的文件
            pass

    async def _async_handle_dir_moved(self, src_path: str, dest_path: str) -> None:
        """
        异步处理目录移动/重命名事件

        Args:
            src_path: 源目录路径
            dest_path: 目标目录路径
        """
        try:
            # 确保路径是字符串类型
            src_path_str = str(src_path)
            dest_path_str = str(dest_path)

            # 计算相对于项目根目录的路径
            src_relative_path = (
                Path(src_path_str).relative_to(self.root_path).as_posix()
            )
            dest_relative_path = (
                Path(dest_path_str).relative_to(self.root_path).as_posix()
            )

            # 检查源目录是否在索引中
            if src_relative_path in self.index_data.path_to_node:
                # 递归移除旧节点及其所有子节点
                self._remove_node_and_children(src_relative_path)

                # 检查目标目录是否应该索引
                should_index, is_core = self._match_pathspec(dest_relative_path, True)

                if should_index:
                    # 创建新节点
                    node = self._create_index_node(
                        Path(dest_path_str).name,
                        dest_relative_path,
                        True,  # 是目录
                        0.0,  # Directory mtime is 0
                        is_core,
                    )

                    # 添加到索引结构中
                    self._add_node_to_index(node)
                    
                    # 扫描目标目录中的文件并添加到索引中
                    dest_dir_path = Path(dest_path_str)
                    scan_results = await asyncio.to_thread(self._scan_directory, dest_dir_path)
                    for name, relative_path, is_dir, mtime, is_core in scan_results:
                        child_node = self._create_index_node(
                            name,
                            relative_path,
                            is_dir,
                            mtime,
                            is_core,
                        )
                        self._add_node_to_index(child_node)
        except Exception:
            # 忽略无法处理的目录
            pass

    def _remove_node_from_index(self, path: str) -> None:
        """
        从索引中移除节点

        该方法从所有相关的索引结构中移除指定路径的节点，包括：
        1. path_to_node字典 - 主索引
        2. path_trie - 路径前缀搜索加速器
        3. name_trie - 名称前缀搜索加速器
        4. dynamic_nodes_lru - 动态节点的LRU管理器
        5. 父节点的children字典 - 父子关系
        确保节点从所有索引结构中完全移除，维护索引的一致性。

        Args:
            path: 要移除的节点路径
        """
        # 检查节点是否存在
        if path not in self.index_data.path_to_node:
            return

        node = self.index_data.path_to_node[path]

        # Remove from path_to_node dictionary
        del self.index_data.path_to_node[path]

        # Remove from path_trie
        self.index_data.path_trie.delete(path)

        # Remove from name_trie
        existing_paths = self.index_data.name_trie.search(node.name)
        if existing_paths is not None:
            # 从路径列表中移除该路径
            if path in existing_paths:
                existing_paths.remove(path)
            # If the list is empty, remove the name from name_trie
            if not existing_paths:
                self.index_data.name_trie.delete(node.name)

        # Remove from dynamic_nodes_lru (if it's a dynamic node)
        if not node.is_core and path in self.index_data.dynamic_nodes_lru:
            del self.index_data.dynamic_nodes_lru[path]

        # Remove from parent node's children dictionary
        if node.parent and node.name in node.parent.children:
            del node.parent.children[node.name]

    def _normalize_input(
        self, query: str, contextual_base_path: str
    ) -> tuple[str, str, bool]:
        """
        两阶段输入规范化处理，确保所有路径操作都在项目根目录范围内进行。
        
        **限制说明**: query 和 contextual_base_path 参数均禁止使用 "/" 开头，
        确保所有路径都是相对于项目根目录的相对路径。

        Args:
            query: 用户输入的原始查询字符串（不能使用 "/" 开头）
            contextual_base_path: 用户发起搜索时所在的上下文目录（不能使用 "/" 开头）

        Returns:
            (normalized_query, normalized_context_path, is_listing_request) 元组
            
        Note:
            如果参数以 "/" 开头，将被视为无效输入并返回空字符串。
        """
        # Save original query to determine if it's a directory listing request
        original_query = query

        # 判断搜索类型
        is_listing_request = original_query.strip().endswith("/")

        # 阶段一：输入验证
        # 1. Validate that query does not start with "/"
        query = query.strip()
        if query.startswith("/"):
            return "", "", is_listing_request

        # 2. Validate that contextual_base_path does not start with "/"
        contextual_base_path = contextual_base_path.strip()
        if contextual_base_path.startswith("/"):
            return "", "", is_listing_request

        # Phase two: contextual_base_path validity validation
        # 1. Unify path separators
        contextual_base_path = contextual_base_path.replace("\\", "/")

        # 2. Path concatenation and parsing
        try:
            # 构建完整路径并解析
            full_context_path = Path(self.root_path) / contextual_base_path
            resolved_context_path = full_context_path.resolve()

            # 4. Security validation
            root_path_obj = Path(self.root_path).resolve()
            if not resolved_context_path.is_relative_to(root_path_obj):
                # 路径超出项目根目录范围，拒绝处理
                return "", "", is_listing_request

            # 提取相对于项目根目录的路径
            if resolved_context_path == root_path_obj:
                normalized_context_path = ""
            else:
                normalized_context_path = resolved_context_path.relative_to(
                    root_path_obj
                ).as_posix()

        except (ValueError, RuntimeError):
            # 路径解析失败，拒绝处理
            return "", "", is_listing_request

        # 阶段二：目标路径构建与规范化
        try:
            # 5. Preliminary query cleanup
            query = query.strip()
            query = query.replace("\\", "/")

            # 6. Build target absolute path
            # Process query relative to context path
            full_target_path = Path(self.root_path) / normalized_context_path / query

            resolved_target_path = full_target_path.resolve()

            # 7. Path resolution and security validation
            if not resolved_target_path.is_relative_to(root_path_obj):
                # 路径超出项目根目录范围，拒绝处理
                return "", "", is_listing_request

            # 8. Extract normalized query string
            if resolved_target_path == root_path_obj:
                normalized_query = ""
            else:
                normalized_query = resolved_target_path.relative_to(
                    root_path_obj
                ).as_posix()

            # 9. Format unification: Ensure no leading/trailing slashes
            normalized_query = normalized_query.strip("/")
            normalized_context_path = normalized_context_path.strip("/")

        except (ValueError, RuntimeError):
            # 路径解析失败，拒绝处理
            return "", "", is_listing_request

        return normalized_query, normalized_context_path, is_listing_request

    async def _wait_for_initialization(self) -> None:
        """
        等待初始化完成
        """
        while self._initializing:
            await asyncio.sleep(0.1)

    def _update_lru_for_nodes(self, nodes: list[IndexNode]) -> None:
        """
        更新节点的LRU状态

        该方法将指定节点列表中的所有非核心节点标记为最近访问，
        将它们移到LRU字典的末尾。这确保了经常访问的节点不会被过早淘汰。

        Args:
            nodes: 需要更新LRU状态的节点列表
        """
        current_time = time.time()
        for node in nodes:
            if not node.is_core:
                if node.path in self.index_data.dynamic_nodes_lru:
                    # Move node to end of LRU (mark as recently accessed)
                    del self.index_data.dynamic_nodes_lru[node.path]
                self.index_data.dynamic_nodes_lru[node.path] = current_time

    def _check_and_evict_lru(self) -> None:
        """
        检查并执行LRU淘汰

        该方法检查动态节点LRU字典中的节点数量，如果超过预设限制，
        则按LRU策略淘汰最久未访问的节点。淘汰数量为超出数量的110%，
        以确保不会频繁触发淘汰操作。
        """
        dynamic_nodes_count = len(self.index_data.dynamic_nodes_lru)
        if dynamic_nodes_count > self.DYNAMIC_NODES_LRU_LIMIT:
            # Calculate number of nodes to evict (110% of overflow count)
            overflow_count = dynamic_nodes_count - self.DYNAMIC_NODES_LRU_LIMIT
            evict_count = int(overflow_count * 1.1)

            # Select least recently accessed nodes from beginning of LRU dictionary for eviction
            nodes_to_evict = []
            for _ in range(evict_count):
                if self.index_data.dynamic_nodes_lru:
                    oldest_path = next(iter(self.index_data.dynamic_nodes_lru))
                    nodes_to_evict.append(oldest_path)
                    del self.index_data.dynamic_nodes_lru[oldest_path]

            # 从所有索引结构中移除被淘汰的节点
            for path in nodes_to_evict:
                self._remove_node_from_index(path)

    def _scan_and_process_gitignore_files(self) -> list[str]:
        """
        同步扫描并处理所有.gitignore文件
        
        Returns:
            处理后的所有.gitignore规则列表
        """
        gitignore_files = []
        # Recursively scan project root directory to locate all .gitignore files
        for gitignore_path in Path(self.root_path).rglob(".gitignore"):
            try:
                gitignore_files.append(gitignore_path)
            except Exception:
                # Ignore .gitignore files that cannot be processed
                continue

        # Process all .gitignore files
        all_lines = []
        for gitignore_path in gitignore_files:
            # 获取相对于项目根目录的目录
            try:
                relative_dir = gitignore_path.parent.relative_to(self.root_path)
            except Exception:
                # 如果无法计算相对路径，跳过该文件
                continue

            # Read .gitignore file
            rules = self._read_gitignore_file(gitignore_path)

            # 处理规则，添加正确的前缀
            processed_rules = self._process_gitignore_rules(rules, relative_dir)

            # 添加到总规则列表
            all_lines.extend(processed_rules)
            
        return all_lines

    def _scan_files(self) -> list[IndexNode]:
        """
        同步扫描文件
        
        Returns:
            IndexNode对象列表
        """
        results = []
        for file_path in Path(self.root_path).rglob("*"):
            try:
                # 计算相对于项目根目录的路径
                relative_path = file_path.relative_to(self.root_path).as_posix()

                # 检查是否应该索引以及是否为核心区文件
                should_index, is_core = self._match_pathspec(
                    relative_path, file_path.is_dir()
                )

                if should_index:
                    # Create IndexNode object
                    node = self._create_index_node(
                        file_path.name,
                        relative_path,
                        file_path.is_dir(),
                        file_path.stat().st_mtime if file_path.is_file() else 0.0,
                        is_core,
                    )
                    results.append(node)
            except Exception:
                # 忽略无法处理的文件
                continue
        return results

    def _scan_directory(self, parent_full_path: Path) -> list[tuple[str, str, bool, float, bool]]:
        """
        同步扫描目录
        
        Args:
            parent_full_path: 父目录的完整路径
            
        Returns:
            (name, relative_path, is_dir, mtime, is_core)元组列表
        """
        results = []
        try:
            for item in parent_full_path.iterdir():
                try:
                    relative_path = item.relative_to(self.root_path).as_posix()
                    # 检查是否应该索引以及是否为核心区文件
                    should_index, is_core = self._match_pathspec(
                        relative_path, item.is_dir()
                    )

                    if (
                        should_index
                        and relative_path not in self.index_data.path_to_node
                    ):
                        results.append((
                            item.name,
                            relative_path,
                            item.is_dir(),
                            item.stat().st_mtime if item.is_file() else 0.0,
                            is_core
                        ))
                except Exception:
                    continue
        except Exception:
            pass
        return results

    def _scan_global(self, query: str) -> list[tuple[str, str, bool, float, bool]]:
        """
        同步全局扫描
        
        Args:
            query: 查询字符串
            
        Returns:
            (name, relative_path, is_dir, mtime, is_core)元组列表
        """
        results = []
        try:
            query_lower = query.lower()
            for item in Path(self.root_path).rglob("*"):
                try:
                    if item.name.lower().startswith(query_lower):
                        relative_path = item.relative_to(self.root_path).as_posix()

                        # 检查是否应该索引以及是否为核心区文件
                        should_index, is_core = self._match_pathspec(
                            relative_path, item.is_dir()
                        )

                        if (
                            should_index
                            and relative_path not in self.index_data.path_to_node
                        ):
                            results.append((
                                item.name,
                                relative_path,
                                item.is_dir(),
                                item.stat().st_mtime if item.is_file() else 0.0,
                                is_core
                            ))
                except Exception:
                    continue
        except Exception:
            pass
        return results
