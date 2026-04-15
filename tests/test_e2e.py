"""E2E tests for CBETA CLI - Testing with real API."""

import pytest
import os
import sys

# 确保 UTF-8 编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# E2E 测试标记
pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def real_client():
    """使用真实 API 客户端."""
    from cli_anything.cbeta.utils.cbeta_backend import CbetaClient
    return CbetaClient()


class TestE2EHealth:
    """E2E: 健康检查测试."""

    def test_health_check(self, real_client):
        """测试 API 健康检查."""
        result = real_client.health()
        # API 可能返回 {"status": "success"} 或直接返回 "success"
        assert result.get("status") == "success" or result == {"status": "success"}


class TestE2ESearch:
    """E2E: 搜索功能测试."""

    def test_basic_search(self, real_client):
        """测试基本搜索."""
        result = real_client.search("般若", rows=5)
        assert "num_found" in result
        assert result["num_found"] > 0
        assert len(result["results"]) <= 5

    def test_search_with_canon_filter(self, real_client):
        """测试藏经筛选搜索."""
        result = real_client.search("金刚", rows=10, canon="T")
        assert result["num_found"] > 0
        # 检查结果（有些可能没有 canon 字段）
        for r in result["results"]:
            if "canon" in r:
                assert r.get("canon") == "T"

    def test_search_kwic(self, real_client):
        """测试 KWIC 搜索."""
        result = real_client.search_kwic("法", work="T0001", juan=1)
        assert "results" in result or "kwic_results" in result

    def test_search_variants(self, real_client):
        """测试异体字搜索."""
        result = real_client.search_variants("法")
        assert "results" in result


class TestE2EWorks:
    """E2E: 佛典查询测试."""

    def test_work_info(self, real_client):
        """测试佛典信息查询."""
        result = real_client.works(work="T0001")
        assert "results" in result
        assert len(result["results"]) > 0
        work = result["results"][0]
        assert work.get("work") == "T0001"
        assert work.get("title") is not None

    def test_work_list_by_canon(self, real_client):
        """测试按藏经查询佛典列表."""
        result = real_client.works(canon="T")
        assert "results" in result

    def test_work_toc(self, real_client):
        """测试佛典目录."""
        result = real_client.work_toc("T0001")
        assert "toc" in result or "results" in result


class TestE2EServer:
    """E2E: 服务器状态测试."""

    def test_report_total(self, real_client):
        """测试统计报表."""
        result = real_client.report_total()
        assert "total" in result
        assert result["total"]["works_all"] > 4000  # CBETA 有 4868 部佛典


class TestE2EExport:
    """E2E: 导出功能测试."""

    def test_export_all_works(self, real_client):
        """测试导出所有佛典."""
        result = real_client.export_all_works()
        assert isinstance(result, list)
        assert len(result) > 4000

    def test_export_creators(self, real_client):
        """测试导出作译者."""
        result = real_client.export_all_creators()
        assert "creators" in result or isinstance(result, list)


class TestE2ETools:
    """E2E: 工具功能测试."""

    def test_sc2tc(self, real_client):
        """测试简繁转换."""
        result = real_client.sc2tc("法华经")
        assert "text" in result

    def test_word_seg(self, real_client):
        """测试中文分词."""
        result = real_client.word_seg("般若波罗蜜多心经")
        assert "seg" in result


# 运行 E2E 测试的说明
# pytest tests/test_e2e.py -v -m e2e