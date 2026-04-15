"""Configuration management for CBETA CLI.

支持从配置文件加载默认设置，包括：
- API 地址
- 默认搜索参数（藏经、部类、返回数量等）
- 输出格式偏好
"""

import os
import json
import copy
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# 默认配置文件位置
DEFAULT_CONFIG_DIR = Path.home() / ".cbeta"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"

# 默认配置
DEFAULT_CONFIG = {
    "api": {
        "base_url": "https://api.cbetaonline.cn",
        "timeout": 30,
        "referer": "cli-anything-cbeta"
    },
    "defaults": {
        "rows": 10,
        "canon": None,
        "category": None,
        "dynasty": None,
        "output_format": "text"  # text, json, table
    },
    "display": {
        "color": True,
        "verbose": False,
        "show_fields": ["work", "title", "category", "juan", "cjk_chars"]
    },
    "cache": {
        "enabled": True,
        "expire_seconds": 3600,
        "max_size_mb": 100
    },
    "logging": {
        "level": "INFO",
        "rotation_days": 1,
        "backup_count": 30
    }
}


class Config:
    """配置管理类."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or DEFAULT_CONFIG_FILE
        self._config = copy.deepcopy(DEFAULT_CONFIG)
        self._loaded = False

    def load(self) -> Dict[str, Any]:
        """加载配置文件."""
        if self._loaded:
            return self._config

        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    if self.config_path.suffix in [".yaml", ".yml"]:
                        loaded = yaml.safe_load(f) or {}
                    else:
                        loaded = json.load(f)

                # 合并配置（深度合并）
                self._merge_config(loaded)
            except Exception as e:
                print(f"警告: 加载配置文件失败: {e}")

        self._loaded = True
        return self._config

    def _merge_config(self, loaded: Dict[str, Any]):
        """深度合并配置."""
        for key, value in loaded.items():
            if key in self._config and isinstance(self._config[key], dict) and isinstance(value, dict):
                self._config[key].update(value)
            else:
                self._config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（支持嵌套键，如 'api.base_url'）."""
        self.load()
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """设置配置项."""
        self.load()
        keys = key.split(".")
        target = self._config
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value

    def save(self):
        """保存配置到文件."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            if self.config_path.suffix in [".yaml", ".yml"]:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            else:
                json.dump(self._config, f, indent=2, ensure_ascii=False)

    def reset(self):
        """重置为默认配置."""
        self._config = copy.deepcopy(DEFAULT_CONFIG)
        self._loaded = True

    def show(self) -> str:
        """显示当前配置."""
        self.load()
        lines = ["当前配置:"]
        for section, values in self._config.items():
            lines.append(f"\n[{section}]")
            if isinstance(values, dict):
                for k, v in values.items():
                    lines.append(f"  {k}: {v}")
            else:
                lines.append(f"  {values}")
        return "\n".join(lines)

    @property
    def base_url(self) -> str:
        """获取 API base_url."""
        return self.get("api.base_url", DEFAULT_CONFIG["api"]["base_url"])

    @property
    def default_rows(self) -> int:
        """获取默认返回数量."""
        return self.get("defaults.rows", DEFAULT_CONFIG["defaults"]["rows"])

    @property
    def default_canon(self) -> Optional[str]:
        """获取默认藏经."""
        return self.get("defaults.canon")

    @property
    def output_format(self) -> str:
        """获取输出格式."""
        return self.get("defaults.output_format", "text")

    @property
    def cache_enabled(self) -> bool:
        """获取缓存是否启用."""
        return self.get("cache.enabled", True)

    @property
    def cache_expire_seconds(self) -> int:
        """获取缓存过期时间（秒）."""
        return self.get("cache.expire_seconds", 3600)

    @property
    def cache_max_size_mb(self) -> int:
        """获取缓存最大大小（MB）."""
        return self.get("cache.max_size_mb", 100)

    @property
    def logging_level(self) -> str:
        """获取日志级别."""
        return self.get("logging.level", "INFO")

    @property
    def logging_rotation_days(self) -> int:
        """获取日志分割间隔（天）."""
        return self.get("logging.rotation_days", 1)

    @property
    def logging_backup_count(self) -> int:
        """获取日志保留数量."""
        return self.get("logging.backup_count", 30)


# 全局配置实例
_config_instance: Optional[Config] = None


def get_config(config_path: Optional[Path] = None) -> Config:
    """获取全局配置实例."""
    global _config_instance
    if _config_instance is None or config_path:
        _config_instance = Config(config_path)
    return _config_instance


def create_default_config():
    """创建默认配置文件."""
    config = Config()
    config.reset()
    config.save()
    print(f"已创建默认配置文件: {config.config_path}")
    print(config.show())