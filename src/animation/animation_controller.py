"""动画控制器：管理状态→动画映射与切换。"""

import os

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QLabel

from src.state.states import PetState
from src.animation.gif_player import GifPlayer
from src.animation.frame_player import FramePlayer
from src.utils.path_helper import asset_path
from src.utils.logger import logger


class AnimationController(QObject):
    """扫描角色资源目录，按状态加载并切换动画。

    资源约定:
      - assets/yuexinmiao/<state>.gif  → 使用 GifPlayer
      - assets/yuexinmiao/<state>/     → 使用 FramePlayer (PNG 序列)
    优先查找 .gif，不存在则查找同名目录。
    """

    animationFinished = pyqtSignal(str)  # state_name

    def __init__(self, label: QLabel, character: str = 'yuexinmiao', parent=None):
        super().__init__(parent)
        self._label = label
        self._character = character
        self._scale: float = 1.0
        self._players: dict[str, object] = {}   # state_name → player
        self._player_types: dict[str, str] = {}  # state_name → 'gif'/'frame'
        self._current_state_name: str = None
        # 心情类别（影响 idle 动画变体选择）
        self._mood_category: str = 'normal'

    @property
    def scale(self) -> float:
        return self._scale

    @scale.setter
    def scale(self, value: float) -> None:
        self._scale = value
        for player in self._players.values():
            player.set_scale(value)

    def load_all(self) -> None:
        """扫描资源目录，为每个状态预加载播放器。"""
        base_dir = asset_path(self._character)
        if not os.path.isdir(base_dir):
            logger.warning(f'角色资源目录不存在: {base_dir}')
            return

        for state in PetState:
            self._load_state(state.state_name)

        # 加载心情 idle 变体（idle-happy / idle-tired / idle-emo）
        self._load_mood_idles()

    def _load_state(self, state_name: str) -> None:
        """为指定状态加载动画资源（gif 优先，否则 PNG 序列目录）。"""
        gif_file = asset_path(self._character, f'{state_name}.gif')
        frames_dir = asset_path(self._character, state_name)

        if os.path.isfile(gif_file):
            player = GifPlayer(gif_file)
            player.set_label(self._label)
            player.set_scale(self._scale)
            self._players[state_name] = player
            self._player_types[state_name] = 'gif'
            logger.debug(f'状态 {state_name} → GIF: {gif_file}')
        elif os.path.isdir(frames_dir):
            player = FramePlayer(frames_dir)
            player.set_label(self._label)
            player.set_scale(self._scale)
            if player.load_frames():
                self._players[state_name] = player
                self._player_types[state_name] = 'frame'
                logger.debug(f'状态 {state_name} → 序列帧: {frames_dir}')
            else:
                logger.warning(f'状态 {state_name} 目录存在但无 PNG 帧: {frames_dir}')
        else:
            logger.info(f'状态 {state_name} 无动画资源，将使用 idle 降级')

    def _load_mood_idles(self) -> None:
        """加载心情 idle 变体（idle-happy.gif / idle-tired.gif / idle-emo.gif）。"""
        for category in ('happy', 'tired', 'emo'):
            variant_name = f'idle-{category}'
            gif_file = asset_path(self._character, f'{variant_name}.gif')
            if os.path.isfile(gif_file):
                player = GifPlayer(gif_file)
                player.set_label(self._label)
                player.set_scale(self._scale)
                self._players[variant_name] = player
                self._player_types[variant_name] = 'gif'
                logger.debug(f'心情变体 {variant_name} → GIF: {gif_file}')
            else:
                logger.info(f'心情变体 {variant_name}.gif 不存在，将降级到 idle')

    def set_mood_category(self, category: str) -> None:
        """设置当前心情类别，若正在播放 idle 则切换到对应变体。

        参数:
            category: happy / normal / tired / emo
        """
        self._mood_category = category
        # 若当前正在播放 idle 系列动画，切换到对应心情变体
        if self._current_state_name and self._current_state_name.startswith('idle'):
            self.play(PetState.IDLE)

    def play(self, state: PetState) -> None:
        """切换到指定状态的动画。"""
        state_name = state.state_name

        # 停止当前播放器
        self._stop_current()

        # IDLE 状态：根据心情类别选择对应变体
        if state == PetState.IDLE:
            variant_name = f'idle-{self._mood_category}'
            player = self._players.get(variant_name)
            if player is not None:
                state_name = variant_name
            else:
                # 心情变体不存在，降级到普通 idle
                player = self._players.get('idle')
                state_name = 'idle'
        else:
            # 查找目标播放器，不存在则降级到 idle
            player = self._players.get(state_name)
            if player is None and state_name != 'idle':
                logger.info(f'状态 {state_name} 无播放器，降级到 idle')
                player = self._players.get('idle')
                state_name = 'idle'

        if player is None:
            logger.warning('无任何可用动画播放器（包括 idle）')
            return

        self._current_state_name = state_name

        # 对交互动画使用单次播放模式（GifPlayer 与 FramePlayer 均支持）
        if state == PetState.INTERACT:
            player.set_loop_finished_callback(self._on_interact_finished)
            player.start(loop=False)
        else:
            player.start(loop=True)

    def _stop_current(self) -> None:
        if self._current_state_name and self._current_state_name in self._players:
            self._players[self._current_state_name].stop()

    def _on_interact_finished(self) -> None:
        """交互动画播完后发出信号。"""
        self.animationFinished.emit('interact')

    def get_player(self, state_name: str):
        return self._players.get(state_name)

    @property
    def current_state_name(self) -> str:
        return self._current_state_name
