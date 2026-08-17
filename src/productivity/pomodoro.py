"""番茄钟管理器：专注工作模式。

启动番茄钟后进入专注状态，专注结束时提示休息，休息结束可继续下一轮。
"""

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from src.config.config_manager import ConfigManager
from src.utils.logger import logger


class PomodoroManager(QObject):
    """番茄钟管理器。

    流程: 开始专注 → 专注结束（提示休息）→ 休息结束（可继续）

    信号:
        focus_started(): 专注开始，请求切换到 FOCUS 状态
        focus_finished(): 专注结束，请求恢复待机并提示休息
        bubble_requested(str): 请求显示气泡文字
        pomodoro_completed(): 一个完整番茄钟完成（专注+休息），供成就系统统计
    """

    focus_started = pyqtSignal()
    focus_finished = pyqtSignal()
    bubble_requested = pyqtSignal(str)
    pomodoro_completed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = ConfigManager()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timer)

        self._is_running: bool = False      # 是否正在专注
        self._is_break: bool = False        # 是否正在休息
        self._completed_count: int = 0      # 本次会话完成的番茄钟数

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_break(self) -> bool:
        return self._is_break

    def get_status_text(self) -> str:
        """获取当前番茄钟状态文本（供右键菜单显示）。"""
        if self._is_running:
            remaining = self._timer.remainingTime() // 1000
            mins = remaining // 60
            secs = remaining % 60
            return f'🍅 专注中 {mins:02d}:{secs:02d}'
        elif self._is_break:
            remaining = self._timer.remainingTime() // 1000
            mins = remaining // 60
            secs = remaining % 60
            return f'☕ 休息中 {mins:02d}:{secs:02d}'
        else:
            return '🍅 开始番茄钟'

    def start(self) -> None:
        """开始专注阶段。"""
        if self._is_running or self._is_break:
            logger.debug('番茄钟已在运行中，忽略重复启动')
            return

        focus_sec = self._config.app_config.pomodoro_focus_min * 60
        self._is_running = True
        self._timer.start(focus_sec * 1000)

        self.focus_started.emit()
        mins = self._config.app_config.pomodoro_focus_min
        self.bubble_requested.emit(f'番茄钟开始！专注 {mins} 分钟，加油喵！')
        logger.info(f'番茄钟专注阶段开始: {mins} 分钟')

    def stop(self) -> None:
        """手动停止番茄钟（取消当前专注/休息）。"""
        if not self._is_running and not self._is_break:
            return

        was_running = self._is_running
        self._timer.stop()
        self._is_running = False
        self._is_break = False
        if was_running:
            self.focus_finished.emit()
        logger.info('番茄钟已手动停止')

    def _on_timer(self) -> None:
        """定时器到期：专注结束或休息结束。"""
        if self._is_running:
            # 专注结束，进入休息
            self._is_running = False
            self._is_break = True
            break_sec = self._config.app_config.pomodoro_break_min * 60
            self._timer.start(break_sec * 1000)

            self.focus_finished.emit()
            mins = self._config.app_config.pomodoro_break_min
            self.bubble_requested.emit(f'专注结束！休息 {mins} 分钟放松一下喵~')
            logger.info(f'番茄钟专注结束，进入休息: {mins} 分钟')

        elif self._is_break:
            # 休息结束
            self._is_break = False
            self._completed_count += 1

            self.pomodoro_completed.emit()
            self.bubble_requested.emit(f'休息结束！已完成 {self._completed_count} 个番茄钟，继续加油喵！')
            logger.info(f'番茄钟休息结束，已完成 {self._completed_count} 个')
