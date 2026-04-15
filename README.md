# CBETA CLI - 中华电子佛典协会 API 命令行工具

**版本**: 2.6.0
**API 地址**: https://api.cbetaonline.cn
**API 版本**: 3.6.9
**资料版本**: 2025R3

---

## 概述

CBETA CLI 是中华电子佛典协会（Chinese Buddhist Electronic Text Association）API 的完整命令行封装工具，提供佛典搜索、典籍信息、全文获取、经目查询等全部功能。

**命令覆盖率**: 42/42 = **100%**

**新增功能 (v2.6.0)**:
- 缓存机制（内存 + 文件缓存）
- 配置文件支持（自定义 API 地址、默认参数、缓存/日志设置）
- Shell 补全（bash/zsh/fish/powershell）
- 批量操作（批量搜索、下载、导出）
- 多格式导出（JSON/CSV/Excel/Markdown/HTML）
- 离线模式（本地 SQLite 数据库）
- 词频分析与统计图表
- 日志系统（按天分割）

---

## 安装与使用

```bash
# CLI 工具已安装在 Python 包中
python -m cli_anything.cbeta [命令]

# Windows 必须设置 UTF-8 编码
export PYTHONIOENCODING=utf-8
```

---

## 命令一览

### 搜索命令组 (`search`)

| 命令 | 功能 | 示例 |
|------|------|------|
| `search query` | 全文搜索 | `search query "般若" --rows 5 --canon T` |
| `search kwic` | KWIC 关键词上下文 | `search kwic "法" --work T0001 --juan 1` |
| `search toc` | 经目搜索 | `search toc "阿含" --rows 10` |
| `search similar` | 相似文本搜索 | `search similar --work T0001` |
| `search notes` | 注释/夹注搜索 | `search notes "译者"` |
| `search title` | 标题搜索 | `search title "金刚"` |
| `search variants` | 异体字搜索 | `search variants "法"` |
| `search facet` | 分面统计 | `search facet "般若" --by canon` |

### 佛典命令组 (`work`)

| 命令 | 功能 | 示例 |
|------|------|------|
| `work info` | 佛典详细信息 | `work info T0001` |
| `work toc` | 佛典目录结构 | `work toc T0001` |
| `work content` | 佛典全文内容 | `work content T0001 --juan 1` |
| `work list` | 佛典列表（可筛选） | `work list --canon T --dynasty 唐` |
| `work wordcount` | 字数统计 | `work wordcount --canon T` |
| `work download` | 下载信息 | `work download T0001` |

### 行内容命令组 (`line`)

| 命令 | 功能 | 示例 |
|------|------|------|
| `line get` | 获取指定行 | `line get --head T0001A001PA0001LB0001` |
| `line range` | 获取行范围 | `line range --start H1 --end H2` |

### 卷命令组 (`juan`)

| 命令 | 功能 | 示例 |
|------|------|------|
| `juan list` | 卷列表 | `juan list --work T0001` |
| `juan goto` | 定位到卷 | `juan goto --work T0001 --juan 1` |

### 目录命令组 (`catalog`)

| 命令 | 功能 | 示例 |
|------|------|------|
| `catalog entry` | 目录条目详情 | `catalog entry T01n0001` |
| `catalog category` | 按部类查询 | `catalog category 般若部类` |

### 工具命令组 (`tools`)

| 命令 | 功能 | 示例 |
|------|------|------|
| `tools sc2tc` | 简繁转换 | `tools sc2tc "法华经"` |
| `tools wordseg` | 中文分词 | `tools wordseg "般若波罗蜜多心经"` |

### 服务器命令组 (`server`)

| 命令 | 功能 | 示例 |
|------|------|------|
| `server health` | API 健康检查 | `server health` |
| `server stats` | 统计报表 | `server stats --by-canon` |
| `server changes` | 数据变更历史 | `server changes --work T0001` |

### 导出命令组 (`export`)

| 命令 | 功能 | 示例 |
|------|------|------|
| `export works` | 导出佛典列表 | `export works` (4868部) |
| `export creators` | 导出作译者 | `export creators` |
| `export dynasty` | 导出朝代信息 | `export dynasty` |
| `export strokes` | 导出笔画数据 | `export strokes` |

### 会话与输出

| 命令 | 功能 | 示例 |
|------|------|------|
| `--json` | JSON 输出 | `--json work info T0001` |
| `session status` | 会话状态 | `session status` |
| `session reset` | 重置会话 | `session reset` |
| `repl` | 交互式 REPL | 直接运行进入 |

### 配置命令组 (`config`)

| 命令 | 功能 | 示例 |
|------|------|------|
| `config show` | 显示当前配置 | `config show` |
| `config init` | 创建配置文件 | `config init --force` |
| `config set` | 设置配置项 | `config set defaults.rows 20` |
| `config get` | 获取配置项 | `config get api.base_url` |
| `config reset` | 重置配置 | `config reset --confirm` |
| `config path` | 显示配置路径 | `config path` |

### 缓存命令组 (`cache`)

| 命令 | 功能 | 示例 |
|------|------|------|
| `cache stats` | 显示缓存统计 | `cache stats` |
| `cache clear` | 清除所有缓存 | `cache clear` |
| `cache clear --expired` | 只清除过期缓存 | `cache clear --expired` |
| `cache path` | 显示缓存目录 | `cache path` |

### 批量操作命令组 (`batch`)

| 命令 | 功能 | 示例 |
|------|------|------|
| `batch search` | 批量搜索多个关键词 | `batch search --keywords "般若,金刚,法华"` |
| `batch download` | 批量下载佛典内容 | `batch download --works T0001,T0002,T0003` |
| `batch export` | 批量导出数据到文件 | `batch export --keywords "般若" --format csv` |

### 离线模式命令组 (`offline`)

| 命令 | 功能 | 示例 |
|------|------|------|
| `offline download` | 导出数据到本地 SQLite | `offline download --limit 100` |
| `offline download --incremental` | 增量更新本地数据 | `offline download --incremental` |
| `offline query` | 离线搜索（本地数据库） | `offline query "般若"` |
| `offline info` | 离线查询佛典信息 | `offline info T0001` |
| `offline status` | 显示离线数据库状态 | `offline status` |

### 分析命令组 (`analyze`)

| 命令 | 功能 | 示例 |
|------|------|------|
| `analyze frequency` | 关键词词频分析 | `analyze frequency "般若" --chart freq.png` |
| `analyze distribution` | 藏经分布分析 | `analyze distribution --by canon --chart dist.png` |
| `analyze compare` | 多关键词对比 | `analyze compare --keywords "般若,金刚,法华"` |
| `analyze timeline` | 时间分布分析 | `analyze timeline "般若" --chart time.png` |
| `analyze chart` | 从数据文件生成图表 | `analyze chart data.json --type bar -o chart.png` |

### Shell 补全命令 (`completion`)

| 命令 | 功能 | 示例 |
|------|------|------|
| `completion bash` | 生成 Bash 补全脚本 | `completion bash` |
| `completion zsh` | 生成 Zsh 补全脚本 | `completion zsh` |
| `completion fish` | 生成 Fish 补全脚本 | `completion fish` |
| `completion powershell` | 生成 PowerShell 补全脚本 | `completion powershell` |

---

## 配置文件

配置文件位于 `~/.cbeta/config.yaml`，支持以下设置：

```yaml
api:
  base_url: https://api.cbetaonline.cn
  timeout: 30
  referer: cli-anything-cbeta

defaults:
  rows: 10           # 默认返回数量
  canon: null        # 默认藏经 (T, X, K 等)
  category: null     # 默认部类
  dynasty: null      # 默认朝代
  output_format: text  # 输出格式 (text, json, table)

display:
  color: true        # 启用颜色输出
  verbose: false     # 详细输出
  show_fields:       # 显示字段列表
    - work
    - title
    - category
    - juan
    - cjk_chars

cache:
  enabled: true      # 启用缓存
  expire_seconds: 3600  # 缓存过期时间（秒）
  max_size_mb: 100   # 最大缓存大小

logging:
  level: INFO        # 日志级别
  rotation_days: 1   # 日志分割间隔（天）
  backup_count: 30   # 保留日志数量
```

### 日志文件

日志文件位于 `~/.cbeta/logs/`：
- `cbeta.log` - 当前日志文件
- `cbeta.log.2026-04-14` - 按天分割的历史日志
- `operations.json` - 操作记录（最多1000条）

### 配置使用示例

```bash
# 创建默认配置文件
python -m cli_anything.cbeta config init

# 设置默认返回数量
python -m cli_anything.cbeta config set defaults.rows 20

# 设置默认藏经为大正藏
python -m cli_anything.cbeta config set defaults.canon T

# 自定义 API 地址
python -m cli_anything.cbeta config set api.base_url https://custom-api.com

# 查看当前配置
python -m cli_anything.cbeta config show
```

## 详细使用示例

### 1. 全文搜索

```bash
# 基本搜索
python -m cli_anything.cbeta search query "般若" --rows 5

# 按藏经筛选（大正藏）
python -m cli_anything.cbeta search query "般若" --canon T --rows 10

# 按部类筛选
python -m cli_anything.cbeta search query "心经" --category 般若部类

# 按朝代筛选
python -m cli_anything.cbeta search query "金刚" --dynasty 唐

# 按年代范围
python -m cli_anything.cbeta search query "佛" --time 800..900

# 排序
python -m cli_anything.cbeta search query "般若" --order time_from-
```

### 2. 词频分析与图表生成

```bash
# 关键词词频分析
python -m cli_anything.cbeta analyze frequency "般若"

# 生成柱状图
python -m cli_anything.cbeta analyze frequency "般若" --chart frequency.png

# 藏经分布分析
python -m cli_anything.cbeta analyze distribution --by canon

# 生成饼图
python -m cli_anything.cbeta analyze distribution --by canon --chart distribution.png

# 多关键词对比
python -m cli_anything.cbeta analyze compare --keywords "般若,金刚,法华" --chart compare.png

# 从数据文件生成图表
python -m cli_anything.cbeta analyze chart data.json --type bar --title "测试图表" -o chart.png
```

### 3. 批量操作

```bash
# 批量搜索多个关键词
python -m cli_anything.cbeta batch search --keywords "般若,金刚,法华" --output-path results.json

# 批量下载佛典内容
python -m cli_anything.cbeta batch download --works T0001,T0002,T0003 --output-dir ./downloads

# 批量导出为 CSV
python -m cli_anything.cbeta batch export --keywords "般若" --format csv --output-path export.csv
```

### 4. 离线模式

```bash
# 导出全部佛典数据到本地
python -m cli_anything.cbeta offline download

# 增量更新（只更新新增/变化的佛典）
python -m cli_anything.cbeta offline download --incremental

# 离线搜索
python -m cli_anything.cbeta offline query "般若"

# 查看离线数据库状态
python -m cli_anything.cbeta offline status
```

### 5. 缓存管理

```bash
# 查看缓存统计
python -m cli_anything.cbeta cache stats

# 清除所有缓存
python -m cli_anything.cbeta cache clear

# 只清除过期缓存
python -m cli_anything.cbeta cache clear --expired
```

### 6. Shell 补全安装

```bash
# Bash 补全（添加到 ~/.bashrc）
python -m cli_anything.cbeta completion bash >> ~/.bashrc

# Zsh 补全（添加到 ~/.zshrc）
python -m cli_anything.cbeta completion zsh >> ~/.zshrc

# Fish 补全
python -m cli_anything.cbeta completion fish > ~/.config/fish/completions/cbeta.fish

# PowerShell 补全
python -m cli_anything.cbeta completion powershell | Out-File -Encoding UTF8 $PROFILE
```

### 2. KWIC 搜索（关键词上下文）

```bash
# 获取关键词及其上下文
python -m cli_anything.cbeta search kwic "法" --work T0001 --juan 1

# 带标记的关键词
python -m cli_anything.cbeta search kwic "般若" --work T0235 --juan 1 --mark 1

# NEAR 搜索语法（找相邻关键词）
python -m cli_anything.cbeta search kwic '"老子" NEAR/7 "道"' --work XXX --juan 1
```

### 3. 佛典信息

```bash
python -m cli_anything.cbeta work info T0001

# 返回：
# work: T0001
# title: 長阿含經
# category: 阿含部類
# juan: 22
# byline: 後秦 佛陀耶舍共竺佛念譯
# time_dynasty: 後秦
# cjk_chars: 198436
```

### 4. 异体字搜索

```bash
python -m cli_anything.cbeta search variants "法"

# 返回：
# 找到 2 条结果
# [0] {'q': '㳒', 'hits': 90}  - "法"的异体字"㳒"，出现90次
# [1] {'q': '灋', 'hits': 217} - "法"的异体字"灋"，出现217次
```

### 5. JSON 输出（适合 AI 代理解析）

```bash
# JSON 输出
python -m cli_anything.cbeta --json work info T0001

# 管道处理
python -m cli_anything.cbeta --json search query "般若" --rows 3 \
  | python -c "import sys,json; d=json.load(sys.stdin); print(d['results'][0]['title'])"
```

### 6. 交互式 REPL

```bash
$ python -m cli_anything.cbeta

╔════════════════════════════════════════════════════════╗
║          CBETA CLI v2.0.0                              ║
║          中华电子佛典协会 API 工具                       ║
╚════════════════════════════════════════════════════════╝

API 地址: https://api.cbetaonline.cn
输入 'help' 查看命令列表，'quit' 退出

cbeta> search query 般若 --rows 3
cbeta> work info T0001
cbeta> server stats
cbeta> quit

再见！阿弥陀佛！
```

---

## 藏经 ID 对照表

| ID | 名称 | 佛典数 |
|----|------|--------|
| **T** | 大正藏 | 2,457 |
| **X** | 新纂卍续藏 | 1,230 |
| A | 宋—金藏 | 9 |
| K | 宋—高丽藏 | 9 |
| S | 宋—宋藏遗珍 | 2 |
| F | 房山石经 | 27 |
| C | 中国佛寺志 | 11 |
| D | 国图善本 | 64 |
| U | 北敦 | 2 |
| P | 敦煌写本 | 13 |
| J | 日本佛寺志 | 285 |
| L | 吕澂佛典 | 21 |
| G | 佛教大藏经 | 53 |
| M | 曼殊院 | 1 |
| N | 南传大藏经 | 38 |
| GA | 金藏校本 | 51 |
| GB | 金藏校本2 | 2 |
| ZS | 正史佛教资料 | 1 |
| ZW | 现代人著作 | 202 |
| B | 编译馆 | 200 |

---

## 部类名称

```
本缘部类、阿含部类、般若部类、法华部类、华严部类
宝积部类、涅槃部类、大集部类、经集部类、密教部类
律部类、毘昙部类、中观部类、瑜伽部类、论集部类
净土宗部类、禅宗部类、史传部类、事汇部类
敦煌写本部类、国图善本部类、南传大藏经部类、新编部类
```

---

## Python 库直接调用

```python
from cli_anything.cbeta import CbetaClient

client = CbetaClient()

# 全文搜索
results = client.search("般若", rows=5, canon="T")
print(f"找到 {results['num_found']} 条，词频 {results['total_term_hits']}")

# 佛典信息
info = client.works(work="T0001")
print(info['results'][0]['title'])  # 長阿含經

# KWIC
kwic = client.search_kwic("法", work="T0001", juan=1)

# 异体字
variants = client.search_variants("法")

# 简繁转换
converted = client.sc2tc("法华经")

# 分词
seg = client.word_seg("般若波罗蜜多心经")

# 统计
stats = client.report_total()
print(stats['total']['works_all'])  # 4868
```

---

## 统计数据

```
总佛典数: 4,868 部
总卷数: 21,955 卷
总字数: 222,949,077 字

大正藏 (T): 2,457部, 8,982卷, 75,101,698字
卍续藏 (X): 1,230部, 5,065卷, 72,944,287字
```

---

## 测试结果

```bash
$ python -m cli_anything.cbeta search query "般若" --rows 3 --canon T
搜索 '般若' 找到 3722 条结果，总词频 70529
results: [3 items]
  [0] T0220 - 大般若波羅蜜多經 (词频:381)
  [1] T0220 - 大般若波羅蜜多經 (词频:334)

$ python -m cli_anything.cbeta work info T0001
佛典 T0001 信息
work: T0001
title: 長阿含經
juan: 22
cjk_chars: 198436

$ python -m cli_anything.cbeta search variants "法"
异体字搜索 '法' 找到 2 条结果
  [0] {'q': '㳒', 'hits': 90}
  [1] {'q': '灋', 'hits': 217}

$ python -m cli_anything.cbeta server stats
总体统计
works_all: 4868
cjk_chars_all: 222949077

$ python -m cli_anything.cbeta --json work info T0001 \
  | python -c "import sys,json; d=json.load(sys.stdin); print(d['title'])"
長阿含經
```

---

| 命令完整性对比表 |

| 功能 | CLI 命令 | 后端方法 | 状态 |
|------|----------|----------|:----:|
| 全文搜索 | `search query` | `search()` | ✅ |
| KWIC搜索 | `search kwic` | `search_kwic()` | ✅ |
| 经目搜索 | `search toc` | `_request` | ✅ |
| 相似文本 | `search similar` | `search_similar()` | ✅ |
| 注释搜索 | `search notes` | `search_notes()` | ✅ |
| 标题搜索 | `search title` | `search_title()` | ✅ |
| 异体字搜索 | `search variants` | `search_variants()` | ✅ |
| 分面统计 | `search facet` | `_request` | ✅ |
| 佛典信息 | `work info` | `works()` | ✅ |
| 佛典目录 | `work toc` | `work_toc()` | ✅ |
| 佛典全文 | `work content` | `work_content()` | ✅ |
| 佛典列表 | `work list` | `works()` | ✅ |
| 字数统计 | `work wordcount` | `work_word_count()` | ✅ |
| 下载信息 | `work download` | `download_info()` | ✅ |
| 获取行 | `line get` | `lines()` | ✅ |
| 行范围 | `line range` | `lines_range()` | ✅ |
| 卷列表 | `juan list` | `juans()` | ✅ |
| 定位卷 | `juan goto` | `juan_goto()` | ✅ |
| 目录条目 | `catalog entry` | `catalog_entry()` | ✅ |
| 按部类查询 | `catalog category` | `category()` | ✅ |
| 简繁转换 | `tools sc2tc` | `sc2tc()` | ✅ |
| 中文分词 | `tools wordseg` | `word_seg()` | ✅ |
| 健康检查 | `server health` | `health()` | ✅ |
| 统计报表 | `server stats` | `report_total()` | ✅ |
| 变更历史 | `server changes` | `changes()` | ✅ |
| 导出佛典 | `export works` | `export_all_works()` | ✅ |
| 导出作译者 | `export creators` | `export_all_creators()` | ✅ |
| 导出朝代 | `export dynasty` | `export_dynasty()` | ✅ |
| JSON输出 | `--json` | - | ✅ |
| 交互REPL | `repl` | - | ✅ |
| **缓存统计** | `cache stats` | `CacheManager.stats()` | ✅ |
| **缓存清除** | `cache clear` | `CacheManager.clear_all()` | ✅ |
| **批量搜索** | `batch search` | - | ✅ |
| **批量下载** | `batch download` | - | ✅ |
| **批量导出** | `batch export` | - | ✅ |
| **离线下载** | `offline download` | - | ✅ |
| **增量下载** | `offline download -i` | - | ✅ |
| **离线查询** | `offline query` | - | ✅ |
| **词频分析** | `analyze frequency` | - | ✅ |
| **分布分析** | `analyze distribution` | - | ✅ |
| **关键词对比** | `analyze compare` | - | ✅ |
| **时间分析** | `analyze timeline` | - | ✅ |
| **图表生成** | `analyze chart` | - | ✅ |
| **Shell补全** | `completion` | - | ✅ |

---

## 参考资料

- [CBETA API 官方文档](https://api.cbetaonline.cn/)
- [CBETA API GitHub](https://github.com/DILA-edu/cbeta-api)
- [CBETA 官网](http://www.cbeta.org/)
- [CLI-Anything 项目](https://github.com/HKUDS/CLI-Anything)

---

## 更新日志

| 版本 | 日期 | 内容 |
|------|------|------|
| 1.0.0 | 2026-04-15 | 基础版本：搜索、佛典、服务器、导出命令 |
| 2.0.0 | 2026-04-15 | **完整版本**：新增相似文本、注释、标题、异体字、分面统计、行内容、卷、目录、工具等全部命令，命令覆盖率 100% |
| 2.1.0 | 2026-04-15 | 配置文件支持、REPL 模式、JSON 输出 |
| **2.6.0** | 2026-04-15 | **功能增强版**：缓存机制、Shell补全、批量操作、多格式导出、离线模式（增量下载）、词频分析、统计图表、日志系统（按天分割）、E2E测试 |

---

*文档生成时间: 2026-04-15*