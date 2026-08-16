"""资源路径解析工具，兼容开发环境与 PyInstaller 打包环境。"""

import os
import shutil
import sys


def _is_frozen() -> bool:
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_project_root() -> str:
    """只读资源（assets、内置默认 config）根目录。

    打包环境：sys._MEIPASS（PyInstaller 临时解压目录，只读）。
    开发环境：项目根目录。
    """
    if _is_frozen():
        return sys._MEIPASS
    # 当前文件: src/utils/path_helper.py → 向上两层到项目根
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_user_data_dir() -> str:
    """可写数据目录（运行时 config、日志）。

    打包环境：%APPDATA%\\YuexinMiao（可持久化）。
    开发环境：项目根目录（保持原有行为）。
    """
    if _is_frozen():
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        return os.path.join(base, 'YuexinMiao')
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def asset_path(*parts: str) -> str:
    """构建 assets 目录下的资源绝对路径（只读）。

    用法: asset_path('yuexinmiao', 'idle.gif')
    """
    return os.path.join(get_project_root(), 'assets', *parts)


def config_path(filename: str) -> str:
    """构建 config 目录下的配置文件绝对路径（可读写）。

    用法: config_path('app_config.json')
    """
    return os.path.join(get_user_data_dir(), 'config', filename)


def ensure_config_dir() -> None:
    """确保用户 config 目录存在；打包首次运行时迁移内置默认配置。"""
    user_config_dir = os.path.join(get_user_data_dir(), 'config')
    os.makedirs(user_config_dir, exist_ok=True)

    if _is_frozen():
        builtin_config_dir = os.path.join(get_project_root(), 'config')
        if os.path.isdir(builtin_config_dir):
            for name in os.listdir(builtin_config_dir):
                src = os.path.join(builtin_config_dir, name)
                dst = os.path.join(user_config_dir, name)
                if os.path.isfile(src) and not os.path.exists(dst):
                    try:
                        shutil.copy2(src, dst)
                    except OSError:
                        pass
