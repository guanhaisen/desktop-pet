"""设置对话框：调整缩放比例与行为开关。"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDoubleSpinBox,
    QCheckBox, QSpinBox, QDialogButtonBox, QLabel
)
from PyQt5.QtCore import Qt

from src.config.config_manager import ConfigManager


class SettingsDialog(QDialog):
    """应用设置对话框。"""

    def __init__(self, config_mgr: ConfigManager, parent=None):
        super().__init__(parent)
        self.setWindowTitle('设置')
        self.setMinimumWidth(380)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._config_mgr = config_mgr
        self._setup_ui()
        self._load_values()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # ── 基础设置 ──
        layout.addWidget(self._section_label('基础设置'))
        form = QFormLayout()

        self._scale_spin = QDoubleSpinBox()
        self._scale_spin.setRange(0.25, 3.0)
        self._scale_spin.setSingleStep(0.25)
        self._scale_spin.setSuffix(' 倍')
        form.addRow('动画缩放:', self._scale_spin)

        self._walk_check = QCheckBox('启用自动行走')
        form.addRow('', self._walk_check)

        self._walk_min_spin = QSpinBox()
        self._walk_min_spin.setRange(5, 600)
        self._walk_min_spin.setSuffix(' 秒')
        form.addRow('行走最小间隔:', self._walk_min_spin)

        self._walk_max_spin = QSpinBox()
        self._walk_max_spin.setRange(5, 3600)
        self._walk_max_spin.setSuffix(' 秒')
        form.addRow('行走最大间隔:', self._walk_max_spin)

        self._sleep_spin = QSpinBox()
        self._sleep_spin.setRange(30, 3600)
        self._sleep_spin.setSuffix(' 秒')
        form.addRow('空闲进入睡眠:', self._sleep_spin)

        layout.addLayout(form)

        # ── 薪资设置 ──
        layout.addWidget(self._section_label('薪资设置'))
        salary_form = QFormLayout()

        self._salary_check = QCheckBox('启用薪资功能')
        salary_form.addRow('', self._salary_check)

        self._salary_spin = QDoubleSpinBox()
        self._salary_spin.setRange(0.0, 1000000.0)
        self._salary_spin.setSingleStep(500.0)
        self._salary_spin.setPrefix('¥ ')
        self._salary_spin.setDecimals(2)
        salary_form.addRow('月薪金额:', self._salary_spin)

        self._payday_spin = QSpinBox()
        self._payday_spin.setRange(1, 31)
        self._payday_spin.setSuffix(' 号')
        salary_form.addRow('发薪日:', self._payday_spin)

        self._work_start_spin = QSpinBox()
        self._work_start_spin.setRange(0, 23)
        self._work_start_spin.setSuffix(' 点')
        salary_form.addRow('上班时间:', self._work_start_spin)

        self._work_end_spin = QSpinBox()
        self._work_end_spin.setRange(1, 24)
        self._work_end_spin.setSuffix(' 点')
        salary_form.addRow('下班时间:', self._work_end_spin)

        self._work_days_spin = QSpinBox()
        self._work_days_spin.setRange(1, 31)
        self._work_days_spin.setSuffix(' 天')
        salary_form.addRow('每月工作日:', self._work_days_spin)

        layout.addLayout(salary_form)

        # ── 摸鱼检测 ──
        layout.addWidget(self._section_label('摸鱼检测'))
        idle_form = QFormLayout()

        self._idle_check = QCheckBox('启用摸鱼检测')
        idle_form.addRow('', self._idle_check)

        self._idle_slacking_spin = QSpinBox()
        self._idle_slacking_spin.setRange(60, 3600)
        self._idle_slacking_spin.setSuffix(' 秒')
        self._idle_slacking_spin.setSingleStep(60)
        idle_form.addRow('摸鱼判定阈值:', self._idle_slacking_spin)

        self._idle_sit_spin = QSpinBox()
        self._idle_sit_spin.setRange(300, 7200)
        self._idle_sit_spin.setSuffix(' 秒')
        self._idle_sit_spin.setSingleStep(300)
        idle_form.addRow('久坐提醒阈值:', self._idle_sit_spin)

        layout.addLayout(idle_form)

        # ── 番茄钟 ──
        layout.addWidget(self._section_label('番茄钟'))
        pomo_form = QFormLayout()

        self._focus_min_spin = QSpinBox()
        self._focus_min_spin.setRange(5, 120)
        self._focus_min_spin.setSuffix(' 分钟')
        pomo_form.addRow('专注时长:', self._focus_min_spin)

        self._break_min_spin = QSpinBox()
        self._break_min_spin.setRange(1, 30)
        self._break_min_spin.setSuffix(' 分钟')
        pomo_form.addRow('休息时长:', self._break_min_spin)

        layout.addLayout(pomo_form)

        # ── 按钮 ──
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _section_label(self, text: str) -> QLabel:
        """创建分节标题标签。"""
        label = QLabel(text)
        label.setStyleSheet('font-weight: bold; color: #555; margin-top: 8px;')
        return label

    def _load_values(self) -> None:
        cfg = self._config_mgr.app_config
        self._scale_spin.setValue(cfg.scale)
        self._walk_check.setChecked(cfg.auto_walk_enabled)
        self._walk_min_spin.setValue(cfg.walk_interval_min_sec)
        self._walk_max_spin.setValue(cfg.walk_interval_max_sec)
        self._sleep_spin.setValue(cfg.idle_to_sleep_seconds)
        # 薪资
        self._salary_check.setChecked(cfg.salary_enabled)
        self._salary_spin.setValue(cfg.monthly_salary)
        self._payday_spin.setValue(cfg.payday_day)
        self._work_start_spin.setValue(cfg.work_start_hour)
        self._work_end_spin.setValue(cfg.work_end_hour)
        self._work_days_spin.setValue(cfg.work_days_per_month)
        # 摸鱼检测
        self._idle_check.setChecked(cfg.idle_detect_enabled)
        self._idle_slacking_spin.setValue(cfg.idle_slacking_sec)
        self._idle_sit_spin.setValue(cfg.idle_sit_too_long_sec)
        # 番茄钟
        self._focus_min_spin.setValue(cfg.pomodoro_focus_min)
        self._break_min_spin.setValue(cfg.pomodoro_break_min)

    def _on_accept(self) -> None:
        cfg = self._config_mgr.app_config
        cfg.scale = self._scale_spin.value()
        cfg.auto_walk_enabled = self._walk_check.isChecked()
        cfg.walk_interval_min_sec = self._walk_min_spin.value()
        cfg.walk_interval_max_sec = max(self._walk_max_spin.value(), cfg.walk_interval_min_sec)
        cfg.idle_to_sleep_seconds = self._sleep_spin.value()
        # 薪资
        cfg.salary_enabled = self._salary_check.isChecked()
        cfg.monthly_salary = self._salary_spin.value()
        cfg.payday_day = self._payday_spin.value()
        cfg.work_start_hour = self._work_start_spin.value()
        cfg.work_end_hour = max(self._work_end_spin.value(), cfg.work_start_hour + 1)
        cfg.work_days_per_month = self._work_days_spin.value()
        # 摸鱼检测
        cfg.idle_detect_enabled = self._idle_check.isChecked()
        cfg.idle_slacking_sec = self._idle_slacking_spin.value()
        cfg.idle_sit_too_long_sec = max(self._idle_sit_spin.value(), cfg.idle_slacking_sec + 60)
        # 番茄钟
        cfg.pomodoro_focus_min = self._focus_min_spin.value()
        cfg.pomodoro_break_min = self._break_min_spin.value()
        self._config_mgr.save_app_config()
        self.accept()

    def get_scale(self) -> float:
        return self._scale_spin.value()
