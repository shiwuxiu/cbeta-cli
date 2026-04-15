"""Unit tests for config module."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from cli_anything.cbeta.utils.config import Config, DEFAULT_CONFIG, get_config


class TestConfigInit:
    """测试 Config 初始化."""

    def test_default_init(self):
        """测试默认初始化."""
        config = Config()
        assert config._config == DEFAULT_CONFIG.copy()
        assert not config._loaded

    def test_custom_path(self):
        """测试自定义配置路径."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = Path(f.name)

        config = Config(temp_path)
        assert config.config_path == temp_path

        # 清理
        temp_path.unlink(missing_ok=True)


class TestConfigLoad:
    """测试配置加载."""

    def test_load_default_when_no_file(self):
        """测试无配置文件时加载默认配置."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "nonexistent.yaml"
            config = Config(temp_path)
            result = config.load()

            assert result == DEFAULT_CONFIG.copy()
            assert config._loaded

    def test_load_yaml_file(self):
        """测试加载 YAML 配置文件."""
        yaml_content = """
api:
  base_url: https://custom.api.com
  timeout: 60
defaults:
  rows: 50
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "config.yaml"
            temp_path.write_text(yaml_content, encoding="utf-8")

            config = Config(temp_path)
            result = config.load()

            assert result["api"]["base_url"] == "https://custom.api.com"
            assert result["api"]["timeout"] == 60
            assert result["defaults"]["rows"] == 50

    def test_load_json_file(self):
        """测试加载 JSON 配置文件."""
        import json

        json_content = {
            "api": {"base_url": "https://json.api.com"},
            "defaults": {"rows": 100}
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "config.json"
            temp_path.write_text(json.dumps(json_content), encoding="utf-8")

            config = Config(temp_path)
            result = config.load()

            assert result["api"]["base_url"] == "https://json.api.com"
            assert result["defaults"]["rows"] == 100

    def test_merge_config(self):
        """测试配置合并."""
        yaml_content = """
defaults:
  rows: 30
  canon: X
new_section:
  new_key: new_value
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "config.yaml"
            temp_path.write_text(yaml_content, encoding="utf-8")

            config = Config(temp_path)
            result = config.load()

            # 默认配置被更新
            assert result["defaults"]["rows"] == 30
            assert result["defaults"]["canon"] == "X"
            # 新配置项添加
            assert result["new_section"]["new_key"] == "new_value"
            # 未改变的配置项保留
            assert result["api"]["base_url"] == DEFAULT_CONFIG["api"]["base_url"]


class TestConfigGet:
    """测试配置获取."""

    def test_get_simple_key(self):
        """测试获取简单键."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "config.yaml"
            config = Config(temp_path)
            config.load()
            assert config.get("api") == config._config["api"]

    def test_get_nested_key(self):
        """测试获取嵌套键."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "config.yaml"
            config = Config(temp_path)
            config.load()
            assert config.get("api.base_url") == DEFAULT_CONFIG["api"]["base_url"]
            assert config.get("defaults.rows") == DEFAULT_CONFIG["defaults"]["rows"]

    def test_get_missing_key(self):
        """测试获取不存在键返回默认值."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "config.yaml"
            config = Config(temp_path)
            config.load()
            assert config.get("missing.key", "default") == "default"
            assert config.get("api.missing", None) is None

    def test_get_before_load(self):
        """测试 get 自动加载配置."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "config.yaml"
            config = Config(temp_path)  # 未显式调用 load

            # get 内部会调用 load
            assert config.get("api.base_url") == DEFAULT_CONFIG["api"]["base_url"]
            assert config._loaded


class TestConfigSet:
    """测试配置设置."""

    def test_set_simple_key(self):
        """测试设置简单键."""
        config = Config()
        config.set("new_key", "new_value")

        assert config._config["new_key"] == "new_value"

    def test_set_nested_key(self):
        """测试设置嵌套键."""
        config = Config()
        config.set("defaults.rows", 50)

        assert config._config["defaults"]["rows"] == 50

    def test_set_creates_nested_path(self):
        """测试设置自动创建嵌套路径."""
        config = Config()
        config.set("new.nested.key", "value")

        assert config._config["new"]["nested"]["key"] == "value"


class TestConfigSave:
    """测试配置保存."""

    def test_save_yaml(self):
        """测试保存 YAML 格式."""
        config = Config()
        config.set("defaults.rows", 100)

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "config.yaml"
            config.config_path = temp_path
            config.save()

            content = temp_path.read_text(encoding="utf-8")
            assert "rows: 100" in content
            assert "api:" in content

    def test_save_json(self):
        """测试保存 JSON 格式."""
        config = Config()
        config.set("defaults.rows", 100)

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "config.json"
            config.config_path = temp_path
            config.save()

            import json
            content = json.loads(temp_path.read_text(encoding="utf-8"))
            assert content["defaults"]["rows"] == 100


class TestConfigReset:
    """测试配置重置."""

    def test_reset(self):
        """测试重置为默认配置."""
        config = Config()
        config.set("defaults.rows", 100)
        config.set("custom.key", "value")

        config.reset()

        assert config._config == DEFAULT_CONFIG.copy()


class TestConfigProperties:
    """测试配置属性."""

    def test_base_url_property(self):
        """测试 base_url 属性."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "config.yaml"
            config = Config(temp_path)
            assert config.base_url == DEFAULT_CONFIG["api"]["base_url"]

    def test_default_rows_property(self):
        """测试 default_rows 属性."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "config.yaml"
            config = Config(temp_path)
            assert config.default_rows == DEFAULT_CONFIG["defaults"]["rows"]

    def test_default_canon_property(self):
        """测试 default_canon 属性."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "config.yaml"
            config = Config(temp_path)
            assert config.default_canon is None

    def test_output_format_property(self):
        """测试 output_format 属性."""
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "config.yaml"
            config = Config(temp_path)
            assert config.output_format == "text"


class TestGetConfigGlobal:
    """测试全局配置实例."""

    def test_get_config_returns_instance(self):
        """测试 get_config 返回 Config 实例."""
        # 重置全局实例
        import cli_anything.cbeta.utils.config as config_module
        config_module._config_instance = None

        config = get_config()
        assert isinstance(config, Config)

        # 重置全局实例
        config_module._config_instance = None

    def test_get_config_singleton(self):
        """测试 get_config 返回相同实例."""
        import cli_anything.cbeta.utils.config as config_module
        config_module._config_instance = None

        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

        # 重置全局实例
        config_module._config_instance = None


class TestConfigShow:
    """测试配置显示."""

    def test_show_format(self):
        """测试 show 输出格式."""
        config = Config()
        output = config.show()

        assert "当前配置:" in output
        assert "[api]" in output
        assert "[defaults]" in output
        assert "base_url:" in output