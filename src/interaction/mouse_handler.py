"""鼠标交互处理器：区分点击与拖拽。"""

from PyQt5.QtCore import QPoint, QObject, pyqtSignal
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt

from src.utils.logger import logger


class MouseHandler(QObject):
    """处理桌宠窗口的鼠标事件，判定点击与拖拽。

    信号:
        clicked: 单击（未拖拽）时发出
        drag_started: 拖拽开始时发出
        drag_finished: 拖拽结束时发出
    """

    clicked = pyqtSignal()
    drag_started = pyqtSignal()
    drag_finished = pyqtSignal()

    # 点击/拖拽判定阈值（曼哈顿距离，像素）
    DRAG_THRESHOLD = 5

    def __init__(self, window: QWidget, parent=None):
        super().__init__(parent)
        self._window = window
        self._press_pos: QPoint = None
        self._window_start_pos: QPoint = None
        self._is_pressed: bool = False
        self._is_dragging: bool = False

    def on_mouse_press(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self._press_pos = event.globalPos()
            self._window_start_pos = self._window.pos()
            self._is_pressed = True
            self._is_dragging = False
            event.accept()

    def on_mouse_move(self, event: QMouseEvent) -> None:
        if not self._is_pressed or event.buttons() != Qt.LeftButton:
            return

        delta = event.globalPos() - self._press_pos
        if not self._is_dragging and delta.manhattanLength() > self.DRAG_THRESHOLD:
            self._is_dragging = True
            self.drag_started.emit()
            logger.debug('拖拽开始')

        if self._is_dragging:
            new_pos = self._window_start_pos + delta
            self._window.move(new_pos)
            event.accept()

    def on_mouse_release(self, event: QMouseEvent) -> None:
        if event.button() != Qt.LeftButton or not self._is_pressed:
            return

        if self._is_dragging:
            logger.debug('拖拽结束')
            self.drag_finished.emit()
        else:
            logger.debug('单击触发')
            self.clicked.emit()

        self._is_pressed = False
        self._is_dragging = False
        event.accept()

    @property
    def is_dragging(self) -> bool:
        return self._is_dragging
