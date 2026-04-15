"""Cache system for CBETA CLI.

支持内存缓存和文件缓存：
- 内存缓存: functools.lru_cache 用于短时缓存
- 文件缓存: JSON 文件缓存，可持久化
- 缓存位置: ~/.cbeta/cache/
- 默认过期时间: 1 小时
"""

import os
import json
import hashlib
import time
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any, Optional, Callable
from datetime import datetime


# 默认缓存目录
DEFAULT_CACHE_DIR = Path.home() / ".cbeta" / "cache"
DEFAULT_EXPIRE_SECONDS = 3600  # 1 小时


class CacheManager:
    """缓存管理类."""

    def __init__(self, cache_dir: Optional[Path] = None, expire_seconds: int = DEFAULT_EXPIRE_SECONDS):
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.expire_seconds = expire_seconds

        # 内存缓存（用于高频请求）
        self._memory_cache: Dict[str, Dict] = {}

    def _generate_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """生成缓存键."""
        params_str = json.dumps(params or {}, sort_keys=True)
        hash_str = hashlib.md5(f"{endpoint}:{params_str}".encode()).hexdigest()
        return hash_str

    def _get_cache_file(self, key: str) -> Path:
        """获取缓存文件路径."""
        return self.cache_dir / f"{key}.json"

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """获取缓存数据."""
        key = self._generate_key(endpoint, params)

        # 先检查内存缓存
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if time.time() - entry["timestamp"] < self.expire_seconds:
                return entry["data"]
            else:
                del self._memory_cache[key]

        # 检查文件缓存
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            try:
                entry = json.loads(cache_file.read_text(encoding="utf-8"))
                if time.time() - entry["timestamp"] < self.expire_seconds:
                    # 同时更新内存缓存
                    self._memory_cache[key] = entry
                    return entry["data"]
                else:
                    # 过期，删除缓存
                    cache_file.unlink(missing_ok=True)
            except:
                pass

        return None

    def set(self, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> None:
        """设置缓存数据."""
        key = self._generate_key(endpoint, params)
        entry = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "endpoint": endpoint,
            "params": params,
            "data": data
        }

        # 写入内存缓存
        self._memory_cache[key] = entry

        # 写入文件缓存
        cache_file = self._get_cache_file(key)
        cache_file.write_text(
            json.dumps(entry, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def delete(self, endpoint: str, params: Optional[Dict] = None) -> bool:
        """删除缓存."""
        key = self._generate_key(endpoint, params)

        # 删除内存缓存
        if key in self._memory_cache:
            del self._memory_cache[key]

        # 删除文件缓存
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            cache_file.unlink()
            return True
        return False

    def clear_all(self) -> int:
        """清除所有缓存."""
        # 清除内存缓存
        count = len(self._memory_cache)
        self._memory_cache.clear()

        # 清除文件缓存
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1

        return count

    def clear_expired(self) -> int:
        """清除过期缓存."""
        count = 0
        current_time = time.time()

        # 清除内存过期缓存
        expired_keys = [
            k for k, v in self._memory_cache.items()
            if current_time - v["timestamp"] >= self.expire_seconds
        ]
        for key in expired_keys:
            del self._memory_cache[key]
            count += 1

        # 清除文件过期缓存
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                entry = json.loads(cache_file.read_text(encoding="utf-8"))
                if current_time - entry["timestamp"] >= self.expire_seconds:
                    cache_file.unlink()
                    count += 1
            except:
                cache_file.unlink()
                count += 1

        return count

    def stats(self) -> Dict:
        """获取缓存统计."""
        memory_count = len(self._memory_cache)
        file_count = len(list(self.cache_dir.glob("*.json")))
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.json"))

        return {
            "memory_cache_count": memory_count,
            "file_cache_count": file_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "expire_seconds": self.expire_seconds
        }

    def cached_request(self, request_func: Callable, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """缓存包装器 - 如果缓存存在则返回缓存，否则执行请求并缓存结果."""
        cached = self.get(endpoint, params)
        if cached is not None:
            return cached

        result = request_func(endpoint, params)
        self.set(endpoint, params, result)
        return result


# 全局缓存实例
_cache_instance: Optional[CacheManager] = None


def get_cache(expire_seconds: Optional[int] = None) -> CacheManager:
    """获取全局缓存实例，从配置读取默认过期时间."""
    global _cache_instance
    if _cache_instance is None:
        # 从配置读取过期时间
        if expire_seconds is None:
            try:
                from cli_anything.cbeta.utils.config import get_config
                config = get_config()
                expire_seconds = config.cache_expire_seconds
            except:
                expire_seconds = DEFAULT_EXPIRE_SECONDS
        _cache_instance = CacheManager(expire_seconds=expire_seconds)
    return _cache_instance


def cached(func: Callable) -> Callable:
    """装饰器：为函数添加缓存."""
    cache = get_cache()

    def wrapper(endpoint: str, params: Optional[Dict] = None, use_cache: bool = True, **kwargs):
        if use_cache:
            cached_data = cache.get(endpoint, params)
            if cached_data is not None:
                return cached_data

        result = func(endpoint, params, **kwargs)

        if use_cache:
            cache.set(endpoint, params, result)

        return result

    return wrapper