"""桌宠右键上下文菜单：构建时读取各管理器状态，选择通过信号发出。"""

from PyQt5.QtWidgets import QMenu, QAction
from PyQt5.QtCore import QObject, QPoint, pyqtSignal


class PetContextMenu(QObject):
    """桌宠右键菜单。

    从 PetWindow 拆出：不依赖 PetWindow，构建时从各管理器
    读取展示数据（心情/薪资/番茄钟），用户选择以语义信号发出，
    由 PetWindow 连接到状态机与转发逻辑。

    信号（与菜单项一一对应）:
        walk_toggled / sleep_toggled / moyu_toggled: 切换对应状态
        force_idle_requested: 强制恢复待机
        pomodoro_toggled: 切换番茄钟
        add_reminder_requested / manage_reminders_requested: 提醒管理
        achievements_requested: 打开成就
        settings_requested: 打开设置
        quit_requested: 退出
    """

    walk_toggled = pyqtSignal()
    sleep_toggled = pyqtSignal()
    moyu_toggled = pyqtSignal()
    force_idle_requested = pyqtSignal()
    pomodoro_toggled = pyqtSignal()
    add_reminder_requested = pyqtSignal()
    manage_reminders_requested = pyqtSignal()
    achievements_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, mood_mgr, parent=None):
        """
        参数:
            mood_mgr: MoodManager，读取心情值与类别
        """
        super().__init__(parent)
        self._mood_mgr = mood_mgr
        self._salary_mgr = None    # 由 set_salary_manager 注入
        self._pomodoro_mgr = None  # 由 set_pomodoro_manager 注入

    def set_salary_manager(self, mgr) -> None:
        """注入薪资管理器，供显示发薪/下班倒计时。"""
        self._salary_mgr = mgr

    def set_pomodoro_manager(self, mgr) -> None:
        """注入番茄钟管理器，供显示番茄钟状态。"""
        self._pomodoro_mgr = mgr

    def exec(self, pos: QPoint) -> None:
        """在指定位置构建并弹出菜单（阻塞至关闭）。"""
        menu = QMenu()
        self._add_state_section(menu)
        self._add_status_section(menu)
        self._add_app_section(menu)
        menu.exec_(pos)
        menu.deleteLater()

    def _add_state_section(self, menu: QMenu) -> None:
        """状态切换区：行走/睡眠/摸鱼/番茄钟/待机。"""
        self._action(menu, '切换行走', self.walk_toggled)
        self._action(menu, '切换睡眠', self.sleep_toggled)
        self._action(menu, '切换摸鱼', self.moyu_toggled)

        # 番茄钟状态（动态显示：开始/专注中/休息中）
        pomodoro_text = '🍅 开始番茄钟'
        if self._pomodoro_mgr is not None:
            pomodoro_text = self._pomodoro_mgr.get_status_text()
        self._action(menu, pomodoro_text, self.pomodoro_toggled)

        self._action(menu, '恢复待机', self.force_idle_requested)

    def _add_status_section(self, menu: QMenu) -> None:
        """只读状态区：心情值 + 薪资倒计时。"""
        menu.addSeparator()

        mood_action = QAction(self._build_mood_label(), menu)
        mood_action.setEnabled(False)
        menu.addAction(mood_action)

        if self._salary_mgr is not None and self._salary_mgr._is_enabled():
            days = self._salary_mgr.get_payday_countdown()
            payday_text = '发薪：今天发薪日！' if days == 0 else f'发薪：{days} 天后'
            payday_action = QAction(payday_text, menu)
            payday_action.setEnabled(False)
            menu.addAction(payday_action)

            offwork_action = QAction(self._salary_mgr.get_offwork_countdown(), menu)
            offwork_action.setEnabled(False)
            menu.addAction(offwork_action)

    def _add_app_section(self, menu: QMenu) -> None:
        """应用功能区：提醒/成就/设置/退出。"""
        menu.addSeparator()

        self._action(menu, '添加提醒...', self.add_reminder_requested)
        self._action(menu, '管理提醒', self.manage_reminders_requested)
        self._action(menu, '🏆 打工成就', self.achievements_requested)

        menu.addSeparator()

        self._action(menu, '设置...', self.settings_requested)

        menu.addSeparator()

        self._action(menu, '退出', self.quit_requested)

    @staticmethod
    def _action(menu: QMenu, text: str, signal) -> None:
        action = QAction(text, menu)
        action.triggered.connect(signal.emit)
        menu.addAction(action)

    def _build_mood_label(self) -> str:
        """根据当前心情值生成菜单显示文本。"""
        value = self._mood_mgr.mood
        category_text = {
            'happy': '开心',
            'normal': '普通',
            'tired': '疲惫',
            'emo': 'emo',
        }.get(self._mood_mgr.mood_category, '普通')
        return f'心情：{value}（{category_text}）'
