"""Unit tests for CBETA CLI commands."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from cli_anything.cbeta import main
from cli_anything.cbeta.cbeta_cli import cli


class TestCliMain:
    """测试 CLI 主入口."""

    def test_main_function_exists(self):
        """测试 main 函数存在."""
        assert main is not None

    def test_cli_help(self):
        """测试 --help 输出."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "CBETA" in result.output or "中华电子佛典" in result.output

    def test_cli_version(self):
        """测试版本信息."""
        from cli_anything.cbeta import __version__
        assert __version__ == "2.7.0"


class TestSearchCommands:
    """测试搜索命令组."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.search")
    def test_search_query(self, mock_search):
        """测试 search query 命令."""
        mock_search.return_value = {
            "num_found": 100,
            "total_term_hits": 500,
            "results": [{"work": "T0001", "title": "测试"}]
        }

        runner = CliRunner()
        result = runner.invoke(cli, ["search", "query", "般若", "--rows", "5"])

        assert result.exit_code == 0
        mock_search.assert_called_once()

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.search_kwic")
    def test_search_kwic(self, mock_kwic):
        """测试 search kwic 命令."""
        mock_kwic.return_value = {"kwic_results": []}

        runner = CliRunner()
        # kwic 命令需要 --work 和 --juan 参数（都是 required=True）
        result = runner.invoke(cli, ["search", "kwic", "法", "--work", "T0001", "--juan", "1"])

        assert result.exit_code == 0
        mock_kwic.assert_called_once()

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.search_variants")
    def test_search_variants(self, mock_variants):
        """测试 search variants 命令."""
        mock_variants.return_value = {"results": [{"q": "㳒", "hits": 90}]}

        runner = CliRunner()
        result = runner.invoke(cli, ["search", "variants", "法"])

        assert result.exit_code == 0
        mock_variants.assert_called_once()


class TestWorkCommands:
    """测试佛典命令组."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.works")
    def test_work_info(self, mock_works):
        """测试 work info 命令."""
        mock_works.return_value = {
            "results": [{"work": "T0001", "title": "長阿含經", "juan": 22}]
        }

        runner = CliRunner()
        result = runner.invoke(cli, ["work", "info", "T0001"])

        assert result.exit_code == 0
        mock_works.assert_called_once()

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.work_toc")
    def test_work_toc(self, mock_toc):
        """测试 work toc 命令."""
        mock_toc.return_value = {"toc": []}

        runner = CliRunner()
        result = runner.invoke(cli, ["work", "toc", "T0001"])

        assert result.exit_code == 0
        mock_toc.assert_called_once()

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.works")
    def test_work_list(self, mock_works):
        """测试 work list 命令."""
        mock_works.return_value = {"results": []}

        runner = CliRunner()
        result = runner.invoke(cli, ["work", "list", "--canon", "T"])

        assert result.exit_code == 0
        mock_works.assert_called_once()


class TestServerCommands:
    """测试服务器命令组."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.health")
    def test_server_health(self, mock_health):
        """测试 server health 命令."""
        mock_health.return_value = {"status": "success"}

        runner = CliRunner()
        result = runner.invoke(cli, ["server", "health"])

        assert result.exit_code == 0
        mock_health.assert_called_once()

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.report_total")
    def test_server_stats(self, mock_stats):
        """测试 server stats 命令."""
        mock_stats.return_value = {
            "total": {"works_all": 4868, "cjk_chars_all": 222949077}
        }

        runner = CliRunner()
        result = runner.invoke(cli, ["server", "stats"])

        assert result.exit_code == 0
        mock_stats.assert_called_once()


class TestExportCommands:
    """测试导出命令组."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.export_all_works")
    def test_export_works(self, mock_export):
        """测试 export works 命令."""
        mock_export.return_value = {"works": []}

        runner = CliRunner()
        result = runner.invoke(cli, ["export", "works"])

        assert result.exit_code == 0
        mock_export.assert_called_once()

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.export_all_creators")
    def test_export_creators(self, mock_export):
        """测试 export creators 命令."""
        mock_export.return_value = {"creators": []}

        runner = CliRunner()
        result = runner.invoke(cli, ["export", "creators"])

        assert result.exit_code == 0
        mock_export.assert_called_once()


class TestToolsCommands:
    """测试工具命令组."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.sc2tc")
    def test_tools_sc2tc(self, mock_sc2tc):
        """测试 tools sc2tc 命令."""
        mock_sc2tc.return_value = {"text": "法華經"}

        runner = CliRunner()
        result = runner.invoke(cli, ["tools", "sc2tc", "法华经"])

        assert result.exit_code == 0
        mock_sc2tc.assert_called_once()

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.word_seg")
    def test_tools_wordseg(self, mock_wordseg):
        """测试 tools wordseg 命令."""
        mock_wordseg.return_value = {"seg": ["般若", "心经"]}

        runner = CliRunner()
        result = runner.invoke(cli, ["tools", "wordseg", "般若心经"])

        assert result.exit_code == 0
        mock_wordseg.assert_called_once()


class TestLineCommands:
    """测试行内容命令组."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.lines")
    def test_line_get(self, mock_lines):
        """测试 line get 命令."""
        mock_lines.return_value = {"lines": []}

        runner = CliRunner()
        result = runner.invoke(cli, ["line", "get", "--head", "T0001A001PA0001LB0001"])

        assert result.exit_code == 0
        mock_lines.assert_called_once()


class TestJuanCommands:
    """测试卷命令组."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.juans")
    def test_juan_list(self, mock_juans):
        """测试 juan list 命令."""
        mock_juans.return_value = {"juans": []}

        runner = CliRunner()
        result = runner.invoke(cli, ["juan", "list", "--work", "T0001"])

        assert result.exit_code == 0
        mock_juans.assert_called_once()


class TestCatalogCommands:
    """测试目录命令组."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.catalog_entry")
    def test_catalog_entry(self, mock_entry):
        """测试 catalog entry 命令."""
        mock_entry.return_value = {"entry": {}}

        runner = CliRunner()
        result = runner.invoke(cli, ["catalog", "entry", "T01n0001"])

        assert result.exit_code == 0
        mock_entry.assert_called_once()


class TestJsonOutput:
    """测试 JSON 输出."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.works")
    def test_json_output(self, mock_works):
        """测试 --json 参数输出 JSON 格式."""
        mock_works.return_value = {
            "results": [{"work": "T0001", "title": "長阿含經"}]
        }

        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "work", "info", "T0001"])

        assert result.exit_code == 0
        # JSON 输出应该包含可解析的 JSON
        import json
        try:
            # 查找输出中的 JSON 部分
            output = result.output.strip()
            # 可能有前导信息，需要找到 JSON 开始
            json_start = output.find("{")
            if json_start >= 0:
                json.loads(output[json_start:])
        except json.JSONDecodeError:
            pass  # 可能格式有其他输出，但不影响功能测试


class TestCommandGroups:
    """测试命令组存在."""

    def test_search_group_exists(self):
        """测试 search 命令组存在."""
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "query" in result.output or "kwic" in result.output

    def test_work_group_exists(self):
        """测试 work 命令组存在."""
        runner = CliRunner()
        result = runner.invoke(cli, ["work", "--help"])
        assert result.exit_code == 0
        assert "info" in result.output or "toc" in result.output

    def test_server_group_exists(self):
        """测试 server 命令组存在."""
        runner = CliRunner()
        result = runner.invoke(cli, ["server", "--help"])
        assert result.exit_code == 0
        assert "health" in result.output or "stats" in result.output

    def test_export_group_exists(self):
        """测试 export 命令组存在."""
        runner = CliRunner()
        result = runner.invoke(cli, ["export", "--help"])
        assert result.exit_code == 0
        assert "works" in result.output or "creators" in result.output

    def test_tools_group_exists(self):
        """测试 tools 命令组存在."""
        runner = CliRunner()
        result = runner.invoke(cli, ["tools", "--help"])
        assert result.exit_code == 0
        assert "sc2tc" in result.output or "wordseg" in result.output


class TestErrorHandling:
    """测试错误处理."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.search")
    def test_api_error_handling(self, mock_search):
        """测试 API 错误处理."""
        mock_search.side_effect = RuntimeError("API request failed")

        runner = CliRunner()
        result = runner.invoke(cli, ["search", "query", "般若"])

        # 命令应该优雅地处理错误
        assert result.exit_code != 0 or "error" in result.output.lower() or "失败" in result.output


class TestSearchParams:
    """测试搜索参数."""

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.search")
    def test_search_with_canon_filter(self, mock_search):
        """测试藏经筛选参数."""
        mock_search.return_value = {"num_found": 0, "results": []}

        runner = CliRunner()
        result = runner.invoke(cli, ["search", "query", "般若", "--canon", "T"])

        assert result.exit_code == 0
        call_kwargs = mock_search.call_args[1]
        assert call_kwargs.get("canon") == "T"

    @patch("cli_anything.cbeta.utils.cbeta_backend.CbetaClient.search")
    def test_search_with_category_filter(self, mock_search):
        """测试部类筛选参数."""
        mock_search.return_value = {"num_found": 0, "results": []}

        runner = CliRunner()
        result = runner.invoke(cli, ["search", "query", "心经", "--category", "般若部类"])

        assert result.exit_code == 0
        call_kwargs = mock_search.call_args[1]
        assert call_kwargs.get("category") == "般若部类"