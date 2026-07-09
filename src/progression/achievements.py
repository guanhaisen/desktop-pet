"""成就定义：每个成就有 ID、名称、描述、解锁条件。"""

from dataclasses import dataclass
from typing import Callable

from src.progression.stats import StatsManager


@dataclass
class Achievement:
    """成就定义。"""
    id: str                    # 唯一标识
    name: str                  # 成就名称
    description: str           # 成就描述
    icon: str                  # 图标符号（emoji 或文字）
    check: Callable            # 解锁条件函数 (StatsManager → bool)


# ── 成就定义列表 ──

ACHIEVEMENTS: list[Achievement] = [
    # 互动类
    Achievement(
        id='first_interaction',
        name='初次见面',
        description='第一次与月薪喵互动',
        icon='👋',
        check=lambda sm: sm.stats.total_interactions >= 1,
    ),
    Achievement(
        id='interactions_50',
        name='热络伙伴',
        description='累计互动 50 次',
        icon='🤝',
        check=lambda sm: sm.stats.total_interactions >= 50,
    ),
    Achievement(
        id='interactions_200',
        name='至交好友',
        description='累计互动 200 次',
        icon='💜',
        check=lambda sm: sm.stats.total_interactions >= 200,
    ),

    # 散步类
    Achievement(
        id='first_walk',
        name='迈出第一步',
        description='第一次带月薪喵散步',
        icon='🐾',
        check=lambda sm: sm.stats.total_walks >= 1,
    ),
    Achievement(
        id='walks_30',
        name='散步达人',
        description='累计散步 30 次',
        icon='🚶',
        check=lambda sm: sm.stats.total_walks >= 30,
    ),

    # 打卡类
    Achievement(
        id='first_checkin',
        name='打卡报到',
        description='第一次每日打卡',
        icon='📋',
        check=lambda sm: len(sm.stats.checkin_dates) >= 1,
    ),
    Achievement(
        id='checkin_7',
        name='一周全勤',
        description='连续打卡 7 天',
        icon='📅',
        check=lambda sm: sm.get_consecutive_days() >= 7,
    ),
    Achievement(
        id='checkin_30',
        name='月度全勤奖',
        description='连续打卡 30 天',
        icon='🏆',
        check=lambda sm: sm.get_consecutive_days() >= 30,
    ),

    # 摸鱼类
    Achievement(
        id='slacking_1',
        name='摸鱼新手',
        description='第一次被检测到摸鱼',
        icon='🐟',
        check=lambda sm: sm.stats.total_slacking_count >= 1,
    ),
    Achievement(
        id='slacking_20',
        name='摸鱼达人',
        description='累计摸鱼 20 次',
        icon='🎣',
        check=lambda sm: sm.stats.total_slacking_count >= 20,
    ),

    # 久坐类
    Achievement(
        id='sit_too_long_5',
        name='久坐反省',
        description='累计收到 5 次久坐提醒',
        icon='💺',
        check=lambda sm: sm.stats.total_sit_too_long_count >= 5,
    ),

    # 提醒类
    Achievement(
        id='reminders_10',
        name='提醒大师',
        description='累计触发 10 次提醒',
        icon='🔔',
        check=lambda sm: sm.stats.total_reminders_triggered >= 10,
    ),

    # 在线时长类
    Achievement(
        id='online_60min',
        name='陪伴一小时',
        description='累计在线 60 分钟',
        icon='⏰',
        check=lambda sm: sm.stats.total_online_minutes >= 60,
    ),
    Achievement(
        id='online_600min',
        name='忠实伙伴',
        description='累计在线 10 小时',
        icon='🌟',
        check=lambda sm: sm.stats.total_online_minutes >= 600,
    ),
    Achievement(
        id='online_3000min',
        name='打工魂觉醒',
        description='累计在线 50 小时',
        icon='🔥',
        check=lambda sm: sm.stats.total_online_minutes >= 3000,
    ),
]


def get_achievement_by_id(achievement_id: str) -> Achievement | None:
    """根据 ID 获取成就定义。"""
    for ach in ACHIEVEMENTS:
        if ach.id == achievement_id:
            return ach
    return None
