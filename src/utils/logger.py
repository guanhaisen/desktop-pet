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
        # 无控制台时（pythonw.exe / 打包 --windowed）写日志到用户数据目录，避免崩溃
        import os
        from src.utils.path_helper import get_user_data_dir
        log_dir = os.path.join(get_user_data_dir(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(os.path.join(log_dir, 'pet.log'), encoding='utf-8')
        handler.setLevel(level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


logger = setup_logger()
