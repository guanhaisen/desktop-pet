"""提醒控制器：提醒状态切换与周期性重复通知。"""

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from src.state.states import PetState
from src.utils.logger import logger


class RemindController(QObject):
    """桌宠提醒控制器。

    从 PetWindow 拆出：触发提醒后持续播放提醒动画并周期性
    重复托盘通知，直到用户左键点击停止。

    信号:
        notification(str, str): (title, message) 请求弹出托盘通知
    """

    # 提醒期间重复弹出托盘通知的间隔（秒）
    NOTIFY_INTERVAL_SEC = 10

    notification = pyqtSignal(str, str)

    def __init__(self, state_machine, parent=None):
        super().__init__(parent)
        self._sm = state_machine
        self._active = False
        self._title = ''
        self._message = ''
        self._repeat_timer = QTimer(self)
        self._repeat_timer.timeout.connect(self._on_repeat)
        self._repeat_timer.setInterval(self.NOTIFY_INTERVAL_SEC * 1000)

    @property
    def is_active(self) -> bool:
        return self._active

    def trigger(self, title: str = '', message: str = '') -> None:
        """触发提醒：切换提醒状态并立即通知一次，随后周期重复。"""
        self._title = title or '提醒'
        self._message = message or '该注意啦！'
        self._active = True

        # REMIND 优先级最高，强制切换
        self._sm.transition_to(PetState.REMIND, force=True)
        self.notification.emit(self._title, self._message)
        self._repeat_timer.start()
        logger.info(f'提醒已触发，将持续提醒直到用户点击: {self._title}')

    def _on_repeat(self) -> None:
        if self._active:
            self.notification.emit(self._title, self._message)

    def stop(self) -> None:
        """停止提醒：关闭重复通知并回到待机。"""
        self._repeat_timer.stop()
        self._active = False
        self._sm.transition_to(PetState.IDLE, force=True)
