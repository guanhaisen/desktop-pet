"""打工人统计数据模型：记录互动、打卡、摸鱼等累计数据。"""

import json
import os
import tempfile
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field, asdict

from PyQt5.QtCore import QObject, QTimer

from src.utils.path_helper import config_path, ensure_config_dir
from src.utils.logger import logger


@dataclass
class Stats:
    """打工人统计数据，持久化到 config/stats.json。"""
    # 互动类
    total_interactions: int = 0          # 累计互动次数（点击、状态切换）
    total_walks: int = 0                 # 累计散步次数
    total_reminders_triggered: int = 0   # 累计提醒触发次数

    # 打卡类
    checkin_dates: list = field(default_factory=list)  # 打卡日期列表 (YYYY-MM-DD)
    last_checkin_date: str = ''          # 最近打卡日期

    # 摸鱼类
    total_slacking_count: int = 0        # 累计被检测到摸鱼次数
    total_sit_too_long_count: int = 0    # 累计久坐提醒次数

    # 在线时长
    total_online_minutes: int = 0        # 累计在线分钟数

    # 成就
    unlocked_achievements: list = field(default_factory=list)  # 已解锁成就 ID 列表

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Stats':
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    @classmethod
    def default(cls) -> 'Stats':
        return cls()


class StatsManager(QObject):
    """统计数据的读写管理，原子写入 + 脏标记节流落盘。

    高频统计（互动、在线分钟）只置脏标记，由定时器批量落盘；
    打卡、成就解锁等低频关键事件仍立即写入。
    """

    # 脏数据落盘间隔（秒）
    FLUSH_INTERVAL_SEC = 30

    def __init__(self, parent=None):
        super().__init__(parent)
        ensure_config_dir()
        self._stats: Stats = self._load()
        self._dirty = False
        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(self.FLUSH_INTERVAL_SEC * 1000)
        self._flush_timer.timeout.connect(self._flush_if_dirty)
        self._flush_timer.start()

    @property
    def stats(self) -> Stats:
        return self._stats

    def _load(self) -> Stats:
        path = config_path('stats.json')
        if not os.path.exists(path):
            logger.info('stats.json 不存在，使用默认统计数据')
            return Stats.default()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Stats.from_dict(data)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f'加载 stats.json 失败: {e}，使用默认统计数据')
            return Stats.default()

    def save(self) -> None:
        """立即原子写入统计数据。"""
        path = config_path('stats.json')
        dir_path = os.path.dirname(path)
        fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(self._stats.to_dict(), f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
        self._dirty = False
        logger.debug('stats.json 已保存')

    def flush(self) -> None:
        """有未落盘修改时立即写入（退出前调用）。"""
        if self._dirty:
            self.save()

    def _flush_if_dirty(self) -> None:
        """定时器回调：有脏数据则落盘。"""
        if self._dirty:
            self.save()

    def _mark_dirty(self) -> None:
        self._dirty = True

    # ── 统计更新方法 ──

    def record_interaction(self) -> None:
        """记录一次互动。"""
        self._stats.total_interactions += 1
        self._mark_dirty()

    def record_walk(self) -> None:
        """记录一次散步。"""
        self._stats.total_walks += 1
        self._mark_dirty()

    def record_reminder(self) -> None:
        """记录一次提醒触发。"""
        self._stats.total_reminders_triggered += 1
        self._mark_dirty()

    def record_slacking(self) -> None:
        """记录一次摸鱼检测。"""
        self._stats.total_slacking_count += 1
        self._mark_dirty()

    def record_sit_too_long(self) -> None:
        """记录一次久坐提醒。"""
        self._stats.total_sit_too_long_count += 1
        self._mark_dirty()

    def checkin(self) -> bool:
        """每日打卡。返回是否为今日首次打卡（True=首次，False=已打过）。"""
        today = datetime.now().strftime('%Y-%m-%d')
        if today == self._stats.last_checkin_date:
            return False
        self._stats.last_checkin_date = today
        if today not in self._stats.checkin_dates:
            self._stats.checkin_dates.append(today)
        self.save()
        logger.info(f'每日打卡成功: {today}')
        return True

    def add_online_minutes(self, minutes: int) -> None:
        """累加在线时长。"""
        self._stats.total_online_minutes += minutes
        self._mark_dirty()

    def get_consecutive_days(self) -> int:
        """计算连续打卡天数。"""
        if not self._stats.checkin_dates:
            return 0
        dates = sorted(self._stats.checkin_dates)
        today = date.today()
        consecutive = 0
        check_date = today
        for d_str in reversed(dates):
            try:
                d = date.fromisoformat(d_str)
            except ValueError:
                continue  # 跳过脏数据
            if d == check_date:
                consecutive += 1
                check_date -= timedelta(days=1)
            elif d < check_date:
                break
        return consecutive
