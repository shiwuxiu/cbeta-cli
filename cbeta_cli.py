#!/usr/bin/env python3
"""CBETA CLI — 中华电子佛典协会 API 命令行工具。

提供 CBETA API 的完整访问，包括佛典搜索、典籍信息、经目查询、全文获取等功能。

Usage:
    # 搜索命令
    cli-anything-cbeta search query "般若" --rows 5
    cli-anything-cbeta search kwic "法" --work T0001 --juan 1
    cli-anything-cbeta search toc "阿含"
    cli-anything-cbeta search similar --work T0001
    cli-anything-cbeta search notes "注释关键词"
    cli-anything-cbeta search title "金刚"
    cli-anything-cbeta search variants "法"
    cli-anything-cbeta search facet --by canon

    # 佛典命令
    cli-anything-cbeta work info T0001
    cli-anything-cbeta work toc T0001
    cli-anything-cbeta work content T0001 --juan 1
    cli-anything-cbeta work list --canon T
    cli-anything-cbeta work wordcount

    # 行内容命令
    cli-anything-cbeta line get --head T0001A001PA0001LB0001
    cli-anything-cbeta line range --start HEAD1 --end HEAD2

    # 卷命令
    cli-anything-cbeta juan list --work T0001
    cli-anything-cbeta juan goto --work T0001 --juan 1

    # 目录命令
    cli-anything-cbeta catalog entry ENTRY001
    cli-anything-cbeta catalog category 般若部类

    # 工具命令
    cli-anything-cbeta tools sc2tc "法华经"
    cli-anything-cbeta tools wordseg "般若波罗蜜多心经"

    # 服务器命令
    cli-anything-cbeta server health
    cli-anything-cbeta server stats --by-canon

    # 导出命令
    cli-anything-cbeta export works
    cli-anything-cbeta export creators
    cli-anything-cbeta export dynasty

    # JSON 输出
    cli-anything-cbeta --json search query "般若"

    # 交互式 REPL
    cli-anything-cbeta
"""

import sys
import os
import json
import hashlib
import click
from datetime import datetime
from cli_anything.cbeta.utils.cbeta_backend import DEFAULT_BASE_URL, CbetaClient
from cli_anything.cbeta.utils.config import get_config
from cli_anything.cbeta.utils.logger import get_logger, log_search

# Global state
_json_output = False
_repl_mode = False
_base_url = DEFAULT_BASE_URL
_client: CbetaClient | None = None


def get_client() -> CbetaClient:
    """Get or create CBETA client."""
    global _client
    if _client is None:
        _client = CbetaClient(base_url=_base_url)
    return _client


def output(data, message: str = ""):
    """Output data in JSON or human-readable format."""
    if _json_output:
        click.echo(json.dumps(data, indent=2, default=str, ensure_ascii=False))
    else:
        if message:
            click.echo(message)
        if isinstance(data, dict):
            _print_dict(data)
        elif isinstance(data, list):
            _print_list(data)
        elif isinstance(data, str):
            # For long text content, print directly
            if len(data) > 200:
                click.echo(data)
            else:
                click.echo(data)
        else:
            click.echo(str(data))


def _print_dict(d: dict, indent: int = 0):
    """Pretty print dict."""
    prefix = "  " * indent
    for k, v in d.items():
        if isinstance(v, dict):
            click.echo(f"{prefix}{k}:")
            _print_dict(v, indent + 1)
        elif isinstance(v, list):
            click.echo(f"{prefix}{k}: [{len(v)} items]")
            if len(v) <= 5 and indent < 2:
                _print_list(v, indent + 1)
        elif isinstance(v, str) and len(v) > 200:
            # Long text - truncate for display
            click.echo(f"{prefix}{k}: {v[:100]}... ({len(v)} chars total)")
        else:
            val_str = str(v)
            if len(val_str) > 100:
                val_str = val_str[:100] + "..."
            click.echo(f"{prefix}{k}: {val_str}")


def _print_list(items: list, indent: int = 0):
    """Pretty print list."""
    prefix = "  " * indent
    for i, item in enumerate(items[:10]):  # Limit to 10 items
        if isinstance(item, dict):
            click.echo(f"{prefix}[{i}] {_item_summary(item)}")
        elif isinstance(item, str):
            val_str = item
            if len(val_str) > 80:
                val_str = val_str[:80] + "..."
            click.echo(f"{prefix}[{i}] {val_str}")
        else:
            click.echo(f"{prefix}[{i}] {item}")
    if len(items) > 10:
        click.echo(f"{prefix}... ({len(items) - 10} more items)")


def _item_summary(item: dict) -> str:
    """Create summary string for dict item."""
    # For search results
    if "work" in item and "title" in item:
        hits = item.get("term_hits", "")
        return f"{item.get('work', '')} - {item.get('title', '')}" + (f" (词频:{hits})" if hits else "")
    # For TOC results
    elif "title" in item:
        type_str = item.get("type", "")
        return f"{item.get('title', '')}" + (f" [{type_str}]" if type_str else "")
    # For work list
    elif "work" in item:
        return item.get("work", "")
    # For juan list
    elif "juan" in item:
        return f"卷 {item.get('juan', '')}"
    # Default
    return str(item)[:50]


def handle_error(func):
    """Decorator to handle errors in CLI commands."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except RuntimeError as e:
            if _json_output:
                click.echo(json.dumps({"error": str(e), "type": "runtime_error"}))
            else:
                click.echo(f"错误: {e}", err=True)
            if not _repl_mode:
                sys.exit(1)
        except Exception as e:
            if _json_output:
                click.echo(json.dumps({"error": str(e), "type": type(e).__name__}))
            else:
                click.echo(f"错误: {e}", err=True)
            if not _repl_mode:
                sys.exit(1)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


# ── Main CLI Group ──────────────────────────────────────────────
@click.group(invoke_without_command=True)
@click.option("--json", "use_json", is_flag=True, help="输出 JSON 格式")
@click.option("--base-url", type=str, default=None,
              help=f"CBETA API 地址 (默认: {DEFAULT_BASE_URL})")
@click.pass_context
def cli(ctx, use_json, base_url):
    """CBETA CLI — 中华电子佛典协会 API 命令行工具。

    不带子命令运行时进入交互式 REPL 模式。
    """
    global _json_output, _base_url, _client
    _json_output = use_json
    if base_url:
        _base_url = base_url.rstrip("/")
    _client = CbetaClient(base_url=_base_url)

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


# ──────────────────────────────────────────────────────────────────
# 搜索命令组 (Search Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def search():
    """搜索命令组 - 全文搜索、KWIC、经目、相似文本、注释等。"""
    pass


@search.command("query")
@click.argument("query")
@click.option("--rows", "-r", type=int, default=None, help="返回结果数量 (默认从配置读取)")
@click.option("--start", "-s", type=int, default=0, help="起始位置（分页）")
@click.option("--canon", "-c", default=None, help="藏经筛选 (T, X, K, A, B 等)")
@click.option("--category", "-cat", default=None, help="部类筛选 (如 般若部类)")
@click.option("--work", "-w", default=None, help="佛典编号筛选 (如 T0001)")
@click.option("--works", default=None, help="多部佛典筛选 (如 T0001,T0002)")
@click.option("--creator", default=None, help="作译者 ID 筛选")
@click.option("--dynasty", "-d", default=None, help="朝代筛选")
@click.option("--time", "-t", default=None, help="年代范围 (如 800..900)")
@click.option("--order", "-o", default=None, help="排序字段 (如 time_from-)")
@click.option("--fields", "-f", default=None, help="返回字段 (如 work,juan,title)")
@handle_error
def search_query(query, rows, start, canon, category, work, works, creator, dynasty, time, order, fields):
    """全文搜索。

    在 CBETA 电子佛典全文数据库中搜索关键词。

    示例:
        search query "般若" --rows 5
        search query "法鼓" --canon T --rows 10
        search query "心经" --category 般若部类
        search query "金刚" --dynasty 唐
        search query "佛" --time 800..900
        search query "阿含" --order time_from-
    """
    # 从配置读取默认值
    config = get_config()
    rows = rows or config.default_rows
    canon = canon or config.default_canon
    category = category or config.get("defaults.category")
    dynasty = dynasty or config.get("defaults.dynasty")

    params = {"rows": rows, "start": start}
    if canon:
        params["canon"] = canon
    if category:
        params["category"] = category
    if work:
        params["work"] = work
    if works:
        params["works"] = works
    if creator:
        params["creator"] = creator
    if dynasty:
        params["dynasty"] = dynasty
    if time:
        params["time"] = time
    if order:
        params["order"] = order
    if fields:
        params["fields"] = fields

    result = get_client().search(query, **params)
    num_found = result.get("num_found", 0)
    total_hits = result.get("total_term_hits", 0)
    output(result, f"搜索 '{query}' 找到 {num_found} 条结果，总词频 {total_hits}")

    # 记录日志
    log_search(query, {"canon": canon, "category": category}, num_found)


@search.command("kwic")
@click.argument("query")
@click.option("--work", "-w", required=True, help="佛典编号 (如 T0001)")
@click.option("--juan", "-j", type=int, required=True, help="卷号")
@click.option("--note", type=int, default=1, help="是否含夹注 (0=不含, 1=含)")
@click.option("--mark", type=int, default=0, help="关键字加标记 (0=不加, 1=加)")
@click.option("--sort", default=None, help="排序方式 (f=forward, b=backward, location)")
@handle_error
def search_kwic(query, work, juan, note, mark, sort):
    """KWIC (关键词上下文) 搜索。

    在指定佛典的指定卷中搜索关键词，返回关键词及其上下文。

    示例:
        search kwic "法" --work T0001 --juan 1
        search kwic "般若" --work T0235 --juan 1 --mark 1
        search kwic "佛" --work T0001 --juan 1 --sort location

    NEAR 搜索语法 (在 query 中使用):
        search kwic '"老子" NEAR/7 "道"' --work XXX --juan 1
    """
    params = {"q": query, "work": work, "juan": juan, "note": note, "mark": mark}
    if sort:
        params["sort"] = sort
    result = get_client().search_kwic(query, **params)
    output(result, f"KWIC 搜索 '{query}' 在 {work} 第 {juan} 卷")


@search.command("toc")
@click.argument("query")
@click.option("--rows", "-r", type=int, default=10, help="返回结果数量")
@handle_error
def search_toc(query, rows):
    """经目搜索。

    搜索部类目录、佛典标题（經名）、佛典内目次标题。

    返回结果 type 字段说明:
    - catalog: 在部类目录中搜寻的结果
    - work: 在佛典标题中搜寻的结果
    - toc: 在佛典内目次标题中搜寻的结果

    示例:
        search toc "阿含"
        search toc "金刚经"
        search toc "般若" --rows 20
    """
    result = get_client()._request("search/toc", {"q": query, "rows": rows})
    output(result, f"经目搜索 '{query}' 找到 {result.get('num_found', 0)} 条结果")


@search.command("similar")
@click.argument("work", required=False)
@click.option("--work", "-w", "work_opt", default=None, help="佛典编号")
@click.option("--juan", "-j", type=int, default=None, help="卷号")
@click.option("--rows", "-r", type=int, default=10, help="返回结果数量")
@handle_error
def search_similar(work, work_opt, juan, rows):
    """相似文本搜索。

    根据指定佛典/卷找到内容相似的文本段落。

    示例:
        search similar --work T0001
        search similar --work T0001 --juan 1
        search similar T0235 --rows 20
    """
    work_id = work or work_opt
    if not work_id:
        click.echo("错误: 请指定佛典编号 (--work 或作为参数)", err=True)
        return

    params = {"rows": rows}
    if juan:
        params["juan"] = juan

    result = get_client().search_similar(work_id, **params)
    output(result, f"相似文本搜索 {work_id}" + (f" 第 {juan} 卷" if juan else ""))


@search.command("notes")
@click.argument("query")
@click.option("--rows", "-r", type=int, default=10, help="返回结果数量")
@click.option("--work", "-w", default=None, help="佛典编号筛选")
@handle_error
def search_notes(query, rows, work):
    """注释/夹注搜索。

    搜索佛典中的注释、夹注内容。

    示例:
        search notes "译者"
        search notes "注" --work T0001
    """
    params = {"rows": rows}
    if work:
        params["work"] = work
    result = get_client().search_notes(query, **params)
    output(result, f"注释搜索 '{query}' 找到 {result.get('num_found', 0)} 条结果")


@search.command("title")
@click.argument("query")
@click.option("--rows", "-r", type=int, default=10, help="返回结果数量")
@handle_error
def search_title(query, rows):
    """标题搜索。

    搜索佛典标题（經名）。

    示例:
        search title "金刚"
        search title "心经"
    """
    result = get_client().search_title(query, rows=rows)
    output(result, f"标题搜索 '{query}' 找到 {result.get('num_found', 0)} 条结果")


@search.command("variants")
@click.argument("query")
@click.option("--rows", "-r", type=int, default=10, help="返回结果数量")
@handle_error
def search_variants(query, rows):
    """异体字搜索。

    搜索时自动包含异体字变体，如搜"法"也会匹配"灋"等异体。

    示例:
        search variants "法"
        search variants "真" --rows 20
    """
    result = get_client().search_variants(query, rows=rows)
    output(result, f"异体字搜索 '{query}' 找到 {result.get('num_found', 0)} 条结果")


@search.command("extended")
@click.argument("query")
@click.option("--rows", "-r", type=int, default=10, help="返回结果数量")
@click.option("--canon", "-c", default=None, help="藏经筛选")
@click.option("--category", default=None, help="部类筛选")
@handle_error
def search_extended(query, rows, canon, category):
    """布林搜索（支持 AND/OR/NOT）。

    支持布尔运算符：
    - | 或 OR: 并集搜索
    - - 或 NOT: 排除搜索

    示例:
        search extended "般若 | 金刚"
        search extended "心经 -般若"
        search extended "佛 AND 法" --canon T
    """
    params = {"rows": rows}
    if canon:
        params["canon"] = canon
    if category:
        params["category"] = category
    result = get_client().search_extended(query, **params)
    output(result, f"布林搜索 '{query}' 找到 {result.get('num_found', 0)} 条结果")


@search.command("fuzzy")
@click.argument("query")
@click.option("--rows", "-r", type=int, default=10, help="返回结果数量")
@click.option("--canon", "-c", default=None, help="藏经筛选")
@handle_error
def search_fuzzy(query, rows, canon):
    """模糊搜索。

    用于处理不确定的查询，允许部分匹配。

    示例:
        search fuzzy "般若波罗蜜"
        search fuzzy "金刚经" --canon T
    """
    params = {"rows": rows}
    if canon:
        params["canon"] = canon
    result = get_client().search_fuzzy(query, **params)
    output(result, f"模糊搜索 '{query}' 找到 {result.get('num_found', 0)} 条结果")


@search.command("synonym")
@click.argument("query")
@click.option("--rows", "-r", type=int, default=10, help="返回结果数量")
@handle_error
def search_synonym(query, rows):
    """同义词搜索。

    搜索概念相关的同义词，发现关联词汇。

    示例:
        search synonym "佛"
        search synonym "智慧"
    """
    result = get_client().search_synonym(query, rows=rows)
    output(result, f"同义词搜索 '{query}'")


@search.command("sc")
@click.argument("query")
@click.option("--rows", "-r", type=int, default=10, help="返回结果数量")
@click.option("--canon", "-c", default=None, help="藏经筛选")
@handle_error
def search_sc(query, rows, canon):
    """简体中文搜索（自动转繁体）。

    输入简体中文关键词，自动转换为繁体后搜索。
    方便简体用户查询。

    示例:
        search sc "金刚经"
        search sc "心经" --canon T
    """
    params = {"rows": rows}
    if canon:
        params["canon"] = canon
    result = get_client().search_sc(query, **params)
    output(result, f"简体搜索 '{query}' 找到 {result.get('num_found', 0)} 条结果")


@search.command("facet")
@click.argument("query", required=False)
@click.option("--by", "-b", "facet_by", default="canon", help="分面统计字段 (canon, category, dynasty)")
@click.option("--rows", "-r", type=int, default=10, help="每组返回数量")
@handle_error
def search_facet(query, facet_by, rows):
    """分面统计搜索。

    按指定字段统计搜索结果的分布情况。

    示例:
        search facet "般若" --by canon
        search facet --by dynasty
    """
    params = {"facet_by": facet_by, "rows": rows}
    if query:
        params["q"] = query
    # 直接请求，因为 search_facet 方法签名不同
    result = get_client()._request("search/facet/" + facet_by, params if query else {"rows": rows})
    output(result, f"分面统计" + (f" '{query}'" if query else "") + f" 按 {facet_by}")


# ──────────────────────────────────────────────────────────────────
# 佛典命令组 (Work Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def work():
    """佛典典籍命令组 - 信息、目录、全文、列表等。"""
    pass


@work.command("info")
@click.argument("work_id")
@handle_error
def work_info(work_id):
    """获取佛典详细信息。

    返回佛典的完整元数据，包括题名、部类、作译者、年代、字数等。

    示例:
        work info T0001    # 大正藏第1号 長阿含經
        work info X0001    # 卍续藏第1号
        work info T0235    # 金刚般若波罗蜜经
    """
    result = get_client().works(work=work_id)
    if result.get("num_found", 0) == 0:
        output({"error": "未找到佛典"}, f"佛典 {work_id} 未找到")
        return
    info = result.get("results", [{}])[0]
    output(info, f"佛典 {work_id} 信息")


@work.command("toc")
@click.argument("work_id")
@click.option("--depth", "-d", type=int, default=3, help="目录深度")
@handle_error
def work_toc(work_id, depth):
    """获取佛典目录结构。

    返回佛典内部的章节目录，包含标题、卷号、位置等。

    示例:
        work toc T0001
        work toc T0235 --depth 5
    """
    result = get_client().work_toc(work_id)
    output(result, f"佛典 {work_id} 目录结构")


@work.command("content")
@click.argument("work_id")
@click.option("--juan", "-j", type=int, required=True, help="卷号")
@click.option("--edition", "-e", default=None, help="版本/校本")
@handle_error
def work_content(work_id, juan, edition):
    """获取佛典全文内容。

    获取指定佛典指定卷的全文内容。

    示例:
        work content T0001 --juan 1
        work content T0235 --juan 1
        work content T0001 --juan 1 --edition 校本A
    """
    result = get_client().work_content(work_id, juan, edition=edition)
    # Check if result contains text content
    if isinstance(result, dict):
        if "text" in result:
            output(result["text"], f"佛典 {work_id} 第 {juan} 卷全文")
        elif "html" in result:
            output(result, f"佛典 {work_id} 第 {juan} 卷内容 (HTML)")
        else:
            output(result, f"佛典 {work_id} 第 {juan} 卷")
    else:
        output(result, f"佛典 {work_id} 第 {juan} 卷")


@work.command("list")
@click.option("--canon", "-c", default=None, help="藏经筛选 (T, X, K, A, B, GA, GB 等)")
@click.option("--category", "-cat", default=None, help="部类筛选")
@click.option("--dynasty", "-d", default=None, help="朝代筛选")
@click.option("--creator", default=None, help="作译者筛选 (ID 或姓名)")
@click.option("--time-start", type=int, default=None, help="起始年代")
@click.option("--time-end", type=int, default=None, help="结束年代")
@click.option("--rows", "-r", type=int, default=20, help="返回数量")
@click.option("--order", "-o", default=None, help="排序字段")
@handle_error
def work_list(canon, category, dynasty, creator, time_start, time_end, rows, order):
    """列出佛典。

    按条件筛选并列出佛典列表。

    示例:
        work list --canon T --rows 10
        work list --category 般若部类
        work list --dynasty 唐
        work list --creator A000439
        work list --time-start 500 --time-end 800
        work list --canon X --order time_from-
    """
    params = {"rows": rows}
    if canon:
        params["canon"] = canon
    if category:
        params["category"] = category
    if dynasty:
        params["dynasty"] = dynasty
    if creator:
        params["creator"] = creator
    if time_start:
        params["time_start"] = time_start
    if time_end:
        params["time_end"] = time_end
    if order:
        params["order"] = order

    result = get_client().works(**params)
    output(result, f"找到 {result.get('num_found', 0)} 部佛典")


@work.command("wordcount")
@click.option("--work", "-w", default=None, help="佛典编号筛选")
@click.option("--canon", "-c", default=None, help="藏经筛选")
@handle_error
def work_wordcount(work, canon):
    """佛典字数统计。

    导出佛典字数统计（CSV格式）。

    示例:
        work wordcount
        work wordcount --canon T
        work wordcount --work T0001
    """
    params = {}
    if work:
        params["work"] = work
    if canon:
        params["canon"] = canon
    result = get_client().work_word_count(**params)
    output(result, "佛典字数统计")


@work.command("download")
@click.argument("work_id")
@handle_error
def work_download(work_id):
    """获取佛典下载信息。

    返回佛典的下载链接和格式信息。

    示例:
        work download T0001
    """
    result = get_client().download_info(work_id)
    output(result, f"佛典 {work_id} 下载信息")


# ──────────────────────────────────────────────────────────────────
# 行内容命令组 (Line Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def line():
    """行内容命令组 - 获取佛典具体行内容。"""
    pass


@line.command("get")
@click.option("--head", "-h", required=True, help="行标识符 (如 T0001A001PA0001LB0001)")
@click.option("--before", "-b", type=int, default=0, help="获取前行数")
@click.option("--after", "-a", type=int, default=0, help="获取后行数")
@handle_error
def line_get(head, before, after):
    """获取指定行的内容。

    行标识符格式说明:
    T0001A001PA0001LB0001
    └─┬─┘└┬┘└──┬──┘└─┬─┘
      │   │     │    │
      │   │     │    行号
      │   │     页栏
      │   册号
      佛典编号

    示例:
        line get --head T0001A001PA0001LB0001
        line get --head T0001A001PA0001LB0001 --before 2 --after 2
    """
    result = get_client().lines(head, before=before, after=after)
    output(result, f"获取行 {head}" + (f" 及前后 {before}+{after} 行" if before or after else ""))


@line.command("range")
@click.option("--start", "-s", required=True, help="起始行标识符")
@click.option("--end", "-e", required=True, help="结束行标识符")
@handle_error
def line_range(start, end):
    """获取指定范围的行内容。

    示例:
        line range --start T0001A001PA0001LB0001 --end T0001A001PA0001LB0010
    """
    result = get_client().lines_range(start, end)
    output(result, f"获取行范围 {start} 到 {end}")


# ──────────────────────────────────────────────────────────────────
# 卷命令组 (Juan Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def juan():
    """卷命令组 - 佛典卷信息查询。"""
    pass


@juan.command("list")
@click.option("--work", "-w", required=True, help="佛典编号")
@handle_error
def juan_list(work):
    """列出佛典的卷信息。

    示例:
        juan list --work T0001
    """
    result = get_client().juans(work)
    output(result, f"佛典 {work} 卷列表")


@juan.command("goto")
@click.option("--work", "-w", required=True, help="佛典编号")
@click.option("--juan", "-j", type=int, required=True, help="卷号")
@handle_error
def juan_goto(work, juan):
    """定位到指定卷。

    获取指定佛典指定卷的位置信息。

    示例:
        juan goto --work T0001 --juan 1
    """
    result = get_client().juan_goto(work, juan)
    output(result, f"定位到 {work} 第 {juan} 卷")


# ──────────────────────────────────────────────────────────────────
# 目录命令组 (Catalog Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def catalog():
    """目录命令组 - 藏经目录查询。"""
    pass


@catalog.command("entry")
@click.argument("entry_id")
@handle_error
def catalog_entry(entry_id):
    """获取目录条目详情。

    示例:
        catalog entry T01n0001
    """
    result = get_client().catalog_entry(entry_id)
    output(result, f"目录条目 {entry_id}")


@catalog.command("category")
@click.argument("category_name")
@handle_error
def catalog_category(category_name):
    """按部类查询佛典。

    可用部类:
    - 本缘部类、阿含部类、般若部类、法华部类、华严部类
    - 宝积部类、涅槃部类、大集部类、经集部类、密教部类
    - 律部类、毘昙部类、中观部类、瑜伽部类、论集部类
    - 净土宗部类、禅宗部类、史传部类、事汇部类
    - 敦煌写本部类、国图善本部类、南传大藏经部类、新编部类

    示例:
        catalog category 般若部类
        catalog category 阿含部类
    """
    result = get_client().category(category_name)
    output(result, f"部类 '{category_name}' 佛典列表")


# ──────────────────────────────────────────────────────────────────
# 工具命令组 (Tools Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def tools():
    """工具命令组 - 中文处理工具。"""
    pass


@tools.command("sc2tc")
@click.argument("text")
@handle_error
def tools_sc2tc(text):
    """简体中文转繁体中文。

    示例:
        tools sc2tc "法华经"
        tools sc2tc "金刚经"
    """
    result = get_client().sc2tc(text)
    output(result, f"简繁转换: '{text}'")


@tools.command("wordseg")
@click.argument("text")
@handle_error
def tools_wordseg(text):
    """中文分词。

    将中文文本进行分词处理。

    示例:
        tools wordseg "般若波罗蜜多心经"
        tools wordseg "金刚般若波罗蜜经"
    """
    result = get_client().word_seg(text)
    output(result, f"分词: '{text}'")


# ──────────────────────────────────────────────────────────────────
# 服务器命令组 (Server Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def server():
    """服务器状态命令组。"""
    pass


@server.command("health")
@handle_error
def server_health():
    """检查 API 服务状态。"""
    result = get_client().health()
    output(result, f"API 状态: {result.get('status', 'unknown')}")


@server.command("stats")
@click.option("--by-canon", is_flag=True, help="按藏经显示统计")
@click.option("--by-category", is_flag=True, help="按部类显示统计")
@handle_error
def server_stats(by_canon, by_category):
    """获取统计报表。

    CBETA 数据库的完整统计数据。

    示例:
        server stats
        server stats --by-canon
    """
    result = get_client().report_total()
    if by_canon:
        canon_stats = result.get("by_canon", {})
        output(canon_stats, "按藏经统计")
    elif by_category:
        # Category stats may not be in the response
        output(result, "统计报表")
    else:
        total = result.get("total", {})
        output(total, "总体统计")


@server.command("changes")
@click.option("--work", "-w", default=None, help="佛典编号筛选")
@click.option("--date", "-d", default=None, help="日期筛选")
@handle_error
def server_changes(work, date):
    """获取数据变更历史。

    示例:
        server changes
        server changes --work T0001
    """
    params = {}
    if work:
        params["work"] = work
    if date:
        params["date"] = date
    result = get_client().changes(**params)
    output(result, "数据变更历史")


@server.command("report-daily")
@click.option("--page", "-p", type=int, default=1, help="页码")
@handle_error
def server_report_daily(page):
    """获取每日访问统计。

    示例:
        server report-daily
        server report-daily --page 2
    """
    result = get_client().report_daily(page=page)
    output(result, f"每日访问统计（第 {page} 页）")


@server.command("report-url")
@click.option("--start", "-s", required=True, help="起始日期 (YYYY-MM-DD)")
@click.option("--end", "-e", required=True, help="结束日期 (YYYY-MM-DD)")
@handle_error
def server_report_url(start, end):
    """获取 URL 访问统计。

    示例:
        server report-url --start 2024-01-01 --end 2024-01-31
    """
    result = get_client().report_url(start, end)
    output(result, f"URL 访问统计 ({start} - {end})")


@server.command("report-referer")
@click.option("--start", "-s", required=True, help="起始日期 (YYYY-MM-DD)")
@click.option("--end", "-e", required=True, help="结束日期 (YYYY-MM-DD)")
@handle_error
def server_report_referer(start, end):
    """获取来源访问统计。

    示例:
        server report-referer --start 2024-01-01 --end 2024-01-31
    """
    result = get_client().report_referer(start, end)
    output(result, f"来源访问统计 ({start} - {end})")


# ──────────────────────────────────────────────────────────────────
# 藏经命令组 (Canons Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def canons():
    """藏经命令组 - 查询各藏经信息。"""
    pass


@canons.command("list")
@handle_error
def canons_list():
    """列出所有藏经。

    显示各藏经的 UUID、名称和作品数量。
    """
    result = get_client().canons()
    output(result, f"藏经列表（共 {len(result) if isinstance(result, list) else result.get('num_found', 0)} 个）")


@canons.command("works")
@click.argument("uuid")
@click.option("--rows", "-r", type=int, default=20, help="返回数量")
@handle_error
def canons_works(uuid, rows):
    """列出指定藏经的所有作品。

    使用 Asia Network API 查询。

    示例:
        canons works <uuid>
    """
    result = get_client().works_by_canon_uuid(uuid)
    output(result, f"藏经 {uuid} 作品列表")


@canons.command("info")
@click.argument("uuid")
@handle_error
def canons_info(uuid):
    """显示藏经详细信息。"""
    result = get_client().canons()
    if isinstance(result, list):
        for canon in result:
            if canon.get("uuid") == uuid:
                output(canon, f"藏经 {uuid} 信息")
                return
    output({"error": "未找到该藏经"}, "错误")


# ──────────────────────────────────────────────────────────────────
# 导出命令组 (Export Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def export():
    """导出数据命令组。"""
    pass


@export.command("works")
@click.option("--format", "-f", type=click.Choice(["json", "csv"]), default="json", help="输出格式")
@handle_error
def export_works(format):
    """导出所有佛典列表。

    导出 CBETA 数据库中所有 4868 部佛典的完整列表。

    示例:
        export works
        export works --format csv
    """
    result = get_client().export_all_works()
    output(result, f"导出 {len(result)} 部佛典")


@export.command("creators")
@handle_error
def export_creators():
    """导出所有作译者列表。

    导出所有译经师、作者的完整列表。
    """
    result = get_client().export_all_creators()
    output(result, "导出作译者数据")


@export.command("dynasty")
@handle_error
def export_dynasty():
    """导出朝代信息。

    导出作品成立年代朝代对照表。
    """
    result = get_client().export_dynasty()
    output(result, "导出朝代信息")


@export.command("strokes")
@click.option("--creator", "-c", default=None, help="作译者筛选")
@handle_error
def export_strokes(creator):
    """导出笔画数据。

    导出作译者笔画索引数据。
    """
    result = get_client()._request("export/creator_strokes", {"creator": creator} if creator else {})
    output(result, "导出笔画数据")


@export.command("strokes-works")
@handle_error
def export_strokes_works():
    """导出按笔画排序的作译者（带作品）。

    包含作品信息的笔画排序作译者列表。
    """
    result = get_client().export_creator_strokes_works()
    output(result, "导出笔画排序作译者（带作品）")


@export.command("dynasty-works")
@handle_error
def export_dynasty_works():
    """导出朝代-作品关联数据。

    各朝代作品数量及详情统计。
    """
    result = get_client().export_dynasty_works()
    output(result, "导出朝代作品数据")


@export.command("creators2")
@handle_error
def export_creators2():
    """导出作译者列表（带别名）。

    导出包含别名信息的作译者列表。
    """
    result = get_client().export_all_creators2()
    output(result, "导出作译者数据（带别名）")


@export.command("creators3")
@handle_error
def export_creators3():
    """导出作译者列表（带别名版本3）。"""
    result = get_client().export_all_creators3()
    output(result, "导出作译者数据（别名版本3）")


@export.command("check-list")
@click.option("--canon", "-c", default="J", help="藏经编号 (默认 J)")
@handle_error
def export_check_list(canon):
    """导出检查清单 CSV。

    导出指定藏经的检查清单。
    """
    result = get_client().export_check_list(canon)
    output(result, f"导出 {canon} 藏检查清单")


@export.command("scope-category")
@handle_error
def export_scope_category():
    """导出按部类的范围选择器。"""
    result = get_client().export_scope_selector_by_category()
    output(result, "导出部类范围选择器")


@export.command("scope-vol")
@click.option("--canon", "-c", default=None, help="藏经筛选")
@handle_error
def export_scope_vol(canon):
    """导出按册号的范围选择器。"""
    params = {}
    if canon:
        params["canon"] = canon
    result = get_client().export_scope_selector_by_vol(**params)
    output(result, "导出册号范围选择器")


# ──────────────────────────────────────────────────────────────────
# TextRef 命令组 (TextRef Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def textref():
    """TextRef 命令组 - DocuSky 集成接口。"""
    pass


@textref.command("meta")
@handle_error
def textref_meta():
    """获取 TextRef 元数据。

    用于 DocuSky 系统集成的 CBETA 元数据。
    """
    result = get_client().textref_meta()
    output(result, "TextRef 元数据")


@textref.command("data")
@handle_error
def textref_data():
    """导出 TextRef 数据 CSV。

    用于 DocuSky 系统下载 CBETA 数据。
    """
    result = get_client().textref_data()
    output(result, "TextRef 数据")


# ──────────────────────────────────────────────────────────────────
# Asia Network API 命令组
# ──────────────────────────────────────────────────────────────────
@cli.group()
def asia():
    """Asia Network API 命令组 - UUID 接口。"""
    pass


@asia.command("juans")
@click.argument("uuid")
@handle_error
def asia_juans(uuid):
    """获取作品的卷列表（UUID）。

    示例:
        asia juans <work_uuid>
    """
    result = get_client().juans_by_work_uuid(uuid)
    output(result, f"作品 {uuid} 卷列表")


@asia.command("juan-content")
@click.argument("uuid")
@handle_error
def asia_juan_content(uuid):
    """获取卷内容（UUID）。

    示例:
        asia juan-content <juan_uuid>
    """
    result = get_client().juan_content_by_uuid(uuid)
    output(result, f"卷 {uuid} 内容")


@asia.command("juan-info")
@click.argument("uuid")
@handle_error
def asia_juan_info(uuid):
    """获取卷元数据（UUID）。

    示例:
        asia juan-info <juan_uuid>
    """
    result = get_client().juan_info_by_uuid(uuid)
    output(result, f"卷 {uuid} 元数据")


# ──────────────────────────────────────────────────────────────────
# 会话命令组 (Session Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def session():
    """会话状态命令组。"""
    pass


@session.command("status")
@handle_error
def session_status():
    """显示当前会话状态。"""
    data = {
        "base_url": _base_url,
        "json_output": _json_output,
        "repl_mode": _repl_mode,
    }
    output(data, "会话状态")


@session.command("reset")
@handle_error
def session_reset():
    """重置会话状态。"""
    global _json_output, _client
    _json_output = False
    _client = None
    output({"status": "reset"}, "会话已重置")


# ──────────────────────────────────────────────────────────────────
# 配置命令组 (Config Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def config():
    """配置命令组 - 管理默认设置、API地址、输出格式等。"""
    pass


@config.command("show")
@handle_error
def config_show():
    """显示当前配置。"""
    from cli_anything.cbeta.utils.config import get_config
    cfg = get_config()
    click.echo(cfg.show())


@config.command("init")
@click.option("--force", "-f", is_flag=True, help="强制覆盖现有配置")
@handle_error
def config_init(force):
    """创建默认配置文件。"""
    from cli_anything.cbeta.utils.config import get_config, DEFAULT_CONFIG_FILE
    cfg = get_config()

    if cfg.config_path.exists() and not force:
        click.echo(f"配置文件已存在: {cfg.config_path}")
        click.echo("使用 --force 参数覆盖现有配置")
        return

    cfg.reset()
    cfg.save()
    click.echo(f"已创建配置文件: {cfg.config_path}")
    click.echo(cfg.show())


@config.command("set")
@click.argument("key")
@click.argument("value")
@handle_error
def config_set(key, value):
    """设置配置项。

    KEY 格式支持嵌套，如 'api.base_url' 或 'defaults.rows'

    示例:
        config set api.base_url https://custom.api.com
        config set defaults.rows 20
        config set defaults.canon T
        config set defaults.output_format json
    """
    from cli_anything.cbeta.utils.config import get_config
    cfg = get_config()

    # 尝试转换 value 类型
    try:
        if value.isdigit():
            value = int(value)
        elif value.replace(".", "").isdigit() and "." in value:
            value = float(value)
        elif value.lower() in ("true", "yes", "on"):
            value = True
        elif value.lower() in ("false", "no", "off", "none", "null"):
            value = False if value.lower() != "none" else None
    except:
        pass

    cfg.set(key, value)
    cfg.save()
    click.echo(f"已设置 {key} = {value}")


@config.command("get")
@click.argument("key")
@handle_error
def config_get(key):
    """获取配置项值。"""
    from cli_anything.cbeta.utils.config import get_config
    cfg = get_config()
    value = cfg.get(key)
    click.echo(f"{key}: {value}")


@config.command("reset")
@click.option("--confirm", is_flag=True, help="确认重置")
@handle_error
def config_reset(confirm):
    """重置为默认配置。"""
    if not confirm:
        click.echo("此操作将重置所有配置为默认值。")
        click.echo("使用 --confirm 参数确认执行。")
        return

    from cli_anything.cbeta.utils.config import get_config
    cfg = get_config()
    cfg.reset()
    cfg.save()
    click.echo("配置已重置为默认值")


@config.command("path")
@handle_error
def config_path():
    """显示配置文件路径。"""
    from cli_anything.cbeta.utils.config import DEFAULT_CONFIG_FILE
    click.echo(f"配置文件路径: {DEFAULT_CONFIG_FILE}")


# ──────────────────────────────────────────────────────────────────
# 交互式 REPL (Interactive REPL)
# ──────────────────────────────────────────────────────────────────
@cli.command()
@handle_error
def repl():
    """启动交互式 REPL 模式。"""
    global _repl_mode
    _repl_mode = True

    click.echo("\n" + "═" * 60)
    click.echo("          CBETA CLI v2.6.0")
    click.echo("          中华电子佛典协会 API 工具")
    click.echo("          https://api.cbetaonline.cn")
    click.echo("═" * 60)
    click.echo(f"\nAPI 地址: {_base_url}")
    click.echo("输入 'help' 查看命令列表，'quit' 退出\n")

    _repl_commands = {
        # 搜索命令
        "search query <关键词> [--rows N] [--canon T]": "全文搜索",
        "search kwic <关键词> --work <编号> --juan <卷号>": "KWIC 关键词上下文搜索",
        "search toc <关键词>": "经目搜索 (目录/标题)",
        "search similar --work <编号> [--juan N]": "相似文本搜索",
        "search notes <关键词>": "注释搜索",
        "search title <关键词>": "标题搜索",
        "search variants <关键词>": "异体字搜索",
        "search facet <关键词> --by <字段>": "分面统计",
        # 佛典命令
        "work info <编号>": "佛典详细信息 (如 T0001)",
        "work toc <编号>": "佛典目录结构",
        "work content <编号> --juan N": "佛典全文内容",
        "work list [--canon T] [--category X]": "佛典列表",
        "work wordcount": "字数统计",
        "work download <编号>": "下载信息",
        # 行内容命令
        "line get --head <行标识>": "获取指定行",
        "line range --start H1 --end H2": "获取行范围",
        # 卷命令
        "juan list --work <编号>": "卷列表",
        "juan goto --work <编号> --juan N": "定位到卷",
        # 目录命令
        "catalog category <部类名>": "按部类查询",
        # 工具命令
        "tools sc2tc <简体文本>": "简繁转换",
        "tools wordseg <文本>": "中文分词",
        # 服务器命令
        "server health": "API 健康检查",
        "server stats [--by-canon]": "统计报表",
        "server changes": "数据变更历史",
        # 导出命令
        "export works": "导出佛典列表 (4868部)",
        "export creators": "导出作译者列表",
        "export dynasty": "导出朝代信息",
        # 会话命令
        "session status": "会话状态",
        "session reset": "重置会话",
        # 配置命令
        "config show": "显示当前配置",
        "config init [--force]": "创建配置文件",
        "config set <键> <值>": "设置配置项",
        "config get <键>": "获取配置项",
        "config reset [--confirm]": "重置配置",
        # 其他
        "--json <命令>": "JSON 格式输出",
        "quit": "退出 REPL",
    }

    while True:
        try:
            line = click.prompt("", prompt_suffix="cbeta> ").strip()
            if not line:
                continue
            if line.lower() in ("quit", "exit", "q"):
                click.echo("\n再见！阿弥陀佛！")
                break
            if line.lower() == "help":
                click.echo("\n可用命令:")
                click.echo("─" * 60)
                for cmd, desc in _repl_commands.items():
                    click.echo(f"  {cmd:<45} {desc}")
                click.echo("─" * 60)
                click.echo("")
                continue

            # Parse and execute command
            import shlex
            try:
                args = shlex.split(line)
            except ValueError:
                args = line.split()

            try:
                cli.main(args, standalone_mode=False)
            except SystemExit:
                pass
            except click.exceptions.UsageError as e:
                click.echo(f"用法错误: {e}")
            except Exception as e:
                click.echo(f"错误: {e}")

        except (EOFError, KeyboardInterrupt):
            click.echo("\n再见！阿弥陀佛！")
            break

    _repl_mode = False


# ──────────────────────────────────────────────────────────────────
# 缓存命令组 (Cache Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def cache():
    """缓存命令组 - 管理请求缓存、查看统计、清除缓存。"""
    pass


@cache.command("stats")
@handle_error
def cache_stats():
    """显示缓存统计信息。"""
    from cli_anything.cbeta.utils.cache import get_cache
    c = get_cache()
    stats = c.stats()
    output(stats, "缓存统计")


@cache.command("clear")
@click.option("--expired", "-e", is_flag=True, help="只清除过期缓存")
@handle_error
def cache_clear(expired):
    """清除缓存。"""
    from cli_anything.cbeta.utils.cache import get_cache
    c = get_cache()

    if expired:
        count = c.clear_expired()
        output({"cleared": count}, f"已清除 {count} 条过期缓存")
    else:
        count = c.clear_all()
        output({"cleared": count}, f"已清除所有缓存（{count} 条）")


@cache.command("path")
@handle_error
def cache_path():
    """显示缓存目录路径。"""
    from cli_anything.cbeta.utils.cache import DEFAULT_CACHE_DIR
    click.echo(f"缓存目录: {DEFAULT_CACHE_DIR}")


# ──────────────────────────────────────────────────────────────────
# 离线模式命令组 (Offline Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def offline():
    """离线模式命令组 - 导出数据到本地，支持离线查询。"""
    pass


@offline.command("download")
@click.option("--output-path", "-o", default=None, help="输出文件路径 (默认 ~/.cbeta/offline.db)")
@click.option("--limit", "-l", type=int, default=None, help="限制导出数量")
@click.option("--incremental", "-i", is_flag=True, help="增量更新（只下载新增/更新的佛典）")
@handle_error
def offline_download(output_path, limit, incremental):
    """导出佛典数据到本地 SQLite 数据库。

    导出后可使用 offline query 进行离线查询。

    使用 --incremental 可只更新新增/变化的数据，避免全量重新下载。
    """
    import sqlite3
    from pathlib import Path

    db_path = Path(output_path) if output_path else Path.home() / ".cbeta" / "offline.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    click.echo(f"开始导出到 {db_path}...")

    # 创建数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建表（添加 updated_at 和 checksum 字段支持增量更新）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS works (
            work_id TEXT PRIMARY KEY,
            title TEXT,
            category TEXT,
            canon TEXT,
            juan INTEGER,
            byline TEXT,
            dynasty TEXT,
            time_from INTEGER,
            time_to INTEGER,
            cjk_chars INTEGER,
            updated_at TEXT,
            checksum TEXT,
            data_json TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            timestamp TEXT,
            result_json TEXT
        )
    """)
    # 创建索引加速查询
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_works_canon ON works(canon)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_works_title ON works(title)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_works_category ON works(category)")

    # 增量更新模式
    existing_works = set()
    if incremental and db_path.exists():
        cursor.execute("SELECT work_id, checksum FROM works")
        existing_works = {row[0]: row[1] for row in cursor.fetchall()}
        click.echo(f"增量模式：本地已有 {len(existing_works)} 条数据")

    # 导出佛典列表
    result = get_client().export_all_works()
    # API 直接返回列表
    if isinstance(result, list):
        works = result
    else:
        works = result.get("works", [])

    if limit:
        works = works[:limit]

    count = 0
    skipped = 0
    updated = 0
    current_time = datetime.now().isoformat()

    for work in works:
        work_id = work.get("work", "")
        work_json = json.dumps(work, ensure_ascii=False)
        checksum = hashlib.md5(work_json.encode()).hexdigest()[:16]

        # 增量检查
        if incremental and work_id in existing_works:
            existing_checksum = existing_works.get(work_id)
            if existing_checksum == checksum:
                skipped += 1
                continue  # 数据未变化，跳过
            else:
                updated += 1  # 数据已变化，需要更新

        cursor.execute("""
            INSERT OR REPLACE INTO works
            (work_id, title, category, canon, juan, byline, dynasty, time_from, time_to, cjk_chars, updated_at, checksum, data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            work_id,
            work.get("title", ""),
            work.get("category", ""),
            work.get("canon", ""),
            work.get("juan", 0),
            work.get("byline", ""),
            work.get("time_dynasty", ""),
            work.get("time_from", 0),
            work.get("time_to", 0),
            work.get("cjk_chars", 0),
            current_time,
            checksum,
            work_json
        ))
        count += 1
        if count % 100 == 0:
            click.echo(f"已处理 {count} 条...")

    conn.commit()
    conn.close()

    if incremental:
        output({
            "count": count,
            "skipped": skipped,
            "updated": updated,
            "path": str(db_path)
        }, f"增量更新完成：新增 {count} 条，跳过 {skipped} 条，更新 {updated} 条")
    else:
        output({"count": count, "path": str(db_path)}, f"导出完成，共 {count} 条")


@offline.command("query")
@click.argument("keyword")
@click.option("--canon", "-c", default=None, help="藏经筛选")
@click.option("--limit", "-l", type=int, default=10, help="返回数量")
@handle_error
def offline_query(keyword, canon, limit):
    """离线搜索（使用本地数据库）。

    需要先运行 offline download 导出数据。
    """
    import sqlite3
    from pathlib import Path

    db_path = Path.home() / ".cbeta" / "offline.db"
    if not db_path.exists():
        click.echo("离线数据库不存在，请先运行 offline download")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 搜索标题
    query = """
        SELECT work_id, title, category, canon, juan, byline
        FROM works
        WHERE title LIKE ?
    """
    params = [f"%{keyword}%"]

    if canon:
        query += " AND canon = ?"
        params.append(canon)

    query += f" LIMIT {limit}"

    cursor.execute(query, params)
    rows = cursor.fetchall()

    conn.close()

    results = []
    for row in rows:
        results.append({
            "work": row[0],
            "title": row[1],
            "category": row[2],
            "canon": row[3],
            "juan": row[4],
            "byline": row[5]
        })

    output({"results": results, "num_found": len(results)}, f"离线搜索 '{keyword}' 找到 {len(results)} 条结果")


@offline.command("info")
@click.argument("work_id")
@handle_error
def offline_info(work_id):
    """离线查询佛典信息（使用本地数据库）。"""
    import sqlite3
    from pathlib import Path

    db_path = Path.home() / ".cbeta" / "offline.db"
    if not db_path.exists():
        click.echo("离线数据库不存在，请先运行 offline download")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT work_id, title, category, canon, juan, byline, dynasty, time_from, time_to, cjk_chars, data_json
        FROM works WHERE work_id = ?
    """, [work_id])

    row = cursor.fetchone()
    conn.close()

    if row:
        data = json.loads(row[10]) if row[10] else {}
        output(data, f"佛典 {work_id} 信息")
    else:
        click.echo(f"未找到佛典 {work_id}")


@offline.command("status")
@handle_error
def offline_status():
    """显示离线数据库状态。"""
    import sqlite3
    from pathlib import Path

    db_path = Path.home() / ".cbeta" / "offline.db"
    if not db_path.exists():
        output({"status": "不存在"}, "离线数据库不存在，请运行 offline download")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM works")
    works_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM searches")
    searches_count = cursor.fetchone()[0]

    # 统计藏经分布
    cursor.execute("SELECT canon, COUNT(*) FROM works GROUP BY canon")
    canon_stats = cursor.fetchall()

    conn.close()

    status = {
        "db_path": str(db_path),
        "works_count": works_count,
        "searches_count": searches_count,
        "canon_distribution": {c[0]: c[1] for c in canon_stats}
    }
    output(status, "离线数据库状态")


# ──────────────────────────────────────────────────────────────────
# 批量操作命令组 (Batch Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def batch():
    """批量操作命令组 - 批量搜索、下载、导出。"""
    pass


@batch.command("search")
@click.option("--keywords", "-k", required=True, help="关键词列表 (逗号分隔)")
@click.option("--output-path", "-o", default=None, help="输出文件路径")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "csv", "excel", "markdown", "html"]), help="输出格式")
@click.option("--rows", "-r", type=int, default=10, help="每个关键词返回数量")
@click.option("--canon", "-c", default=None, help="藏经筛选")
@handle_error
def batch_search(keywords, output_path, format, rows, canon):
    """批量搜索多个关键词。

    示例:
        batch search --keywords "般若,金刚,法华" --output results.csv --format csv
    """
    from pathlib import Path
    from cli_anything.cbeta.utils.exporters import get_exporter

    keyword_list = [k.strip() for k in keywords.split(",")]
    all_results = []

    for kw in keyword_list:
        click.echo(f"搜索 '{kw}'...")
        params = {"rows": rows}
        if canon:
            params["canon"] = canon

        result = get_client().search(kw, **params)
        all_results.append({
            "keyword": kw,
            "num_found": result.get("num_found", 0),
            "results": result.get("results", [])
        })

    # 汇总结果
    summary = {
        "total_keywords": len(keyword_list),
        "searches": all_results,
        "generated_at": datetime.now().isoformat()
    }

    if output_path:
        file_path = Path(output_path)
        exporter = get_exporter(format)
        exporter(summary, file_path)
        click.echo(f"结果已保存到 {file_path}")
    else:
        output(summary, f"批量搜索完成，共 {len(keyword_list)} 个关键词")


@batch.command("download")
@click.option("--works", "-w", required=True, help="佛典编号列表 (逗号分隔)")
@click.option("--output-dir", "-o", default="./downloads", help="输出目录")
@click.option("--format", "-f", default="markdown", type=click.Choice(["json", "csv", "markdown", "html"]), help="输出格式")
@handle_error
def batch_download(works, output_dir, format):
    """批量下载多个佛典信息。

    示例:
        batch download --works T0001,T0002,T0003 --output-dir ./downloads
    """
    import os
    from pathlib import Path
    from cli_anything.cbeta.utils.exporters import get_exporter

    work_list = [w.strip() for w in works.split(",")]
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    all_results = []
    for work_id in work_list:
        click.echo(f"获取 {work_id}...")
        result = get_client().works(work=work_id)
        results = result.get("results", [])
        if results:
            work_data = results[0]
            all_results.append(work_data)

            # 保存单个佛典文件
            exporter = get_exporter(format)
            file_path = output_path / f"{work_id}.{format}"
            exporter(work_data, file_path)
            click.echo(f"  -> {file_path}")

    # 汇总文件
    summary_path = output_path / f"summary.{format}"
    exporter = get_exporter(format)
    exporter({"works": all_results, "count": len(all_results)}, summary_path)

    output({"count": len(all_results), "output_dir": str(output_path)}, f"批量下载完成，共 {len(all_results)} 个佛典")


@batch.command("export")
@click.option("--query", "-q", default=None, help="搜索关键词（可选）")
@click.option("--canon", "-c", default=None, help="藏经筛选")
@click.option("--output-path", "-o", required=True, help="输出文件路径")
@click.option("--format", "-f", default="csv", type=click.Choice(["json", "csv", "excel", "markdown", "html"]), help="输出格式")
@click.option("--limit", "-l", type=int, default=100, help="限制数量")
@handle_error
def batch_export(query, canon, output_path, format, limit):
    """批量导出数据到文件。

    示例:
        batch export --query 般若 --output results.xlsx --format excel --limit 50
        batch export --canon T --output t_works.csv --format csv --limit 200
    """
    from pathlib import Path
    from cli_anything.cbeta.utils.exporters import get_exporter

    file_path = Path(output_path)
    exporter = get_exporter(format)

    if query:
        # 从搜索结果导出
        click.echo(f"搜索 '{query}'...")
        params = {"rows": limit}
        if canon:
            params["canon"] = canon

        result = get_client().search(query, **params)
        exporter(result, file_path)
    else:
        # 从佛典列表导出
        click.echo("导出佛典列表...")
        params = {}
        if canon:
            params["canon"] = canon

        result = get_client().works(**params)
        results = result.get("results", [])[:limit]
        exporter({"results": results, "count": len(results)}, file_path)

    click.echo(f"已导出到 {file_path}")


# ──────────────────────────────────────────────────────────────────
# 分析命令组 (Analyze Commands)
# ──────────────────────────────────────────────────────────────────
@cli.group()
def analyze():
    """分析命令组 - 词频分析、分布分析、统计图表。"""
    pass


@analyze.command("frequency")
@click.argument("keyword")
@click.option("--canon", "-c", default=None, help="藏经筛选")
@click.option("--chart", "-o", default=None, help="输出图表文件 (PNG)")
@click.option("--top", "-t", type=int, default=10, help="显示前 N 条")
@handle_error
def analyze_frequency(keyword, canon, chart, top):
    """分析关键词在各藏经中的词频分布。

    示例:
        analyze frequency "般若" --canon T
        analyze frequency "金刚" --chart frequency.png
    """
    # 搜索关键词
    params = {"rows": 100}
    if canon:
        params["canon"] = canon

    result = get_client().search(keyword, **params)
    results = result.get("results", [])

    # 按藏经统计词频
    canon_freq = {}
    work_freq = {}

    for r in results:
        c = r.get("canon", "未知")
        w = r.get("work", "")
        hits = r.get("term_hits", 0)

        canon_freq[c] = canon_freq.get(c, 0) + hits
        work_freq[w] = work_freq.get(w, 0) + hits

    # 排序
    top_canon = sorted(canon_freq.items(), key=lambda x: x[1], reverse=True)[:top]
    top_works = sorted(work_freq.items(), key=lambda x: x[1], reverse=True)[:top]

    analysis = {
        "keyword": keyword,
        "total_hits": result.get("total_term_hits", 0),
        "num_found": result.get("num_found", 0),
        "canon_distribution": dict(top_canon),
        "top_works": dict(top_works)
    }

    output(analysis, f"'{keyword}' 词频分析")

    # 生成图表
    if chart:
        from pathlib import Path
        from cli_anything.cbeta.utils.charts import generate_bar_chart

        file_path = Path(chart)
        generate_bar_chart(dict(top_canon), f"'{keyword}' 各藏经词频分布", file_path, xlabel="藏经", ylabel="词频")
        click.echo(f"图表已保存到 {file_path}")


@analyze.command("distribution")
@click.option("--by", "-b", default="canon", type=click.Choice(["canon", "category", "dynasty"]), help="统计维度")
@click.option("--chart", "-o", default=None, help="输出图表文件 (PNG)")
@handle_error
def analyze_distribution(by, chart):
    """分析佛典分布统计。

    示例:
        analyze distribution --by canon
        analyze distribution --by category --chart distribution.png
    """
    # 获取统计数据
    stats = get_client().report_total()

    if by == "canon":
        # 各藏经佛典数量
        result = get_client().search_facet("canon")
        distribution = {}
        for r in result.get("results", [])[:20]:
            canon = r.get("canon", "")
            count = r.get("count", 0)
            if canon:
                distribution[canon] = count

        output({"distribution": distribution, "by": "canon"}, "藏经分布统计")

        if chart:
            from pathlib import Path
            from cli_anything.cbeta.utils.charts import generate_pie_chart

            file_path = Path(chart)
            generate_pie_chart(distribution, "各藏经佛典数量分布", file_path)
            click.echo(f"图表已保存到 {file_path}")

    elif by == "category":
        # 部类分布
        result = get_client().search_facet("category")
        distribution = {}
        for r in result.get("results", [])[:20]:
            cat = r.get("category", "")
            count = r.get("count", 0)
            if cat:
                distribution[cat] = count

        output({"distribution": distribution, "by": "category"}, "部类分布统计")

        if chart:
            from pathlib import Path
            from cli_anything.cbeta.utils.charts import generate_bar_chart

            file_path = Path(chart)
            generate_bar_chart(distribution, "各部类佛典数量分布", file_path, xlabel="部类", ylabel="数量")

    elif by == "dynasty":
        # 朝代分布
        result = get_client().search_facet("dynasty")
        distribution = {}
        for r in result.get("results", [])[:20]:
            dynasty = r.get("dynasty", "")
            count = r.get("count", 0)
            if dynasty:
                distribution[dynasty] = count

        output({"distribution": distribution, "by": "dynasty"}, "朝代分布统计")

        if chart:
            from pathlib import Path
            from cli_anything.cbeta.utils.charts import generate_bar_chart

            file_path = Path(chart)
            generate_bar_chart(distribution, "各朝代佛典数量分布", file_path, xlabel="朝代", ylabel="数量")


@analyze.command("compare")
@click.option("--keywords", "-k", required=True, help="关键词列表 (逗号分隔)")
@click.option("--chart", "-o", default=None, help="输出图表文件 (PNG)")
@handle_error
def analyze_compare(keywords, chart):
    """对比多个关键词的词频。

    示例:
        analyze compare --keywords "般若,金刚,法华"
        analyze compare --keywords "佛,法,僧" --chart compare.png
    """
    keyword_list = [k.strip() for k in keywords.split(",")]
    comparison = {}

    for kw in keyword_list:
        result = get_client().search(kw, rows=50)
        comparison[kw] = {
            "total_hits": result.get("total_term_hits", 0),
            "num_found": result.get("num_found", 0)
        }

    output({"comparison": comparison, "keywords": keyword_list}, "关键词词频对比")

    if chart:
        from pathlib import Path
        from cli_anything.cbeta.utils.charts import generate_bar_chart

        file_path = Path(chart)
        # 对比图
        data = {k: comparison[k]["total_hits"] for k in keyword_list}
        generate_bar_chart(data, "关键词词频对比", file_path, xlabel="关键词", ylabel="词频")
        click.echo(f"图表已保存到 {file_path}")


@analyze.command("timeline")
@click.argument("keyword")
@click.option("--chart", "-o", default=None, help="输出图表文件 (PNG)")
@click.option("--limit", "-l", type=int, default=50, help="数据点数量")
@handle_error
def analyze_timeline(keyword, chart, limit):
    """分析关键词的时间分布。

    示例:
        analyze timeline "般若" --chart timeline.png
    """
    # 搜索并按时间排序
    result = get_client().search(keyword, rows=limit, order="time_from+")
    results = result.get("results", [])

    # 按时间统计
    time_data = []
    for r in results:
        time_from = r.get("time_from", 0)
        if time_from > 0:
            time_data.append({
                "year": time_from,
                "hits": r.get("term_hits", 0),
                "work": r.get("work", ""),
                "title": r.get("title", "")
            })

    output({"keyword": keyword, "time_data": time_data}, f"'{keyword}' 时间分布分析")

    if chart and time_data:
        from pathlib import Path
        from cli_anything.cbeta.utils.charts import generate_line_chart

        file_path = Path(chart)
        generate_line_chart(time_data, "year", "hits", f"'{keyword}' 时间分布", file_path)
        click.echo(f"图表已保存到 {file_path}")


@analyze.command("chart")
@click.argument("data_file", type=click.Path(exists=True))
@click.option("--type", "-t", type=click.Choice(["bar", "pie", "line", "wordcloud"]), default="bar", help="图表类型")
@click.option("--title", default=None, help="图表标题")
@click.option("--output", "-o", required=True, help="输出图片路径 (PNG)")
@click.option("--xlabel", default=None, help="X轴标签")
@click.option("--ylabel", default=None, help="Y轴标签")
@handle_error
def analyze_chart(data_file, type, title, output, xlabel, ylabel):
    """从 JSON 数据文件生成图表。

    数据文件格式支持：
    - 字典格式: {"T": 100, "X": 50, "K": 30} (适用于 bar/pie)
    - 列表格式: [{"word": "般若", "count": 100}, ...] (适用于 bar/wordcloud)
    - 时间格式: [{"year": 100, "hits": 50}, ...] (适用于 line)

    示例:
        analyze chart data.json --type bar --output chart.png
        analyze chart data.json --type pie --title "分布图" -o pie.png
        analyze chart keywords.json --type wordcloud -o cloud.png
    """
    from pathlib import Path
    import json

    # 读取数据文件
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 处理列表格式数据
    if isinstance(data, list):
        if type == "bar":
            # 从列表提取 key-value
            if data and isinstance(data[0], dict):
                # 尝试自动识别字段
                keys = list(data[0].keys())
                if "word" in keys and "count" in keys:
                    data = {item["word"]: item["count"] for item in data}
                elif "name" in keys and "value" in keys:
                    data = {item["name"]: item["value"] for item in data}
                elif "key" in keys and "value" in keys:
                    data = {item["key"]: item["value"] for item in data}
        elif type == "line":
            # 保持列表格式，需要 x_field 和 y_field
            pass

    file_path = Path(output)
    chart_title = title or "数据分析图表"

    from cli_anything.cbeta.utils.charts import (
        generate_bar_chart, generate_pie_chart,
        generate_line_chart, generate_wordcloud
    )

    if type == "bar":
        generate_bar_chart(data, chart_title, file_path, xlabel=xlabel, ylabel=ylabel)
    elif type == "pie":
        generate_pie_chart(data, chart_title, file_path)
    elif type == "line":
        # line 图需要字段名参数
        if isinstance(data, list) and data:
            x_field = xlabel or list(data[0].keys())[0]
            y_field = ylabel or list(data[0].keys())[1] if len(data[0]) > 1 else list(data[0].keys())[0]
            generate_line_chart(data, x_field, y_field, chart_title, file_path)
        else:
            click.echo("line 图表需要列表格式数据")
            return
    elif type == "wordcloud":
        # wordcloud 需要词频字典或列表
        generate_wordcloud(data, chart_title, file_path)

    click.echo(f"图表已保存到 {file_path}")


# ──────────────────────────────────────────────────────────────────
# 命令补全 (Shell Completion)
# ──────────────────────────────────────────────────────────────────
@cli.command("completion")
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish", "powershell"]))
@click.option("--install", "-i", is_flag=True, help="输出安装指令")
@handle_error
def completion(shell, install):
    """生成 shell 命令补全脚本。

    支持的 shell: bash, zsh, fish, powershell

    示例:
        # Bash
        python -m cli_anything.cbeta completion bash > ~/.cbeta-completion.bash
        source ~/.cbeta-completion.bash

        # Zsh
        python -m cli_anything.cbeta completion zsh > ~/.cbeta-completion.zsh
        source ~/.cbeta-completion.zsh

        # 一键安装提示
        python -m cli_anything.cbeta completion bash --install
    """
    commands = [
        "search", "work", "line", "juan", "catalog",
        "tools", "server", "export", "session", "config", "repl"
    ]
    search_subcmds = ["query", "kwic", "toc", "similar", "notes", "title", "variants", "facet"]
    work_subcmds = ["info", "toc", "content", "list", "wordcount", "download"]
    server_subcmds = ["health", "stats", "changes"]
    export_subcmds = ["works", "creators", "dynasty", "strokes"]
    config_subcmds = ["show", "init", "set", "get", "reset", "path"]

    if shell == "bash":
        script = f'''# CBETA CLI Bash Completion
_cbeta_complete() {{
    local cur prev words
    COMPREPLY=()
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    # Main commands
    local main_cmds="{' '.join(commands)}"
    local search_cmds="{' '.join(search_subcmds)}"
    local work_cmds="{' '.join(work_subcmds)}"
    local server_cmds="{' '.join(server_subcmds)}"
    local export_cmds="{' '.join(export_subcmds)}"
    local config_cmds="{' '.join(config_subcmds)}"

    # Complete main commands
    if [[ $prev == "cli-anything-cbeta" || $prev == "python" && ${{COMP_WORDS[COMP_CWORD-2]}} == "-m" ]]; then
        COMPREPLY=( $(compgen -W "${{main_cmds}}" -- $cur) )
        return 0
    fi

    # Complete subcommands
    case $prev in
        search)
            COMPREPLY=( $(compgen -W "${{search_cmds}}" -- $cur) )
            ;;
        work)
            COMPREPLY=( $(compgen -W "${{work_cmds}}" -- $cur) )
            ;;
        server)
            COMPREPLY=( $(compgen -W "${{server_cmds}}" -- $cur) )
            ;;
        export)
            COMPREPLY=( $(compgen -W "${{export_cmds}}" -- $cur) )
            ;;
        config)
            COMPREPLY=( $(compgen -W "${{config_cmds}}" -- $cur) )
            ;;
        --canon|-c)
            COMPREPLY=( $(compgen -W "T X A K S F C D U P J L G M N GA GB ZS ZW B" -- $cur) )
            ;;
        --category|-cat)
            COMPREPLY=( $(compgen -W "本缘部类 阿含部类 般若部类 法华部类 华严部类 宝积部类 涅槃部类 大集部类 经集部类 密教部类 律部类 毘昙部类 中观部类 瑜伽部类 论集部类 净土宗部类 禅宗部类 史传部类 事汇部类" -- $cur) )
            ;;
    esac
    return 0
}}
complete -F _cbeta_complete cli-anything-cbeta
complete -F _cbeta_complete python -m cli_anything.cbeta
'''
    elif shell == "zsh":
        script = f'''# CBETA CLI Zsh Completion
#compdef cli-anything-cbeta

_cbeta() {{
    local -a commands
    commands=(
        'search:搜索命令组'
        'work:佛典命令组'
        'line:行内容命令组'
        'juan:卷命令组'
        'catalog:目录命令组'
        'tools:工具命令组'
        'server:服务器命令组'
        'export:导出命令组'
        'session:会话命令组'
        'config:配置命令组'
        'repl:交互式 REPL'
    )

    _describe 'command' commands
}}

_cbeta_search() {{
    local -a subcmds
    subcmds=(
        'query:全文搜索'
        'kwic:KWIC 关键词上下文'
        'toc:经目搜索'
        'similar:相似文本搜索'
        'notes:注释搜索'
        'title:标题搜索'
        'variants:异体字搜索'
        'facet:分面统计'
    )
    _describe 'subcommand' subcmds
}}

_cbeta_work() {{
    local -a subcmds
    subcmds=(
        'info:佛典信息'
        'toc:佛典目录'
        'content:佛典全文'
        'list:佛典列表'
        'wordcount:字数统计'
        'download:下载信息'
    )
    _describe 'subcommand' subcmds
}}

_cbeta() {{
    case ${{words[2]}} in
        search) _cbeta_search ;;
        work) _cbeta_work ;;
    esac
}}

_cbeta
'''
    elif shell == "fish":
        script = f'''# CBETA CLI Fish Completion
complete -c cli-anything-cbeta -n '__fish_use_subcommand' -a 'search' -d '搜索命令组'
complete -c cli-anything-cbeta -n '__fish_use_subcommand' -a 'work' -d '佛典命令组'
complete -c cli-anything-cbeta -n '__fish_use_subcommand' -a 'line' -d '行内容命令组'
complete -c cli-anything-cbeta -n '__fish_use_subcommand' -a 'juan' -d '卷命令组'
complete -c cli-anything-cbeta -n '__fish_use_subcommand' -a 'catalog' -d '目录命令组'
complete -c cli-anything-cbeta -n '__fish_use_subcommand' -a 'tools' -d '工具命令组'
complete -c cli-anything-cbeta -n '__fish_use_subcommand' -a 'server' -d '服务器命令组'
complete -c cli-anything-cbeta -n '__fish_use_subcommand' -a 'export' -d '导出命令组'
complete -c cli-anything-cbeta -n '__fish_use_subcommand' -a 'config' -d '配置命令组'
complete -c cli-anything-cbeta -n '__fish_use_subcommand' -a 'repl' -d '交互式 REPL'

# Search subcommands
complete -c cli-anything-cbeta -n '__fish_seen_subcommand_from search' -a 'query' -d '全文搜索'
complete -c cli-anything-cbeta -n '__fish_seen_subcommand_from search' -a 'kwic' -d 'KWIC'
complete -c cli-anything-cbeta -n '__fish_seen_subcommand_from search' -a 'toc' -d '经目搜索'
complete -c cli-anything-cbeta -n '__fish_seen_subcommand_from search' -a 'variants' -d '异体字搜索'

# Work subcommands
complete -c cli-anything-cbeta -n '__fish_seen_subcommand_from work' -a 'info' -d '佛典信息'
complete -c cli-anything-cbeta -n '__fish_seen_subcommand_from work' -a 'toc' -d '佛典目录'
complete -c cli-anything-cbeta -n '__fish_seen_subcommand_from work' -a 'content' -d '佛典全文'
'''
    elif shell == "powershell":
        script = f'''# CBETA CLI PowerShell Completion
Register-ArgumentCompleter -Native -CommandName 'cli-anything-cbeta' -ScriptBlock {{
    param($wordToComplete, $commandAst, $cursorPosition)
    $commands = @(
        'search', 'work', 'line', 'juan', 'catalog',
        'tools', 'server', 'export', 'config', 'repl'
    )
    $commands | Where-Object {{ $_ -like "$wordToComplete*" }} | ForEach-Object {{
        [System.Management.Automation.CompletionResult]::new($_, $_, 'ParameterValue', $_)
    }}
}}
'''

    click.echo(script)

    if install:
        click.echo(f"\n安装步骤 ({shell}):")
        if shell == "bash":
            click.echo("  1. 保存脚本: python -m cli_anything.cbeta completion bash > ~/.cbeta-completion.bash")
            click.echo("  2. 添加到 ~/.bashrc: source ~/.cbeta-completion.bash")
            click.echo("  3. 重新加载: source ~/.bashrc")
        elif shell == "zsh":
            click.echo("  1. 保存脚本: python -m cli_anything.cbeta completion zsh > ~/.cbeta-completion.zsh")
            click.echo("  2. 添加到 ~/.zshrc: source ~/.cbeta-completion.zsh")
            click.echo("  3. 重新加载: source ~/.zshrc")
        elif shell == "fish":
            click.echo("  1. 保存脚本: python -m cli_anything.cbeta completion fish > ~/.config/fish/completions/cbeta.fish")
            click.echo("  2. 重新加载: source ~/.config/fish/config.fish")
        elif shell == "powershell":
            click.echo("  1. 保存脚本到 PowerShell profile")


# ── Entry Point ─────────────────────────────────────────────────
def main():
    cli()


if __name__ == "__main__":
    main()