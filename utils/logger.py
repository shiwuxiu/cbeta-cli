"""Logging system for CBETA CLI.

记录操作历史到 ~/.cbeta/logs/ 目录，支持：
- 搜索关键词记录
- API 请求时间记录
- 错误日志
- 操作审计
- 按天分割日志文件
"""

import os
import json
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


# 默认日志目录
DEFAULT_LOG_DIR = Path.home() / ".cbeta" / "logs"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "cbeta.log"
OPERATIONS_LOG = DEFAULT_LOG_DIR / "operations.json"


class CbetaLogger:
    """CBETA CLI 日志管理类."""

    def __init__(self, log_dir: Optional[Path] = None, level: str = "INFO",
                 rotation_days: int = 1, backup_count: int = 30):
        self.log_dir = log_dir or DEFAULT_LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 设置 Python logging
        self.logger = logging.getLogger("cbeta")
        level_int = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(level_int)

        # 使用 TimedRotatingFileHandler 实现按天分割
        log_file = self.log_dir / "cbeta.log"
        file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when="midnight" if rotation_days == 1 else f"D{rotation_days}",
            interval=rotation_days,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.suffix = "%Y-%m-%d"
        file_handler.setLevel(logging.DEBUG)

        # 格式
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)

        # 清除已有 handlers，添加新 handler
        self.logger.handlers.clear()
        self.logger.addHandler(file_handler)

        # 操作记录（JSON 格式）
        self.operations_file = self.log_dir / "operations.json"
        self._init_operations_log()

    def _init_operations_log(self):
        """初始化操作记录文件."""
        if not self.operations_file.exists():
            self.operations_file.write_text("[]", encoding="utf-8")

    def log(self, level: str, message: str, **kwargs):
        """记录日志."""
        level_method = getattr(self.logger, level.lower(), self.logger.info)
        level_method(message, **kwargs)

    def info(self, message: str, **kwargs):
        """记录 INFO 级别日志."""
        self.logger.info(message, **kwargs)

    def debug(self, message: str, **kwargs):
        """记录 DEBUG 级别日志."""
        self.logger.debug(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """记录 WARNING 级别日志."""
        self.logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """记录 ERROR 级别日志."""
        self.logger.error(message, **kwargs)

    def log_operation(self, operation: str, params: Dict[str, Any], result: Optional[Dict] = None):
        """记录操作到 JSON 文件."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "params": params,
            "result_summary": self._summarize_result(result) if result else None
        }

        # 读取现有记录
        try:
            records = json.loads(self.operations_file.read_text(encoding="utf-8"))
        except:
            records = []

        # 添加新记录
        records.append(entry)

        # 限制记录数量（保留最近 1000 条）
        if len(records) > 1000:
            records = records[-1000:]

        # 写入文件
        self.operations_file.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def _summarize_result(self, result: Dict) -> Dict:
        """摘要结果（不记录完整数据）."""
        if isinstance(result, dict):
            return {
                "num_found": result.get("num_found"),
                "total_term_hits": result.get("total_term_hits"),
                "results_count": len(result.get("results", []))
            }
        return {"type": type(result).__name__}

    def log_api_request(self, endpoint: str, params: Dict, duration_ms: float, success: bool):
        """记录 API 请求."""
        self.info(
            f"API Request: {endpoint} | params={params} | duration={duration_ms:.0f}ms | success={success}"
        )

    def log_search(self, query: str, filters: Dict, num_found: int):
        """记录搜索操作."""
        self.log_operation(
            operation="search",
            params={"query": query, "filters": filters},
            result={"num_found": num_found}
        )
        self.info(f"Search: '{query}' found {num_found} results")

    def log_work_access(self, work_id: str, operation: str):
        """记录佛典访问."""
        self.log_operation(
            operation=f"work_{operation}",
            params={"work": work_id}
        )
        self.info(f"Work access: {work_id} - {operation}")

    def get_recent_operations(self, limit: int = 50) -> list:
        """获取最近的操作记录."""
        try:
            records = json.loads(self.operations_file.read_text(encoding="utf-8"))
            return records[-limit:]
        except:
            return []

    def clear_logs(self):
        """清除所有日志."""
        self.operations_file.write_text("[]", encoding="utf-8")
        log_file = self.log_dir / "cbeta.log"
        if log_file.exists():
            log_file.write_text("", encoding="utf-8")


# 全局日志实例
_logger_instance: Optional[CbetaLogger] = None


def get_logger(level: Optional[str] = None) -> CbetaLogger:
    """获取全局日志实例，从配置读取默认设置."""
    global _logger_instance
    if _logger_instance is None:
        # 从配置读取日志设置
        try:
            from cli_anything.cbeta.utils.config import get_config
            config = get_config()
            level = level or config.logging_level
            rotation_days = config.logging_rotation_days
            backup_count = config.logging_backup_count
        except:
            level = level or "INFO"
            rotation_days = 1
            backup_count = 30
        _logger_instance = CbetaLogger(
            level=level,
            rotation_days=rotation_days,
            backup_count=backup_count
        )
    return _logger_instance


def log_search(query: str, filters: Dict, num_found: int):
    """便捷函数：记录搜索."""
    get_logger().log_search(query, filters, num_found)


def log_operation(operation: str, params: Dict, result: Optional[Dict] = None):
    """便捷函数：记录操作."""
    get_logger().log_operation(operation, params, result)