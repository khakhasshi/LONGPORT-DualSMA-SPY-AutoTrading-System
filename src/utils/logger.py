import logging
import os
from pathlib import Path
from rich.logging import RichHandler
from datetime import datetime

def setup_logger(name: str = "realtrade", level: str = "INFO", log_dir: str = "logs"):
    """
    配置日志记录器
    
    Args:
        name: Logger 名称
        level: 日志级别 (INFO, DEBUG, WARNING, ERROR)
        log_dir: 日志文件存储目录
    """
    # 确保日志目录存在
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # 获取根 logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 清除现有的 handlers 防止重复
    if logger.handlers:
        logger.handlers.clear()
        
    # 格式化器
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 1. 控制台 Handler (使用 Rich)
    # RichHandler 自动处理 timestamp 和 level 颜色，不需要复杂的 formatter
    console_handler = RichHandler(
        rich_tracebacks=True,
        show_time=True,
        show_path=False
    )
    console_handler.setLevel(level)
    logger.addHandler(console_handler)
    
    # 2. 文件 Handler (按日期轮转或单文件)
    # 这里简单使用按日期命名的文件
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{today}.log")
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = "realtrade"):
    return logging.getLogger(name)

