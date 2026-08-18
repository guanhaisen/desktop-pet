"""GIF 动画播放器，封装 QMovie。"""

from PyQt5.QtGui import QMovie, QImage
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QSize

from src.utils.logger import logger


class GifPlayer:
    """使用 QMovie 播放单个 GIF 动画。

    QMovie 懒加载后常驻复用，避免每次播放都从磁盘重新读取解码；
    常驻对象也保证了播放器停止后 label 不会持有悬空指针。
    """

    def __init__(self, gif_path: str):
        self._gif_path = gif_path
        self._movie: QMovie = None
        self._label: QLabel = None
        self._scale: float = 1.0
        self._frame_size: QSize = QSize()  # 缓存的帧尺寸
        self._loop_finished_callback = None
        self._loop_mode = True

    def set_label(self, label: QLabel) -> None:
        self._label = label

    def set_scale(self, scale: float) -> None:
        self._scale = scale
        if self._movie and self._label:
            self._apply_scaled_size()

    def set_loop_finished_callback(self, callback) -> None:
        """设置单次播放完成回调（用于交互动画播完后回到 idle）。"""
        self._loop_finished_callback = callback

    def _ensure_movie(self) -> QMovie:
        """懒加载 QMovie 并常驻复用。"""
        if self._movie is None:
            movie = QMovie(self._gif_path)
            if not movie.isValid():
                logger.warning(f'GIF 文件无法加载: {self._gif_path}')
                return None
            # 跳转到第一帧以获取实际帧尺寸
            movie.jumpToFrame(0)
            pm = movie.currentPixmap()
            if not pm.isNull():
                self._frame_size = pm.size()
                logger.debug(f'GIF 帧尺寸: {self._frame_size.width()}x{self._frame_size.height()}')
            movie.frameChanged.connect(self._on_frame_changed)
            self._movie = movie
        return self._movie

    def start(self, loop: bool = True) -> None:
        if not self._label:
            logger.warning('GifPlayer.start() 被调用但未设置 label')
            return

        movie = self._ensure_movie()
        if movie is None:
            if not loop and self._loop_finished_callback:
                self._loop_finished_callback()
            return

        self._loop_mode = loop
        movie.stop()
        movie.jumpToFrame(0)

        self._apply_scaled_size()
        if self._label.movie() is not movie:
            self._label.setMovie(movie)
        movie.start()
        logger.debug(f'GIF 播放开始: {self._gif_path} (loop={loop})')

    def _on_frame_changed(self, frame_number: int) -> None:
        """单次播放模式：到达最后一帧时停止并回调。"""
        if self._loop_mode:
            return
        if self._movie and frame_number >= self._movie.frameCount() - 1:
            self._movie.stop()
            if self._loop_finished_callback:
                self._loop_finished_callback()

    def stop(self) -> None:
        # 仅停止播放，保留 QMovie 供下次复用；
        # label 的引用由控制器切换播放器时统一更换
        if self._movie:
            self._movie.stop()

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
