"""统一日志工具。"""

import logging
import sys


def setup_logger(name: str = 'yuexinmiao', level: int = logging.INFO) -> logging.Logger:
    """配置并返回一个带控制台输出的 logger。"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if sys.stdout is not None:
        # 有控制台时输出到 stdout（python.exe）
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    else:
        # 无控制台时（pythonw.exe）写日志到文件，避免崩溃
        import os
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(os.path.join(log_dir, 'pet.log'), encoding='utf-8')
        handler.setLevel(level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


logger = setup_logger()
