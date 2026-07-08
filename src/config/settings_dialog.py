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
        self.setMinimumWidth(360)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self._config_mgr = config_mgr
        self._setup_ui()
        self._load_values()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
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

        self._remind_spin = QSpinBox()
        self._remind_spin.setRange(1, 60)
        self._remind_spin.setSuffix(' 秒')
        form.addRow('提醒动画时长:', self._remind_spin)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_values(self) -> None:
        cfg = self._config_mgr.app_config
        self._scale_spin.setValue(cfg.scale)
        self._walk_check.setChecked(cfg.auto_walk_enabled)
        self._walk_min_spin.setValue(cfg.walk_interval_min_sec)
        self._walk_max_spin.setValue(cfg.walk_interval_max_sec)
        self._sleep_spin.setValue(cfg.idle_to_sleep_seconds)
        self._remind_spin.setValue(cfg.remind_animation_duration_sec)

    def _on_accept(self) -> None:
        cfg = self._config_mgr.app_config
        cfg.scale = self._scale_spin.value()
        cfg.auto_walk_enabled = self._walk_check.isChecked()
        cfg.walk_interval_min_sec = self._walk_min_spin.value()
        cfg.walk_interval_max_sec = max(self._walk_max_spin.value(), cfg.walk_interval_min_sec)
        cfg.idle_to_sleep_seconds = self._sleep_spin.value()
        cfg.remind_animation_duration_sec = self._remind_spin.value()
        self._config_mgr.save_app_config()
        self.accept()

    def get_scale(self) -> float:
        return self._scale_spin.value()
