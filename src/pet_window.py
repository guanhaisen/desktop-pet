"""桌宠主窗口：透明无边框置顶窗口，承载动画与交互。

行走/提醒/右键菜单逻辑分别拆分至：
  src/pet/walk_controller.py / src/pet/remind_controller.py / src/ui/context_menu.py
"""

import random

from PyQt5.QtWidgets import QWidget, QLabel, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QMouseEvent

from src.state.states import PetState
from src.state.state_machine import StateMachine
from src.animation.animation_controller import AnimationController
from src.interaction.mouse_handler import MouseHandler
from src.config.config_manager import ConfigManager
from src.content.quotes import get_random_quote
from src.pet.mood import MoodManager
from src.pet.walk_controller import WalkController
from src.pet.remind_controller import RemindController
from src.ui.context_menu import PetContextMenu
from src.utils.logger import logger


class PetWindow(QWidget):
    """月薪喵桌面宠物主窗口。

    职责:
      - 透明无边框置顶窗口，QLabel 承载动画
      - 委托 MouseHandler 处理鼠标事件
      - 状态机驱动动画切换与各控制器联动
      - 拦截 closeEvent 隐藏到托盘

    信号:
        settings_requested: 右键菜单中点击"设置"时发出
        add_reminder_requested: 右键菜单中点击"添加提醒"时发出
        manage_reminders_requested: 右键菜单中点击"管理提醒"时发出
        quit_requested: 右键菜单中点击"退出"时发出
        以上信号均由 PetApp 接收并处理
    """

    settings_requested = pyqtSignal()
    add_reminder_requested = pyqtSignal()
    manage_reminders_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    achievements_requested = pyqtSignal()          # 请求打开成就列表
    pomodoro_toggle_requested = pyqtSignal()        # 请求切换番茄钟
    remind_notification = pyqtSignal(str, str)  # (title, message) 请求重复弹出托盘通知

    # 气泡相关信号
    bubble_requested = pyqtSignal(str)            # 请求显示气泡文字
    position_changed = pyqtSignal(int, int, int)  # (x, y, width) 窗口位置变化，供气泡跟随
    interacted = pyqtSignal()                      # 用户互动事件（点击等），供成就系统埋点

    # 气泡触发概率（状态切换时随机弹出气泡的概率）
    BUBBLE_TRIGGER_PROBABILITY = 0.3

    # 交互动画兜底时长（秒）：超过此时长仍未收到完成信号则强制回 IDLE
    INTERACT_MAX_SEC = 8

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

        # ── 心情管理器 ──
        self._mood_mgr = MoodManager(self)

        # ── 控制器 ──
        self._walk_ctrl = WalkController(self, self._state_machine, self._config, parent=self)
        self._remind_ctrl = RemindController(self._state_machine, parent=self)
        self._context_menu = PetContextMenu(self._mood_mgr, parent=self)

        # ── 定时器 ──
        self._sleep_timer = QTimer(self)      # 空闲进入睡眠
        self._interact_fallback_timer = QTimer(self)  # 交互动画兜底（单次）

        self._setup_connections()
        self._setup_window()

    def _setup_connections(self) -> None:
        # 状态变化 → 动画切换
        self._state_machine.stateChanged.connect(self._on_state_changed)

        # 鼠标交互
        self._mouse_handler.clicked.connect(self._on_clicked)
        self._mouse_handler.right_clicked.connect(self._context_menu.exec)
        self._mouse_handler.drag_started.connect(self._on_drag_started)
        self._mouse_handler.drag_finished.connect(self._on_drag_finished)

        # 交互动画播放完毕
        self._anim_controller.animationFinished.connect(self._on_interact_finished)

        # 行走控制器：移动时气泡跟随
        self._walk_ctrl.moved.connect(
            lambda x, y, w: self.position_changed.emit(x, y, w)
        )

        # 提醒控制器：托盘通知转发
        self._remind_ctrl.notification.connect(self.remind_notification.emit)

        # 睡眠定时器
        self._sleep_timer.timeout.connect(
            lambda: self._state_machine.transition_to(PetState.SLEEP)
        )

        # 交互动画兜底定时器（单次）：动画完成信号异常时强制回 IDLE
        self._interact_fallback_timer.setSingleShot(True)
        self._interact_fallback_timer.timeout.connect(
            lambda: self._on_interact_finished('interact')
        )

        # 右键菜单 → 状态切换
        self._context_menu.walk_toggled.connect(self._toggle_walk)
        self._context_menu.sleep_toggled.connect(self._toggle_sleep)
        self._context_menu.moyu_toggled.connect(self._toggle_moyu)
        self._context_menu.force_idle_requested.connect(self._force_idle)
        self._context_menu.pomodoro_toggled.connect(self.pomodoro_toggle_requested.emit)
        self._context_menu.add_reminder_requested.connect(self.add_reminder_requested.emit)
        self._context_menu.manage_reminders_requested.connect(self.manage_reminders_requested.emit)
        self._context_menu.achievements_requested.connect(self.achievements_requested.emit)
        self._context_menu.settings_requested.connect(self.settings_requested.emit)
        self._context_menu.quit_requested.connect(self.quit_requested.emit)

        # 心情系统：心情类别变化 → 更新动画
        self._mood_mgr.mood_category_changed.connect(
            self._anim_controller.set_mood_category
        )

    def _setup_window(self) -> None:
        """设置窗口初始位置和尺寸。

        启动时固定定位到屏幕右下角，忽略上次保存的位置。
        """
        self.resize(self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
        self._move_to_bottom_right()

    def _move_to_bottom_right(self) -> None:
        """将窗口移动到主屏幕右下角，留出边距。

        右边距 120px（更靠左，避开屏幕右缘），下边距 20px。
        """
        screen = QApplication.desktop().availableGeometry()
        x = screen.right() - self.width() - 120
        y = screen.bottom() - self.height() - 20
        self.move(x, y)

    # ── 资源加载 ──

    def load_assets(self) -> None:
        """加载所有动画资源并适配窗口尺寸。应在 show() 前调用。

        注意：本方法只加载资源与确定尺寸，不开始播放动画，
        避免在窗口未显示时启动 QMovie 导致首帧不渲染。
        播放请调用 start_idle()（在 show() 之后）。
        """
        self._anim_controller.load_all()

        # 设置初始心情类别，使 idle 动画选择正确的变体
        self._anim_controller.set_mood_category(self._mood_mgr.mood_category)

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

        # 尺寸确定后重新贴合到屏幕右下角
        self._move_to_bottom_right()

    def start_idle(self) -> None:
        """开始播放 idle 动画并启动空闲定时器。应在 show() 后调用。

        直接调用动画控制器播放 idle，而非经状态机 transition_to——
        状态机初始状态即为 IDLE，同状态转换会被跳过导致动画不播放。
        """
        self._anim_controller.play(PetState.IDLE)
        self._start_idle_timers()

    # ── 状态回调 ──

    def _on_state_changed(self, state: PetState) -> None:
        self._anim_controller.play(state)

        # 根据状态管理定时器
        if state == PetState.IDLE:
            self._start_idle_timers()
        else:
            self._stop_idle_timers()

        self._walk_ctrl.on_state_changed(state)

        # 交互动画期间启动兜底定时器，其他状态清除
        if state == PetState.INTERACT:
            self._interact_fallback_timer.start(self.INTERACT_MAX_SEC * 1000)
        else:
            self._interact_fallback_timer.stop()

        # 状态切换时尝试增加心情值（5 分钟冷却）
        self._mood_mgr.try_increase()

        # 状态切换时随机触发气泡
        self._maybe_show_bubble(state)

    def _on_clicked(self) -> None:
        # 提醒激活时，左键点击停止提醒
        if self._remind_ctrl.is_active:
            self._remind_ctrl.stop()
            logger.info('用户点击停止提醒')
            return
        # 摸鱼状态被点击时恢复待机
        if self._state_machine.current_state == PetState.MOYU:
            self._state_machine.transition_to(PetState.INTERACT)
            return
        self._state_machine.transition_to(PetState.INTERACT)

    def _on_drag_started(self) -> None:
        self._state_machine.transition_to(PetState.DRAGGING)

    def _on_drag_finished(self) -> None:
        # 通知气泡跟随新位置
        self._emit_position()
        # 提醒激活时拖拽结束回到提醒状态，而非待机
        if self._remind_ctrl.is_active:
            self._state_machine.transition_to(PetState.REMIND, force=True)
        else:
            self._state_machine.transition_to(PetState.IDLE, force=True)

    def _on_interact_finished(self, state_name: str) -> None:
        # 仅当仍处于互动状态时回到待机，避免误打断提醒/拖拽等更高优先级状态
        if state_name == 'interact' and self._state_machine.current_state == PetState.INTERACT:
            self._interact_fallback_timer.stop()
            self._state_machine.transition_to(PetState.IDLE, force=True)

    # ── 行走 ──

    def trigger_walk(self) -> None:
        """手动指示行走（不受自动行走开关影响）。

        仅在待机/睡眠状态下响应，避免打断互动、提醒等高优先级状态。
        """
        if self._state_machine.current_state in (PetState.IDLE, PetState.SLEEP):
            self._mood_mgr.record_interaction()  # 托盘操作也算互动
            self._walk_ctrl.start_walk()
            logger.info('收到手动行走指示')

    def _toggle_walk(self) -> None:
        """切换行走状态：行走中则停止，否则开始行走。"""
        if self._walk_ctrl.is_walking:
            self._state_machine.transition_to(PetState.IDLE, force=True)
        else:
            self._walk_ctrl.start_walk()

    def _toggle_sleep(self) -> None:
        """切换睡眠状态：睡眠中则唤醒，否则进入睡眠。"""
        if self._state_machine.current_state == PetState.SLEEP:
            self._state_machine.transition_to(PetState.IDLE, force=True)
        else:
            self._state_machine.transition_to(PetState.SLEEP, force=True)

    def _toggle_moyu(self) -> None:
        """切换摸鱼状态：摸鱼中则恢复待机，否则进入摸鱼。"""
        if self._state_machine.current_state == PetState.MOYU:
            self._state_machine.transition_to(PetState.IDLE, force=True)
        else:
            self.trigger_moyu()

    def _force_idle(self) -> None:
        """强制恢复待机状态，忽略当前状态优先级。"""
        self._state_machine.transition_to(PetState.IDLE, force=True)

    # ── 定时器管理 ──

    def _start_idle_timers(self) -> None:
        """启动空闲状态的定时器（随机行走 + 睡眠触发）。"""
        self._walk_ctrl.start_auto_interval()
        self._sleep_timer.start(self._config.app_config.idle_to_sleep_seconds * 1000)

    def _stop_idle_timers(self) -> None:
        self._walk_ctrl.stop_auto_interval()
        self._sleep_timer.stop()

    def reset_idle_timer(self) -> None:
        """重置空闲计时（任何交互后调用）。"""
        self._stop_idle_timers()
        if self._state_machine.current_state == PetState.IDLE:
            self._start_idle_timers()

    # ── 状态触发（供 PetApp 调用）──

    def trigger_remind(self, title: str = '', message: str = '') -> None:
        """触发提醒状态，参数含义见 RemindController.trigger。"""
        self._remind_ctrl.trigger(title, message)

    def trigger_moyu(self) -> None:
        """触发摸鱼状态：切换到 MOYU 动画。

        在 IDLE/SLEEP/WALK/MOYU 状态下均可触发，
        提醒、互动、拖拽等高优先级状态不打断。
        """
        current = self._state_machine.current_state
        if current in (PetState.IDLE, PetState.SLEEP, PetState.WALK, PetState.MOYU):
            self._state_machine.transition_to(PetState.MOYU, force=True)
            logger.info(f'触发摸鱼状态（从 {current.state_name}）')
        else:
            logger.debug(f'摸鱼状态未触发，当前状态 {current.state_name} 优先级更高')

    def trigger_focus(self) -> None:
        """触发专注状态：切换到 FOCUS 动画。"""
        self._state_machine.transition_to(PetState.FOCUS, force=True)
        logger.info('触发专注状态')

    def stop_focus(self) -> None:
        """专注结束，恢复待机。"""
        if self._state_machine.current_state == PetState.FOCUS:
            self._state_machine.transition_to(PetState.IDLE, force=True)
            logger.info('专注状态结束，恢复待机')

    def set_salary_manager(self, mgr) -> None:
        """注入薪资管理器，供右键菜单显示发薪/下班倒计时。"""
        self._context_menu.set_salary_manager(mgr)

    def set_pomodoro_manager(self, mgr) -> None:
        """注入番茄钟管理器，供右键菜单显示番茄钟状态。"""
        self._context_menu.set_pomodoro_manager(mgr)

    # ── 气泡系统 ──

    def _maybe_show_bubble(self, state: PetState) -> None:
        """状态切换时按概率触发气泡。

        DRAGGING 状态不弹气泡（拖拽中不方便看）。
        """
        if state == PetState.DRAGGING:
            return
        if random.random() < self.BUBBLE_TRIGGER_PROBABILITY:
            quote = get_random_quote(state.state_name)
            self.bubble_requested.emit(quote)

    def _emit_position(self) -> None:
        """发出当前位置信号，供气泡跟随。"""
        self.position_changed.emit(self.x(), self.y(), self.width())

    # ── 鼠标事件委托 ──

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.reset_idle_timer()
        self._mood_mgr.record_interaction()  # 任何鼠标互动重置心情衰减计时
        self.interacted.emit()               # 发出互动信号供成就系统埋点
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
