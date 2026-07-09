"""桌宠主窗口：透明无边框置顶窗口，承载动画与交互。"""

import random

from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QMenu, QAction
from PyQt5.QtCore import Qt, QTimer, QPoint, pyqtSignal
from PyQt5.QtGui import QMouseEvent

from src.state.states import PetState
from src.state.state_machine import StateMachine
from src.animation.animation_controller import AnimationController
from src.interaction.mouse_handler import MouseHandler
from src.config.config_manager import ConfigManager
from src.content.quotes import get_random_quote
from src.pet.mood import MoodManager
from src.utils.logger import logger


class PetWindow(QWidget):
    """月薪喵桌面宠物主窗口。

    职责:
      - 透明无边框置顶窗口
      - QLabel 承载动画
      - 委托 MouseHandler 处理鼠标事件
      - 状态机驱动动画切换
      - 自动行走与睡眠定时器
      - 右键上下文菜单（切换行走/睡眠、恢复待机、提醒、设置、退出）
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
    remind_notification = pyqtSignal(str, str)  # (title, message) 请求重复弹出托盘通知

    # 气泡相关信号
    bubble_requested = pyqtSignal(str)            # 请求显示气泡文字
    position_changed = pyqtSignal(int, int, int)  # (x, y, width) 窗口位置变化，供气泡跟随
    interacted = pyqtSignal()                      # 用户互动事件（点击等），供成就系统埋点

    # 气泡触发概率（状态切换时随机弹出气泡的概率）
    BUBBLE_TRIGGER_PROBABILITY = 0.3

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

        # ── 薪资管理器（由 PetApp 注入，默认 None）──
        self._salary_mgr = None

        # ── 定时器 ──
        self._walk_timer = QTimer(self)       # 随机行走触发
        self._sleep_timer = QTimer(self)      # 空闲进入睡眠
        self._walk_move_timer = QTimer(self)  # 行走时持续移动
        self._walk_stop_timer = QTimer(self)  # 行走停止（单次）
        self._remind_repeat_timer = QTimer(self)  # 提醒期间重复通知

        self._walk_direction = 1  # 1=右, -1=左
        self._walk_speed = 2     # 每次移动像素

        # 提醒状态
        self._remind_active: bool = False
        self._remind_title: str = ''
        self._remind_message: str = ''

        self._setup_connections()
        self._setup_window()

    def _setup_connections(self) -> None:
        # 状态变化 → 动画切换
        self._state_machine.stateChanged.connect(self._on_state_changed)

        # 鼠标交互
        self._mouse_handler.clicked.connect(self._on_clicked)
        self._mouse_handler.right_clicked.connect(self._show_context_menu)
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

        # 提醒重复通知定时器（周期性，直到用户点击停止）
        self._remind_repeat_timer.timeout.connect(self._on_remind_repeat)

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

        if state == PetState.WALK:
            self._walk_move_timer.start(30)  # 30ms 移动一次
        else:
            self._walk_move_timer.stop()
            self._walk_stop_timer.stop()    # 离开行走状态时取消停止定时器

        # 状态切换时尝试增加心情值（5 分钟冷却）
        self._mood_mgr.try_increase()

        # 状态切换时随机触发气泡
        self._maybe_show_bubble(state)

    def _on_clicked(self) -> None:
        # 提醒激活时，左键点击停止提醒
        if self._remind_active:
            self._stop_remind()
            logger.info('用户点击停止提醒')
            return
        self._state_machine.transition_to(PetState.INTERACT)

    def _on_drag_started(self) -> None:
        self._state_machine.transition_to(PetState.DRAGGING)

    def _on_drag_finished(self) -> None:
        # 保存窗口位置
        self._config.update_window_position(self.x(), self.y())
        # 通知气泡跟随新位置
        self._emit_position()
        # 提醒激活时拖拽结束回到提醒状态，而非待机
        if self._remind_active:
            self._state_machine.transition_to(PetState.REMIND, force=True)
        else:
            self._state_machine.transition_to(PetState.IDLE, force=True)

    def _on_interact_finished(self, state_name: str) -> None:
        if state_name == 'interact':
            self._state_machine.transition_to(PetState.IDLE, force=True)

    def _on_walk_triggered(self) -> None:
        """随机行走定时器触发。"""
        if self._remind_active:
            return
        if self._config.app_config.auto_walk_enabled:
            self._start_walk()

    def trigger_walk(self) -> None:
        """手动指示行走（不受自动行走开关影响）。

        仅在待机/睡眠状态下响应，避免打断互动、提醒等高优先级状态。
        """
        if self._state_machine.current_state in (PetState.IDLE, PetState.SLEEP):
            self._mood_mgr.record_interaction()  # 托盘操作也算互动
            self._start_walk()
            logger.info('收到手动行走指示')

    def _start_walk(self) -> None:
        """开始一次行走：切换状态、随机方向、设定停止时刻。"""
        self._state_machine.transition_to(PetState.WALK, force=True)
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
        # 行走时通知气泡跟随
        self._emit_position()

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

    # 提醒期间重复弹出托盘通知的间隔（秒）
    REMIND_NOTIFY_INTERVAL_SEC = 10

    def trigger_remind(self, title: str = '', message: str = '') -> None:
        """触发提醒状态：持续播放提醒动画并周期性通知，直到用户左键点击。

        参数:
            title: 提醒标题（用于托盘通知）
            message: 提醒内容（用于托盘通知）
        """
        self._remind_title = title or '提醒'
        self._remind_message = message or '该注意啦！'
        self._remind_active = True

        # 切换到提醒动画（强制，REMIND 优先级最高）
        self._state_machine.transition_to(PetState.REMIND, force=True)

        # 立即弹出一次托盘通知
        self.remind_notification.emit(self._remind_title, self._remind_message)

        # 启动周期性重复通知定时器
        self._remind_repeat_timer.start(self.REMIND_NOTIFY_INTERVAL_SEC * 1000)
        logger.info(f'提醒已触发，将持续提醒直到用户点击: {self._remind_title}')

    def _on_remind_repeat(self) -> None:
        """提醒期间周期性重复弹出托盘通知。"""
        if self._remind_active:
            self.remind_notification.emit(self._remind_title, self._remind_message)

    def _stop_remind(self) -> None:
        """停止提醒：关闭重复通知定时器并回到待机状态。"""
        self._remind_repeat_timer.stop()
        self._remind_active = False
        self._state_machine.transition_to(PetState.IDLE, force=True)

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

    def show_bubble(self, text: str, duration_sec: int = 4) -> None:
        """主动请求显示气泡（供外部调用，如后续的倒计时功能）。

        参数:
            text: 气泡文字
            duration_sec: 显示时长（秒）
        """
        self.bubble_requested.emit(text)

    def _emit_position(self) -> None:
        """发出当前位置信号，供气泡跟随。"""
        self.position_changed.emit(self.x(), self.y(), self.width())

    # ── 右键上下文菜单 ──

    def _show_context_menu(self, pos: QPoint) -> None:
        """在鼠标位置显示右键上下文菜单。"""
        menu = QMenu(self)

        walk_action = QAction('切换行走', menu)
        walk_action.triggered.connect(self._toggle_walk)
        menu.addAction(walk_action)

        sleep_action = QAction('切换睡眠', menu)
        sleep_action.triggered.connect(self._toggle_sleep)
        menu.addAction(sleep_action)

        idle_action = QAction('恢复待机', menu)
        idle_action.triggered.connect(self._force_idle)
        menu.addAction(idle_action)

        menu.addSeparator()

        # 心情值显示（只读，不可点击）
        mood_label = self._build_mood_label()
        mood_action = QAction(mood_label, menu)
        mood_action.setEnabled(False)
        menu.addAction(mood_action)

        # 薪资信息显示（发薪倒计时 + 下班倒计时）
        if self._salary_mgr is not None and self._salary_mgr._is_enabled():
            payday_info = f'发薪：{self._salary_mgr.get_payday_countdown()} 天后'
            if self._salary_mgr.get_payday_countdown() == 0:
                payday_info = '发薪：今天发薪日！'
            payday_action = QAction(payday_info, menu)
            payday_action.setEnabled(False)
            menu.addAction(payday_action)

            offwork_info = self._salary_mgr.get_offwork_countdown()
            offwork_action = QAction(offwork_info, menu)
            offwork_action.setEnabled(False)
            menu.addAction(offwork_action)

        menu.addSeparator()

        add_reminder_action = QAction('添加提醒...', menu)
        add_reminder_action.triggered.connect(self.add_reminder_requested.emit)
        menu.addAction(add_reminder_action)

        manage_reminders_action = QAction('管理提醒', menu)
        manage_reminders_action.triggered.connect(self.manage_reminders_requested.emit)
        menu.addAction(manage_reminders_action)

        achievements_action = QAction('🏆 打工成就', menu)
        achievements_action.triggered.connect(self.achievements_requested.emit)
        menu.addAction(achievements_action)

        menu.addSeparator()

        settings_action = QAction('设置...', menu)
        settings_action.triggered.connect(self.settings_requested.emit)
        menu.addAction(settings_action)

        menu.addSeparator()

        quit_action = QAction('退出', menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        menu.exec_(pos)

    def _build_mood_label(self) -> str:
        """根据当前心情值生成右键菜单显示文本。"""
        value = self._mood_mgr.mood
        category = self._mood_mgr.mood_category
        category_text = {
            'happy': '开心',
            'normal': '普通',
            'tired': '疲惫',
            'emo': 'emo',
        }.get(category, '普通')
        return f'心情：{value}（{category_text}）'

    def set_salary_manager(self, mgr) -> None:
        """注入薪资管理器，供右键菜单显示发薪/下班倒计时。"""
        self._salary_mgr = mgr

    def _toggle_walk(self) -> None:
        """切换行走状态：行走中则停止，否则开始行走。"""
        if self._state_machine.current_state == PetState.WALK:
            self._state_machine.transition_to(PetState.IDLE, force=True)
        else:
            self._start_walk()

    def _toggle_sleep(self) -> None:
        """切换睡眠状态：睡眠中则唤醒，否则进入睡眠。"""
        if self._state_machine.current_state == PetState.SLEEP:
            self._state_machine.transition_to(PetState.IDLE, force=True)
        else:
            self._state_machine.transition_to(PetState.SLEEP, force=True)

    def _force_idle(self) -> None:
        """强制恢复待机状态，忽略当前状态优先级。"""
        self._state_machine.transition_to(PetState.IDLE, force=True)

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
