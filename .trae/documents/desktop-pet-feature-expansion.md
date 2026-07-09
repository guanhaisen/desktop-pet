# 月薪喵桌面宠物 - 功能拓展计划

## 总览

基于对现有项目代码的全景分析和 2024-2026 桌面宠物趋势调研，为「月薪喵」规划了 12 个功能拓展方向，分三个梯队推进。

### 功能进度总表

| 编号 | 功能 | 梯队 | 状态 | 依赖 |
|------|------|------|------|------|
| 1 | 对话气泡系统 | 第一梯队 | ✅ 已完成 | 无 |
| 2 | 发薪日倒计时 | 第一梯队 | ⏳ 待实施 | 功能 1 |
| 3 | 实时时薪 / 今日已赚 | 第一梯队 | ⏳ 待实施 | 功能 1 |
| 4 | 下班倒计时 | 第一梯队 | ⏳ 待实施 | 功能 1 |
| 5 | 番茄钟 / 专注模式 | 第二梯队 | ⏳ 待实施 | 无 |
| 6 | 情绪 / 心情系统 | 第二梯队 | ⏳ 待实施 | 功能 1 |
| 7 | 摸鱼检测 / 久坐提醒 | 第二梯队 | ⏳ 待实施 | 功能 1 |
| 8 | 鼠标跟随 / 视线追踪 | 第二梯队 | ⏳ 待实施 | 无 |
| 9 | AI 陪伴对话 | 第三梯队 | ⏳ 待实施 | 功能 1 + 6 |
| 10 | 打工人成就 / 养成系统 | 第三梯队 | ⏳ 待实施 | 功能 5 + 7 |
| 11 | 自定义皮肤 / 换装 | 第三梯队 | ⏳ 待实施 | 无 |
| 12 | Live2D 动画升级 | 第三梯队 | ⏳ 待实施 | 无 |

---

## 功能 1：对话气泡系统 ✅ 已完成

### 做什么

在桌宠上方弹出透明气泡，显示文字（吐槽、倒计时、金句）。内容库以打工人/薪资为主题。气泡定时消失，位置跟随主窗口移动。

### 实现内容

**新增文件：**
- `src/ui/bubble.py` - `BubbleWindow` 气泡窗口组件
- `src/content/quotes.py` - 打工人主题金句库

**修改文件：**
- `src/pet_window.py` - 新增气泡信号与触发逻辑
- `src/app.py` - 装配气泡系统

### 技术细节

**`BubbleWindow`（`src/ui/bubble.py`）：**
- 透明无边框置顶窗口，`FramelessWindowHint | WindowStaysOnTopHint | Qt.Tool` + `WA_TranslucentBackground` + `WA_ShowWithoutActivating`（不抢焦点）
- `QPainter` 绘制圆角矩形（半径 12px）+ 下方三角小尾巴，背景半透明白色（alpha 230）
- `show_message(text, duration_sec=4)`：显示文字并启动单次 `QTimer`，4 秒后自动隐藏
- `follow_pos(pet_x, pet_y, pet_width)`：根据桌宠位置计算气泡位置（正上方居中）
- `QFontMetrics` 计算文字尺寸，气泡宽度自适应（80px~260px），文字自动换行

**金句库（`src/content/quotes.py`）：**
- 5 个场景分类：`IDLE_QUOTES`（10条）、`WALK_QUOTES`（6条）、`INTERACT_QUOTES`（8条）、`REMIND_QUOTES`（6条）、`SLEEP_QUOTES`（6条）
- `get_random_quote(category)` 返回随机金句

**`PetWindow` 接入（`src/pet_window.py`）：**
- 新增 `bubble_requested = pyqtSignal(str)` 信号
- 新增 `position_changed = pyqtSignal(int, int, int)` 信号（x, y, width）
- `_maybe_show_bubble(state)`：状态切换时 30% 概率触发气泡，DRAGGING 状态不弹
- `_emit_position()`：拖拽结束、行走移动时发出位置信号
- `show_bubble(text)`：公开方法，供后续功能主动调用

**`PetApp` 装配（`src/app.py`）：**
- 实例化 `BubbleWindow`
- `_on_bubble_requested`：收到气泡请求时同步桌宠位置并显示
- `_on_position_changed`：桌宠移动时同步气泡位置

### 设计决策

- **气泡独立窗口**：不嵌入 PetWindow 内，避免动画层与文字层耦合
- **半透明圆角风格**：白色半透明背景 + 圆角 + 小尾巴，符合桌宠可爱风格
- **随机触发**：状态切换时 30% 概率弹气泡，保持新鲜感但不打扰
- **手动触发接口**：`show_bubble()` 方法供后续功能（倒计时等）主动调用
- **金句分类**：按状态分类，气泡内容与当前动画状态语义一致

### 验证方式

1. 启动程序，桌宠显示 idle 动画
2. 点击桌宠（触发 INTERACT），有概率弹出气泡显示互动金句
3. 拖拽桌宠时气泡跟随移动（若气泡正在显示）
4. 气泡显示约 4 秒后自动消失
5. 右键菜单切换睡眠/行走状态，有概率弹出对应场景金句
6. 气泡位置始终在桌宠正上方，不遮挡桌宠本体
7. 气泡显示期间桌宠动画正常播放，交互不受影响

---

## 后续梯队（待实施）

### 第一梯队：高价值易实现（主题核心）

#### 功能 2：发薪日倒计时
- **做什么**：设置每月发薪日，桌宠显示距发薪还有多少天，临近时自动提醒
- **为什么**：月薪喵角色灵魂功能，打工人最关心的就是发薪
- **实现思路**：`AppConfig` 加 `payday_day` 字段；新增 `src/salary/payday_tracker.py` 用 `QTimer` 计算天数差；临近时调用 `PetWindow.trigger_remind()`
- **涉及模块**：`app_config.py`、`config_manager.py`、`pet_window.py`、`tray_manager.py`

#### 功能 3：实时时薪 / 今日已赚
- **做什么**：设置月薪与工作时段，实时计算「今天已赚 X 元」
- **为什么**：把抽象月薪变成具象的「看着钱进账」即时反馈
- **实现思路**：`AppConfig` 加 `monthly_salary`/`work_start_hour`/`work_end_hour`；新增 `src/salary/earnings_calculator.py`；结果通过气泡周期弹出
- **涉及模块**：`app_config.py`、`settings_dialog.py`、`tray_manager.py`、依赖功能 1 气泡

#### 功能 4：下班倒计时
- **做什么**：设置上下班时间，桌宠显示距下班还有多久，到点触发「下班啦！」
- **为什么**：打工人刚需，每日高频使用，复用提醒系统成本低
- **实现思路**：复用 `ReminderManager` 每分钟检查机制，到点调用 `PetWindow.trigger_remind()`
- **涉及模块**：`reminder_manager.py`、`pet_window.py`、`tray_manager.py`

### 第二梯队：中等难度（增强陪伴感）

#### 功能 5：番茄钟 / 专注工作模式
- **做什么**：启动番茄钟（25分钟专注+5分钟休息），专注期间进入「陪伴工作」状态
- **为什么**：把桌宠从装饰升级为效率伙伴
- **实现思路**：新增 `PetState.FOCUS` 状态；新增 `src/productivity/pomodoro.py`；托盘菜单增加「开始番茄钟」
- **涉及模块**：`states.py`、`state_machine.py`、`tray_manager.py`、`pet_window.py`

#### 功能 6：情绪 / 心情系统
- **做什么**：桌宠有心情值（开心/普通/疲惫/emo），受互动频率影响，不同心情下 idle 动画不同
- **为什么**：养成感是桌宠长期粘性的关键
- **实现思路**：新增 `PetState.HAPPY`/`TIRED`/`EMO`；新增 `src/pet/mood.py` 维护心情值
- **涉及模块**：`states.py`、`state_machine.py`、`animation_controller.py`、`mouse_handler.py`

#### 功能 7：摸鱼检测 / 久坐提醒
- **做什么**：检测系统空闲时间，长时间久坐触发提醒，可统计摸鱼时长
- **为什么**：健康提醒+趣味性双重价值，打工人共鸣强
- **实现思路**：Windows `ctypes` 调 `GetLastInputInfo`；新增 `src/health/idle_detector.py`
- **涉及模块**：`pet_window.py`、`tray_manager.py`、SLEEP 状态链路

#### 功能 8：鼠标跟随 / 视线追踪
- **做什么**：桌宠朝向跟随鼠标光标移动，增强「活着」的感觉
- **为什么**：低成本的拟人化提升，桌宠「灵性」的关键体验
- **实现思路**：`QTimer` 轮询 `QCursor.pos()`，鼠标在左/右侧时朝向翻转
- **涉及模块**：`pet_window.py`、`mouse_handler.py`

### 第三梯队：进阶（深度体验，长期演进）

#### 功能 9：AI 陪伴对话
- **做什么**：双击打开聊天框与月薪喵对话，角色设定为懂打工人的猫咪伙伴
- **为什么**：2024-2026 桌宠最大趋势，LLM 让桌宠具备真正陪伴能力
- **实现思路**：新增 `src/ai/chat_manager.py` 封装 LLM API；新增 `src/ai/chat_dialog.py`；支持本地 Ollama 兜底
- **涉及模块**：`app.py`、`config_manager.py`、`tray_manager.py`、依赖功能 1+6

#### 功能 10：打工人成就 / 养成系统
- **做什么**：记录工作时长、打卡天数、完成番茄数等，解锁成就（「连续打工30天」「摸鱼达人」）
- **为什么**：长期粘性的游戏化设计，自带社交话题性
- **实现思路**：新增 `src/progression/stats.py` + `achievements.py`；数据持久化到 `config/stats.json`
- **涉及模块**：`config_manager.py`、`pet_window.py`、依赖功能 1+5+7

#### 功能 11：自定义皮肤 / 换装系统
- **做什么**：支持切换不同角色皮肤或动画包，即时生效
- **为什么**：个性化是桌宠趋势，`AnimationController` 已有 `character` 参数
- **实现思路**：`AnimationController` 加 `set_character()` 方法；`assets/` 按角色名组织多套资源
- **涉及模块**：`animation_controller.py`、`path_helper.py`、`app_config.py`

#### 功能 12：Live2D 动画升级
- **做什么**：将 GIF/PNG 升级为 Live2D 模型，实现更流畅的物理摆动、表情变化
- **为什么**：表现力质的飞跃，高端桌宠标配
- **实现思路**：引入 Live2D Cubism SDK，用 `QOpenGLWidget` 承载渲染，重构播放器抽象
- **风险**：Python 生态 Live2D 支持不成熟，需评估可行性

---

## 实施依赖与建议顺序

```
功能 1 对话气泡系统 ✅ 已完成（基础设施）
        │
        ├──> 功能 2 发薪日倒计时 ⏳
        ├──> 功能 3 实时时薪/今日已赚 ⏳
        └──> 功能 4 下班倒计时 ⏳
                （第一梯队，主题核心）

功能 5 番茄钟 ⏳ ──> 功能 10 成就系统（数据源）
功能 6 心情系统 ⏳ ──> 功能 9 AI 对话（上下文）
功能 7 摸鱼检测 ⏳ ──> 功能 10 成就系统（数据源）
功能 8 鼠标跟随 ⏳（独立）
                （第二梯队，陪伴感增强）

功能 9 AI 对话 ⏳（依赖气泡+心情）
功能 10 成就系统 ⏳（依赖多个数据源）
功能 11 换装 ⏳（独立）
功能 12 Live2D ⏳（独立，高难度）
                （第三梯队，长期演进）
```

---

## 假设与决策

- **主题优先**：功能拓展围绕「月薪喵」打工人/薪资主题，发薪日倒计时、时薪计算等强主题功能优先
- **复用优先**：所有功能设计为复用现有五大子系统（状态机、动画、提醒、配置、托盘），避免改动核心链路
- **气泡先行**：对话气泡是文字类功能的基础设施，已最先实现
- **动画降级**：新状态需对应动画资源，但 `AnimationController` 已有降级到 idle 的机制，可先上线功能用 idle 占位
- **配置拆分**：多个功能加配置项后，建议按功能域拆分配置模型（如 `SalaryConfig`、`PomodoroConfig`）

---

## 潜在挑战与规避

1. **配置膨胀**：按功能域拆分配置模型，`ConfigManager` 统一管理多个 JSON 文件，复用 `_atomic_write` 模式
2. **状态机复杂度**：新增状态后优先级数值预留间隔（如 100/70/50/40/30/10/5/1），便于插入新状态
3. **动画资源缺口**：可先上线功能用 idle 占位，资源就绪后放入目录即自动生效
4. **性能**：多定时器叠加注意 QTimer 数量与频率控制，建议用单一「心跳定时器」统一驱动周期性检查
5. **AI 功能隐私**：涉及 API key 与网络，建议支持本地模型兜底，key 不明文日志
