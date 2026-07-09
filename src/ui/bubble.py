"""对话气泡窗口：在桌宠上方显示文字，定时消失。"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import (
    QPainter, QColor, QPainterPath, QFont, QFontMetrics, QPen
)

from src.utils.logger import logger


class BubbleWindow(QWidget):
    """透明无边框气泡窗口，用 QPainter 绘制圆角气泡 + 小尾巴。

    使用方式:
        bubble = BubbleWindow()
        bubble.show_message('喵~', duration_sec=4)
        bubble.follow_pos(pet_x, pet_y, pet_width)  # 跟随桌宠位置

    特性:
        - 透明背景 + 无边框 + 置顶
        - 圆角白色半透明背景 + 下方三角小尾巴
        - 文字自动换行，气泡尺寸自适应
        - QTimer 控制定时隐藏
        - 可跟随桌宠位置移动
    """

    # 气泡样式参数
    BUBBLE_PADDING = 12          # 文字到气泡边缘的内边距
    BUBBLE_RADIUS = 12           # 圆角半径
    TAIL_WIDTH = 14              # 小尾巴底部宽度
    TAIL_HEIGHT = 8              # 小尾巴高度
    MAX_BUBBLE_WIDTH = 260       # 气泡最大宽度
    MIN_BUBBLE_WIDTH = 80        # 气泡最小宽度
    BUBBLE_GAP = 4               # 气泡与桌宠之间的间距
    BG_COLOR = QColor(255, 255, 255, 230)  # 半透明白色
    BORDER_COLOR = QColor(200, 200, 200, 180)  # 浅灰边框
    TEXT_COLOR = QColor(60, 60, 60)        # 深灰文字

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_window()

        self._text: str = ''
        self._text_rect: QRect = QRect()    # 文字绘制区域
        self._bubble_rect: QRect = QRect()  # 气泡圆角矩形区域（不含尾巴）
        self._pet_rect: QRect = QRect()     # 桌宠位置参考

        self._timer: QTimer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

        self._font = QFont('Microsoft YaHei', 10)
        self._font_metrics = QFontMetrics(self._font)

    def _setup_window(self) -> None:
        """设置透明无边框置顶窗口属性。"""
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)  # 不抢焦点

    def show_message(self, text: str, duration_sec: int = 4) -> None:
        """显示一条气泡消息，duration_sec 秒后自动隐藏。

        参数:
            text: 要显示的文字
            duration_sec: 显示时长（秒），0 表示不自动隐藏
        """
        self._text = text
        self._calculate_size()
        self._update_position()
        self.show()
        self.raise_()

        if duration_sec > 0:
            self._timer.start(duration_sec * 1000)
        else:
            self._timer.stop()

        logger.debug(f'气泡显示: {text!r}')

    def follow_pos(self, pet_x: int, pet_y: int, pet_width: int) -> None:
        """根据桌宠位置更新气泡位置（在桌宠正上方居中）。

        参数:
            pet_x: 桌宠窗口 x 坐标
            pet_y: 桌宠窗口 y 坐标
            pet_width: 桌宠窗口宽度
        """
        self._pet_rect = QRect(pet_x, pet_y, pet_width, 0)
        if self.isVisible():
            self._update_position()

    def hide(self) -> None:
        """隐藏气泡并停止定时器。"""
        self._timer.stop()
        super().hide()
        logger.debug('气泡隐藏')

    # ── 内部计算 ──

    def _calculate_size(self) -> None:
        """根据文字内容计算气泡尺寸与文字绘制区域。"""
        # 计算换行后的文字尺寸
        max_text_width = self.MAX_BUBBLE_WIDTH - 2 * self.BUBBLE_PADDING
        text_rect = self._font_metrics.boundingRect(
            QRect(0, 0, max_text_width, 0),
            Qt.AlignCenter | Qt.TextWordWrap,
            self._text
        )

        text_width = text_rect.width()
        text_height = text_rect.height()

        # 气泡总宽高（文字 + 内边距）
        bubble_width = min(
            max(text_width + 2 * self.BUBBLE_PADDING, self.MIN_BUBBLE_WIDTH),
            self.MAX_BUBBLE_WIDTH
        )
        bubble_height = text_height + 2 * self.BUBBLE_PADDING

        # 窗口总高度 = 气泡高度 + 尾巴高度
        window_width = int(bubble_width)
        window_height = int(bubble_height + self.TAIL_HEIGHT)

        self.resize(window_width, window_height)

        # 气泡圆角矩形区域（不含尾巴）
        self._bubble_rect = QRect(0, 0, window_width, int(bubble_height))
        # 文字绘制区域
        self._text_rect = QRect(
            self.BUBBLE_PADDING,
            self.BUBBLE_PADDING,
            window_width - 2 * self.BUBBLE_PADDING,
            text_height
        )

    def _update_position(self) -> None:
        """根据桌宠位置计算气泡窗口位置。"""
        if self._pet_rect.isNull():
            return

        # 气泡水平居中于桌宠
        bubble_x = self._pet_rect.x() + self._pet_rect.width() // 2 - self.width() // 2
        # 气泡在桌宠正上方
        bubble_y = self._pet_rect.y() - self.height() - self.BUBBLE_GAP

        # 防止气泡飞出屏幕左侧
        bubble_x = max(bubble_x, 0)

        self.move(bubble_x, bubble_y)

    # ── 绘制 ──

    def paintEvent(self, event) -> None:
        """绘制圆角气泡背景 + 小尾巴 + 文字。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setFont(self._font)

        # 绘制气泡圆角矩形 + 尾巴的路径
        path = QPainterPath()
        rect = self._bubble_rect

        # 圆角矩形
        path.addRoundedRect(
            rect.x(), rect.y(),
            rect.width(), rect.height(),
            self.BUBBLE_RADIUS, self.BUBBLE_RADIUS
        )

        # 小尾巴（指向下方的三角形）
        tail_center_x = rect.width() // 2
        tail_top = rect.height()
        path.moveTo(tail_center_x - self.TAIL_WIDTH // 2, tail_top)
        path.lineTo(tail_center_x, tail_top + self.TAIL_HEIGHT)
        path.lineTo(tail_center_x + self.TAIL_WIDTH // 2, tail_top)
        path.closeSubpath()

        # 填充背景
        painter.fillPath(path, self.BG_COLOR)

        # 绘制边框
        pen = QPen(self.BORDER_COLOR)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawPath(path)

        # 绘制文字
        painter.setPen(self.TEXT_COLOR)
        painter.drawText(
            self._text_rect,
            Qt.AlignCenter | Qt.TextWordWrap,
            self._text
        )
