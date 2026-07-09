"""摸鱼检测器：检测系统空闲时长，触发久坐提醒与摸鱼吐槽。

使用 Windows API GetLastInputInfo 获取系统级空闲时长（鼠标+键盘均无操作）。
用单一 QTimer 周期检查，区分两个阈值:
    - 久坐提醒: 空闲 < 摸鱼阈值 但用户可能坐太久（通过 PetWindow 的 idle 计时辅助）
    - 摸鱼判定: 空闲 >= 摸鱼阈值 → 桌宠吐槽「又摸鱼？」
    - 久离判定: 空闲 >= 久坐阈值 → 桌宠吐槽「该站起来活动了」
"""

import ctypes
import random

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from src.config.config_manager import ConfigManager
from src.utils.logger import logger


class IdleDetector(QObject):
    """摸鱼检测器，周期性检查系统空闲时长。

    信号:
        slacking_detected(str): 检测到摸鱼（空闲超摸鱼阈值），请求气泡吐槽
        sit_too_long(str): 久坐提醒（空闲超久坐阈值），请求气泡提醒
    """

    slacking_detected = pyqtSignal(str)
    sit_too_long = pyqtSignal(str)

    # 检查间隔（秒）
    CHECK_INTERVAL_SEC = 30
    # 同一提醒的最小间隔（秒），避免重复打扰
    REMIND_COOLDOWN_SEC = 600  # 10 分钟

    # 摸鱼吐槽金句
    SLACKING_QUOTES = [
        '又摸鱼？被我发现了吧喵~',
        '10分钟没动了，在打瞌睡吗？',
        '摸鱼达人就是你！',
        '键盘长蘑菇了喵，动一动嘛',
        ' detected: 摸鱼行为已记录在案',
        '老板在你身后！...开玩笑的喵',
    ]

    # 久坐提醒金句
    SIT_TOO_LONG_QUOTES = [
        '坐太久啦，站起来活动活动喵~',
        '该动动了，坐一天腰要断了喵',
        '健康第一！起来走走吧',
        '久坐伤身，活动一下筋骨喵',
        '你的颈椎在抗议了，快站起来！',
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = ConfigManager()

        # 状态跟踪
        self._last_slacking_remind_ts: float = 0.0
        self._last_sit_remind_ts: float = 0.0

        # 检查定时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_check)

        if self._is_enabled():
            self._start()
            logger.info(f'摸鱼检测已启动 - '
                        f'摸鱼阈值: {self._config.app_config.idle_slacking_sec}s, '
                        f'久坐阈值: {self._config.app_config.idle_sit_too_long_sec}s')
        else:
            logger.info('摸鱼检测未启用')

    def _is_enabled(self) -> bool:
        return self._config.app_config.idle_detect_enabled

    def _start(self) -> None:
        self._timer.start(self.CHECK_INTERVAL_SEC * 1000)

    def reload(self) -> None:
        """设置变更后重新加载。"""
        if self._is_enabled():
            if not self._timer.isActive():
                self._start()
                logger.info('摸鱼检测已重新启动')
        else:
            if self._timer.isActive():
                self._timer.stop()
                logger.info('摸鱼检测已停止')

    def _get_system_idle_seconds(self) -> float:
        """获取系统空闲时长（秒）。

        使用 Windows API GetLastInputInfo 获取最后一次输入时间，
        与当前时间相减得到空闲时长。

        返回: 空闲秒数，获取失败返回 0.0
        """
        try:
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [('cbSize', ctypes.c_uint),
                            ('dwTime', ctypes.c_uint)]

            info = LASTINPUTINFO()
            info.cbSize = ctypes.sizeof(info)
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
                # GetLastInputInfo 返回的是系统启动后的毫秒数
                current = ctypes.windll.kernel32.GetTickCount()
                idle_ms = current - info.dwTime
                return idle_ms / 1000.0
            return 0.0
        except Exception as e:
            logger.warning(f'获取系统空闲时长失败: {e}')
            return 0.0

    def _on_check(self) -> None:
        """周期检查系统空闲时长。"""
        import time
        idle_sec = self._get_system_idle_seconds()
        now = time.time()
        cfg = self._config.app_config

        # 久坐提醒（空闲超久坐阈值）
        if idle_sec >= cfg.idle_sit_too_long_sec:
            if now - self._last_sit_remind_ts >= self.REMIND_COOLDOWN_SEC:
                quote = random.choice(self.SIT_TOO_LONG_QUOTES)
                self.sit_too_long.emit(quote)
                self._last_sit_remind_ts = now
                logger.info(f'久坐提醒触发: 空闲 {idle_sec:.0f}s, "{quote}"')
            return

        # 摸鱼判定（空闲超摸鱼阈值但未到久坐）
        if idle_sec >= cfg.idle_slacking_sec:
            if now - self._last_slacking_remind_ts >= self.REMIND_COOLDOWN_SEC:
                quote = random.choice(self.SLACKING_QUOTES)
                self.slacking_detected.emit(quote)
                self._last_slacking_remind_ts = now
                logger.info(f'摸鱼检测触发: 空闲 {idle_sec:.0f}s, "{quote}"')
