"""随机行走控制器：自动行走定时、边界移动与停止。"""

import random

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from src.state.states import PetState


class WalkController(QObject):
    """桌宠随机行走控制器。

    从 PetWindow 拆出：持有行走相关定时器与移动逻辑，
    窗口仅提供定位接口（x/y/move/width）。

    信号:
        moved(int, int, int): 行走移动时发出 (x, y, width)，供气泡跟随
    """

    moved = pyqtSignal(int, int, int)

    MOVE_INTERVAL_MS = 30   # 移动定时器间隔
    SPEED_PX = 2            # 每次移动像素
    MIN_DURATION_MS = 2000  # 单次行走最短时长
    MAX_DURATION_MS = 5000  # 单次行走最长时长

    def __init__(self, window, state_machine, config, parent=None):
        """
        参数:
            window: PetWindow，仅使用 x/y/move/width 定位接口
            state_machine: 状态机，用于状态切换
            config: ConfigManager，读取自动行走配置
        """
        super().__init__(parent)
        self._window = window
        self._sm = state_machine
        self._config = config

        self._walk_timer = QTimer(self)          # 随机行走触发
        self._walk_move_timer = QTimer(self)     # 行走时持续移动
        self._walk_stop_timer = QTimer(self)     # 行走停止（单次）

        self._walk_timer.timeout.connect(self._on_walk_triggered)
        self._walk_move_timer.timeout.connect(self.move_step)
        self._walk_stop_timer.setSingleShot(True)
        self._walk_stop_timer.timeout.connect(self.stop_walking)

        self._direction = 1  # 1=右, -1=左

    # ── 自动行走（空闲期间） ──

    def start_auto_interval(self) -> None:
        """按配置的随机间隔启动自动行走定时器。"""
        cfg = self._config.app_config
        if cfg.auto_walk_enabled:
            interval = random.randint(cfg.walk_interval_min_sec, cfg.walk_interval_max_sec) * 1000
            self._walk_timer.start(interval)

    def stop_auto_interval(self) -> None:
        self._walk_timer.stop()

    def _on_walk_triggered(self) -> None:
        if self._config.app_config.auto_walk_enabled:
            self.start_walk()

    # ── 行走控制 ──

    def start_walk(self) -> None:
        """开始一次行走：切换状态、随机方向、设定停止时刻。"""
        self._sm.transition_to(PetState.WALK, force=True)
        self._direction = random.choice([1, -1])
        self._walk_stop_timer.start(random.randint(self.MIN_DURATION_MS, self.MAX_DURATION_MS))

    def move_step(self) -> None:
        """行走时持续移动窗口位置，碰到屏幕边缘反向。"""
        new_x = self._window.x() + self._direction * self.SPEED_PX
        screen = QApplication.desktop().availableGeometry()

        if new_x <= screen.left():
            new_x = screen.left()
            self._direction = 1
        elif new_x + self._window.width() >= screen.right():
            new_x = screen.right() - self._window.width()
            self._direction = -1

        self._window.move(new_x, self._window.y())
        self.moved.emit(self._window.x(), self._window.y(), self._window.width())

    def stop_walking(self) -> None:
        """行走停止定时器触发，回到 idle。"""
        if self._sm.current_state == PetState.WALK:
            self._sm.transition_to(PetState.IDLE, force=True)

    # ── 状态联动 ──

    def on_state_changed(self, state: PetState) -> None:
        """状态机变化时同步移动定时器；离开行走状态时取消停止定时器。"""
        if state == PetState.WALK:
            self._walk_move_timer.start(self.MOVE_INTERVAL_MS)
        else:
            self._walk_move_timer.stop()
            self._walk_stop_timer.stop()

    @property
    def is_walking(self) -> bool:
        return self._sm.current_state == PetState.WALK
