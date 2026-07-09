"""薪资管理器：发薪日倒计时、实时时薪、下班倒计时。

用单一心跳定时器（60 秒）统一驱动三个子功能，避免定时器碎片。
"""

import calendar
import random
from datetime import datetime, timedelta

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from src.config.config_manager import ConfigManager
from src.utils.logger import logger


class SalaryManager(QObject):
    """薪资系统管理器，统一处理发薪日倒计时、实时时薪、下班倒计时。

    功能:
        - 发薪日倒计时：计算距下次发薪的天数，临近时（前 1-3 天）触发提醒
        - 实时时薪：工作时段内每几分钟随机弹气泡显示「今日已赚 X 元」
        - 下班倒计时：到下班点触发「下班啦」提醒

    信号:
        bubble_requested(str): 请求显示气泡文字
        remind_requested(str, str): 请求触发提醒 (title, message)
        payday_info_changed(str): 发薪倒计时信息变化（供菜单/tooltip 显示）
    """

    bubble_requested = pyqtSignal(str)
    remind_requested = pyqtSignal(str, str)
    payday_info_changed = pyqtSignal(str)

    # 心跳间隔（秒）
    HEARTBEAT_INTERVAL_SEC = 60
    # 时薪气泡最小间隔（秒）—— 避免频繁弹出
    EARNINGS_BUBBLE_MIN_INTERVAL_SEC = 300  # 5 分钟
    # 时薪气泡弹出概率（每次心跳检查时）
    EARNINGS_BUBBLE_PROBABILITY = 0.3
    # 发薪日临近提醒天数
    PAYDAY_REMIND_DAYS = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config = ConfigManager()

        # 状态跟踪
        self._last_payday_remind_date: str = ''   # 已触发发薪提醒的日期（YYYY-MM-DD）
        self._last_offwork_remind_date: str = ''  # 已触发下班提醒的日期
        self._last_earnings_bubble_ts: float = 0.0

        # 心跳定时器
        self._heartbeat = QTimer(self)
        self._heartbeat.timeout.connect(self._on_heartbeat)

        if self._is_enabled():
            self._start()
            logger.info(f'薪资系统已启动 - '
                        f'月薪: {self._config.app_config.monthly_salary}, '
                        f'发薪日: {self._config.app_config.payday_day}号, '
                        f'工作时间: {self._config.app_config.work_start_hour}:00-{self._config.app_config.work_end_hour}:00')
        else:
            logger.info('薪资系统未启用（月薪未设置）')

    def _is_enabled(self) -> bool:
        """薪资功能是否启用：需要用户开启且设置了月薪。"""
        cfg = self._config.app_config
        return cfg.salary_enabled and cfg.monthly_salary > 0

    def _start(self) -> None:
        """启动心跳定时器并立即执行一次检查。"""
        self._heartbeat.start(self.HEARTBEAT_INTERVAL_SEC * 1000)
        # 启动时立即计算一次发薪信息
        self._update_payday_info()

    def reload(self) -> None:
        """设置变更后重新加载（启停心跳）。"""
        if self._is_enabled():
            if not self._heartbeat.isActive():
                self._start()
                logger.info('薪资系统已重新启动')
            else:
                self._update_payday_info()
        else:
            if self._heartbeat.isActive():
                self._heartbeat.stop()
                logger.info('薪资系统已停止')

    # ── 发薪日倒计时 ──

    def get_payday_countdown(self) -> int:
        """计算距下次发薪还有多少天（0 表示今天发薪）。"""
        cfg = self._config.app_config
        payday_day = cfg.payday_day
        today = datetime.now().date()

        # 计算本月发薪日（处理月末天数不足的情况）
        _, days_in_month = calendar.monthrange(today.year, today.month)
        actual_payday = min(payday_day, days_in_month)

        if today.day <= actual_payday:
            # 本月还未到发薪日
            payday_date = today.replace(day=actual_payday)
        else:
            # 本月已过发薪日，算下月
            if today.month == 12:
                next_month = today.replace(year=today.year + 1, month=1, day=1)
            else:
                next_month = today.replace(month=today.month + 1, day=1)
            _, next_days = calendar.monthrange(next_month.year, next_month.month)
            payday_date = next_month.replace(day=min(payday_day, next_days))

        return (payday_date - today).days

    def _update_payday_info(self) -> None:
        """更新发薪倒计时信息并发出信号。"""
        days = self.get_payday_countdown()
        if days == 0:
            info = '今天是发薪日！'
        else:
            info = f'距发薪还有 {days} 天'
        self.payday_info_changed.emit(info)

    def _check_payday_remind(self) -> None:
        """检查是否需要触发发薪日临近提醒。"""
        today_str = datetime.now().strftime('%Y-%m-%d')
        if today_str == self._last_payday_remind_date:
            return  # 今天已提醒过

        days = self.get_payday_countdown()
        if 0 < days <= self.PAYDAY_REMIND_DAYS:
            title = '发薪日提醒'
            message = f'快发工资啦！还有 {days} 天就到发薪日了喵~'
            self.remind_requested.emit(title, message)
            self._last_payday_remind_date = today_str
            logger.info(f'发薪日提醒已触发: {message}')
        elif days == 0:
            title = '发薪日快乐！'
            message = '今天是发薪日！工资到账了吗喵~'
            self.remind_requested.emit(title, message)
            self._last_payday_remind_date = today_str
            logger.info('发薪日当天提醒已触发')

    # ── 实时时薪 / 今日已赚 ──

    def get_today_earnings(self) -> float:
        """计算今日已赚金额。

        工作时段内：按时间比例累计
        下班后：全额日薪
        上班前：0
        """
        cfg = self._config.app_config
        if cfg.monthly_salary <= 0 or cfg.work_days_per_month <= 0:
            return 0.0

        now = datetime.now()
        current_hour = now.hour + now.minute / 60.0 + now.second / 3600.0

        # 不在工作时段
        if current_hour < cfg.work_start_hour:
            return 0.0
        if current_hour >= cfg.work_end_hour:
            # 下班了，全额日薪
            return cfg.monthly_salary / cfg.work_days_per_month

        # 工作时段内，按比例计算
        daily_salary = cfg.monthly_salary / cfg.work_days_per_month
        work_hours = cfg.work_end_hour - cfg.work_start_hour
        elapsed_hours = current_hour - cfg.work_start_hour
        return daily_salary * (elapsed_hours / work_hours)

    def _check_earnings_bubble(self) -> None:
        """工作时段内随机弹出今日已赚气泡。"""
        import time
        now_ts = time.time()
        if now_ts - self._last_earnings_bubble_ts < self.EARNINGS_BUBBLE_MIN_INTERVAL_SEC:
            return

        cfg = self._config.app_config
        now = datetime.now()
        current_hour = now.hour + now.minute / 60.0

        # 仅在工作时段内弹
        if not (cfg.work_start_hour <= current_hour < cfg.work_end_hour):
            return

        if random.random() < self.EARNINGS_BUBBLE_PROBABILITY:
            earnings = self.get_today_earnings()
            text = f'今日已赚 ¥{earnings:.2f}，加油打工喵！'
            self.bubble_requested.emit(text)
            self._last_earnings_bubble_ts = now_ts
            logger.debug(f'时薪气泡: {text}')

    # ── 下班倒计时 ──

    def get_offwork_countdown(self) -> str:
        """获取下班倒计时文本。

        工作时段内: '距下班还有 X 小时 Y 分钟'
        下班后: '今日已下班'
        上班前: '距上班还有 X 小时'
        """
        cfg = self._config.app_config
        now = datetime.now()
        current_hour = now.hour + now.minute / 60.0

        if current_hour >= cfg.work_end_hour:
            return '今日已下班'
        elif current_hour < cfg.work_start_hour:
            diff = cfg.work_start_hour - current_hour
            hours = int(diff)
            minutes = int((diff - hours) * 60)
            return f'距上班还有 {hours} 小时 {minutes} 分钟'
        else:
            diff = cfg.work_end_hour - current_hour
            hours = int(diff)
            minutes = int((diff - hours) * 60)
            if hours == 0:
                return f'距下班还有 {minutes} 分钟'
            return f'距下班还有 {hours} 小时 {minutes} 分钟'

    def _check_offwork_remind(self) -> None:
        """检查是否到达下班时间，触发提醒。"""
        today_str = datetime.now().strftime('%Y-%m-%d')
        if today_str == self._last_offwork_remind_date:
            return  # 今天已提醒过

        cfg = self._config.app_config
        now = datetime.now()
        # 到达下班时间（精确到分钟）
        if now.hour == cfg.work_end_hour and now.minute == 0:
            title = '下班啦！'
            message = '辛苦一天，该撤了喵~ 明天见！'
            self.remind_requested.emit(title, message)
            self._last_offwork_remind_date = today_str
            logger.info('下班提醒已触发')
        # 也处理刚好过下班时间的情况（启动时已过点）
        elif now.hour == cfg.work_end_hour and now.minute <= 5:
            title = '下班啦！'
            message = '已经到下班时间了，快撤喵~'
            self.remind_requested.emit(title, message)
            self._last_offwork_remind_date = today_str
            logger.info('下班提醒已触发（延迟检测）')

    # ── 心跳 ──

    def _on_heartbeat(self) -> None:
        """每分钟执行一次，检查所有薪资相关事件。"""
        self._check_payday_remind()
        self._check_earnings_bubble()
        self._check_offwork_remind()
        self._update_payday_info()
