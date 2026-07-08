"""配置管理器（单例），负责 JSON 配置文件的读写与持久化。"""

import json
import os
import tempfile

from src.config.app_config import AppConfig
from src.utils.path_helper import config_path, ensure_config_dir
from src.utils.logger import logger


class ConfigManager:
    """应用配置与提醒数据的集中读写管理。

    采用临时文件 + 原子替换写入，避免异常中断损坏配置。
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        ensure_config_dir()
        self._app_config: AppConfig = self._load_app_config()

    @property
    def app_config(self) -> AppConfig:
        return self._app_config

    # ── 应用配置 ──────────────────────────────────────────

    def _load_app_config(self) -> AppConfig:
        path = config_path('app_config.json')
        if not os.path.exists(path):
            logger.info('app_config.json 不存在，使用默认配置')
            return AppConfig.default()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return AppConfig.from_dict(data)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f'加载 app_config.json 失败: {e}，使用默认配置')
            return AppConfig.default()

    def save_app_config(self) -> None:
        """将当前 app_config 持久化到 JSON 文件。"""
        path = config_path('app_config.json')
        self._atomic_write(path, self._app_config.to_dict())
        logger.debug('app_config.json 已保存')

    def update_window_position(self, x: int, y: int) -> None:
        """更新并保存窗口位置。"""
        self._app_config.window_x = x
        self._app_config.window_y = y
        self.save_app_config()

    def update_scale(self, scale: float) -> None:
        self._app_config.scale = scale
        self.save_app_config()

    # ── 提醒数据 ──────────────────────────────────────────

    def load_reminders_raw(self) -> list:
        """加载 reminders.json，返回原始字典列表。"""
        path = config_path('reminders.json')
        if not os.path.exists(path):
            return []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('reminders', [])
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f'加载 reminders.json 失败: {e}')
            return []

    def save_reminders_raw(self, reminders_data: list) -> None:
        """保存提醒列表到 reminders.json。"""
        path = config_path('reminders.json')
        self._atomic_write(path, {'reminders': reminders_data})
        logger.debug(f'reminders.json 已保存 ({len(reminders_data)} 条)')

    # ── 工具方法 ──────────────────────────────────────────

    @staticmethod
    def _atomic_write(path: str, data: dict) -> None:
        """原子写入：先写临时文件，再替换目标文件。"""
        dir_path = os.path.dirname(path)
        fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # Windows 上 os.replace 可原子替换
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
