"""状态机：管理桌宠状态转换。"""

from PyQt5.QtCore import QObject, pyqtSignal

from src.state.states import PetState
from src.utils.logger import logger


class StateMachine(QObject):
    """桌宠状态转换引擎。

    发出 stateChanged 信号通知动画控制器切换动画。
    状态优先级：REMIND 可中断任何状态；INTERACT 高于 IDLE/WALK/SLEEP。
    """

    stateChanged = pyqtSignal(PetState)

    # 状态优先级（数值越高优先级越高）
    _PRIORITY = {
        PetState.REMIND: 100,
        PetState.INTERACT: 50,
        PetState.DRAGGING: 40,
        PetState.FOCUS: 35,
        PetState.MOYU: 30,
        PetState.WALK: 10,
        PetState.IDLE: 5,
        PetState.SLEEP: 1,
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_state: PetState = PetState.IDLE

    @property
    def current_state(self) -> PetState:
        return self._current_state

    def transition_to(self, state: PetState, force: bool = False) -> bool:
        """尝试转换到目标状态。

        参数:
            state: 目标状态
            force: 为 True 时忽略优先级直接切换

        返回: 是否成功切换
        """
        if state == self._current_state:
            return False

        if not force:
            # 低优先级状态不能中断高优先级状态
            if self._PRIORITY.get(state, 0) < self._PRIORITY.get(self._current_state, 0):
                logger.debug(f'状态转换被阻止: {self._current_state.state_name} → {state.state_name}（优先级不足）')
                return False

        old_state = self._current_state
        self._current_state = state
        logger.info(f'状态转换: {old_state.state_name} → {state.state_name}')
        self.stateChanged.emit(state)
        return True
