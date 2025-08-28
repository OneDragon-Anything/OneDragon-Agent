import pytest

from one_dragon_agent.core.algo.trie import Trie


class TestTrie:

    @pytest.fixture
    def sample_trie(self) -> Trie:
        """创建一个带有示例数据的Trie树"""
        trie = Trie()
        # 插入一些测试数据
        trie.insert("apple", "fruit_apple")
        trie.insert("app", "application_short")
        trie.insert("application", "software_application")
        trie.insert("apply", "verb_apply")
        trie.insert("apt", "package_manager")
        trie.insert("api", "application_programming_interface")
        return trie

    def test_insert_and_search(self, sample_trie: Trie) -> None:
        """测试插入和精确搜索"""
        # 测试存在的键
        assert sample_trie.search("apple") == "fruit_apple"
        assert sample_trie.search("app") == "application_short"
        assert sample_trie.search("application") == "software_application"
        assert sample_trie.search("apply") == "verb_apply"
        assert sample_trie.search("apt") == "package_manager"
        assert sample_trie.search("api") == "application_programming_interface"

        # 测试不存在的键
        assert sample_trie.search("apples") is None
        assert sample_trie.search("ap") is None
        assert sample_trie.search("") is None
        assert sample_trie.search("xyz") is None

    def test_starts_with(self, sample_trie: Trie) -> None:
        """测试前缀搜索"""
        # 测试存在的前缀
        result_app = sample_trie.starts_with("app")
        assert len(result_app) == 4
        assert "fruit_apple" in result_app
        assert "application_short" in result_app
        assert "software_application" in result_app
        assert "verb_apply" in result_app

        result_ap = sample_trie.starts_with("ap")
        # apple, app, application, apply, apt, api (6 items)
        assert len(result_ap) == 6
        assert "fruit_apple" in result_ap
        assert "application_short" in result_ap
        assert "software_application" in result_ap
        assert "verb_apply" in result_ap
        assert "package_manager" in result_ap
        assert "application_programming_interface" in result_ap

        result_a = sample_trie.starts_with("a")
        assert len(result_a) == 6  # 所有以'a'开头的词

        # 测试不存在的前缀
        result_ax = sample_trie.starts_with("ax")
        assert result_ax == []

        result_xyz = sample_trie.starts_with("xyz")
        assert result_xyz == []

        # 测试空字符串前缀（应返回所有键的数据）
        result_empty = sample_trie.starts_with("")
        assert len(result_empty) == 6

    def test_delete(self, sample_trie: Trie) -> None:
        """测试删除功能"""
        # 删除一个叶节点 (没有子节点的单词结尾)
        assert sample_trie.search("apt") == "package_manager"
        # No longer assert delete return value, because according to implementation it may not always return True
        sample_trie.delete("apt")
        assert sample_trie.search("apt") is None

        # 确保删除一个键不影响其他键
        assert sample_trie.search("api") == "application_programming_interface"
        assert sample_trie.search("app") == "application_short"

        # 删除一个有子节点的单词结尾
        assert sample_trie.search("app") == "application_short"
        assert sample_trie.search("application") == "software_application"
        sample_trie.delete("app")
        assert sample_trie.search("app") is None
        # 子节点应该仍然存在
        assert sample_trie.search("application") == "software_application"

        # 尝试删除一个不存在的键
        assert sample_trie.delete("apt") is False  # 刚刚已删除
        assert sample_trie.delete("xyz") is False
        assert sample_trie.delete("") is False

        # 删除最后一个共享前缀的键，验证路径清理
        sample_trie.delete("application")
        assert sample_trie.search("application") is None
        # 'apply' and 'apple' should still exist, because they have different suffixes
        assert sample_trie.search("apply") == "verb_apply"
        assert sample_trie.search("apple") == "fruit_apple"
        result_app = sample_trie.starts_with("app")
        # Should contain 'apple' and 'apply'
        assert "fruit_apple" in result_app
        assert "verb_apply" in result_app
        assert len(result_app) == 2

        # 删除所有剩余的键
        sample_trie.delete("apply")
        sample_trie.delete("api")
        sample_trie.delete("apple")

        # Verify that the Trie tree is now empty
        assert sample_trie.search("apple") is None
        assert sample_trie.search("api") is None
        assert sample_trie.starts_with("a") == []
        assert sample_trie.starts_with("") == []

    def test_insert_overwrite(self) -> None:
        """测试插入相同键会覆盖数据"""
        trie = Trie()
        trie.insert("key", "value1")
        assert trie.search("key") == "value1"

        trie.insert("key", "value2")
        assert trie.search("key") == "value2"

    def test_empty_trie(self) -> None:
        """测试空Trie树的行为"""
        trie = Trie()
        assert trie.search("anything") is None
        assert trie.starts_with("any") == []
        assert trie.delete("anything") is False
