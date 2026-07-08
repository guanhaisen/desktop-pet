"""PNG 序列帧动画播放器，使用 QTimer 切换帧。"""

import glob
import os

from PyQt5.QtCore import QTimer, QSize
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel

from src.utils.logger import logger


class FramePlayer:
    """使用 QTimer 轮换 PNG 序列帧实现动画。"""

    def __init__(self, frames_dir: str, frame_interval_ms: int = 50):
        self._frames_dir = frames_dir
        self._frame_interval = frame_interval_ms
        self._frames: list[QPixmap] = []
        self._current_index: int = 0
        self._timer: QTimer = None
        self._label: QLabel = None
        self._scale: float = 1.0
        self._loop_finished_callback = None

    def load_frames(self) -> bool:
        """加载目录下所有 PNG 帧，按文件名排序。

        返回: 是否成功加载至少一帧
        """
        pattern = os.path.join(self._frames_dir, '*.png')
        files = sorted(glob.glob(pattern))
        if not files:
            logger.warning(f'帧目录无 PNG 文件: {self._frames_dir}')
            return False

        self._frames = [QPixmap(f) for f in files]
        self._current_index = 0
        logger.debug(f'已加载 {len(self._frames)} 帧从 {self._frames_dir}')
        return True

    def set_label(self, label: QLabel) -> None:
        self._label = label

    def set_scale(self, scale: float) -> None:
        self._scale = scale

    def set_loop_finished_callback(self, callback) -> None:
        """设置单次播放完成回调（用于交互动画播完后回到 idle）。"""
        self._loop_finished_callback = callback

    def start(self, loop: bool = True) -> None:
        if not self._frames:
            if not self.load_frames():
                return

        if not self._label:
            logger.warning('FramePlayer.start() 被调用但未设置 label')
            return

        self.stop()
        self._current_index = 0
        self._show_current_frame()

        self._timer = QTimer()
        self._timer.timeout.connect(self._next_frame)
        self._timer.start(self._frame_interval)

        self._loop = loop
        logger.debug(f'帧动画播放开始: {self._frames_dir} (loop={loop})')

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None

    def _next_frame(self) -> None:
        self._current_index += 1
        if self._current_index >= len(self._frames):
            if self._loop:
                self._current_index = 0
            else:
                # 单次播放完毕
                self._timer.stop()
                self._timer = None
                if self._loop_finished_callback:
                    self._loop_finished_callback()
                return

        self._show_current_frame()

    def _show_current_frame(self) -> None:
        if not self._frames or not self._label:
            return

        frame = self._frames[self._current_index]
        if self._scale != 1.0:
            size = QSize(
                int(frame.width() * self._scale),
                int(frame.height() * self._scale)
            )
            frame = frame.scaled(size, aspectMode=1)  # Qt.KeepAspectRatio
        self._label.setPixmap(frame)
