"""Unit tests for charts module."""

import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Check if matplotlib is available
MATPLOTLIB_AVAILABLE = False
try:
    import matplotlib
    matplotlib.use('Agg')
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    pass


@pytest.fixture
def temp_png():
    """创建临时 PNG 文件路径."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()


class TestGenerateBarChart:
    """测试柱状图生成."""

    @pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="matplotlib not installed")
    def test_generate_bar_chart_dict(self, temp_png):
        """测试字典数据柱状图."""
        from cli_anything.cbeta.utils.charts import generate_bar_chart

        data = {"T": 100, "X": 50, "K": 30}
        generate_bar_chart(data, "测试柱状图", temp_png)
        assert temp_png.exists()

    @pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="matplotlib not installed")
    def test_generate_bar_chart_with_labels(self, temp_png):
        """测试带轴标签的柱状图."""
        from cli_anything.cbeta.utils.charts import generate_bar_chart

        data = {"A": 10, "B": 20}
        generate_bar_chart(data, "测试", temp_png, xlabel="类别", ylabel="数量")
        assert temp_png.exists()


class TestGeneratePieChart:
    """测试饼图生成."""

    @pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="matplotlib not installed")
    def test_generate_pie_chart(self, temp_png):
        """测试饼图生成."""
        from cli_anything.cbeta.utils.charts import generate_pie_chart

        data = {"T": 60, "X": 30, "K": 10}
        generate_pie_chart(data, "测试饼图", temp_png)
        assert temp_png.exists()


class TestGenerateLineChart:
    """测试折线图生成."""

    @pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="matplotlib not installed")
    def test_generate_line_chart(self, temp_png):
        """测试折线图生成."""
        from cli_anything.cbeta.utils.charts import generate_line_chart

        data = [
            {"year": 100, "hits": 50},
            {"year": 200, "hits": 100},
            {"year": 300, "hits": 150}
        ]
        generate_line_chart(data, "year", "hits", "时间分布", temp_png)
        assert temp_png.exists()


class TestGenerateHistogram:
    """测试直方图生成."""

    @pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="matplotlib not installed")
    def test_generate_histogram(self, temp_png):
        """测试直方图生成."""
        from cli_anything.cbeta.utils.charts import generate_histogram

        data = [10, 20, 30, 40, 50]
        generate_histogram(data, "测试直方图", temp_png)
        assert temp_png.exists()


class TestGenerateWordcloud:
    """测试词云生成."""

    @pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="matplotlib/wordcloud not installed")
    def test_generate_wordcloud_dict(self, temp_png):
        """测试字典数据词云."""
        try:
            from wordcloud import WordCloud
        except ImportError:
            pytest.skip("wordcloud not installed")

        from cli_anything.cbeta.utils.charts import generate_wordcloud

        data = {"般若": 100, "金刚": 80, "法华": 60}
        generate_wordcloud(data, "测试词云", temp_png)
        assert temp_png.exists()


class TestCheckMatplotlib:
    """测试 matplotlib 检查."""

    def test_check_matplotlib(self):
        """测试 matplotlib 检查函数."""
        from cli_anything.cbeta.utils.charts import check_matplotlib
        # 返回实际状态
        result = check_matplotlib()
        assert result == MATPLOTLIB_AVAILABLE

    def test_generate_chart_without_matplotlib(self):
        """测试没有 matplotlib 时抛出错误."""
        from cli_anything.cbeta.utils.charts import generate_bar_chart

        if MATPLOTLIB_AVAILABLE:
            pytest.skip("matplotlib is installed, cannot test error")

        with pytest.raises(RuntimeError, match="matplotlib"):
            generate_bar_chart({"A": 1}, "test", Path("test.png"))