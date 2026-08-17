"""提醒数据模型。"""

import uuid
from dataclasses import dataclass, asdict, field


@dataclass
class Reminder:
    """单条提醒，对应 reminders.json 中的一条记录。"""
    title: str = ''
    message: str = ''
    hour: int = 9
    minute: int = 0
    repeat: str = 'daily'          # none / daily / weekly
    weekday: int = 0               # 每周提醒的星期（0=周一 … 6=周日），仅 repeat=weekly 时生效
    enabled: bool = True
    id: str = field(default_factory=lambda: f'r-{uuid.uuid4().hex[:8]}')

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Reminder':
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    def __repr__(self) -> str:
        return (f'Reminder(id={self.id}, title={self.title!r}, '
                f'time={self.hour:02d}:{self.minute:02d}, repeat={self.repeat})')
