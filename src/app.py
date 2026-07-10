"""桌宠应用主控制器：组装各子系统并连接信号。"""

import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QIcon

from src.pet_window import PetWindow
from src.tray.tray_manager import TrayManager
from src.reminder.reminder_manager import ReminderManager
from src.reminder.reminder_dialog import ReminderDialog
from src.config.config_manager import ConfigManager
from src.ui.bubble import BubbleWindow
from src.salary.salary_manager import SalaryManager
from src.health.idle_detector import IdleDetector
from src.progression.achievement_manager import AchievementManager
from src.productivity.pomodoro import PomodoroManager
from src.utils.path_helper import asset_path
from src.utils.logger import logger


class PetApp(QObject):
    """月薪喵桌宠应用主控制器。

    职责:
      - 创建 QApplication
      - 实例化并装配 PetWindow / TrayManager / ReminderManager
      - 连接各子系统信号
      - 提供提醒管理对话框
    """

    def __init__(self, argv: list = None):
        super().__init__()
        self._app = QApplication(argv or sys.argv)
        self._app.setApplicationName('月薪喵')
        self._app.setOrganizationName('YuexinMiao')
        # 设置应用窗口图标（任务栏等处显示）
        self._app.setWindowIcon(QIcon(asset_path('yuexinmiao', 'yuexinmiao.png')))
        # 确保最后一个窗口关闭时不自动退出（我们用托盘控制）
        self._app.setQuitOnLastWindowClosed(False)

        self._config = ConfigManager()
        self._window = PetWindow()
        self._tray = TrayManager()
        self._reminder_mgr = ReminderManager()
        self._bubble = BubbleWindow()
        self._salary_mgr = SalaryManager()
        self._idle_detector = IdleDetector()
        self._ach_mgr = AchievementManager()
        self._pomodoro_mgr = PomodoroManager()

        self._setup_tray()
        self._connect_signals()
        self._window.set_salary_manager(self._salary_mgr)
        self._window.set_pomodoro_manager(self._pomodoro_mgr)
        self._load_data()
        self._ach_mgr.start()

    def _setup_tray(self) -> None:
        if not self._tray.setup():
            logger.warning('托盘初始化失败，应用将无托盘功能')

    def _connect_signals(self) -> None:
        # 托盘信号
        self._tray.show_pet.connect(self._on_show_pet)
        self._tray.quit_app.connect(self._on_quit)
        self._tray.add_reminder.connect(self._on_add_reminder)
        self._tray.manage_reminders.connect(self._on_manage_reminders)
        self._tray.toggle_settings.connect(self._on_settings)
        self._tray.walk_now.connect(self._on_walk_now)
        self._tray.show_achievements.connect(self._on_achievements)

        # 窗口右键菜单信号
        self._window.settings_requested.connect(self._on_settings)
        self._window.add_reminder_requested.connect(self._on_add_reminder)
        self._window.manage_reminders_requested.connect(self._on_manage_reminders)
        self._window.achievements_requested.connect(self._on_achievements)
        self._window.quit_requested.connect(self._on_quit)

        # 提醒触发信号
        self._reminder_mgr.reminderTriggered.connect(self._on_reminder_triggered)

        # 提醒期间重复托盘通知
        self._window.remind_notification.connect(self._tray.show_message)

        # 气泡系统信号
        self._window.bubble_requested.connect(self._on_bubble_requested)
        self._window.position_changed.connect(self._on_position_changed)
        self._window.interacted.connect(self._ach_mgr.record_interaction)

        # 薪资系统信号
        self._salary_mgr.bubble_requested.connect(self._on_bubble_requested)
        self._salary_mgr.remind_requested.connect(self._on_salary_remind)
        self._salary_mgr.payday_info_changed.connect(self._on_payday_info_changed)

        # 摸鱼检测信号（通过气泡显示吐槽）+ 统计埋点 + 状态切换
        self._idle_detector.slacking_detected.connect(self._on_bubble_requested)
        self._idle_detector.slacking_detected.connect(self._on_slacking_detected)
        self._idle_detector.sit_too_long.connect(self._on_bubble_requested)
        self._idle_detector.slacking_detected.connect(
            lambda _: self._ach_mgr.record_slacking()
        )
        self._idle_detector.sit_too_long.connect(
            lambda _: self._ach_mgr.record_sit_too_long()
        )

        # 成就系统信号（解锁庆祝气泡）
        self._ach_mgr.achievement_unlocked.connect(self._on_bubble_requested)

        # 番茄钟信号
        self._pomodoro_mgr.focus_started.connect(self._on_focus_started)
        self._pomodoro_mgr.focus_finished.connect(self._on_focus_finished)
        self._pomodoro_mgr.bubble_requested.connect(self._on_bubble_requested)
        self._pomodoro_mgr.pomodoro_completed.connect(
            lambda: self._ach_mgr.record_interaction()  # 番茄完成也算互动
        )
        self._window.pomodoro_toggle_requested.connect(self._on_pomodoro_toggle)

    def _load_data(self) -> None:
        # 加载提醒
        self._reminder_mgr.load()
        # 加载动画资源并适配窗口尺寸（不播放）
        self._window.load_assets()
        # 先显示窗口，再播放动画——避免 QMovie 在窗口未显示时启动导致不渲染
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()
        self._window.start_idle()
        logger.info(f'月薪喵已启动 - 窗口位置: ({self._window.x()}, {self._window.y()}), '
                    f'尺寸: {self._window.width()}x{self._window.height()}, '
                    f'可见: {self._window.isVisible()}')

    # ── 信号处理 ──

    def _on_show_pet(self) -> None:
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()
        logger.info('显示桌宠窗口')

    def _on_walk_now(self) -> None:
        """手动指示桌宠去散步。"""
        self._window.trigger_walk()
        self._ach_mgr.record_walk()

    def _on_quit(self) -> None:
        # 退出前保存配置
        self._config.update_window_position(self._window.x(), self._window.y())
        logger.info('月薪喵退出')
        self._app.quit()

    def _on_add_reminder(self) -> None:
        dialog = ReminderDialog(parent=self._window)
        if dialog.exec_() == ReminderDialog.Accepted:
            reminder = dialog.get_reminder()
            self._reminder_mgr.add(reminder)

    def _on_manage_reminders(self) -> None:
        """打开提醒管理列表对话框。"""
        from src.reminder.reminder_list_dialog import ReminderListDialog
        dialog = ReminderListDialog(self._reminder_mgr, parent=self._window)
        dialog.exec_()

    def _on_achievements(self) -> None:
        """打开成就列表对话框。"""
        from src.progression.achievement_dialog import AchievementDialog
        dialog = AchievementDialog(self._ach_mgr, parent=self._window)
        dialog.exec_()

    def _on_settings(self) -> None:
        """打开设置对话框。"""
        from src.config.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self._config, parent=self._window)
        if dialog.exec_() == SettingsDialog.Accepted:
            # 应用新设置
            scale = dialog.get_scale()
            self._config.update_scale(scale)
            self._window._anim_controller.scale = scale
            # 重新加载薪资系统（用户可能修改了薪资配置）
            self._salary_mgr.reload()
            # 重新加载摸鱼检测（用户可能修改了开关或阈值）
            self._idle_detector.reload()
            logger.info(f'缩放比例已更新: {scale}')

    def _on_reminder_triggered(self, reminder) -> None:
        """提醒触发：切换到持续提醒状态（直到用户左键点击桌宠）。"""
        title = reminder.title or '提醒'
        message = reminder.message or '该注意啦！'
        # 如果窗口隐藏则显示
        if not self._window.isVisible():
            self._window.show()
            self._window.raise_()
            self._window.activateWindow()
        # trigger_remind 会立即弹出首次托盘通知并启动周期性重复通知
        self._window.trigger_remind(title, message)
        self._ach_mgr.record_reminder()

    # ── 气泡处理 ──

    def _on_bubble_requested(self, text: str) -> None:
        """收到气泡请求：显示气泡并同步当前桌宠位置。"""
        self._bubble.follow_pos(
            self._window.x(), self._window.y(), self._window.width()
        )
        self._bubble.show_message(text, duration_sec=4)

    def _on_position_changed(self, x: int, y: int, width: int) -> None:
        """桌宠位置变化时同步气泡位置。"""
        self._bubble.follow_pos(x, y, width)

    # ── 薪资处理 ──

    def _on_salary_remind(self, title: str, message: str) -> None:
        """薪资系统触发提醒（发薪日/下班）。"""
        if not self._window.isVisible():
            self._window.show()
            self._window.raise_()
            self._window.activateWindow()
        self._window.trigger_remind(title, message)
        self._ach_mgr.record_reminder()

    def _on_payday_info_changed(self, info: str) -> None:
        """发薪倒计时信息变化，更新托盘 tooltip。"""
        self._tray.set_tooltip(info)

    # ── 摸鱼检测处理 ──

    def _on_slacking_detected(self, text: str) -> None:
        """检测到摸鱼：切换桌宠到摸鱼动画状态。"""
        self._window.trigger_moyu()

    # ── 番茄钟处理 ──

    def _on_pomodoro_toggle(self) -> None:
        """切换番茄钟：未运行则开始，运行中则停止。"""
        if self._pomodoro_mgr.is_running or self._pomodoro_mgr.is_break:
            self._pomodoro_mgr.stop()
        else:
            self._pomodoro_mgr.start()

    def _on_focus_started(self) -> None:
        """番茄钟专注开始：切换到专注动画。"""
        self._window.trigger_focus()

    def _on_focus_finished(self) -> None:
        """番茄钟专注结束：恢复待机。"""
        self._window.stop_focus()

    # ── 运行 ──

    def run(self) -> int:
        """启动应用事件循环。"""
        return self._app.exec_()
