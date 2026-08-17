"""心情管理器：维护心情值，驱动 idle 动画变体切换。"""

import time

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from src.config.config_manager import ConfigManager
from src.utils.logger import logger


class MoodManager(QObject):
    """维护桌宠心情值 (0-100)，管理增减与类别切换。

    心情类别阈值:
        >= 90  → happy  (开心)   idle-happy.gif
        >= 60  → normal (普通)   idle.gif
        >= 30  → tired  (疲惫)   idle-tired.gif
        <  30  → emo    (emo)    idle-emo.gif

    规则:
        - 点击 / 状态切换: 尝试 +5（5 分钟冷却，冷却期内不增加）
        - 1 小时无互动: -10（周期性，每次重置计时）
        - 任何互动重置 1 小时衰减计时器
        - 心情值持久化到 app_config.json

    信号:
        mood_category_changed(str): 心情类别变化 (happy/normal/tired/emo)
    """

    mood_category_changed = pyqtSignal(str)

    # 心情阈值
    MOOD_HAPPY_THRESHOLD = 90
    MOOD_NORMAL_THRESHOLD = 60
    MOOD_TIRED_THRESHOLD = 30

    # 互动参数
    INTERACTION_COOLDOWN_SEC = 300   # 5 分钟冷却
    DECAY_INTERVAL_SEC = 3600        # 1 小时衰减周期
    DECAY_AMOUNT = 10
    INCREASE_AMOUNT = 5

    # 心情范围
    DEFAULT_MOOD = 70
    MAX_MOOD = 100
    MIN_MOOD = 0

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = ConfigManager()
        self._mood: int = self._config.app_config.mood_value
        self._last_increase_ts: float = self._config.app_config.last_mood_increase_ts
        self._mood_category: str = self._compute_category(self._mood)

        # 1 小时无互动衰减定时器
        self._decay_timer = QTimer(self)
        self._decay_timer.timeout.connect(self._on_decay)
        self._decay_timer.start(self.DECAY_INTERVAL_SEC * 1000)

        logger.info(f'心情系统初始化: 值={self._mood}, 类别={self._mood_category}')

    @property
    def mood(self) -> int:
        """当前心情值。"""
        return self._mood

    @property
    def mood_category(self) -> str:
        """当前心情类别 (happy/normal/tired/emo)。"""
        return self._mood_category

    def try_increase(self) -> bool:
        """尝试通过互动增加心情值 (+5)。

        受 5 分钟冷却限制：冷却期内调用不会增加心情值。

        返回: 是否成功增加
        """
        now = time.time()
        elapsed = now - self._last_increase_ts
        if elapsed < self.INTERACTION_COOLDOWN_SEC:
            remaining = self.INTERACTION_COOLDOWN_SEC - elapsed
            logger.debug(f'心情增加冷却中，剩余 {remaining:.0f}s')
            return False

        old_category = self._mood_category
        self._mood = min(self.MAX_MOOD, self._mood + self.INCREASE_AMOUNT)
        self._last_increase_ts = now
        self._save()
        logger.info(f'心情增加 +{self.INCREASE_AMOUNT} → {self._mood}')

        new_category = self._compute_category(self._mood)
        if new_category != old_category:
            self._mood_category = new_category
            self.mood_category_changed.emit(new_category)
            logger.info(f'心情类别变化: {old_category} → {new_category}')

        return True

    def record_interaction(self) -> None:
        """记录一次互动，重置 1 小时衰减定时器。

        任何用户互动（点击、拖拽、右键操作等）都应调用此方法。
        注意：此方法不增加心情值，仅重置衰减计时。
        """
        self._decay_timer.stop()
        self._decay_timer.start(self.DECAY_INTERVAL_SEC * 1000)

    def _on_decay(self) -> None:
        """1 小时无互动，心情值 -10。"""
        old_category = self._mood_category
        self._mood = max(self.MIN_MOOD, self._mood - self.DECAY_AMOUNT)
        self._save()
        logger.info(f'心情衰减 -{self.DECAY_AMOUNT} → {self._mood}')

        new_category = self._compute_category(self._mood)
        if new_category != old_category:
            self._mood_category = new_category
            self.mood_category_changed.emit(new_category)
            logger.info(f'心情类别变化: {old_category} → {new_category}')

    def _compute_category(self, mood: int) -> str:
        """根据心情值计算类别。"""
        if mood >= self.MOOD_HAPPY_THRESHOLD:
            return 'happy'
        elif mood >= self.MOOD_NORMAL_THRESHOLD:
            return 'normal'
        elif mood >= self.MOOD_TIRED_THRESHOLD:
            return 'tired'
        else:
            return 'emo'

    def _save(self) -> None:
        """持久化心情值与时间戳。"""
        self._config.app_config.mood_value = self._mood
        self._config.app_config.last_mood_increase_ts = self._last_increase_ts
        self._config.save_app_config()
