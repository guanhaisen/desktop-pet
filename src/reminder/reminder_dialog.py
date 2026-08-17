"""提醒对话框：新增/编辑提醒的表单 UI。"""

import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QSpinBox, QComboBox, QCheckBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt

from src.reminder.reminder import Reminder

WEEKDAY_NAMES = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']


class ReminderDialog(QDialog):
    """新增或编辑提醒的对话框。"""

    def __init__(self, reminder: Reminder = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle('编辑提醒' if reminder else '添加提醒')
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._reminder = reminder
        self._setup_ui()
        if reminder:
            self._fill_form(reminder)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText('例如：该领月薪啦')
        form.addRow('标题:', self._title_edit)

        self._message_edit = QTextEdit()
        self._message_edit.setPlaceholderText('提醒内容（可选）')
        self._message_edit.setMaximumHeight(80)
        form.addRow('内容:', self._message_edit)

        time_layout = QVBoxLayout()
        time_row = QFormLayout()
        self._hour_spin = QSpinBox()
        self._hour_spin.setRange(0, 23)
        self._hour_spin.setSuffix(' 时')
        time_row.addRow('时', self._hour_spin)

        self._minute_spin = QSpinBox()
        self._minute_spin.setRange(0, 59)
        self._minute_spin.setSuffix(' 分')
        time_row.addRow('分', self._minute_spin)
        form.addRow('触发时间:', time_row)

        self._repeat_combo = QComboBox()
        self._repeat_combo.addItem('每天', 'daily')
        self._repeat_combo.addItem('仅一次', 'none')
        self._repeat_combo.addItem('每周', 'weekly')
        form.addRow('重复:', self._repeat_combo)

        self._weekday_combo = QComboBox()
        for i, name in enumerate(WEEKDAY_NAMES):
            self._weekday_combo.addItem(name, i)
        # 新建时默认选中今天；重复方式非"每周"时禁用
        self._weekday_combo.setCurrentIndex(datetime.date.today().weekday())
        self._repeat_combo.currentIndexChanged.connect(self._on_repeat_changed)
        form.addRow('星期:', self._weekday_combo)

        self._enabled_check = QCheckBox('启用此提醒')
        self._enabled_check.setChecked(True)
        form.addRow('', self._enabled_check)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_repeat_changed(self) -> None:
        """重复方式切换时启用/禁用星期选择。"""
        self._weekday_combo.setEnabled(
            self._repeat_combo.currentData() == 'weekly'
        )

    def _fill_form(self, reminder: Reminder) -> None:
        self._title_edit.setText(reminder.title)
        self._message_edit.setPlainText(reminder.message)
        self._hour_spin.setValue(reminder.hour)
        self._minute_spin.setValue(reminder.minute)
        idx = self._repeat_combo.findData(reminder.repeat)
        if idx >= 0:
            self._repeat_combo.setCurrentIndex(idx)
        self._weekday_combo.setCurrentIndex(reminder.weekday)
        self._enabled_check.setChecked(reminder.enabled)
        self._on_repeat_changed()

    def get_reminder(self) -> Reminder:
        """从表单数据构造 Reminder 对象。"""
        if self._reminder:
            r = self._reminder
        else:
            r = Reminder()
        r.title = self._title_edit.text().strip() or '提醒'
        r.message = self._message_edit.toPlainText().strip()
        r.hour = self._hour_spin.value()
        r.minute = self._minute_spin.value()
        r.repeat = self._repeat_combo.currentData()
        r.weekday = self._weekday_combo.currentData()
        r.enabled = self._enabled_check.isChecked()
        return r
