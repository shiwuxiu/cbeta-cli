"""pytest configuration for CBETA CLI tests."""

import pytest
import sys
import os

# 确保 UTF-8 编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


@pytest.fixture
def mock_client():
    """提供 mock CbetaClient 实例."""
    from unittest.mock import MagicMock
    from cli_anything.cbeta.utils.cbeta_backend import CbetaClient
    return MagicMock(spec=CbetaClient)


@pytest.fixture
def cli_runner():
    """提供 Click CliRunner 实例."""
    from click.testing import CliRunner
    return CliRunner()


# 忽略 SSL 警告
pytestmark = pytest.mark.filterwarnings("ignore::urllib3.exceptions.InsecureRequestWarning")