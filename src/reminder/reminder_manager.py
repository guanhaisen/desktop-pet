"""提醒管理器：加载/调度/CRUD 提醒数据。"""

import datetime
from typing import Optional

from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QTime

from src.reminder.reminder import Reminder
from src.config.config_manager import ConfigManager
from src.utils.logger import logger


class ReminderManager(QObject):
    """管理所有提醒的调度与增删改查。

    信号:
        reminderTriggered(Reminder): 提醒到时触发
        remindersChanged: 提醒列表变更（增删改后发出）
    """

    reminderTriggered = pyqtSignal(Reminder)
    remindersChanged = pyqtSignal()

    # 每分钟检查一次到期提醒
    CHECK_INTERVAL_MS = 60 * 1000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._reminders: list[Reminder] = []
        self._config = ConfigManager()
        self._timers: dict[str, QTimer] = {}  # reminder.id → QTimer
        self._check_timer: QTimer = None
        self._last_check_minute: int = -1

    def load(self) -> None:
        """从 JSON 加载所有提醒并启动调度。"""
        raw_list = self._config.load_reminders_raw()
        self._reminders = [Reminder.from_dict(d) for d in raw_list]
        logger.info(f'已加载 {len(self._reminders)} 条提醒')

        # 启动周期检查定时器
        self._check_timer = QTimer(self)
        self._check_timer.timeout.connect(self._check_due)
        self._check_timer.start(self.CHECK_INTERVAL_MS)

        # 启动时立即检查一次（处理程序关闭期间错过的时间）
        QTimer.singleShot(2000, self._check_due)

    def _check_due(self) -> None:
        """检查是否有提醒在当前时间触发。"""
        now = datetime.datetime.now()
        current_minute = now.hour * 60 + now.minute

        # 避免同一分钟内重复触发
        if current_minute == self._last_check_minute:
            return
        self._last_check_minute = current_minute

        triggered_any = False
        for reminder in self._reminders:
            if not reminder.enabled:
                continue
            if reminder.hour == now.hour and reminder.minute == now.minute:
                # none 类型只触发一次
                if reminder.repeat == 'none':
                    # 检查是否今天已经触发过
                    pass  # 简化处理：none 类型仍然每天到点触发，由用户手动关闭
                logger.info(f'提醒触发: {reminder}')
                self.reminderTriggered.emit(reminder)
                triggered_any = True

                # none 类型触发后自动禁用
                if reminder.repeat == 'none':
                    reminder.enabled = False
                    self.save()

    # ── CRUD 接口 ──────────────────────────────────────────

    def add(self, reminder: Reminder) -> None:
        self._reminders.append(reminder)
        self.save()
        self.remindersChanged.emit()
        logger.info(f'新增提醒: {reminder}')

    def update(self, reminder: Reminder) -> None:
        for i, r in enumerate(self._reminders):
            if r.id == reminder.id:
                self._reminders[i] = reminder
                self.save()
                self.remindersChanged.emit()
                logger.info(f'更新提醒: {reminder}')
                return
        logger.warning(f'更新失败，未找到提醒: {reminder.id}')

    def delete(self, reminder_id: str) -> None:
        self._reminders = [r for r in self._reminders if r.id != reminder_id]
        self.save()
        self.remindersChanged.emit()
        logger.info(f'删除提醒: {reminder_id}')

    def toggle(self, reminder_id: str) -> None:
        for r in self._reminders:
            if r.id == reminder_id:
                r.enabled = not r.enabled
                self.save()
                self.remindersChanged.emit()
                logger.info(f'切换提醒 {reminder_id} 启用状态: {r.enabled}')
                return

    def list_all(self) -> list[Reminder]:
        return list(self._reminders)

    def save(self) -> None:
        """持久化提醒列表到 JSON。"""
        data = [r.to_dict() for r in self._reminders]
        self._config.save_reminders_raw(data)
