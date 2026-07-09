"""成就管理器：检查成就解锁、每日打卡、在线时长累计。"""

import time

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from src.progression.stats import StatsManager
from src.progression.achievements import ACHIEVEMENTS, get_achievement_by_id
from src.utils.logger import logger


class AchievementManager(QObject):
    """成就系统管理器。

    职责:
        - 持有 StatsManager，提供统计记录接口
        - 每日打卡（启动时自动打卡）
        - 在线时长累计（每分钟累加）
        - 检查成就解锁，发出庆祝信号

    信号:
        achievement_unlocked(str): 成就解锁，请求气泡庆祝 (成就名称)
    """

    achievement_unlocked = pyqtSignal(str)

    # 在线时长累计间隔（秒）
    ONLINE_TICK_SEC = 60

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stats_mgr = StatsManager()

        # 在线时长定时器
        self._online_timer = QTimer(self)
        self._online_timer.timeout.connect(self._on_online_tick)

        logger.info(f'成就系统已启动 - 已解锁 {len(self._stats_mgr.stats.unlocked_achievements)}/{len(ACHIEVEMENTS)} 个成就')

    @property
    def stats_mgr(self) -> StatsManager:
        return self._stats_mgr

    def start(self) -> None:
        """启动定时器并执行每日打卡。"""
        self._online_timer.start(self.ONLINE_TICK_SEC * 1000)

        # 启动时自动每日打卡
        is_first = self._stats_mgr.checkin()
        if is_first:
            logger.info('今日首次打卡完成')
            self._check_achievements()

    # ── 统计记录接口（供 PetApp 埋点调用）──

    def record_interaction(self) -> None:
        self._stats_mgr.record_interaction()
        self._check_achievements()

    def record_walk(self) -> None:
        self._stats_mgr.record_walk()
        self._check_achievements()

    def record_reminder(self) -> None:
        self._stats_mgr.record_reminder()
        self._check_achievements()

    def record_slacking(self) -> None:
        self._stats_mgr.record_slacking()
        self._check_achievements()

    def record_sit_too_long(self) -> None:
        self._stats_mgr.record_sit_too_long()
        self._check_achievements()

    # ── 在线时长 ──

    def _on_online_tick(self) -> None:
        """每分钟累加在线时长。"""
        self._stats_mgr.add_online_minutes(1)
        self._check_achievements()

    # ── 成就检测 ──

    def _check_achievements(self) -> None:
        """检查所有成就，解锁新成就并发出庆祝信号。"""
        unlocked = self._stats_mgr.stats.unlocked_achievements
        newly_unlocked = []

        for ach in ACHIEVEMENTS:
            if ach.id in unlocked:
                continue
            try:
                if ach.check(self._stats_mgr):
                    unlocked.append(ach.id)
                    newly_unlocked.append(ach)
            except Exception as e:
                logger.warning(f'检查成就 {ach.id} 失败: {e}')

        if newly_unlocked:
            self._stats_mgr.save()
            for ach in newly_unlocked:
                logger.info(f'成就解锁: {ach.name} ({ach.id})')
                self.achievement_unlocked.emit(f'{ach.icon} 成就解锁：{ach.name}！{ach.description}')

    def get_unlocked_count(self) -> int:
        return len(self._stats_mgr.stats.unlocked_achievements)

    def get_total_count(self) -> int:
        return len(ACHIEVEMENTS)

    def is_unlocked(self, achievement_id: str) -> bool:
        return achievement_id in self._stats_mgr.stats.unlocked_achievements
