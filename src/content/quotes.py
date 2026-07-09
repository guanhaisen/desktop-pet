"""打工人主题金句库：按场景分类，供气泡系统使用。"""

import random

# 待机时的随机吐槽
IDLE_QUOTES = [
    '今天又是为猫粮打工的一天...',
    '老板还没走，我先装作很忙',
    '打工喵，打工魂，打工都是人上人',
    '再坚持一下，离发薪又近了一天',
    '摸鱼？不，我在思考人生',
    '咖啡续命，键盘打字',
    '今天的工作量，明天再说吧',
    ' stare at screen... 灵魂出窍中',
    '月薪到账的声音，是世界上最美的音乐',
    '我不是在发呆，我是在充电',
]

# 散步时的金句
WALK_QUOTES = [
    '溜达溜达，假装在巡工',
    '巡视一下我的领地~',
    '走一走，活到九十九',
    '坐太久了，起来运动运动',
    '散步是灵感之母喵',
    '我在巡逻，别偷懒哦',
]

# 被点击/互动时的金句
INTERACT_QUOTES = [
    '别戳了别戳了，在打工呢！',
    '喵~ 你今天辛苦啦',
    '点击有惊喜... 才怪，继续干活',
    '撸猫可以，先把手头活干完',
    '你的鼠标，我的快乐',
    '喵呜~ 再摸摸我嘛',
    '打工喵正在被吸，请勿打扰',
    '你的指法很温柔嘛~',
]

# 提醒触发时的金句
REMIND_QUOTES = [
    '叮！该干活啦',
    '再不动起来就要长蘑菇了',
    '提醒到位，打工不累',
    '时间到！冲鸭！',
    '你的待办事项在召唤你',
    '叮咚~ 别忘了这件事喵',
]

# 睡眠时的金句
SLEEP_QUOTES = [
    'Zzz... 梦见加薪了...',
    '打工喵需要美容觉',
    '嘘... 我在梦游，别叫醒我',
    '充电中... 请勿打扰...',
    'Zzz... 老板别扣我工资...',
    '梦里什么都有，包括年终奖',
]

# 场景 → 金句列表 映射
QUOTES_BY_CATEGORY = {
    'idle': IDLE_QUOTES,
    'walk': WALK_QUOTES,
    'interact': INTERACT_QUOTES,
    'remind': REMIND_QUOTES,
    'sleep': SLEEP_QUOTES,
}


def get_random_quote(category: str) -> str:
    """从指定场景的金句库中随机返回一条。

    参数:
        category: 场景名（idle/walk/interact/remind/sleep）

    返回: 随机金句。若场景不存在则返回待机金句。
    """
    quotes = QUOTES_BY_CATEGORY.get(category, IDLE_QUOTES)
    return random.choice(quotes)
