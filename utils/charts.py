"""Charts and visualization for CBETA CLI.

使用 matplotlib 生成图表：
- 柱状图：各藏经佛典数量
- 词云：关键词分布
- 折线图：时间分布
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


def check_matplotlib():
    """检查 matplotlib 是否安装."""
    try:
        import matplotlib
        matplotlib.use('Agg')  # 非交互式后端
        import matplotlib.pyplot as plt
        return True
    except ImportError:
        return False


def generate_bar_chart(data: Dict[str, int], title: str, file_path: Path, xlabel: str = "", ylabel: str = "数量") -> None:
    """生成柱状图."""
    if not check_matplotlib():
        raise RuntimeError("需要安装 matplotlib: pip install matplotlib")

    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(12, 6))

    labels = list(data.keys())
    values = list(data.values())

    ax.bar(labels, values, color='steelblue')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # 旋转标签（如果标签太长）
    if max(len(str(l)) for l in labels) > 5:
        plt.xticks(rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(file_path, dpi=150, bbox_inches='tight')
    plt.close()


def generate_pie_chart(data: Dict[str, int], title: str, file_path: Path) -> None:
    """生成饼图."""
    if not check_matplotlib():
        raise RuntimeError("需要安装 matplotlib: pip install matplotlib")

    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(10, 8))

    labels = list(data.keys())
    values = list(data.values())

    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.set_title(title)

    plt.tight_layout()
    plt.savefig(file_path, dpi=150, bbox_inches='tight')
    plt.close()


def generate_line_chart(data: List[Dict], x_key: str, y_key: str, title: str, file_path: Path) -> None:
    """生成折线图."""
    if not check_matplotlib():
        raise RuntimeError("需要安装 matplotlib: pip install matplotlib")

    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(12, 6))

    x_values = [d.get(x_key) for d in data]
    y_values = [d.get(y_key) for d in data]

    ax.plot(x_values, y_values, marker='o', linestyle='-', color='steelblue')
    ax.set_title(title)
    ax.set_xlabel(x_key)
    ax.set_ylabel(y_key)

    plt.tight_layout()
    plt.savefig(file_path, dpi=150, bbox_inches='tight')
    plt.close()


def generate_wordcloud(text: str, title: str, file_path: Path) -> None:
    """生成词云."""
    try:
        from wordcloud import WordCloud
    except ImportError:
        raise RuntimeError("需要安装 wordcloud: pip install wordcloud")

    wc = WordCloud(
        font_path=None,  # 使用默认字体或指定中文字体路径
        width=800,
        height=600,
        background_color='white',
        max_words=100,
        colormap='viridis'
    )

    # 尝试使用中文字体
    try:
        wc = WordCloud(
            font_path='C:/Windows/Fonts/simhei.ttf',  # Windows 黑体
            width=800,
            height=600,
            background_color='white',
            max_words=100,
            colormap='viridis'
        )
    except:
        pass

    wc.generate(text)

    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    ax.set_title(title)

    plt.tight_layout()
    plt.savefig(file_path, dpi=150, bbox_inches='tight')
    plt.close()


def generate_histogram(data: List[int], title: str, file_path: Path, bins: int = 20) -> None:
    """生成直方图."""
    if not check_matplotlib():
        raise RuntimeError("需要安装 matplotlib: pip install matplotlib")

    import matplotlib.pyplot as plt
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.hist(data, bins=bins, color='steelblue', edgecolor='black')
    ax.set_title(title)
    ax.set_xlabel("值")
    ax.set_ylabel("频数")

    plt.tight_layout()
    plt.savefig(file_path, dpi=150, bbox_inches='tight')
    plt.close()