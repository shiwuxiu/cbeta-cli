"""Unit tests for exporters module."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from cli_anything.cbeta.utils.exporters import (
    export_to_json, export_to_csv, export_to_markdown, export_to_html,
    export_to_excel, get_exporter
)


class TestExportToJson:
    """测试 JSON 导出."""

    def test_export_json_dict(self):
        """测试字典数据导出."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        data = {"results": [{"work": "T0001", "title": "测试"}], "count": 1}
        export_to_json(data, temp_path)

        # 读取验证
        with open(temp_path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["count"] == 1
        assert loaded["results"][0]["work"] == "T0001"

        temp_path.unlink()

    def test_export_json_list(self):
        """测试列表数据导出."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        data = [{"work": "T0001"}, {"work": "T0002"}]
        export_to_json(data, temp_path)

        with open(temp_path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert len(loaded) == 2

        temp_path.unlink()


class TestExportToCsv:
    """测试 CSV 导出."""

    def test_export_csv_list(self):
        """测试列表数据导出."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)

        data = [
            {"work": "T0001", "title": "长阿含经", "juan": 1},
            {"work": "T0002", "title": "中阿含经", "juan": 2}
        ]
        export_to_csv(data, temp_path)

        # 读取验证
        with open(temp_path, encoding="utf-8-sig") as f:
            content = f.read()
        assert "work" in content
        assert "title" in content
        assert "T0001" in content

        temp_path.unlink()

    def test_export_csv_dict(self):
        """测试字典数据导出."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)

        data = {"results": [{"work": "T0001", "title": "测试"}]}
        export_to_csv(data, temp_path)

        with open(temp_path, encoding="utf-8-sig") as f:
            content = f.read()
        assert "T0001" in content

        temp_path.unlink()

    def test_export_csv_empty(self):
        """测试空数据导出."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)

        export_to_csv([], temp_path)
        assert temp_path.exists()

        temp_path.unlink()


class TestExportToMarkdown:
    """测试 Markdown 导出."""

    def test_export_markdown(self):
        """测试 Markdown 导出."""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            temp_path = Path(f.name)

        data = {"results": [{"work": "T0001", "title": "测试"}], "count": 1}
        export_to_markdown(data, temp_path)

        # 读取验证
        with open(temp_path, encoding="utf-8") as f:
            content = f.read()
        assert "CBETA" in content or "|" in content

        temp_path.unlink()


class TestExportToHtml:
    """测试 HTML 导出."""

    def test_export_html(self):
        """测试 HTML 导出."""
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            temp_path = Path(f.name)

        data = {"results": [{"work": "T0001", "title": "测试"}], "count": 1}
        export_to_html(data, temp_path)

        # 读取验证
        with open(temp_path, encoding="utf-8") as f:
            content = f.read()
        assert "<html" in content.lower() or "<table" in content.lower()

        temp_path.unlink()


class TestGetExporter:
    """测试导出器选择."""

    def test_get_json_exporter(self):
        """测试获取 JSON 导出器."""
        exporter = get_exporter("json")
        assert exporter == export_to_json

    def test_get_csv_exporter(self):
        """测试获取 CSV 导出器."""
        exporter = get_exporter("csv")
        assert exporter == export_to_csv

    def test_get_excel_exporter(self):
        """测试获取 Excel 导出器."""
        exporter = get_exporter("excel")
        assert exporter == export_to_excel
        exporter = get_exporter("xlsx")
        assert exporter == export_to_excel

    def test_get_markdown_exporter(self):
        """测试获取 Markdown 导出器."""
        exporter = get_exporter("markdown")
        assert exporter == export_to_markdown
        exporter = get_exporter("md")
        assert exporter == export_to_markdown

    def test_get_html_exporter(self):
        """测试获取 HTML 导出器."""
        exporter = get_exporter("html")
        assert exporter == export_to_html

    def test_get_exporter_invalid(self):
        """测试无效格式."""
        with pytest.raises((KeyError, ValueError)):
            get_exporter("invalid_format")