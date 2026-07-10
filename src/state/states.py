"""桌宠状态枚举定义。"""

from enum import Enum


class PetState(Enum):
    """月薪喵的所有状态。状态名与 assets/yuexinmiao/ 下的资源名对应。"""
    IDLE = 'idle'          # 待机
    WALK = 'walk'          # 行走
    INTERACT = 'interact'  # 被点击/互动
    DRAGGING = 'dragging'  # 被拖拽中
    REMIND = 'remind'      # 提醒触发
    SLEEP = 'sleep'        # 长时间无操作进入睡眠
    MOYU = 'moyv'          # 摸鱼中（资源名为 moyv.gif）
    FOCUS = 'zhuanzhu'     # 专注工作中（资源名为 zhuanzhu.gif）

    @property
    def state_name(self) -> str:
        """返回用于匹配资源目录/文件的字符串。"""
        return self.value
