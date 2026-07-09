"""成就列表对话框：卡片轮播式，左右切换一次显示一张成就卡片。"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QFrame, QStackedWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from src.progression.achievements import ACHIEVEMENTS
from src.progression.achievement_manager import AchievementManager


class AchievementDialog(QDialog):
    """成就列表对话框，卡片轮播式展示。

    一次只显示一张成就卡片，通过左右箭头按钮切换。
    顶部显示进度条和统计摘要。
    """

    def __init__(self, ach_mgr: AchievementManager, parent=None):
        super().__init__(parent)
        self._ach_mgr = ach_mgr
        self._current_index = 0
        self.setWindowTitle('打工成就')
        self.setFixedSize(560, 520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        stats = self._ach_mgr.stats_mgr.stats
        unlocked_count = self._ach_mgr.get_unlocked_count()
        total_count = self._ach_mgr.get_total_count()

        # ── 顶部标题区 ──
        title = QLabel('🏆 打工成就')
        title.setStyleSheet('font-size: 22px; font-weight: bold; color: #333;')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 进度文字
        progress_label = QLabel(f'已解锁 {unlocked_count} / {total_count}')
        progress_label.setStyleSheet('font-size: 14px; color: #666;')
        progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(progress_label)

        # 进度条
        bar_container = QFrame()
        bar_container.setFixedHeight(10)
        bar_container.setStyleSheet(
            'background-color: #e0e0e0; border-radius: 5px;'
        )
        bar_layout = QHBoxLayout(bar_container)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)
        fill_pct = int(unlocked_count / total_count * 100) if total_count > 0 else 0
        fill = QFrame()
        fill.setFixedHeight(10)
        fill.setStyleSheet('background-color: #4CAF50; border-radius: 5px;')
        bar_layout.addWidget(fill, fill_pct)
        bar_layout.addStretch(100 - fill_pct)
        layout.addWidget(bar_container)

        # 统计摘要
        summary = QLabel(
            f'互动 {stats.total_interactions} 次  ·  '
            f'散步 {stats.total_walks} 次  ·  '
            f'打卡 {len(stats.checkin_dates)} 天  ·  '
            f'摸鱼 {stats.total_slacking_count} 次  ·  '
            f'在线 {stats.total_online_minutes} 分钟'
        )
        summary.setStyleSheet('font-size: 12px; color: #999; padding: 2px;')
        summary.setWordWrap(True)
        summary.setAlignment(Qt.AlignCenter)
        layout.addWidget(summary)

        # ── 卡片轮播区 ──
        carousel_layout = QHBoxLayout()
        carousel_layout.setSpacing(8)

        # 左箭头
        self._prev_btn = QPushButton('‹')
        self._prev_btn.setFixedSize(44, 44)
        self._prev_btn.setStyleSheet(self._arrow_style())
        self._prev_btn.clicked.connect(self._prev_card)
        carousel_layout.addWidget(self._prev_btn)

        # 卡片堆栈
        self._stack = QStackedWidget()
        for ach in ACHIEVEMENTS:
            is_unlocked = self._ach_mgr.is_unlocked(ach.id)
            card = self._create_achievement_card(ach, is_unlocked)
            self._stack.addWidget(card)
        carousel_layout.addWidget(self._stack, 1)

        # 右箭头
        self._next_btn = QPushButton('›')
        self._next_btn.setFixedSize(44, 44)
        self._next_btn.setStyleSheet(self._arrow_style())
        self._next_btn.clicked.connect(self._next_card)
        carousel_layout.addWidget(self._next_btn)

        layout.addLayout(carousel_layout)

        # ── 底部页码 ──
        self._page_label = QLabel()
        self._page_label.setStyleSheet('font-size: 13px; color: #888;')
        self._page_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._page_label)

        self._update_page_label()
        self._update_arrow_state()

    def _arrow_style(self) -> str:
        return (
            'QPushButton { '
            '  font-size: 24px; font-weight: bold; '
            '  background-color: #f0f0f0; '
            '  border: 1px solid #ddd; border-radius: 22px; '
            '  color: #666; '
            '} '
            'QPushButton:hover { background-color: #e0e0e0; color: #333; } '
            'QPushButton:disabled { color: #ccc; background-color: #f8f8f8; }'
        )

    def _create_achievement_card(self, ach, is_unlocked: bool) -> QFrame:
        """创建单张成就大卡片（垂直布局：大图标 | 名称 | 描述 | 状态）。"""
        card = QFrame()
        card.setStyleSheet(
            f'QFrame {{ '
            f'  background-color: {"#f0f9ff" if is_unlocked else "#fafafa"}; '
            f'  border: 2px solid {"#b3d9f2" if is_unlocked else "#e8e8e8"}; '
            f'  border-radius: 16px; '
            f'}}'
        )

        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setAlignment(Qt.AlignCenter)

        # 大图标
        icon_label = QLabel(ach.icon)
        icon_label.setFixedSize(100, 100)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(
            f'font-size: 56px; '
            f'background-color: {"#e3f2fd" if is_unlocked else "#f0f0f0"}; '
            f'border-radius: 50px; '
            f'{"color: #333;" if is_unlocked else "color: #ccc;"}'
        )
        card_layout.addWidget(icon_label, 0, Qt.AlignCenter)

        # 名称
        name_label = QLabel(ach.name)
        name_label.setStyleSheet(
            f'font-size: 24px; font-weight: bold; '
            f'color: {"#333" if is_unlocked else "#bbb"};'
        )
        name_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(name_label)

        # 描述
        desc_label = QLabel(ach.description)
        desc_label.setStyleSheet(
            f'font-size: 16px; '
            f'color: {"#666" if is_unlocked else "#ccc"};'
        )
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        card_layout.addWidget(desc_label)

        # 状态
        if is_unlocked:
            status_label = QLabel('✅ 已解锁')
            status_label.setStyleSheet(
                'font-size: 14px; color: #4CAF50; font-weight: bold; '
                'background-color: #e8f5e9; border-radius: 10px; padding: 4px 16px;'
            )
        else:
            status_label = QLabel('🔒 未解锁')
            status_label.setStyleSheet(
                'font-size: 14px; color: #aaa; '
                'background-color: #f5f5f5; border-radius: 10px; padding: 4px 16px;'
            )
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setFixedHeight(28)

        status_container = QHBoxLayout()
        status_container.addStretch()
        status_container.addWidget(status_label)
        status_container.addStretch()
        card_layout.addLayout(status_container)

        return card

    # ── 切换逻辑 ──

    def _prev_card(self) -> None:
        if self._current_index > 0:
            self._current_index -= 1
            self._stack.setCurrentIndex(self._current_index)
            self._update_page_label()
            self._update_arrow_state()

    def _next_card(self) -> None:
        if self._current_index < len(ACHIEVEMENTS) - 1:
            self._current_index += 1
            self._stack.setCurrentIndex(self._current_index)
            self._update_page_label()
            self._update_arrow_state()

    def _update_page_label(self) -> None:
        total = len(ACHIEVEMENTS)
        self._page_label.setText(f'{self._current_index + 1} / {total}')

    def _update_arrow_state(self) -> None:
        self._prev_btn.setEnabled(self._current_index > 0)
        self._next_btn.setEnabled(self._current_index < len(ACHIEVEMENTS) - 1)
