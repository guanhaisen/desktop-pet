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

        self._setup_tray()
        self._connect_signals()
        self._load_data()

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

        # 窗口右键菜单信号
        self._window.settings_requested.connect(self._on_settings)
        self._window.add_reminder_requested.connect(self._on_add_reminder)
        self._window.manage_reminders_requested.connect(self._on_manage_reminders)
        self._window.quit_requested.connect(self._on_quit)

        # 提醒触发信号
        self._reminder_mgr.reminderTriggered.connect(self._on_reminder_triggered)

        # 提醒期间重复托盘通知
        self._window.remind_notification.connect(self._tray.show_message)

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

    def _on_settings(self) -> None:
        """打开设置对话框。"""
        from src.config.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self._config, parent=self._window)
        if dialog.exec_() == SettingsDialog.Accepted:
            # 应用新设置
            scale = dialog.get_scale()
            self._config.update_scale(scale)
            self._window._anim_controller.scale = scale
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

    # ── 运行 ──

    def run(self) -> int:
        """启动应用事件循环。"""
        return self._app.exec_()
