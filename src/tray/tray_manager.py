"""系统托盘管理器：图标、右键菜单、通知。"""

from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, pyqtSignal

from src.utils.path_helper import asset_path
from src.utils.logger import logger


class TrayManager(QObject):
    """管理系统托盘图标与交互。

    信号:
        show_pet: 请求显示桌宠窗口
        quit_app: 请求退出应用
        add_reminder: 请求打开添加提醒对话框
        manage_reminders: 请求打开提醒管理
        toggle_settings: 请求打开设置
        walk_now: 请求手动触发一次行走
    """

    show_pet = pyqtSignal()
    quit_app = pyqtSignal()
    add_reminder = pyqtSignal()
    manage_reminders = pyqtSignal()
    toggle_settings = pyqtSignal()
    walk_now = pyqtSignal()
    show_achievements = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tray: QSystemTrayIcon = None
        self._menu: QMenu = None

    def setup(self) -> bool:
        """初始化系统托盘。返回是否成功。"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning('系统不支持托盘图标')
            return False

        self._tray = QSystemTrayIcon(parent=self)
        icon_path = asset_path('yuexinmiao', 'yuexinmiao.png')
        icon = QIcon(icon_path)
        if icon.isNull():
            logger.warning(f'托盘图标加载失败: {icon_path}，使用默认图标')
            icon = QIcon()
        self._tray.setIcon(icon)
        self._tray.setToolTip('月薪喵')
        self._tray.activated.connect(self._on_activated)

        self._build_menu()
        self._tray.show()
        logger.info('系统托盘已初始化')
        return True

    def _build_menu(self) -> None:
        # 持有引用，避免被 Python GC 回收导致托盘菜单失效
        self._menu = QMenu()

        show_action = QAction('显示月薪喵', self._menu)
        show_action.triggered.connect(self.show_pet.emit)
        self._menu.addAction(show_action)

        walk_action = QAction('去散步', self._menu)
        walk_action.triggered.connect(self.walk_now.emit)
        self._menu.addAction(walk_action)

        self._menu.addSeparator()

        add_reminder_action = QAction('添加提醒...', self._menu)
        add_reminder_action.triggered.connect(self.add_reminder.emit)
        self._menu.addAction(add_reminder_action)

        manage_action = QAction('管理提醒', self._menu)
        manage_action.triggered.connect(self.manage_reminders.emit)
        self._menu.addAction(manage_action)

        achievements_action = QAction('🏆 打工成就', self._menu)
        achievements_action.triggered.connect(self.show_achievements.emit)
        self._menu.addAction(achievements_action)

        self._menu.addSeparator()

        settings_action = QAction('设置...', self._menu)
        settings_action.triggered.connect(self.toggle_settings.emit)
        self._menu.addAction(settings_action)

        self._menu.addSeparator()

        quit_action = QAction('退出', self._menu)
        quit_action.triggered.connect(self.quit_app.emit)
        self._menu.addAction(quit_action)

        self._tray.setContextMenu(self._menu)

    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_pet.emit()

    def show_message(self, title: str, message: str,
                     duration_ms: int = 5000) -> None:
        """弹出系统通知气泡。"""
        if self._tray:
            self._tray.showMessage(
                title, message,
                QSystemTrayIcon.Information,
                duration_ms
            )

    def set_tooltip(self, text: str) -> None:
        """更新托盘 tooltip。"""
        if self._tray:
            self._tray.setToolTip(text)

    @property
    def is_available(self) -> bool:
        return self._tray is not None and self._tray.isVisible()
