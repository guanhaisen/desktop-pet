"""GIF 动画播放器，封装 QMovie。"""

from PyQt5.QtGui import QMovie, QImage
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QSize

from src.utils.logger import logger


class GifPlayer:
    """使用 QMovie 播放单个 GIF 循环动画。"""

    def __init__(self, gif_path: str):
        self._gif_path = gif_path
        self._movie: QMovie = None
        self._label: QLabel = None
        self._scale: float = 1.0
        self._frame_size: QSize = QSize()  # 缓存的帧尺寸
        self._loop_finished_callback = None

    def set_label(self, label: QLabel) -> None:
        self._label = label

    def set_scale(self, scale: float) -> None:
        self._scale = scale
        if self._movie and self._label:
            self._apply_scaled_size()

    def set_loop_finished_callback(self, callback) -> None:
        """设置单次播放完成回调（用于交互动画播完后回到 idle）。"""
        self._loop_finished_callback = callback

    def start(self, loop: bool = True) -> None:
        if not self._label:
            logger.warning('GifPlayer.start() 被调用但未设置 label')
            return

        # 停止旧的 movie
        self.stop()

        self._movie = QMovie(self._gif_path)
        if not self._movie.isValid():
            logger.warning(f'GIF 文件无法加载: {self._gif_path}')
            if not loop and self._loop_finished_callback:
                self._loop_finished_callback()
            return

        # 跳转到第一帧以获取实际帧尺寸
        self._movie.jumpToFrame(0)
        pm = self._movie.currentPixmap()
        if not pm.isNull():
            self._frame_size = pm.size()
            logger.debug(f'GIF 帧尺寸: {self._frame_size.width()}x{self._frame_size.height()}')

        if not loop:
            self._movie.frameChanged.connect(self._on_frame_changed)

        self._apply_scaled_size()
        self._label.setMovie(self._movie)
        self._movie.start()
        logger.debug(f'GIF 播放开始: {self._gif_path} (loop={loop})')

    def _on_frame_changed(self, frame_number: int) -> None:
        """单次播放模式：到达最后一帧时停止并回调。"""
        if self._movie and frame_number >= self._movie.frameCount() - 1:
            self._movie.stop()
            if self._loop_finished_callback:
                self._loop_finished_callback()

    def stop(self) -> None:
        if self._movie:
            try:
                self._movie.frameChanged.disconnect(self._on_frame_changed)
            except TypeError:
                pass  # 循环播放模式下未连接
            self._movie.stop()
            self._movie = None

    def get_frame_size(self) -> QSize:
        """获取 GIF 帧尺寸（start 后可用）。"""
        # 优先使用缓存
        if not self._frame_size.isEmpty():
            return self._frame_size
        # 尝试从 movie 获取
        if self._movie:
            pm = self._movie.currentPixmap()
            if not pm.isNull():
                self._frame_size = pm.size()
                return self._frame_size
        # 最后尝试用 QImage 读取
        img = QImage(self._gif_path)
        if not img.isNull():
            self._frame_size = img.size()
            return self._frame_size
        return QSize()

    def _apply_scaled_size(self) -> None:
        """按缩放比例调整 GIF 显示尺寸。"""
        if not self._movie:
            return
        original = self._frame_size
        if original.isEmpty():
            original = self._movie.currentPixmap().size()
        if original.isEmpty():
            original = self._movie.frameRect().size()
        if not original.isEmpty():
            scaled = QSize(
                int(original.width() * self._scale),
                int(original.height() * self._scale)
            )
            self._movie.setScaledSize(scaled)
            logger.debug(f'GIF 缩放: {original.width()}x{original.height()} → {scaled.width()}x{scaled.height()}')
