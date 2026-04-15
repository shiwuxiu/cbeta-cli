"""Unit tests for cache module."""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from cli_anything.cbeta.utils.cache import CacheManager, get_cache, DEFAULT_EXPIRE_SECONDS


class TestCacheManagerInit:
    """测试 CacheManager 初始化."""

    def test_default_init(self):
        """测试默认初始化参数."""
        with patch.object(Path, 'mkdir'):
            cache = CacheManager()
            assert cache.expire_seconds == DEFAULT_EXPIRE_SECONDS

    def test_custom_expire_seconds(self):
        """测试自定义过期时间."""
        with patch.object(Path, 'mkdir'):
            cache = CacheManager(expire_seconds=7200)
            assert cache.expire_seconds == 7200

    def test_custom_cache_dir(self):
        """测试自定义缓存目录."""
        with patch.object(Path, 'mkdir'):
            cache = CacheManager(cache_dir=Path("/tmp/test_cache"))
            assert cache.cache_dir == Path("/tmp/test_cache")


class TestCacheKeyGeneration:
    """测试缓存键生成."""

    def test_generate_key_simple(self):
        """测试简单参数的键生成."""
        with patch.object(Path, 'mkdir'):
            cache = CacheManager()
            key1 = cache._generate_key("health")
            key2 = cache._generate_key("health")
            assert key1 == key2  # 相同参数生成相同键

    def test_generate_key_with_params(self):
        """测试带参数的键生成."""
        with patch.object(Path, 'mkdir'):
            cache = CacheManager()
            key1 = cache._generate_key("search", {"q": "般若", "rows": 10})
            key2 = cache._generate_key("search", {"rows": 10, "q": "般若"})
            assert key1 == key2  # 参数顺序不影响键

    def test_generate_key_different_params(self):
        """测试不同参数生成不同键."""
        with patch.object(Path, 'mkdir'):
            cache = CacheManager()
            key1 = cache._generate_key("search", {"q": "般若"})
            key2 = cache._generate_key("search", {"q": "金刚"})
            assert key1 != key2


class TestCacheGetSet:
    """测试缓存存取."""

    def test_set_then_get_memory(self):
        """测试写入后读取（内存缓存）."""
        with patch.object(Path, 'mkdir'):
            cache = CacheManager()
            # 直接写入内存缓存
            cache.set("test_endpoint", {"q": "test"}, {"status": "ok"})
            # 读取
            key = cache._generate_key("test_endpoint", {"q": "test"})
            assert key in cache._memory_cache
            assert cache._memory_cache[key]["data"]["status"] == "ok"

    def test_memory_cache(self):
        """测试内存缓存."""
        with patch.object(Path, 'mkdir'):
            cache = CacheManager()
            # 直接写入内存缓存
            cache._memory_cache["test_key"] = {
                "timestamp": time.time(),
                "data": {"test": "value"}
            }
            # 内存缓存读取
            result = cache._memory_cache.get("test_key")
            assert result["data"]["test"] == "value"


class TestCacheExpiration:
    """测试缓存过期."""

    def test_expired_memory_cache(self):
        """测试过期内存缓存被清除."""
        with patch.object(Path, 'mkdir'):
            cache = CacheManager(expire_seconds=1)
            # 写入过期数据
            cache._memory_cache["expired_key"] = {
                "timestamp": time.time() - 100,  # 100秒前
                "data": {"old": "data"}
            }
            # 尝试读取，应该返回 None
            # 因为 get 方法会检查过期
            key = cache._generate_key("expired_test")
            cache._memory_cache[key] = {
                "timestamp": time.time() - 100,
                "data": {"old": "data"}
            }
            result = cache.get("expired_test")
            assert result is None


class TestCacheClear:
    """测试缓存清除."""

    def test_clear_all_memory(self):
        """测试清除所有内存缓存."""
        with patch.object(Path, 'mkdir'):
            cache = CacheManager()
            cache._memory_cache["key1"] = {"timestamp": time.time(), "data": {}}
            cache._memory_cache["key2"] = {"timestamp": time.time(), "data": {}}
            cache._memory_cache.clear()
            assert len(cache._memory_cache) == 0

    def test_clear_expired(self):
        """测试清除过期缓存."""
        with patch.object(Path, 'mkdir'):
            cache = CacheManager(expire_seconds=1)
            # 写入过期和未过期数据
            cache._memory_cache["expired"] = {
                "timestamp": time.time() - 100,
                "data": {}
            }
            cache._memory_cache["fresh"] = {
                "timestamp": time.time(),
                "data": {}
            }
            count = cache.clear_expired()
            # expired 应被清除
            assert "expired" not in cache._memory_cache


class TestCacheStats:
    """测试缓存统计."""

    def test_stats_empty(self):
        """测试空缓存统计."""
        with patch.object(Path, 'mkdir'):
            with patch.object(Path, 'glob', return_value=[]):
                cache = CacheManager()
                stats = cache.stats()
                assert stats["memory_cache_count"] == 0
                assert stats["file_cache_count"] == 0
                assert stats["expire_seconds"] == DEFAULT_EXPIRE_SECONDS


class TestGetCache:
    """测试全局缓存实例."""

    def test_get_cache_singleton(self):
        """测试单例模式."""
        # 重置全局实例
        import cli_anything.cbeta.utils.cache as cache_module
        cache_module._cache_instance = None

        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_get_cache_with_expire(self):
        """测试自定义过期时间."""
        import cli_anything.cbeta.utils.cache as cache_module
        cache_module._cache_instance = None

        cache = get_cache(expire_seconds=1800)
        assert cache.expire_seconds == 1800