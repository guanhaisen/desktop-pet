# 月薪喵桌面宠物 - 实现计划

## 概述

基于 Python + PyQt5 开发个人桌面宠物「月薪喵」，包含动画交互与时钟提醒两大核心功能。用户已有现成 GIF/图片素材。技术方案经调研确认：PyQt5 在透明窗口、GIF 动画、系统托盘三方面均优于 Tkinter。

---

## 当前状态分析

- 项目目录为空白（全新工程），需从零搭建
- 用户已有月薪喵角色的 GIF/图片素材
- 目标平台：Windows，个人使用
- 技术选型已确定：PyQt5

---

## 技术方案要点（基于调研）

| 关键技术 | 方案 | 原因 |
|---------|------|------|
| 透明窗口 | `WA_TranslucentBackground` + `FramelessWindowHint \| WindowStaysOnTopHint \| Qt.Tool` | PyQt 支持真 alpha 透明，Tkinter 仅支持单色透明（锯齿明显） |
| GIF 动画 | `QMovie` + `QLabel.setMovie()` | 内置循环、帧率控制、缩放，一行代码显示 |
| 多状态动画 | PNG 序列帧 + `QTimer` 切换 | 支持按状态灵活切换帧集、方向翻转 |
| 系统托盘 | `QSystemTrayIcon` + `QMenu` | 原生完整支持图标、菜单、消息通知 |
| 鼠标交互 | 重写 `mousePress/Move/ReleaseEvent` | 用移动距离阈值区分点击与拖拽 |
| 提醒调度 | `QTimer` 定时 + `tray.showMessage()` | 系统通知 + 动画状态切换 |

---

## 项目结构

```
desktop-pet\
├── main.py                          # 程序入口
├── requirements.txt                 # 依赖：PyQt5
├── config\                          # 运行期配置（程序读写）
│   ├── app_config.json              # 窗口位置、缩放、行为开关
│   └── reminders.json               # 提醒数据
├── assets\yuexinmiao\               # 月薪喵角色资源
│   ├── idle.gif                     # 待机动画（GIF 循环）
│   ├── walk\walk_0001.png ...       # 行走 PNG 序列
│   ├── interact\...                 # 交互动画
│   ├── remind\...                   # 提醒动画
│   ├── sleep\...                    # 睡眠动画
│   └── tray_icon.png                # 托盘图标
└── src\                             # 源代码
    ├── __init__.py
    ├── app.py                       # PetApp：QApplication 初始化
    ├── pet_window.py                # PetWindow：透明窗口主体
    ├── animation\
    │   ├── animation_controller.py  # 状态→动画映射与切换
    │   ├── gif_player.py            # QMovie 封装
    │   └── frame_player.py          # PNG 序列 + QTimer 播放
    ├── interaction\
    │   └── mouse_handler.py         # 点击/拖拽判定
    ├── tray\
    │   └── tray_manager.py          # 托盘图标、菜单、通知
    ├── reminder\
    │   ├── reminder.py              # 提醒数据模型
    │   ├── reminder_manager.py      # 调度与触发
    │   └── reminder_dialog.py       # 新增/编辑对话框
    ├── state\
    │   ├── states.py                # PetState 枚举
    │   └── state_machine.py         # 状态转换引擎
    ├── config\
    │   ├── app_config.py            # 配置数据模型
    │   └── config_manager.py        # JSON 读写持久化
    └── utils\
        ├── path_helper.py           # 资源路径解析
        └── logger.py                # 日志工具
```

**资源约定**：`assets\yuexinmiao\` 下按状态名组织，每个状态可放一个 `.gif`（QMovie 循环）或一个 PNG 序列目录。`AnimationController` 加载时优先查找同名 `.gif`。PNG 命名规范：`<状态名>_<4位序号>.png`。

---

## 核心架构

### 分层结构

```
main.py → PetApp（QApplication 单例）
            ├── PetWindow（视图层：透明窗口 + QLabel 动画）
            │     ├── AnimationController（动画）
            │     ├── MouseHandler（交互）
            │     └── StateMachine（状态）
            ├── TrayManager（托盘 + 通知）
            └── ReminderManager（提醒调度）
                  └── ConfigManager（配置持久化，单例）
```

### 设计模式

- **状态模式**：`StateMachine` + `PetState` 枚举，状态切换驱动动画切换
- **策略模式**：`GifPlayer` 与 `FramePlayer` 实现统一接口，按资源类型选择播放策略
- **观察者模式**：PyQt `pyqtSignal` 连接各子系统（状态变化→动画切换，提醒触发→通知+动画）

### 关键信号链路

**点击交互**：`MouseHandler.clicked` → `StateMachine.transition_to(INTERACT)` → `AnimationController.switch_to('interact')` → 完成回 IDLE

**拖拽**：`mouseMoveEvent`（超过 5px 阈值）→ `PetWindow.move()` → 释放回 IDLE

**提醒**：`QTimer` 触发 → `reminderTriggered` 信号 → `TrayManager.show_message()` + `StateMachine.transition_to(REMIND)` → N 秒后回 IDLE

---

## 关键类职责

| 类名 | 文件 | 职责 |
|------|------|------|
| `PetApp` | `src/app.py` | QApplication 初始化，组装子系统，启动事件循环 |
| `PetWindow` | `src/pet_window.py` | 透明无边框窗口，QLabel 承载动画，重写鼠标事件，拦截 closeEvent |
| `AnimationController` | `src/animation/animation_controller.py` | 扫描资源目录加载动画，按状态切换播放器 |
| `GifPlayer` | `src/animation/gif_player.py` | 封装 QMovie，循环播放 |
| `FramePlayer` | `src/animation/frame_player.py` | QTimer 轮换 PNG 序列 |
| `MouseHandler` | `src/interaction/mouse_handler.py` | 点击/拖拽判定，移动距离阈值 5px |
| `TrayManager` | `src/tray/tray_manager.py` | 托盘图标、右键菜单、showMessage 通知 |
| `ReminderManager` | `src/reminder/reminder_manager.py` | 加载提醒 JSON，QTimer 调度，CRUD 接口 |
| `Reminder` | `src/reminder/reminder.py` | 数据模型：id/title/message/time/repeat/enabled |
| `ReminderDialog` | `src/reminder/reminder_dialog.py` | 表单 UI 新增/编辑提醒 |
| `StateMachine` | `src/state/state_machine.py` | 状态管理，stateChanged 信号 |
| `PetState` | `src/state/states.py` | 枚举：IDLE/WALK/INTERACT/DRAGGING/REMIND/SLEEP |
| `ConfigManager` | `src/config/config_manager.py` | 单例，JSON 读写，原子替换写入 |
| `AppConfig` | `src/config/app_config.py` | 配置模型：window_x/y/scale/行为开关 |

---

## 分阶段实施

### 阶段一：工程脚手架与环境准备
- 创建目录结构
- `requirements.txt`（PyQt5）
- `main.py` 最小骨架：QApplication + 空透明窗口
- `src/utils/path_helper.py`：资源路径解析（基于 `__file__`，预留 PyInstaller 兼容）

**验证**：运行 `main.py` 弹出透明无边框置顶窗口

### 阶段二：透明窗口 + 基础动画（QMovie）
- `PetWindow`：设置窗口属性 `FramelessWindowHint | WindowStaysOnTopHint | Tool` + `WA_TranslucentBackground`
- `QLabel` + `QMovie` 加载 `idle.gif` 循环播放
- 窗口大小匹配 GIF 尺寸，默认屏幕右下角

**验证**：月薪喵待机动画出现，背景透明，置顶

### 阶段三：鼠标交互（拖拽 + 点击）
- `MouseHandler`：重写三个鼠标事件
- 拖拽移动窗口（`window.move(start_pos + delta)`）
- 点击判定（移动距离 < 5px 视为点击），点击时切换动画或日志
- 拖拽结束保存窗口位置到 ConfigManager

**验证**：可拖拽宠物，单击有响应

### 阶段四：系统托盘
- `TrayManager`：QSystemTrayIcon + tray_icon.png
- 右键菜单：显示宠物、退出
- `closeEvent` 拦截 → `event.ignore()` + 隐藏窗口
- 双击托盘 → 显示窗口
- 托盘「退出」→ `QApplication.quit()`

**验证**：关闭隐藏到托盘，托盘可恢复/退出（MVP 完成）

### 阶段五：状态机 + 多状态动画
- `PetState` 枚举 + `StateMachine`
- `FramePlayer`（PNG 序列）+ `GifPlayer`
- `AnimationController`：扫描资源目录，按状态名加载播放器
- 信号连接：`stateChanged` → `AnimationController.play()`
- INTERACT 状态：点击 → 交互动画 → 回 IDLE
- WALK 状态：随机定时器，水平移动 + 边界检测

**验证**：idle/walk/interact 间自动切换，单击触发交互动画

### 阶段六：提醒系统
- `Reminder` 数据模型 + `ReminderDialog`（表单 UI）
- `ReminderManager`：加载 reminders.json，QTimer 调度，CRUD
- 触发 → `tray.showMessage()` + `StateMachine.transition_to(REMIND)`
- 托盘菜单增加「添加提醒」「管理提醒」

**验证**：添加 1 分钟后提醒，到时弹通知 + 播放提醒动画

### 阶段七：配置持久化完善
- `AppConfig` + `ConfigManager` 单例
- 持久化：窗口位置、缩放、自动行走、行走间隔、睡眠触发时长、提醒列表
- 启动恢复上次窗口位置
- 托盘菜单增加「设置」对话框（缩放、行为开关）

**验证**：重启后窗口位置与提醒列表恢复

### 阶段八：打磨（可选）
- SLEEP 状态：长时间无操作播放睡眠动画
- 动画切换防闪烁
- 资源缺失降级回退 idle + 日志告警
- PyInstaller 打包为 exe（可选）

---

## 配置文件示例

### `config/app_config.json`
```json
{
  "window_x": 1200,
  "window_y": 600,
  "scale": 1.0,
  "auto_walk_enabled": true,
  "walk_interval_min_sec": 30,
  "walk_interval_max_sec": 90,
  "idle_to_sleep_seconds": 300,
  "remind_animation_duration_sec": 5
}
```

### `config/reminders.json`
```json
{
  "reminders": [
    {
      "id": "r-001",
      "title": "该领月薪啦",
      "message": "今天是发工资日，记得查收月薪喵！",
      "hour": 10,
      "minute": 0,
      "repeat": "daily",
      "enabled": true,
      "animation_state": "remind"
    }
  ]
}
```

---

## 技术注意事项

1. **窗口属性顺序**：先 `setWindowFlags` 再 `setAttribute(WA_TranslucentBackground)`，在 `show()` 之前设置
2. **Qt.Tool**：使窗口不在任务栏显示，符合桌宠特性
3. **点击/拖拽阈值**：`QPoint.manhattanLength()` 比较，阈值 3~5px
4. **QMovie 缩放**：`movie.setScaledSize(QSize(...))` 按 scale 缩放
5. **动画切换防闪烁**：先停旧播放器再启新播放器，切换瞬间 `label.clear()`
6. **行走边界检测**：`QApplication.desktop().availableGeometry()` 防止走出屏幕
7. **托盘消息**：确保 `QSystemTrayIcon.show()` 后才调 `showMessage()`
8. **退出流程**：`closeEvent` 拦截隐藏，真正退出靠托盘菜单 → 退出前 `ConfigManager.save()`
9. **资源路径**：`path_helper.py` 基于 `__file__` 定位，预留 `sys._MEIPASS` 兼容打包
10. **缺失资源降级**：加载失败回退 idle + warning 日志，不崩溃
11. **配置写入**：临时文件 + 原子替换，UTF-8 编码，`ensure_ascii=False`

---

## 假设与决策

- **框架选择 PyQt5**（非 PyQt6）：社区资料最丰富，桌宠教程最多，API 稳定
- **动画方案**：单一循环用 QMovie，多状态用 PNG 序列帧（用户有 GIF 素材，idle 用 GIF；其他状态如需多帧用 PNG 序列）
- **配置存储用 JSON**：简单可读，个人项目无需数据库
- **不做 AI 对话**：用户需求为动画交互 + 时钟提醒，不含对话功能
- **打包可选**：阶段八为可选项，核心功能在阶段七完成

---

## 验证步骤

1. **阶段一验证**：`python main.py` 弹出透明窗口
2. **阶段二验证**：月薪喵 GIF 动画显示，背景透明
3. **阶段三验证**：拖拽移动正常，单击有响应
4. **阶段四验证**：关闭隐藏到托盘，托盘恢复/退出正常（MVP）
5. **阶段五验证**：idle/walk/interact 状态自动切换
6. **阶段六验证**：1 分钟提醒触发通知 + 动画
7. **阶段七验证**：重启后配置恢复
8. **阶段八验证**：睡眠动画、无崩溃、打包成功
