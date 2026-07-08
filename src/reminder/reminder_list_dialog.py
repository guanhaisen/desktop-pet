"""提醒列表管理对话框。"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QHBoxLayout, QLabel, QAbstractItemView
)
from PyQt5.QtCore import Qt

from src.reminder.reminder import Reminder
from src.reminder.reminder_manager import ReminderManager
from src.reminder.reminder_dialog import ReminderDialog
from src.utils.logger import logger


class ReminderListDialog(QDialog):
    """管理现有提醒的列表对话框。"""

    def __init__(self, reminder_mgr: ReminderManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle('提醒管理')
        self.setMinimumSize(420, 360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._mgr = reminder_mgr
        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel('提醒列表')
        title.setStyleSheet('font-size: 14px; font-weight: bold; margin-bottom: 8px;')
        layout.addWidget(title)

        # 列表
        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list.setAlternatingRowColors(True)
        layout.addWidget(self._list)

        # 按钮区
        btn_layout = QHBoxLayout()

        add_btn = QPushButton('添加')
        add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton('编辑')
        edit_btn.clicked.connect(self._on_edit)
        btn_layout.addWidget(edit_btn)

        toggle_btn = QPushButton('启用/禁用')
        toggle_btn.clicked.connect(self._on_toggle)
        btn_layout.addWidget(toggle_btn)

        delete_btn = QPushButton('删除')
        delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()

        close_btn = QPushButton('关闭')
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _refresh_list(self) -> None:
        self._list.clear()
        for r in self._mgr.list_all():
            status = '✓' if r.enabled else '✗'
            text = f'{status}  {r.title}  ({r.hour:02d}:{r.minute:02d} {r.repeat})'
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, r.id)
            self._list.addItem(item)

    def _get_selected_id(self) -> str:
        item = self._list.currentItem()
        if item:
            return item.data(Qt.UserRole)
        return None

    def _on_add(self) -> None:
        dialog = ReminderDialog(parent=self)
        if dialog.exec_() == ReminderDialog.Accepted:
            reminder = dialog.get_reminder()
            self._mgr.add(reminder)
            self._refresh_list()

    def _on_edit(self) -> None:
        rid = self._get_selected_id()
        if not rid:
            return
        # 找到对应的 reminder
        reminder = next((r for r in self._mgr.list_all() if r.id == rid), None)
        if not reminder:
            return
        dialog = ReminderDialog(reminder=reminder, parent=self)
        if dialog.exec_() == ReminderDialog.Accepted:
            updated = dialog.get_reminder()
            self._mgr.update(updated)
            self._refresh_list()

    def _on_toggle(self) -> None:
        rid = self._get_selected_id()
        if rid:
            self._mgr.toggle(rid)
            self._refresh_list()

    def _on_delete(self) -> None:
        rid = self._get_selected_id()
        if rid:
            self._mgr.delete(rid)
            self._refresh_list()
