"""
日志工具
"""

import logging
import sys
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """
    配置日志系统

    参数:
        level: 日志级别（DEBUG/INFO/WARNING/ERROR）
        log_file: 日志文件路径（可选）
    """
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handlers = [logging.StreamHandler(sys.stderr)]
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        datefmt=datefmt,
        handlers=handlers,
    )


def get_logger(name: str) -> logging.Logger:
    """获取命名日志器"""
    return logging.getLogger(f"code_agent_pipeline.{name}")
