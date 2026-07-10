"""应用配置数据模型。"""

import json
from dataclasses import dataclass, asdict, field


@dataclass
class AppConfig:
    """应用运行时配置，对应 config/app_config.json。"""
    window_x: int = -1          # -1 表示尚未保存，使用默认位置
    window_y: int = -1
    scale: float = 1.0          # 动画缩放比例
    auto_walk_enabled: bool = False
    walk_interval_min_sec: int = 30
    walk_interval_max_sec: int = 90
    idle_to_sleep_seconds: int = 300       # 5 分钟无操作进入睡眠
    remind_animation_duration_sec: int = 5  # 提醒动画播放时长
    # 心情系统
    mood_value: int = 70                 # 当前心情值 (0-100)
    last_mood_increase_ts: float = 0.0   # 上次心情增加的时间戳
    # 薪资系统
    salary_enabled: bool = False         # 是否启用薪资功能
    payday_day: int = 15                 # 发薪日（每月几号）
    monthly_salary: float = 0.0          # 月薪金额（元）
    work_start_hour: int = 9             # 上班时间（小时，24小时制）
    work_end_hour: int = 18              # 下班时间（小时，24小时制）
    work_days_per_month: int = 22        # 每月工作日数
    # 摸鱼检测
    idle_detect_enabled: bool = True     # 是否启用摸鱼检测
    idle_sit_too_long_sec: int = 3600    # 久坐提醒阈值（秒，默认1小时）
    idle_slacking_sec: int = 600         # 摸鱼判定阈值（秒，默认10分钟）
    # 番茄钟
    pomodoro_focus_min: int = 25         # 专注时长（分钟）
    pomodoro_break_min: int = 5          # 休息时长（分钟）

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'AppConfig':
        """从字典构造，忽略未知字段，缺失字段用默认值。"""
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    @classmethod
    def default(cls) -> 'AppConfig':
        return cls()
