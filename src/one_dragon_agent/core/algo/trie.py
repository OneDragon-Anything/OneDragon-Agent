from typing import Any


class TrieNode:
    """
    Trie树的节点
    """

    def __init__(self) -> None:
        """
        初始化TrieNode
        """
        self.children: dict[str, TrieNode] = {}
        self.is_end_of_word: bool = False
        self.data: Any = None


class Trie:
    """
    Trie树(前缀树)的实现

    用于高效存储和检索字符串键的树形数据结构。
    """

    def __init__(self) -> None:
        """
        初始化Trie树
        """
        self.root: TrieNode = TrieNode()

    def insert(self, key: str, data: Any = None) -> None:
        """
        向Trie树中插入一个键值对

        Args:
            key: 要插入的键（字符串）
            data: 与键关联的数据。如果未提供，则默认为键本身。
        """
        if data is None:
            data = key

        node = self.root
        for char in key:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.data = data

    def search(self, key: str) -> Any | None:
        """
        在Trie树中搜索一个键

        Args:
            key: 要搜索的键（字符串）

        Returns:
            如果找到键，返回关联的数据；否则返回None。
        """
        node = self.root
        for char in key:
            if char not in node.children:
                return None
            node = node.children[char]
        if node.is_end_of_word:
            return node.data
        return None

    def starts_with(self, prefix: str) -> list[Any]:
        """
        查找所有以给定前缀开头的键关联的数据

        Args:
            prefix: 要查找的前缀（字符串）

        Returns:
            一个包含所有匹配键关联数据的列表。
        """
        results: list[Any] = []

        # 首先找到前缀的最后一个节点
        node = self.root
        for char in prefix:
            if char not in node.children:
                return results  # 前缀不存在，直接返回空列表
            node = node.children[char]

        # 从该节点开始深度优先遍历，收集所有数据
        self._dfs_collect_data(node, results)
        return results

    def _dfs_collect_data(self, node: TrieNode, results: list[Any]) -> None:
        """
        深度优先遍历，收集所有以当前节点为根的子树中，标记为单词结尾的节点的数据

        Args:
            node: 当前遍历的节点
            results: 用于收集数据的列表
        """
        if node.is_end_of_word:
            results.append(node.data)
        for child_node in node.children.values():
            self._dfs_collect_data(child_node, results)

    def delete(self, key: str) -> bool:
        """
        从Trie树中删除一个键

        Args:
            key: 要删除的键（字符串）

        Returns:
            如果键存在并被成功删除，返回True；否则返回False。
        """
        return self._delete_helper(self.root, key, 0)

    def _delete_helper(self, current_node: TrieNode, key_str: str, index: int) -> bool:
        """
        递归辅助函数，用于删除键

        Args:
            current_node: 当前处理的节点
            key_str: 要删除的键
            index: 当前处理的字符在键中的索引

        Returns:
            如果当前子树可以被删除（即它不包含任何其他键的结尾），返回True；否则返回False。
        """
        # 基本情况：已经到达键的末尾
        if index == len(key_str):
            # 检查键是否真的存在
            if not current_node.is_end_of_word:
                return False  # 键不存在

            # 标记为非单词结尾
            current_node.is_end_of_word = False

            # 如果当前节点没有子节点，可以删除它
            return len(current_node.children) == 0

        # 获取当前字符
        char = key_str[index]

        # 检查字符是否在子节点中
        if char not in current_node.children:
            return False  # 键不存在

        # 递归处理子节点
        child_node = current_node.children[char]
        should_delete_child = self._delete_helper(child_node, key_str, index + 1)

        # 如果子树应该被删除，则从当前节点中移除它
        if should_delete_child:
            del current_node.children[char]
            # 如果当前节点不是单词结尾且没有其他子节点，则当前节点也可以被删除
            return not current_node.is_end_of_word and len(current_node.children) == 0

        # 子树不应该被删除（因为它包含其他键）
        return False
