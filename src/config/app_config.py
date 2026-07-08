"""应用配置数据模型。"""

import json
from dataclasses import dataclass, asdict


@dataclass
class AppConfig:
    """应用运行时配置，对应 config/app_config.json。"""
    window_x: int = -1          # -1 表示尚未保存，使用默认位置
    window_y: int = -1
    scale: float = 1.0          # 动画缩放比例
    auto_walk_enabled: bool = True
    walk_interval_min_sec: int = 30
    walk_interval_max_sec: int = 90
    idle_to_sleep_seconds: int = 300       # 5 分钟无操作进入睡眠
    remind_animation_duration_sec: int = 5  # 提醒动画播放时长

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
