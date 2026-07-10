# 月薪喵桌面宠物 - 功能拓展计划

## 总览

基于对现有项目代码的全景分析和 2024-2026 桌面宠物趋势调研，为「月薪喵」规划了 12 个功能拓展方向，分三个梯队推进。

### 功能进度总表

| 编号 | 功能 | 梯队 | 状态 | 依赖 |
|------|------|------|------|------|
| 1 | 对话气泡系统 | 第一梯队 | ✅ 已完成 | 无 |
| 2 | 发薪日倒计时 | 第一梯队 | ✅ 已完成 | 功能 1 |
| 3 | 实时时薪 / 今日已赚 | 第一梯队 | ✅ 已完成 | 功能 1 |
| 4 | 下班倒计时 | 第一梯队 | ✅ 已完成 | 功能 1 |
| 5 | 番茄钟 / 专注模式 | 第二梯队 | ⏳ 待实施 | 无 |
| 6 | 情绪 / 心情系统 | 第二梯队 | ✅ 已完成 | 功能 1 |
| 7 | 摸鱼检测 / 久坐提醒 | 第二梯队 | ✅ 已完成 | 功能 1 |
| 8 | 鼠标跟随 / 视线追踪 | 第二梯队 | ⏳ 待实施 | 无 |
| 9 | AI 陪伴对话 | 第三梯队 | ⏳ 待实施 | 功能 1 + 6 |
| 10 | 打工人成就 / 养成系统 | 第三梯队 | ✅ 已完成 | 功能 5 + 7 |
| 11 | 自定义皮肤 / 换装 | 第三梯队 | ⏳ 待实施 | 无 |
| 12 | Live2D 动画升级 | 第三梯队 | ⏳ 待实施 | 无 |

**进度：7/15 已完成（46.7%）**

---

## 已完成功能详情

### 功能 1：对话气泡系统 ✅

**做什么**：桌宠上方弹出透明气泡显示文字（吐槽、金句），定时消失，跟随窗口移动。

**新增文件**：
- `src/ui/bubble.py` - `BubbleWindow` 气泡窗口：透明无边框置顶，`QPainter` 绘制圆角矩形+小尾巴，4 秒自动隐藏，`follow_pos()` 跟随桌宠位置
- `src/content/quotes.py` - 5 个场景分类金句库（idle/walk/interact/remind/sleep），共 36 条

**修改文件**：
- `src/pet_window.py` - 新增 `bubble_requested`/`position_changed` 信号，状态切换时 30% 概率触发气泡
- `src/app.py` - 实例化 `BubbleWindow`，连接信号

**设计决策**：气泡独立窗口不嵌入动画层；`show_bubble()` 公开方法供后续功能主动调用

---

### 功能 2：发薪日倒计时 ✅

**做什么**：设置每月发薪日，实时显示距发薪还有多少天，临近 1-3 天自动提醒。

**实现**：`SalaryManager.get_payday_countdown()` 计算天数差（处理月末天数不足），临近时通过 `remind_requested` 信号触发提醒动画+托盘通知；右键菜单和托盘 tooltip 显示倒计时。

**配置字段**：`payday_day`（默认 15 号）

---

### 功能 3：实时时薪 / 今日已赚 ✅

**做什么**：设置月薪与工作时段，工作时段内每 5 分钟随机弹气泡显示「今日已赚 ¥X.XX」。

**实现**：`SalaryManager.get_today_earnings()` 按工作时段比例计算已赚金额（日薪 = 月薪/工作日，按时间线性累计），下班后显示全额日薪。

**配置字段**：`monthly_salary`、`work_start_hour`、`work_end_hour`、`work_days_per_month`

---

### 功能 4：下班倒计时 ✅

**做什么**：实时显示距下班还有多久，到点触发「下班啦！」提醒动画。

**实现**：`SalaryManager.get_offwork_countdown()` 返回倒计时文本，`_check_offwork_remind()` 每分钟检查是否到达下班时间，到点触发提醒。右键菜单显示倒计时。

**技术亮点**：功能 2/3/4 统一由 `src/salary/salary_manager.py` 的单一 60 秒心跳定时器驱动，避免定时器碎片。

---

### 功能 6：情绪 / 心情系统 ✅

**做什么**：桌宠有心情值（0-100），初始 70（普通），点击/切换状态 +5（5 分钟冷却），1 小时不互动 -10。不同心情 idle 动画不同。

**新增文件**：
- `src/pet/mood.py` - `MoodManager` 心情管理器：维护心情值，5 分钟冷却防连续增加，1 小时衰减定时器，心情值持久化到配置

**修改文件**：
- `src/config/app_config.py` - 新增 `mood_value`、`last_mood_increase_ts` 字段
- `src/animation/animation_controller.py` - 加载 `idle-happy.gif`/`idle-tired.gif`/`idle-emo.gif` 心情变体，播放 IDLE 时按心情选择对应动画
- `src/pet_window.py` - 实例化 MoodManager，状态切换时 `try_increase()`，鼠标互动时 `record_interaction()` 重置衰减

**心情阈值**：

| 心情值 | 类别 | 动画 |
|--------|------|------|
| >= 90 | 开心 | `idle-happy.gif` |
| >= 60 | 普通 | `idle.gif` |
| >= 30 | 疲惫 | `idle-tired.gif` |
| < 30 | emo | `idle-emo.gif` |

**右键菜单**：心情值下方显示「发薪：X 天后」和下班倒计时

---

### 功能 7：摸鱼检测 / 久坐提醒 ✅

**做什么**：检测系统空闲时长，空闲超摸鱼阈值弹气泡吐槽，超久坐阈值弹气泡提醒活动。

**新增文件**：
- `src/health/idle_detector.py` - `IdleDetector` 摸鱼检测器：Windows API `GetLastInputInfo` 获取系统空闲时长，每 30 秒检查，同一类型提醒 10 分钟冷却，各有 6 条随机金句

**修改文件**：
- `src/config/app_config.py` - 新增 `idle_detect_enabled`、`idle_sit_too_long_sec`（默认 3600）、`idle_slacking_sec`（默认 600）
- `src/app.py` - 实例化 IdleDetector，连接摸鱼/久坐信号到气泡系统
- `src/config/settings_dialog.py` - 新增「摸鱼检测」设置分区

**检测类型**：

| 类型 | 阈值 | 效果 |
|------|------|------|
| 摸鱼判定 | >= 10 分钟（可调） | 气泡吐槽「又摸鱼？被我发现了吧喵~」 |
| 久坐提醒 | >= 1 小时（可调） | 气泡提醒「坐太久啦，站起来活动活动喵~」 |

---

### 功能 10：打工人成就 / 养成系统 ✅

**做什么**：记录互动、散步、打卡、摸鱼等累计数据，解锁 15 个成就，轮播卡片式展示。

**新增文件**：
- `src/progression/stats.py` - `Stats` 数据模型 + `StatsManager`，持久化到 `config/stats.json`（原子写入）
- `src/progression/achievements.py` - 15 个成就定义（互动/散步/打卡/摸鱼/久坐/提醒/在线时长）
- `src/progression/achievement_manager.py` - `AchievementManager`：每日打卡、在线时长累计（每分钟）、成就检测解锁
- `src/progression/achievement_dialog.py` - 轮播卡片式成就对话框：`QStackedWidget` 一次显示一张大卡片，左右箭头切换

**修改文件**：
- `src/app.py` - 实例化 AchievementManager，各事件埋点（互动/散步/提醒/摸鱼/久坐），成就解锁弹气泡庆祝
- `src/pet_window.py` - 新增 `interacted`/`achievements_requested` 信号，右键菜单添加成就入口
- `src/tray/tray_manager.py` - 托盘菜单添加成就入口

**15 个成就**：

| 类别 | 成就 | 解锁条件 |
|------|------|---------|
| 互动 | 👋 初次见面 | 首次互动 |
| 互动 | 🤝 热络伙伴 | 互动 50 次 |
| 互动 | 💜 至交好友 | 互动 200 次 |
| 散步 | 🐾 迈出第一步 | 首次散步 |
| 散步 | 🚶 散步达人 | 散步 30 次 |
| 打卡 | 📋 打卡报到 | 首次打卡 |
| 打卡 | 📅 一周全勤 | 连续 7 天 |
| 打卡 | 🏆 月度全勤奖 | 连续 30 天 |
| 摸鱼 | 🐟 摸鱼新手 | 首次摸鱼 |
| 摸鱼 | 🎣 摸鱼达人 | 摸鱼 20 次 |
| 久坐 | 💺 久坐反省 | 久坐 5 次 |
| 提醒 | 🔔 提醒大师 | 提醒 10 次 |
| 在线 | ⏰ 陪伴一小时 | 在线 60 分钟 |
| 在线 | 🌟 忠实伙伴 | 在线 10 小时 |
| 在线 | 🔥 打工魂觉醒 | 在线 50 小时 |

**成就对话框**：轮播卡片式，一次显示一张大卡片（56px 图标 + 名称 + 描述 + 状态），左右箭头切换，底部页码，顶部进度条+统计摘要。

---

## 待实施功能

### 第二梯队

#### 功能 5：番茄钟 / 专注工作模式
- **做什么**：启动番茄钟（25 分钟专注+5 分钟休息），专注期间进入「陪伴工作」状态
- **为什么**：把桌宠从装饰升级为效率伙伴
- **实现思路**：新增 `PetState.FOCUS` 状态；新增 `src/productivity/pomodoro.py`；托盘菜单增加「开始番茄钟」
- **涉及模块**：`states.py`、`state_machine.py`、`tray_manager.py`、`pet_window.py`
- **数据联动**：番茄完成数可接入成就系统统计

#### 功能 8：鼠标跟随 / 视线追踪
- **做什么**：桌宠朝向跟随鼠标光标移动，增强「活着」的感觉
- **为什么**：低成本的拟人化提升，桌宠「灵性」的关键体验
- **实现思路**：`QTimer` 轮询 `QCursor.pos()`，鼠标在左/右侧时朝向翻转
- **涉及模块**：`src/pet_window.py`、`src/interaction/mouse_handler.py`

### 第三梯队

#### 功能 9：AI 陪伴对话
- **做什么**：双击打开聊天框与月薪喵对话，角色设定为懂打工人的猫咪伙伴
- **为什么**：2024-2026 桌宠最大趋势，LLM 让桌宠具备真正陪伴能力
- **实现思路**：新增 `src/ai/chat_manager.py` 封装 LLM API；新增 `src/ai/chat_dialog.py`；支持本地 Ollama 兜底
- **涉及模块**：`app.py`、`config_manager.py`、`tray_manager.py`、依赖功能 1（气泡）+ 6（心情上下文）

#### 功能 11：自定义皮肤 / 换装系统
- **做什么**：支持切换不同角色皮肤或动画包，即时生效
- **为什么**：个性化是桌宠趋势，`AnimationController` 已有 `character` 参数
- **实现思路**：`AnimationController` 加 `set_character()` 方法；`assets/` 按角色名组织多套资源；可与成就系统联动解锁
- **涉及模块**：`animation_controller.py`、`path_helper.py`、`app_config.py`、`settings_dialog.py`

#### 功能 12：Live2D 动画升级
- **做什么**：将 GIF/PNG 升级为 Live2D 模型，实现更流畅的物理摆动、表情变化
- **为什么**：表现力质的飞跃，高端桌宠标配
- **实现思路**：引入 Live2D Cubism SDK，用 `QOpenGLWidget` 承载渲染，重构播放器抽象
- **风险**：Python 生态 Live2D 支持不成熟，需评估可行性

---

## 项目架构概览（当前）

```
src/
├── app.py                          # 主控制器，装配所有子系统
├── pet_window.py                   # 桌宠窗口（动画+交互+状态机+心情+气泡信号）
├── animation/
│   ├── animation_controller.py     # 动画控制器（GIF/帧播放+心情变体）
│   ├── gif_player.py               # QMovie 播放器
│   └── frame_player.py             # PNG 序列帧播放器
├── state/
│   ├── states.py                   # PetState 枚举
│   └── state_machine.py            # 优先级状态机
├── interaction/
│   └── mouse_handler.py            # 鼠标交互（拖拽/点击/右键）
├── tray/
│   └── tray_manager.py             # 系统托盘（菜单+通知+tooltip）
├── reminder/
│   ├── reminder_manager.py         # 提醒调度
│   ├── reminder_dialog.py          # 添加提醒对话框
│   └── reminder_list_dialog.py     # 管理提醒列表
├── config/
│   ├── app_config.py               # 配置数据模型（含心情+薪资+摸鱼字段）
│   ├── config_manager.py           # 配置读写管理
│   └── settings_dialog.py          # 设置对话框（基础+薪资+摸鱼）
├── ui/
│   └── bubble.py                   # 对话气泡窗口
├── content/
│   └── quotes.py                   # 打工人金句库
├── pet/
│   └── mood.py                     # 心情管理器
├── salary/
│   └── salary_manager.py           # 薪资系统（发薪倒计时+时薪+下班倒计时）
├── health/
│   └── idle_detector.py            # 摸鱼检测器
├── progression/
│   ├── stats.py                    # 统计数据模型
│   ├── achievements.py             # 15 个成就定义
│   ├── achievement_manager.py      # 成就管理器
│   └── achievement_dialog.py       # 轮播卡片式成就对话框
└── utils/
    ├── logger.py                   # 日志
    └── path_helper.py              # 资源/配置路径
```

---

## 实施依赖与建议顺序

```
功能 1 对话气泡系统 ✅
        │
        ├──> 功能 2 发薪日倒计时 ✅
        ├──> 功能 3 实时时薪/今日已赚 ✅
        └──> 功能 4 下班倒计时 ✅
                （第一梯队，全部完成）

功能 5 番茄钟 ⏳ ──> 功能 10 成就系统 ✅（数据源）
功能 6 心情系统 ✅ ──> 功能 9 AI 对话 ⏳（上下文）
功能 7 摸鱼检测 ✅ ──> 功能 10 成就系统 ✅（数据源）
功能 8 鼠标跟随 ⏳（独立）
                （第二梯队，2/4 完成）

功能 9 AI 对话 ⏳（依赖气泡+心情，前置已就绪）
功能 10 成就系统 ✅（已完成，可接入番茄钟数据）
功能 11 换装 ⏳（独立）
功能 12 Live2D ⏳（独立，高难度）
                （第三梯队，1/4 完成）
```

---

## 假设与决策

- **主题优先**：功能拓展围绕「月薪喵」打工人/薪资主题，发薪日倒计时、时薪计算等强主题功能优先
- **复用优先**：所有功能复用现有五大子系统（状态机、动画、提醒、配置、托盘），避免改动核心链路
- **气泡先行**：对话气泡是文字类功能的基础设施，已最先实现并作为后续功能的输出通道
- **心跳定时器**：薪资系统用单一 60 秒心跳统一驱动三个子功能，避免定时器碎片
- **动画降级**：`AnimationController` 自动加载心情变体，缺失时降级到 idle
- **数据持久化**：成就统计数据独立存 `config/stats.json`，复用原子写入模式
- **埋点驱动**：成就系统通过信号埋点收集各子系统事件，不侵入核心逻辑

---

## 潜在挑战与规避

1. **配置膨胀**：`AppConfig` 已有 15 个字段，后续可按功能域拆分配置模型
2. **状态机复杂度**：新增状态后优先级数值预留间隔，便于插入新状态
3. **动画资源缺口**：可先上线功能用 idle 占位，资源就绪后放入目录即自动生效
4. **性能**：当前有薪资心跳(60s)、摸鱼检测(30s)、心情衰减(1h)、在线时长(1min) 四个定时器，注意控制
5. **AI 功能隐私**：涉及 API key 与网络，建议支持本地模型兜底，key 不明文日志
