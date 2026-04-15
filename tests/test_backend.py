"""Unit tests for CbetaClient backend."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from cli_anything.cbeta.utils.cbeta_backend import CbetaClient, DEFAULT_BASE_URL, TIMEOUT


class TestCbetaClientInit:
    """测试 CbetaClient 初始化."""

    def test_default_init(self):
        """测试默认初始化参数."""
        client = CbetaClient()
        assert client.base_url == DEFAULT_BASE_URL
        assert client.referer == "cli-anything-cbeta"
        assert "Referer" in client.session.headers
        assert client.session.headers["Referer"] == "cli-anything-cbeta"

    def test_custom_base_url(self):
        """测试自定义 base_url."""
        client = CbetaClient(base_url="https://custom.api.com")
        assert client.base_url == "https://custom.api.com"

    def test_custom_referer(self):
        """测试自定义 referer."""
        client = CbetaClient(referer="my-app")
        assert client.referer == "my-app"
        assert client.session.headers["Referer"] == "my-app"

    def test_base_url_trailing_slash_removed(self):
        """测试 base_url 末尾斜杠被移除."""
        client = CbetaClient(base_url="https://api.example.com/")
        assert client.base_url == "https://api.example.com"


class TestCbetaClientRequest:
    """测试 _request 方法."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_request_success(self, mock_get):
        """测试成功的请求."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok", "data": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        result = client._request("health", cache=False)

        assert result == {"status": "ok", "data": []}
        mock_get.assert_called_once()

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_request_json_decode_error(self, mock_get):
        """测试 JSON 解码错误时返回纯文本."""
        mock_response = Mock()
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError("error", "", 0)
        mock_response.text = "success"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        result = client._request("health", cache=False)

        assert result == {"status": "success"}

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_request_failure(self, mock_get):
        """测试请求失败抛出 RuntimeError."""
        mock_get.side_effect = requests.exceptions.ConnectionError("connection failed")

        client = CbetaClient(use_cache=False)
        with pytest.raises(RuntimeError, match="API request failed"):
            client._request("health", cache=False)

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_request_with_params(self, mock_get):
        """测试带参数的请求."""
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client._request("search", {"q": "般若", "rows": 10}, cache=False)

        call_args = mock_get.call_args
        assert call_args[1]["params"] == {"q": "般若", "rows": 10}


class TestCbetaClientHealth:
    """测试 health 方法."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_health_returns_status(self, mock_get):
        """测试 health 返回状态."""
        mock_response = Mock()
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError("error", "", 0)
        mock_response.text = "success"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        result = client.health()

        assert result == {"status": "success"}


class TestCbetaClientSearch:
    """测试搜索相关方法."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_search_basic(self, mock_get):
        """测试基本搜索."""
        mock_response = Mock()
        mock_response.json.return_value = {"num_found": 100, "results": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        result = client.search("般若")

        assert result["num_found"] == 100
        call_params = mock_get.call_args[1]["params"]
        assert call_params["q"] == "般若"

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_search_with_filters(self, mock_get):
        """测试带筛选的搜索."""
        mock_response = Mock()
        mock_response.json.return_value = {"num_found": 50}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.search("金刚", canon="T", rows=5, category="般若部类")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["q"] == "金刚"
        assert call_params["canon"] == "T"
        assert call_params["rows"] == 5
        assert call_params["category"] == "般若部类"

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_search_kwic(self, mock_get):
        """测试 KWIC 搜索."""
        mock_response = Mock()
        mock_response.json.return_value = {"kwic_results": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.search_kwic("法", work="T0001", juan=1)

        call_params = mock_get.call_args[1]["params"]
        assert call_params["q"] == "法"
        assert call_params["work"] == "T0001"
        assert call_params["juan"] == 1

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_search_variants(self, mock_get):
        """测试异体字搜索."""
        mock_response = Mock()
        mock_response.json.return_value = {"results": [{"q": "㳒", "hits": 90}]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        result = client.search_variants("法")

        assert "results" in result
        call_params = mock_get.call_args[1]["params"]
        assert call_params["q"] == "法"


class TestCbetaClientWorks:
    """测试佛典相关方法."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_works_info(self, mock_get):
        """测试佛典信息查询."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [{"work": "T0001", "title": "長阿含經"}]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        result = client.works(work="T0001")

        assert result["results"][0]["work"] == "T0001"
        call_params = mock_get.call_args[1]["params"]
        assert call_params["work"] == "T0001"

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_works_list_with_filters(self, mock_get):
        """测试佛典列表筛选."""
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.works(canon="T", dynasty="唐")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["canon"] == "T"
        assert call_params["dynasty"] == "唐"

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_work_toc(self, mock_get):
        """测试佛典目录."""
        mock_response = Mock()
        mock_response.json.return_value = {"toc": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.work_toc("T0001")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["work"] == "T0001"


class TestCbetaClientExport:
    """测试导出方法."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_export_all_works(self, mock_get):
        """测试导出所有佛典."""
        mock_response = Mock()
        # API 返回列表格式
        mock_response.json.return_value = [{"work": "T0001", "title": "测试"}]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        result = client.export_all_works()

        assert isinstance(result, list)

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_export_creators(self, mock_get):
        """测试导出作译者."""
        mock_response = Mock()
        mock_response.json.return_value = {"creators": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        result = client.export_all_creators()

        assert "creators" in result

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_export_dynasty(self, mock_get):
        """测试导出朝代."""
        mock_response = Mock()
        mock_response.json.return_value = {"dynasty": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        result = client.export_dynasty()

        assert "dynasty" in result


class TestCbetaClientTools:
    """测试工具方法."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_sc2tc(self, mock_get):
        """测试简繁转换."""
        mock_response = Mock()
        mock_response.json.return_value = {"text": "法華經"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        result = client.sc2tc("法华经")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["text"] == "法华经"

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_word_seg(self, mock_get):
        """测试分词."""
        mock_response = Mock()
        mock_response.json.return_value = {"seg": ["般若", "波罗蜜", "多", "心经"]}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        result = client.word_seg("般若波罗蜜多心经")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["text"] == "般若波罗蜜多心经"


class TestCbetaClientLines:
    """测试行内容方法."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_lines_basic(self, mock_get):
        """测试获取行内容."""
        mock_response = Mock()
        mock_response.json.return_value = {"lines": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.lines("T0001A001PA0001LB0001")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["linehead"] == "T0001A001PA0001LB0001"

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_lines_with_context(self, mock_get):
        """测试带上下文的行内容."""
        mock_response = Mock()
        mock_response.json.return_value = {"lines": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.lines("T0001A001PA0001LB0001", before=3, after=3)

        call_params = mock_get.call_args[1]["params"]
        assert call_params["before"] == 3
        assert call_params["after"] == 3

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_lines_range(self, mock_get):
        """测试行范围."""
        mock_response = Mock()
        mock_response.json.return_value = {"lines": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.lines_range("T0001A001PA0001LB0001", "T0001A001PA0001LB0010")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["linehead_start"] == "T0001A001PA0001LB0001"
        assert call_params["linehead_end"] == "T0001A001PA0001LB0010"


class TestCbetaClientJuans:
    """测试卷方法."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_juans(self, mock_get):
        """测试卷列表."""
        mock_response = Mock()
        mock_response.json.return_value = {"juans": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.juans("T0001")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["work"] == "T0001"

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_juan_goto(self, mock_get):
        """测试定位到卷."""
        mock_response = Mock()
        mock_response.json.return_value = {"juan": 1}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.juan_goto("T0001", 1)

        call_params = mock_get.call_args[1]["params"]
        assert call_params["work"] == "T0001"
        assert call_params["juan"] == 1


class TestCbetaClientCatalog:
    """测试目录方法."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_catalog_entry(self, mock_get):
        """测试目录条目."""
        mock_response = Mock()
        mock_response.json.return_value = {"entry": {}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.catalog_entry("T01n0001")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["entry"] == "T01n0001"

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_category(self, mock_get):
        """测试部类查询."""
        mock_response = Mock()
        mock_response.json.return_value = {"works": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.category("般若部类")

        # category 使用路径参数而非查询参数
        call_args = mock_get.call_args
        assert "般若部类" in call_args[0][0] or "般若部类" in str(call_args)


class TestCbetaClientReport:
    """测试统计方法."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_report_total(self, mock_get):
        """测试总体统计."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "total": {"works_all": 4868, "cjk_chars_all": 222949077}
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        result = client.report_total()

        assert result["total"]["works_all"] == 4868


class TestCbetaClientContent:
    """测试佛典内容方法."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_work_content(self, mock_get):
        """测试佛典内容."""
        mock_response = Mock()
        mock_response.json.return_value = {"content": "经文内容"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.work_content("T0001", 1)

        call_args = mock_get.call_args
        assert "T0001" in call_args[0][0]
        assert "juan/1" in call_args[0][0]

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_work_content_with_edition(self, mock_get):
        """测试带版本号的佛典内容."""
        mock_response = Mock()
        mock_response.json.return_value = {"content": ""}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.work_content("T0001", 1, edition="orig")

        call_args = mock_get.call_args
        assert "edition/orig" in call_args[0][0]


class TestCbetaClientChanges:
    """测试变更历史方法."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_changes(self, mock_get):
        """测试变更历史."""
        mock_response = Mock()
        mock_response.json.return_value = {"changes": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.changes(work="T0001")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["work"] == "T0001"


class TestCbetaClientDownload:
    """测试下载信息方法."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_download_info(self, mock_get):
        """测试下载信息."""
        mock_response = Mock()
        mock_response.json.return_value = {"downloads": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.download_info("T0001")

        call_args = mock_get.call_args
        assert "download/T0001" in call_args[0][0]


class TestCbetaClientSimilar:
    """测试相似文本搜索."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_search_similar(self, mock_get):
        """测试相似文本搜索."""
        mock_response = Mock()
        mock_response.json.return_value = {"similar": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.search_similar("T0001")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["work"] == "T0001"

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_search_similar_with_juan(self, mock_get):
        """测试带卷号的相似文本搜索."""
        mock_response = Mock()
        mock_response.json.return_value = {"similar": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.search_similar("T0001", juan=5)

        call_params = mock_get.call_args[1]["params"]
        assert call_params["work"] == "T0001"
        assert call_params["juan"] == 5


class TestCbetaClientFacet:
    """测试分面搜索."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_search_facet_with_query(self, mock_get):
        """测试带查询的分面搜索."""
        mock_response = Mock()
        mock_response.json.return_value = {"facet": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.search_facet("canon", q="般若")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["facet_by"] == "canon"
        assert call_params["q"] == "般若"

    @patch("cli_anything.cbeta.utils.cbeta_backend.requests.Session.get")
    def test_search_facet_without_query(self, mock_get):
        """测试不带查询的分面搜索."""
        mock_response = Mock()
        mock_response.json.return_value = {"facet": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = CbetaClient(use_cache=False)
        client.search_facet("canon")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["facet_by"] == "canon"
        assert "q" not in call_params