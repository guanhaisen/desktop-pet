"""资源路径解析工具，兼容开发环境与 PyInstaller 打包环境。"""

import os
import sys


def get_project_root() -> str:
    """返回项目根目录路径。

    开发环境：基于当前文件位置向上定位。
    打包环境：使用 sys._MEIPASS（PyInstaller 临时解压目录）。
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    # 当前文件: src/utils/path_helper.py → 向上两层到项目根
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def asset_path(*parts: str) -> str:
    """构建 assets 目录下的资源绝对路径。

    用法: asset_path('yuexinmiao', 'idle.gif')
    """
    return os.path.join(get_project_root(), 'assets', *parts)


def config_path(filename: str) -> str:
    """构建 config 目录下的配置文件绝对路径。

    用法: config_path('app_config.json')
    """
    return os.path.join(get_project_root(), 'config', filename)


def ensure_config_dir() -> None:
    """确保 config 目录存在（首次运行时创建）。"""
    config_dir = os.path.join(get_project_root(), 'config')
    os.makedirs(config_dir, exist_ok=True)
