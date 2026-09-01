"""动画控制器：管理状态→动画映射与切换。"""

import glob
import os
import random

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QLabel

from src.state.states import PetState
from src.animation.gif_player import GifPlayer
from src.animation.frame_player import FramePlayer
from src.utils.path_helper import asset_path
from src.utils.logger import logger


class AnimationController(QObject):
    """扫描角色资源目录，按状态加载并切换动画。

    素材组织约定（assets/yuexinmiao/）:
      每个状态对应一个「候选池」，播放时随机挑一张，素材来源：
        - <state>.gif          该状态的主文件（若存在）
        - <state>/*.gif        该状态的候选文件夹（若存在，与主文件一起随机）
      例：多张睡眠素材丢 sleep/、多张摸鱼素材丢 moyv/、
          多张交互素材丢 interact/，即可让桌宠在对应状态下随机轮播。

      待机按心情分池：
        normal/happy/tired/emo → idle / idle-happy / idle-tired / idle-emo

      兜底：
        - 状态无 GIF 但 <state>/ 目录含 PNG 序列 → 使用帧序列播放器
        - 状态无任何资源 → 播放时降级到普通待机池
    """

    animationFinished = pyqtSignal(str)  # state_name

    # 心情分类 → 待机候选池前缀
    IDLE_POOL_NAMES = {
        'normal': 'idle',
        'happy': 'idle-happy',
        'tired': 'idle-tired',
        'emo': 'idle-emo',
    }

    def __init__(self, label: QLabel, character: str = 'yuexinmiao', parent=None):
        super().__init__(parent)
        self._label = label
        self._character = character
        self._scale: float = 1.0
        self._pools: dict[str, list] = {}   # 池名 → [player, ...] 随机候选
        self._current_player: object = None
        self._current_state_name: str = None
        self._mood_category: str = 'normal'

    @property
    def scale(self) -> float:
        return self._scale

    @scale.setter
    def scale(self, value: float) -> None:
        self._scale = value
        for pool in self._pools.values():
            for player in pool:
                player.set_scale(value)

    def load_all(self) -> None:
        """扫描资源目录，为每个状态预加载候选池。"""
        base_dir = asset_path(self._character)
        if not os.path.isdir(base_dir):
            logger.warning(f'角色资源目录不存在: {base_dir}')
            return

        for state in PetState:
            if state == PetState.IDLE:
                continue  # 待机由心情分池，单独加载
            self._load_pool(state.state_name)

        # 待机心情池
        for category in ('normal', 'happy', 'tired', 'emo'):
            self._load_pool(self.IDLE_POOL_NAMES[category])

    def _load_pool(self, pool_name: str) -> None:
        """为指定池加载动画候选（gif 主文件 + 候选目录，否则 PNG 序列）。"""
        players = []
        # 主文件 <pool>.gif
        gif_file = asset_path(self._character, f'{pool_name}.gif')
        if os.path.isfile(gif_file):
            players.append(self._make_gif_player(gif_file))
            logger.debug(f'池 {pool_name} → 主文件: {gif_file}')
        # 候选目录 <pool>/*.gif
        pool_dir = asset_path(self._character, pool_name)
        if os.path.isdir(pool_dir):
            for f in sorted(glob.glob(os.path.join(pool_dir, '*.gif'))):
                players.append(self._make_gif_player(f))
                logger.debug(f'池 {pool_name} → 候选: {f}')

        if players:
            self._finalize_pool(pool_name, players)
            return

        # 无 GIF：尝试 <pool>/ 目录内的 PNG 帧序列
        if os.path.isdir(pool_dir):
            player = FramePlayer(pool_dir)
            player.set_label(self._label)
            player.set_scale(self._scale)
            if player.load_frames():
                self._pools[pool_name] = [player]
                logger.debug(f'池 {pool_name} → 序列帧: {pool_dir}')
                return
            logger.warning(f'池 {pool_name} 目录存在但无 GIF/PNG 帧: {pool_dir}')
        else:
            logger.info(f'池 {pool_name} 无动画资源，播放时降级到待机')

    def _finalize_pool(self, pool_name: str, players: list) -> None:
        """将候选播放器落池，并对齐基准尺寸（候选尺寸可能与主文件不一致）。"""
        base = self._pick_base_player(pool_name, players)
        base_size = base.get_frame_size()
        if not base_size.isEmpty():
            for p in players:
                p.set_fixed_size(base_size)
        self._pools[pool_name] = players

    @staticmethod
    def _pick_base_player(pool_name: str, players: list):
        """选取池的基准播放器：优先同名主文件（<pool>.gif），否则池首。"""
        target = f'{pool_name}.gif'
        for p in players:
            if os.path.basename(p._gif_path).lower() == target.lower():
                return p
        return players[0]

    def _make_gif_player(self, gif_file: str) -> GifPlayer:
        player = GifPlayer(gif_file)
        player.set_label(self._label)
        player.set_scale(self._scale)
        return player

    def set_mood_category(self, category: str) -> None:
        """设置当前心情类别，若正在播放 idle 则切换到对应变体。

        参数:
            category: happy / normal / tired / emo
        """
        self._mood_category = category
        # 若当前正在播放 idle 系列动画，切换到对应心情池随机播放
        if self._current_state_name and self._current_state_name.startswith('idle'):
            self.play(PetState.IDLE)

    def play(self, state: PetState) -> None:
        """切换到指定状态的动画。"""
        # 停止当前播放器
        self._stop_current()

        if state == PetState.IDLE:
            pool_name = self.IDLE_POOL_NAMES.get(self._mood_category, 'idle')
            pool = self._pools.get(pool_name) or self._pools.get('idle')
        else:
            pool_name = state.state_name
            pool = self._pools.get(pool_name)
            if pool is None:
                logger.info(f'状态 {pool_name} 无播放器，降级到 idle')
                pool_name = 'idle'
                pool = self._pools.get('idle')

        if not pool:
            logger.warning('无任何可用动画播放器（包括 idle）')
            return

        player = random.choice(pool)
        self._current_state_name = pool_name
        self._current_player = player

        # 对交互动画使用单次播放模式（GifPlayer 与 FramePlayer 均支持）
        if state == PetState.INTERACT:
            player.set_loop_finished_callback(self._on_interact_finished)
            player.start(loop=False)
        else:
            player.start(loop=True)

    def _stop_current(self) -> None:
        if self._current_player is not None:
            self._current_player.stop()
            self._current_player = None

    def _on_interact_finished(self) -> None:
        """交互动画播完后发出信号。"""
        self.animationFinished.emit('interact')

    def get_player(self, state_name: str):
        """返回某池的首个播放器（兼容器尺寸适配等场景，优先同名主文件）。"""
        pool = self._pools.get(state_name)
        if not pool:
            return None
        return self._pick_base_player(state_name, pool)

    @property
    def current_state_name(self) -> str:
        return self._current_state_name