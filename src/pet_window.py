"""桌宠主窗口：透明无边框置顶窗口，承载动画与交互。"""

import random

from PyQt5.QtWidgets import QWidget, QLabel, QApplication
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QMouseEvent

from src.state.states import PetState
from src.state.state_machine import StateMachine
from src.animation.animation_controller import AnimationController
from src.interaction.mouse_handler import MouseHandler
from src.config.config_manager import ConfigManager
from src.utils.logger import logger


class PetWindow(QWidget):
    """月薪喵桌面宠物主窗口。

    职责:
      - 透明无边框置顶窗口
      - QLabel 承载动画
      - 委托 MouseHandler 处理鼠标事件
      - 状态机驱动动画切换
      - 自动行走与睡眠定时器
      - 拦截 closeEvent 隐藏到托盘
    """

    # 默认窗口尺寸
    DEFAULT_WIDTH = 200
    DEFAULT_HEIGHT = 200

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = ConfigManager()
        self._state_machine = StateMachine(self)

        # ── 窗口属性 ──
        # 注意：不使用 Qt.Tool，该标志在 Windows 上可能导致窗口不显示
        self.setWindowFlags(
            Qt.FramelessWindowHint      # 无边框
            | Qt.WindowStaysOnTopHint   # 置顶
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # 真透明背景

        # ── 动画显示层 ──
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet('background: transparent;')
        self._label.setGeometry(0, 0, self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        # ── 动画控制器 ──
        self._anim_controller = AnimationController(
            self._label, character='yuexinmiao', parent=self
        )
        self._anim_controller.scale = self._config.app_config.scale

        # ── 鼠标交互处理器 ──
        self._mouse_handler = MouseHandler(self, self)

        # ── 定时器 ──
        self._walk_timer = QTimer(self)       # 随机行走触发
        self._sleep_timer = QTimer(self)      # 空闲进入睡眠
        self._walk_move_timer = QTimer(self)  # 行走时持续移动
        self._walk_stop_timer = QTimer(self)  # 行走停止（单次）
        self._remind_return_timer = QTimer(self)  # 提醒动画后回 idle

        self._walk_direction = 1  # 1=右, -1=左
        self._walk_speed = 2     # 每次移动像素

        self._setup_connections()
        self._setup_window()

    def _setup_connections(self) -> None:
        # 状态变化 → 动画切换
        self._state_machine.stateChanged.connect(self._on_state_changed)

        # 鼠标交互
        self._mouse_handler.clicked.connect(self._on_clicked)
        self._mouse_handler.drag_started.connect(self._on_drag_started)
        self._mouse_handler.drag_finished.connect(self._on_drag_finished)

        # 交互动画播放完毕
        self._anim_controller.animationFinished.connect(self._on_interact_finished)

        # 行走定时器
        self._walk_timer.timeout.connect(self._on_walk_triggered)
        self._walk_move_timer.timeout.connect(self._do_walk_move)
        self._walk_stop_timer.setSingleShot(True)
        self._walk_stop_timer.timeout.connect(self._stop_walking)

        # 睡眠定时器
        self._sleep_timer.timeout.connect(self._on_sleep_triggered)

        # 提醒结束定时器（单次）
        self._remind_return_timer.setSingleShot(True)
        self._remind_return_timer.timeout.connect(self._return_to_idle)

    def _setup_window(self) -> None:
        """设置窗口初始位置和尺寸。"""
        cfg = self._config.app_config
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)

        if cfg.window_x >= 0 and cfg.window_y >= 0:
            self.move(cfg.window_x, cfg.window_y)
        else:
            # 默认屏幕右下角
            screen = QApplication.desktop().availableGeometry()
            x = screen.right() - self.DEFAULT_WIDTH - 20
            y = screen.bottom() - self.DEFAULT_HEIGHT - 20
            self.move(x, y)

    # ── 资源加载 ──

    def load_assets(self) -> None:
        """加载所有动画资源。应在 show() 前调用。"""
        self._anim_controller.load_all()
        # 初始播放 idle
        self._state_machine.transition_to(PetState.IDLE, force=True)

        # 根据 idle GIF 尺寸调整窗口大小
        idle_player = self._anim_controller.get_player('idle')
        if idle_player and hasattr(idle_player, 'get_frame_size'):
            frame_size = idle_player.get_frame_size()
            if not frame_size.isEmpty():
                scale = self._config.app_config.scale
                w = int(frame_size.width() * scale)
                h = int(frame_size.height() * scale)
                self.resize(w, h)
                self._label.setGeometry(0, 0, w, h)
                logger.info(f'窗口尺寸已适配 GIF: {w}x{h}')

        self._start_idle_timers()

    # ── 状态回调 ──

    def _on_state_changed(self, state: PetState) -> None:
        self._anim_controller.play(state)

        # 根据状态管理定时器
        if state == PetState.IDLE:
            self._start_idle_timers()
        else:
            self._stop_idle_timers()

        if state == PetState.WALK:
            self._walk_move_timer.start(30)  # 30ms 移动一次
        else:
            self._walk_move_timer.stop()
            self._walk_stop_timer.stop()    # 离开行走状态时取消停止定时器

    def _on_clicked(self) -> None:
        self._state_machine.transition_to(PetState.INTERACT)

    def _on_drag_started(self) -> None:
        self._state_machine.transition_to(PetState.DRAGGING)

    def _on_drag_finished(self) -> None:
        # 保存窗口位置
        self._config.update_window_position(self.x(), self.y())
        self._state_machine.transition_to(PetState.IDLE, force=True)

    def _on_interact_finished(self, state_name: str) -> None:
        if state_name == 'interact':
            self._state_machine.transition_to(PetState.IDLE, force=True)

    def _on_walk_triggered(self) -> None:
        """随机行走定时器触发。"""
        if self._config.app_config.auto_walk_enabled:
            self._state_machine.transition_to(PetState.WALK)
            # 随机选择方向
            self._walk_direction = random.choice([1, -1])
            # 设置一次性停止定时器（行走 2-5 秒后停止）
            walk_duration_ms = random.randint(2000, 5000)
            self._walk_stop_timer.start(walk_duration_ms)

    def _on_sleep_triggered(self) -> None:
        """空闲超时进入睡眠。"""
        self._state_machine.transition_to(PetState.SLEEP)

    def _do_walk_move(self) -> None:
        """行走时持续移动窗口位置。"""
        new_x = self.x() + self._walk_direction * self._walk_speed
        screen = QApplication.desktop().availableGeometry()

        # 边界检测：碰到屏幕边缘反向
        if new_x <= screen.left():
            new_x = screen.left()
            self._walk_direction = 1
        elif new_x + self.width() >= screen.right():
            new_x = screen.right() - self.width()
            self._walk_direction = -1

        self.move(new_x, self.y())

    def _stop_walking(self) -> None:
        """行走停止定时器触发，回到 idle。"""
        if self._state_machine.current_state == PetState.WALK:
            self._state_machine.transition_to(PetState.IDLE, force=True)

    # ── 定时器管理 ──

    def _start_idle_timers(self) -> None:
        """启动空闲状态的定时器（随机行走 + 睡眠触发）。"""
        cfg = self._config.app_config
        if cfg.auto_walk_enabled:
            min_sec = cfg.walk_interval_min_sec
            max_sec = cfg.walk_interval_max_sec
            interval = random.randint(min_sec, max_sec) * 1000
            self._walk_timer.start(interval)

        sleep_ms = cfg.idle_to_sleep_seconds * 1000
        self._sleep_timer.start(sleep_ms)

    def _stop_idle_timers(self) -> None:
        self._walk_timer.stop()
        self._sleep_timer.stop()

    def reset_idle_timer(self) -> None:
        """重置空闲计时（任何交互后调用）。"""
        self._stop_idle_timers()
        if self._state_machine.current_state == PetState.IDLE:
            self._start_idle_timers()

    # ── 提醒触发 ──

    def trigger_remind(self, duration_sec: int = None) -> None:
        """触发提醒状态动画。"""
        if duration_sec is None:
            duration_sec = self._config.app_config.remind_animation_duration_sec

        self._state_machine.transition_to(PetState.REMIND, force=True)
        self._remind_return_timer.start(duration_sec * 1000)

    def _return_to_idle(self) -> None:
        self._state_machine.transition_to(PetState.IDLE, force=True)

    # ── 鼠标事件委托 ──

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.reset_idle_timer()
        self._mouse_handler.on_mouse_press(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self._mouse_handler.on_mouse_move(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._mouse_handler.on_mouse_release(event)

    # ── 关闭事件拦截 ──

    def closeEvent(self, event) -> None:
        """拦截关闭事件，隐藏到托盘而非退出。"""
        event.ignore()
        self.hide()
        logger.info('窗口隐藏到托盘')
