# 小鼠三键序列任务模拟程序

## 目录

- [项目概述](#项目概述)
- [主要功能](#主要功能)
- [系统要求](#系统要求)
- [安装和配置](#安装和配置)
- [详细使用说明](#详细使用说明)
- [任务模式详解](#任务模式详解)
- [参数配置](#参数配置)
- [热键操作](#热键操作)
- [数据记录](#数据记录)
- [版本更新历史](#版本更新历史)
- [常见问题解答](#常见问题解答)
- [技术架构](#技术架构)
- [未来扩展](#未来扩展)

## 项目概述

本项目是一个基于Python和Pygame开发的行为学实验程序，用于模拟小鼠三键序列任务。该程序完全使用键盘和屏幕来模拟真实的动物行为学实验环境，为研究人员提供了一个高精度、可配置的实验平台。

程序采用严格的状态机架构，实现了精确的时序控制和"松开判定"逻辑，能够准确记录和分析实验数据。支持两种训练模式（入门训练和完整序列），具备实时UI显示、离线数据记录、自适应难度调节等功能。

### 设计目标

- **高精度时序控制**：使用`time.perf_counter()`实现毫秒级精度的时间测量
- **严谨的实验逻辑**：完整实现"松开判定"、错误分类、ITI管理等行为学实验要求
- **可扩展架构**：预留硬件接口，便于未来连接DAQ设备或移植到MATLAB平台
- **完整数据记录**：提供详细的trial级别数据和会话汇总统计
- **用户友好界面**：实时显示实验状态、参数调整、历史结果等信息

## 主要功能

### 🎯 双模式训练系统
- **Shaping-1模式**：入门训练，单LED响应训练
- **Sequence-3模式**：完整三键序列任务（L1→B1→I1→L2→B2→I2→L3→B3→奖励）

### ⏱️ 精确时序控制
- 高精度计时系统（基于`perf_counter()`）
- 严格的"松开判定"逻辑
- 可配置的等待窗口和释放窗口
- 精确的ITI（试间间隔）管理

### 📊 实时数据监控
- 实时UI显示当前试次状态
- 历史结果条带（最近30个trial）
- 累计统计信息（正确率、错误分类统计）
- 当前参数实时显示

### 🔧 灵活参数配置
- JSON配置文件支持
- 热键实时参数调整
- 自适应难度调节（可选）
- 完整的参数快照记录

### 📝 完整数据记录
- 每个trial独立JSON文件
- 会话汇总CSV文件
- 详细事件时间戳记录
- 参数变更历史追踪

### 🎮 丰富交互控制
- 完整热键系统
- 暂停/恢复功能
- 阶段切换
- 参数实时调整
- 帮助信息显示

### 🔌 可扩展架构
- 硬件抽象层设计
- 预留DAQ接口
- 便于MATLAB平台移植
- 模块化代码结构

## 系统要求

### 硬件要求
- **处理器**：Intel/AMD双核处理器或更高
- **内存**：至少4GB RAM（推荐8GB）
- **存储空间**：至少500MB可用磁盘空间
- **显示器**：分辨率至少1024x768（推荐1920x1080）
- **键盘**：标准QWERTY键盘，支持J、K、L键

### 软件要求
- **操作系统**：
  - Windows 10/11（推荐）
  - macOS 10.14+
  - Linux（Ubuntu 18.04+）
- **Python版本**：Python 3.8或更高版本

### Python依赖包
```
pygame >= 2.0.0    # 图形界面和事件处理
```

### 可选依赖（用于未来扩展）
- **MATLAB Runtime**：用于MATLAB平台移植
- **DAQ驱动**：用于硬件设备连接
- **NumPy/SciPy**：用于高级数据分析

## 安装和配置

### 快速安装

#### 1. 安装Python
确保系统已安装Python 3.8或更高版本：
```bash
python --version
```

#### 2. 安装依赖包
```bash
pip install pygame
```

#### 3. 下载项目
```bash
git clone <repository-url>
cd tasktrain
```

#### 4. 运行程序
```bash
python mouse_sequence_task.py
```

### 详细配置

#### 配置文件设置
程序使用`config.json`文件存储参数配置：

```json
{
  "wait_window_ms": 2000,
  "release_window_ms": 500,
  "iti_duration_ms": 3000,
  "adaptive_enabled": false,
  "adaptive_target_accuracy": 0.8,
  "adaptive_adjustment_factor": 0.1,
  "session_max_trials": 100
}
```

#### 输入法配置（Windows）
程序会自动处理中文输入法问题：
- 启动时自动切换到英文输入法
- 运行时自动检测和修复输入法状态
- 确保J、K、L键正常响应

#### 数据目录结构
```
tasktrain/
├── mouse_sequence_task.py    # 主程序
├── config.json              # 配置文件
├── data/                    # 数据目录
│   ├── trials/             # 单个trial数据
│   └── sessions/           # 会话汇总数据
└── README.md               # 说明文档
```

### 验证安装

运行程序后应看到：
1. Pygame初始化成功信息
2. 配置文件加载确认
3. 输入法切换成功提示（Windows）
4. 实验界面正常显示

如果遇到问题，请参考[常见问题解答](#常见问题解答)部分。

## 详细使用说明

### 程序启动和界面概览

#### 启动程序
```bash
python mouse_sequence_task.py
```

#### 主界面布局
程序启动后显示以下界面元素：

```
┌─────────────────────────────────────────────────────────────┐
│                    小鼠三键序列任务                            │
├─────────────────────────────────────────────────────────────┤
│ 当前状态: WAITING_FOR_START                                  │
│ 当前模式: Sequence-3                                         │
│ Trial: 0/100                                                │
├─────────────────────────────────────────────────────────────┤
│ [L1] [B1] [I1] [L2] [B2] [I2] [L3] [B3] [奖励]               │
│  J    K    L    J    K    L    J    K                       │
├─────────────────────────────────────────────────────────────┤
│ 历史结果: ✓✗✓✓✗✓✓✓✗✓ (最近10个trial)                        │
├─────────────────────────────────────────────────────────────┤
│ 参数设置:                                                    │
│ 等待窗口: 2000ms  释放窗口: 500ms  ITI: 3000ms                │
│ 自适应: 关闭      目标正确率: 80%                              │
├─────────────────────────────────────────────────────────────┤
│ 统计信息:                                                    │
│ 总试次: 45  正确: 36  错误: 9  正确率: 80.0%                   │
│ 错误类型: 序列错误:3 超时:4 提前释放:2                          │
└─────────────────────────────────────────────────────────────┘
```

### 操作控制

#### 基本控制键
- **空格键**：开始/暂停实验
- **ESC键**：退出程序
- **H键**：显示/隐藏帮助信息
- **R键**：重置当前会话

#### 模式切换
- **1键**：切换到Shaping-1模式（入门训练）
- **2键**：切换到Sequence-3模式（完整序列）

#### 参数调整热键
- **Q/A键**：增加/减少等待窗口时间（步长：100ms）
- **W/S键**：增加/减少释放窗口时间（步长：50ms）
- **E/D键**：增加/减少ITI时间（步长：200ms）
- **T键**：切换自适应模式开关
- **Y/G键**：增加/减少自适应目标正确率（步长：5%）

#### 配置管理
- **F5键**：保存当前参数到config.json
- **F9键**：从config.json重新加载参数

## 任务模式详解

### Shaping-1模式（入门训练）

#### 任务目标
训练受试者学会基本的按键-释放操作模式。

#### 操作流程
1. **等待阶段**：屏幕显示单个LED指示灯
2. **按键阶段**：受试者按下对应键（J、K或L）
3. **保持阶段**：在释放窗口内保持按键
4. **释放阶段**：在释放窗口内释放按键
5. **奖励阶段**：成功完成后给予奖励反馈

#### 成功条件
- 在等待窗口内按下正确的键
- 在释放窗口内释放按键
- 整个过程无错误按键

#### 错误类型
- **超时错误**：等待窗口内未按键
- **错误按键**：按下非目标键
- **提前释放**：释放窗口前释放按键
- **超时释放**：释放窗口后仍未释放

### Sequence-3模式（完整序列）

#### 任务目标
完成完整的三键序列任务：L1→B1→I1→L2→B2→I2→L3→B3→奖励

#### 详细操作流程

**阶段1：L1（左键1）**
1. 屏幕显示L1 LED亮起
2. 受试者按下J键
3. 在释放窗口内保持按键
4. 在释放窗口内释放J键

**阶段2：B1（中键1）**
1. L1成功后，B1 LED亮起
2. 受试者按下K键
3. 在释放窗口内保持按键
4. 在释放窗口内释放K键

**阶段3：I1（右键1）**
1. B1成功后，I1 LED亮起
2. 受试者按下L键
3. 在释放窗口内保持按键
4. 在释放窗口内释放L键

**阶段4-6：重复L2→B2→I2序列**
**阶段7-8：重复L3→B3序列**

**阶段9：奖励**
- 所有序列完成后显示奖励反馈
- 记录完整trial数据
- 进入ITI阶段

#### 松开判定逻辑

程序实现严格的"松开判定"机制：

```python
# 伪代码示例
if key_pressed:
    if current_time - press_time >= release_window_start:
        if current_time - press_time <= release_window_end:
            # 在释放窗口内，等待释放
            if key_released:
                success = True
                advance_to_next_stage()
        else:
            # 超过释放窗口，判定为超时
            error_type = "TIMEOUT_RELEASE"
            fail_trial()
    else:
        # 还未到释放窗口，继续等待
        continue
else:
    if press_time > 0:  # 之前有按键
        if current_time - press_time < release_window_start:
            # 提前释放
            error_type = "EARLY_RELEASE"
            fail_trial()
```

#### 错误处理机制

**立即失败情况**：
- 按下错误的键
- 在释放窗口前释放按键
- 超过等待窗口未按键
- 超过释放窗口未释放

**错误后处理**：
1. 立即停止当前trial
2. 记录错误类型和时间戳
3. 进入ITI阶段
4. ITI结束后开始新trial

### ITI（试间间隔）管理

#### ITI阶段特点
- 所有LED熄灭
- 显示倒计时
- 检测意外按键

#### ITI期间按键处理
- **检测机制**：持续监控所有按键
- **错误记录**：每次按键记录为ITI错误
- **时间处理**：ITI时间不会重置，继续倒计时
- **统计影响**：ITI错误单独统计，不影响trial正确率

#### ITI结束条件
- 倒计时结束
- 且当前无任何按键被按下
- 确保"干净"的trial开始状态

## 参数配置

### 核心时序参数

#### 等待窗口（Wait Window）
- **定义**：从LED亮起到必须按下按键的最大时间
- **默认值**：2000ms
- **调整范围**：500ms - 10000ms
- **调整热键**：Q（增加100ms）/ A（减少100ms）
- **影响**：过短会增加超时错误，过长会降低任务难度

#### 释放窗口（Release Window）
- **定义**：按键后必须保持按下的时间窗口
- **默认值**：500ms
- **调整范围**：100ms - 2000ms
- **调整热键**：W（增加50ms）/ S（减少50ms）
- **影响**：过短会增加提前释放错误，过长会增加超时释放错误

#### ITI持续时间（ITI Duration）
- **定义**：trial间的休息时间
- **默认值**：3000ms
- **调整范围**：1000ms - 10000ms
- **调整热键**：E（增加200ms）/ D（减少200ms）
- **影响**：影响实验节奏和受试者疲劳度

### 自适应参数

#### 自适应模式开关
- **功能**：根据表现自动调整难度
- **默认状态**：关闭
- **切换热键**：T键
- **工作原理**：监控最近trials的正确率，自动调整时序参数

#### 目标正确率
- **定义**：自适应模式的目标正确率
- **默认值**：80%
- **调整范围**：50% - 95%
- **调整热键**：Y（增加5%）/ G（减少5%）
- **作用**：正确率高于目标时增加难度，低于目标时降低难度

#### 调整因子
- **定义**：自适应调整的步长
- **默认值**：0.1（10%）
- **范围**：0.05 - 0.3
- **作用**：控制参数调整的激进程度

### 会话参数

#### 最大Trial数
- **定义**：单次会话的最大trial数量
- **默认值**：100
- **调整方式**：修改config.json文件
- **达到后**：自动结束会话并保存数据

#### 参数快照
- **功能**：记录每次参数变更
- **存储位置**：trial数据中的parameter_snapshot字段
- **用途**：分析参数变化对表现的影响

### 配置文件管理

#### config.json结构
```json
{
  "wait_window_ms": 2000,
  "release_window_ms": 500,
  "iti_duration_ms": 3000,
  "adaptive_enabled": false,
  "adaptive_target_accuracy": 0.8,
  "adaptive_adjustment_factor": 0.1,
  "session_max_trials": 100,
  "ui_update_interval_ms": 16,
  "data_save_interval": 1
}
```

#### 参数保存和加载
- **保存**：F5键保存当前参数到config.json
- **加载**：F9键从config.json重新加载参数
- **自动保存**：程序退出时自动保存当前参数
- **验证**：加载时验证参数范围，无效值使用默认值

## 热键操作

### 完整热键列表

#### 基本控制
| 按键 | 功能 | 说明 |
|------|------|------|
| 空格 | 开始/暂停 | 切换实验运行状态 |
| ESC | 退出程序 | 安全退出并保存数据 |
| H | 帮助信息 | 显示/隐藏热键说明 |
| R | 重置会话 | 清空当前会话数据，重新开始 |

#### 模式切换
| 按键 | 功能 | 说明 |
|------|------|------|
| 1 | Shaping-1模式 | 切换到入门训练模式 |
| 2 | Sequence-3模式 | 切换到完整序列模式 |

#### 参数调整
| 按键 | 功能 | 步长 | 范围 |
|------|------|------|------|
| Q | 增加等待窗口 | +100ms | 500-10000ms |
| A | 减少等待窗口 | -100ms | 500-10000ms |
| W | 增加释放窗口 | +50ms | 100-2000ms |
| S | 减少释放窗口 | -50ms | 100-2000ms |
| E | 增加ITI时间 | +200ms | 1000-10000ms |
| D | 减少ITI时间 | -200ms | 1000-10000ms |
| T | 切换自适应模式 | - | 开启/关闭 |
| Y | 增加目标正确率 | +5% | 50-95% |
| G | 减少目标正确率 | -5% | 50-95% |

#### 配置管理
| 按键 | 功能 | 说明 |
|------|------|------|
| F5 | 保存配置 | 保存当前参数到config.json |
| F9 | 加载配置 | 从config.json重新加载参数 |

#### 任务执行键
| 按键 | 功能 | 对应LED |
|------|------|--------|
| J | 左键操作 | L1, L2, L3 |
| K | 中键操作 | B1, B2, B3 |
| L | 右键操作 | I1, I2, I3 |

### 热键使用技巧

#### 实时参数调整
1. **观察表现**：通过历史结果条带观察最近表现
2. **识别问题**：根据错误类型判断需要调整的参数
3. **渐进调整**：小步长调整，观察效果
4. **保存设置**：找到合适参数后用F5保存

#### 常见调整策略
- **超时错误多**：增加等待窗口（Q键）
- **提前释放多**：增加释放窗口（W键）
- **任务太简单**：减少等待窗口（A键）或释放窗口（S键）
- **受试者疲劳**：增加ITI时间（E键）
- **进度太慢**：减少ITI时间（D键）

#### 自适应模式使用
1. **启用自适应**：按T键开启
2. **设置目标**：用Y/G键调整目标正确率
3. **观察调整**：系统会自动调整参数
4. **手动干预**：必要时可手动微调

## 数据记录

### 数据存储结构

#### 目录组织
```
data/
├── trials/                    # 单个trial详细数据
│   ├── trial_20240115_143022_001.json
│   ├── trial_20240115_143025_002.json
│   └── ...
├── sessions/                  # 会话汇总数据
│   ├── session_20240115_143022.csv
│   ├── session_20240115_150000.csv
│   └── ...
└── config_history/           # 配置变更历史
    ├── config_20240115_143022.json
    └── ...
```

### Trial级别数据

#### 数据文件命名
格式：`trial_YYYYMMDD_HHMMSS_NNN.json`
- YYYYMMDD：日期
- HHMMSS：时间
- NNN：trial序号（001-999）

#### Trial数据结构
```json
{
  "trial_id": "trial_20240115_143022_001",
  "session_id": "session_20240115_143022",
  "trial_number": 1,
  "start_time": "2024-01-15T14:30:22.123456",
  "end_time": "2024-01-15T14:30:28.654321",
  "mode": "Sequence-3",
  "result": "SUCCESS",
  "error_type": null,
  "total_duration_ms": 6531,
  
  "stages": [
    {
      "stage_name": "L1",
      "target_key": "j",
      "led_on_time": "2024-01-15T14:30:22.123456",
      "key_press_time": "2024-01-15T14:30:22.856789",
      "key_release_time": "2024-01-15T14:30:23.456789",
      "stage_duration_ms": 1333,
      "result": "SUCCESS"
    },
    {
      "stage_name": "B1",
      "target_key": "k",
      "led_on_time": "2024-01-15T14:30:23.456789",
      "key_press_time": "2024-01-15T14:30:24.123456",
      "key_release_time": "2024-01-15T14:30:24.723456",
      "stage_duration_ms": 1267,
      "result": "SUCCESS"
    }
    // ... 更多stages
  ],
  
  "events": [
    {
      "timestamp": "2024-01-15T14:30:22.123456",
      "event_type": "LED_ON",
      "stage": "L1",
      "details": {"led": "L1"}
    },
    {
      "timestamp": "2024-01-15T14:30:22.856789",
      "event_type": "KEY_PRESS",
      "stage": "L1",
      "details": {"key": "j", "reaction_time_ms": 733}
    },
    {
      "timestamp": "2024-01-15T14:30:23.456789",
      "event_type": "KEY_RELEASE",
      "stage": "L1",
      "details": {"key": "j", "hold_duration_ms": 600}
    }
    // ... 更多events
  ],
  
  "parameters_snapshot": {
    "wait_window_ms": 2000,
    "release_window_ms": 500,
    "iti_duration_ms": 3000,
    "adaptive_enabled": false,
    "adaptive_target_accuracy": 0.8
  },
  
  "statistics": {
    "reaction_times_ms": [733, 667, 589, 612, 701, 634, 578, 623],
    "hold_durations_ms": [600, 580, 620, 590, 610, 595, 605, 588],
    "stage_durations_ms": [1333, 1247, 1209, 1202, 1311, 1229, 1183, 1211],
    "total_key_presses": 8,
    "error_key_presses": 0
  }
}
```

### 会话级别数据

#### CSV文件结构
```csv
trial_number,timestamp,mode,result,error_type,total_duration_ms,reaction_time_avg_ms,hold_duration_avg_ms,stage_count,parameter_changes
1,2024-01-15T14:30:22.123456,Sequence-3,SUCCESS,,6531,645.5,596.25,8,
2,2024-01-15T14:30:35.789012,Sequence-3,FAILURE,WRONG_KEY,2156,1200,0,1,
3,2024-01-15T14:30:45.345678,Sequence-3,SUCCESS,,7234,678.2,602.1,8,wait_window_ms:2100
```

#### 会话汇总统计
每个会话文件末尾包含汇总统计：
```csv
# SESSION SUMMARY
# Total Trials: 45
# Successful Trials: 36
# Failed Trials: 9
# Success Rate: 80.0%
# Error Breakdown:
#   WRONG_KEY: 3
#   TIMEOUT: 4
#   EARLY_RELEASE: 2
# ITI Errors: 12
# Average Reaction Time: 652.3ms
# Average Hold Duration: 598.7ms
# Session Duration: 15min 32sec
```

### 实时数据更新

#### 数据保存时机
- **Trial完成**：立即保存trial JSON文件
- **会话进行中**：每10个trial更新一次CSV文件
- **参数变更**：立即记录参数快照
- **程序退出**：保存完整会话汇总

#### 数据完整性保证
- **原子写入**：使用临时文件+重命名确保数据完整性
- **备份机制**：重要数据自动创建备份
- **错误恢复**：程序异常退出时自动恢复未保存数据

### 数据分析支持

#### 导出格式
- **JSON**：完整的trial级别数据，支持复杂分析
- **CSV**：会话级别汇总，便于Excel/R/Python分析
- **时间戳**：ISO 8601格式，支持跨时区分析

#### 分析建议
- **反应时间分析**：使用reaction_times_ms数组
- **学习曲线**：分析连续trials的成功率变化
- **参数优化**：对比不同参数设置下的表现
- **错误模式**：分析error_type分布和时间模式

## 版本更新历史

### v1.8.0 - 输入法解决方案 (2024-01-15)

#### 🔧 重要修复
- **输入法自动切换**：解决Windows系统默认中文输入法导致JKL键无响应的问题
- **启动时IME处理**：程序启动时自动切换到英文输入法
- **运行时IME检测**：添加输入法状态检测和自动修复功能
- **跨平台兼容**：仅在Windows平台启用IME处理，其他平台保持原有逻辑

#### 📝 技术实现
- 使用`ctypes`和`wintypes`调用Windows API
- 实现`set_english_ime()`和`disable_ime_for_pygame()`函数
- 在关键处理中添加IME状态检测机制

### v1.7.0 - 参数设置功能增强 (2024-01-10)

#### ✨ 新增功能
- **配置文件管理**：支持参数保存到/加载自`config.json`文件
- **热键配置操作**：
  - F5键：保存当前参数配置
  - F9键：重新加载配置文件
- **操作反馈**：显示保存/加载成功/失败消息
- **参数验证**：加载时自动验证参数有效性

#### 🔧 改进
- 程序退出时自动保存当前参数
- 启动时自动加载已保存的配置
- 无效参数自动回退到默认值

### v1.6.0 - 统计逻辑优化 (2024-01-08)

#### 📊 统计系统重构
- **ITI错误独立统计**：ITI期间的按键错误单独计数
- **Trial计数优化**："总试次"仅反映实际完成的trial
- **正确率计算修正**：ITI错误不影响trial正确率计算
- **错误分类细化**：
  - Trial错误：WRONG_KEY, TIMEOUT, EARLY_RELEASE, TIMEOUT_RELEASE
  - ITI错误：单独计数，不影响主要统计

#### 🎯 显示改进
- 实时统计信息更准确
- 错误类型分类显示
- 历史结果条带仅显示实际trial结果

### v1.5.0 - ITI时间管理优化 (2024-01-05)

#### ⏱️ ITI逻辑改进
- **时间重置防止**：ITI期间按键不再重置倒计时
- **连续倒计时**：ITI时间持续递减，不受按键干扰
- **错误记录保持**：按键错误仍正常记录
- **状态一致性**：确保ITI阶段的时间管理逻辑一致

#### 🔧 技术优化
- 改进ITI状态机逻辑
- 优化时间计算精度
- 增强错误处理机制

### v1.4.0 - UI布局调整 (2024-01-03)

#### 🎨 界面优化
- **元素间距增加**：改善UI元素之间的视觉间距
- **可读性提升**：优化文字显示和布局结构
- **信息层次**：更清晰的信息组织和展示
- **视觉体验**：整体界面更加美观和易读

#### 📱 显示改进
- 参数区域布局优化
- 统计信息显示改进
- 状态指示更加明显

### v1.3.0 - 代码结构优化 (2024-01-01)

#### 🏗️ 架构改进
- **辅助方法添加**：增加多个helper方法提高代码复用性
- **结构问题修正**：修复代码组织和模块化问题
- **可维护性提升**：改善代码可读性和维护性
- **性能优化**：优化关键路径的执行效率

#### 🔧 技术债务清理
- 重构重复代码段
- 改进错误处理逻辑
- 优化内存使用

### v1.2.0 - ITI按键状态检测 (2023-12-28)

#### 🔍 状态检测增强
- **ITI开始前检测**：确保ITI开始时无按键被按下
- **干净状态保证**：只有在无按键状态下才开始新trial
- **错误计数优化**：ITI期间多次按键仅记录一次错误
- **状态一致性**：确保trial开始时的状态一致性

#### 🎯 逻辑改进
- 改进状态转换逻辑
- 优化按键检测机制
- 增强错误分类精度

### v1.1.0 - 释放窗口优化 (2023-12-25)

#### ⚡ 响应速度提升
- **立即处理机制**：按键超过释放窗口时立即处理
- **快速失败**：trial立即失败并进入ITI状态
- **响应性改进**：减少不必要的等待时间
- **用户体验**：更快的错误反馈

#### 🔧 技术实现
- 优化时间窗口检测逻辑
- 改进状态机转换
- 增强实时性处理

### v1.0.0 - 初始版本 (2023-12-20)

#### 🎉 核心功能实现
- **双模式支持**：Shaping-1和Sequence-3训练模式
- **精确时序控制**：基于`perf_counter()`的高精度计时
- **完整状态机**：严格的trial状态管理
- **数据记录系统**：JSON和CSV格式的完整数据记录
- **实时UI显示**：参数、统计、历史结果实时更新
- **热键控制**：完整的键盘快捷键系统
- **参数调整**：实时参数调整和自适应模式
- **错误分类**：详细的错误类型识别和统计
- **ITI管理**：完整的试间间隔处理
- **可扩展架构**：预留硬件接口和MATLAB移植支持

## 常见问题解答

### 安装和运行问题

#### Q: 程序启动时提示"No module named 'pygame'"？
**A:** 需要安装pygame库：
```bash
pip install pygame
```
如果使用conda环境：
```bash
conda install pygame
```

#### Q: Windows系统下JKL键无响应？
**A:** 这通常是中文输入法导致的问题。程序已内置解决方案：
- 程序启动时会自动切换到英文输入法
- 运行时会自动检测和修复输入法状态
- 如果问题持续，请手动切换到英文输入法（Shift键）

#### Q: 程序运行缓慢或卡顿？
**A:** 检查以下几点：
- 确保Python版本为3.8或更高
- 关闭其他占用CPU的程序
- 降低UI更新频率（修改config.json中的ui_update_interval_ms）
- 检查磁盘空间是否充足

### 配置和参数问题

#### Q: 如何重置所有参数到默认值？
**A:** 有两种方法：
1. 删除`config.json`文件，程序会使用默认参数
2. 手动编辑`config.json`文件，设置所需的默认值

#### Q: 自适应模式如何工作？
**A:** 自适应模式会：
- 监控最近20个trial的正确率
- 如果正确率高于目标值，增加难度（减少时间窗口）
- 如果正确率低于目标值，降低难度（增加时间窗口）
- 调整幅度由adaptive_adjustment_factor控制

#### Q: 参数调整的范围限制是什么？
**A:** 参数范围如下：
- 等待窗口：500ms - 10000ms
- 释放窗口：100ms - 2000ms
- ITI时间：1000ms - 10000ms
- 目标正确率：50% - 95%

### 数据和分析问题

#### Q: 数据文件保存在哪里？
**A:** 数据保存在程序目录下的`data`文件夹：
- `data/trials/`：单个trial的详细JSON数据
- `data/sessions/`：会话汇总CSV数据
- `data/config_history/`：参数变更历史

#### Q: 如何分析实验数据？
**A:** 推荐分析方法：
- **Excel分析**：直接打开CSV文件进行基础统计
- **Python分析**：使用pandas读取JSON/CSV数据
- **R分析**：使用jsonlite和readr包处理数据
- **MATLAB分析**：使用jsondecode和readtable函数

#### Q: 数据文件损坏怎么办？
**A:** 程序有多重保护机制：
- 使用原子写入防止文件损坏
- 自动创建重要数据的备份
- 如果发现损坏，检查同目录下的.backup文件

### 实验设计问题

#### Q: 如何设计合适的训练方案？
**A:** 建议的训练流程：
1. **入门阶段**：使用Shaping-1模式，较长的时间窗口
2. **适应阶段**：逐步减少时间窗口，提高难度
3. **正式训练**：切换到Sequence-3模式
4. **自适应训练**：启用自适应模式维持稳定表现

#### Q: ITI时间如何设置？
**A:** ITI时间设置考虑：
- **短ITI（1-2秒）**：适合熟练受试者，提高训练效率
- **中等ITI（3-5秒）**：平衡训练效率和受试者舒适度
- **长ITI（5-10秒）**：适合初学者或需要充分休息的情况

#### Q: 如何判断训练效果？
**A:** 关键指标：
- **正确率**：目标通常为80%以上
- **反应时间**：应逐渐缩短并趋于稳定
- **错误类型分布**：随机错误减少，系统性错误消失
- **学习曲线**：正确率呈上升趋势

### 技术和扩展问题

#### Q: 如何连接硬件设备？
**A:** 程序预留了硬件接口：
1. 修改`IOBackend`类实现硬件通信
2. 实现DAQ设备的读写方法
3. 替换键盘输入为硬件信号检测
4. 参考代码中的抽象接口设计

#### Q: 如何移植到MATLAB平台？
**A:** 移植建议：
1. **状态机逻辑**：使用MATLAB的switch-case结构
2. **时序控制**：使用tic/toc或timer对象
3. **数据记录**：使用struct和table数据结构
4. **UI界面**：使用App Designer或GUIDE
5. **配置管理**：使用JSON或MAT文件

#### Q: 程序支持多受试者同时训练吗？
**A:** 当前版本为单受试者设计。多受试者支持需要：
- 修改数据存储结构添加受试者ID
- 实现受试者切换界面
- 独立的参数配置管理
- 多线程或多进程架构

### 故障排除

#### Q: 程序意外退出怎么办？
**A:** 检查步骤：
1. 查看控制台错误信息
2. 检查data目录权限
3. 确认磁盘空间充足
4. 重启程序，数据会自动恢复

#### Q: 时间测量不准确？
**A:** 可能原因和解决方案：
- **系统负载高**：关闭其他程序
- **Python版本过低**：升级到Python 3.8+
- **时钟精度问题**：检查系统时钟设置
- **Pygame版本问题**：升级到pygame 2.0+

#### Q: 如何获得技术支持？
**A:** 技术支持渠道：
1. 查看本README文档
2. 检查代码注释和文档字符串
3. 提交Issue描述具体问题
4. 提供错误日志和系统信息

## 技术架构

### 核心架构设计

#### 状态机模式
程序采用有限状态机（FSM）架构，确保实验流程的严格控制：

```
状态转换图：
IDLE → WAITING → HOLDING → RELEASE_WINDOW → ITI → IDLE
     ↓         ↓        ↓              ↓
   错误处理   错误处理   错误处理      错误处理
```

**状态定义：**
- `IDLE`：程序空闲，等待开始
- `WAITING`：等待按键按下
- `HOLDING`：按键保持阶段
- `RELEASE_WINDOW`：释放窗口检测
- `ITI`：试间间隔

#### 模块化设计

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Module     │    │  Logic Module   │    │  Data Module    │
│                 │    │                 │    │                 │
│ • 参数显示      │◄──►│ • 状态机        │◄──►│ • JSON记录      │
│ • 统计信息      │    │ • 时序控制      │    │ • CSV汇总       │
│ • 历史结果      │    │ • 错误检测      │    │ • 配置管理      │
│ • 热键处理      │    │ • 自适应调整    │    │ • 备份机制      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  IO Backend     │
                    │                 │
                    │ • 键盘输入      │
                    │ • 硬件接口      │
                    │ • 时间测量      │
                    │ • 平台适配      │
                    └─────────────────┘
```

### 关键技术实现

#### 高精度时序控制
```python
# 使用perf_counter()确保微秒级精度
import time

class TimingController:
    def __init__(self):
        self.start_time = time.perf_counter()
    
    def get_elapsed_ms(self):
        return (time.perf_counter() - self.start_time) * 1000
```

#### 释放判断逻辑
```python
def check_release_timing(self, press_time, release_time, target_window):
    """
    精确的释放时间判断逻辑
    """
    hold_duration = release_time - press_time
    
    if hold_duration < target_window[0]:  # 过早释放
        return "EARLY_RELEASE"
    elif hold_duration > target_window[1]:  # 超时释放
        return "TIMEOUT_RELEASE"
    else:
        return "SUCCESS"
```

#### 自适应难度调整
```python
class AdaptiveController:
    def __init__(self, target_accuracy=0.8, window_size=20):
        self.target_accuracy = target_accuracy
        self.recent_results = deque(maxlen=window_size)
    
    def adjust_difficulty(self, current_params):
        if len(self.recent_results) < self.window_size:
            return current_params
        
        accuracy = sum(self.recent_results) / len(self.recent_results)
        
        if accuracy > self.target_accuracy:
            # 增加难度：缩短时间窗口
            current_params['release_window_ms'] *= 0.95
        elif accuracy < self.target_accuracy:
            # 降低难度：延长时间窗口
            current_params['release_window_ms'] *= 1.05
        
        return current_params
```

### 数据流架构

#### 实时数据流
```
用户输入 → 事件检测 → 状态更新 → UI刷新
    ↓           ↓          ↓         ↓
时间戳记录 → 逻辑判断 → 统计更新 → 数据保存
```

#### 数据存储策略
- **实时记录**：每个trial立即写入JSON文件
- **会话汇总**：定期更新CSV统计文件
- **配置备份**：参数变更时自动备份
- **原子操作**：使用临时文件确保数据完整性

### 扩展接口设计

#### 硬件抽象层
```python
class IOBackend:
    """硬件输入输出抽象基类"""
    
    def read_inputs(self):
        """读取输入信号"""
        raise NotImplementedError
    
    def write_outputs(self, signals):
        """输出控制信号"""
        raise NotImplementedError
    
    def get_timestamp(self):
        """获取高精度时间戳"""
        return time.perf_counter()

class KeyboardBackend(IOBackend):
    """键盘输入实现"""
    pass

class DAQBackend(IOBackend):
    """数据采集卡实现（预留）"""
    pass
```

#### MATLAB移植接口
```matlab
% MATLAB状态机实现示例
classdef TaskStateMachine < handle
    properties
        current_state
        timing_controller
        data_recorder
    end
    
    methods
        function obj = TaskStateMachine()
            obj.current_state = 'IDLE';
            obj.timing_controller = TimingController();
            obj.data_recorder = DataRecorder();
        end
        
        function update(obj, input_event)
            switch obj.current_state
                case 'IDLE'
                    % 处理空闲状态逻辑
                case 'WAITING'
                    % 处理等待状态逻辑
                % ... 其他状态
            end
        end
    end
end
```

### 性能优化策略

#### 内存管理
- 使用循环缓冲区存储历史数据
- 定期清理过期的临时文件
- 延迟加载大型数据结构

#### CPU优化
- 事件驱动架构减少轮询开销
- 关键路径代码优化
- 合理的UI更新频率控制

#### I/O优化
- 异步文件写入
- 批量数据操作
- 智能缓存策略

### 错误处理机制

#### 多层错误处理
1. **输入验证**：参数范围检查
2. **运行时检查**：状态一致性验证
3. **异常捕获**：文件I/O和系统调用保护
4. **优雅降级**：关键功能失败时的备用方案

#### 日志系统
```python
import logging

# 配置多级日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('task_train.log'),
        logging.StreamHandler()
    ]
)
```

## 未来扩展

### 硬件集成计划

#### 数据采集系统
- **DAQ设备支持**：集成National Instruments、Measurement Computing等DAQ卡
- **实时信号处理**：支持模拟/数字信号的高速采集和处理
- **同步触发**：与外部设备的精确时序同步
- **多通道支持**：同时监控多个输入输出通道

#### 神经接口扩展
- **脑机接口**：支持EEG、fNIRS等神经信号采集
- **实时反馈**：基于神经信号的实时任务调整
- **信号预处理**：内置滤波、去噪、特征提取功能
- **在线分析**：实时神经信号分析和分类

### MATLAB平台移植

#### 核心功能移植
- **状态机重构**：使用MATLAB面向对象编程实现状态机
- **GUI开发**：基于App Designer的现代化界面
- **数据处理**：利用MATLAB强大的数据分析能力
- **工具箱集成**：与Signal Processing、Statistics工具箱深度集成

#### 移植优势
- **科学计算**：更强大的数学计算和统计分析功能
- **可视化**：丰富的数据可视化和图表生成
- **算法库**：访问MATLAB丰富的算法库和工具箱
- **部署选项**：支持独立应用程序打包和分发

### 功能增强计划

#### 多模态任务支持
- **视觉任务**：添加视觉刺激和眼动追踪支持
- **听觉任务**：集成音频刺激和反应时间测量
- **触觉反馈**：支持振动、力反馈等触觉刺激
- **多感官整合**：跨模态的复合任务设计

#### 高级分析功能
- **机器学习**：集成学习曲线预测和个性化训练
- **统计建模**：高级统计分析和假设检验
- **数据挖掘**：模式识别和异常检测
- **预测分析**：基于历史数据的表现预测

#### 云端集成
- **数据同步**：多设备间的数据同步和备份
- **远程监控**：实时监控训练进度和表现
- **协作分析**：多用户协作的数据分析平台
- **版本控制**：实验设计和数据的版本管理

### 研究应用扩展

#### 临床应用
- **康复训练**：针对运动功能康复的定制化训练
- **认知评估**：标准化的认知功能评估工具
- **治疗监控**：治疗效果的量化评估和追踪
- **个性化方案**：基于个体差异的训练方案定制

#### 教育应用
- **技能训练**：精细运动技能的系统化训练
- **学习评估**：学习效果的客观量化评估
- **适应性学习**：基于表现的自适应学习系统
- **游戏化设计**：增加训练的趣味性和参与度

#### 科研工具
- **实验设计**：灵活的实验范式设计工具
- **数据标准化**：符合科研标准的数据格式和元数据
- **统计分析**：内置常用的统计分析方法
- **结果可视化**：科研级别的图表和报告生成

### 技术发展路线

#### 短期目标（3-6个月）
1. **硬件接口开发**：完成基础DAQ设备支持
2. **MATLAB原型**：实现核心功能的MATLAB版本
3. **数据分析增强**：添加高级统计分析功能
4. **用户界面优化**：改进用户体验和界面设计

#### 中期目标（6-12个月）
1. **多模态支持**：集成视觉、听觉任务模块
2. **云端平台**：开发基础的云端数据管理
3. **机器学习集成**：添加智能分析和预测功能
4. **移动端支持**：开发移动设备版本

#### 长期目标（1-2年）
1. **神经接口**：完整的脑机接口支持
2. **AI驱动训练**：基于AI的个性化训练系统
3. **虚拟现实**：VR/AR环境下的沉浸式训练
4. **标准化平台**：成为行业标准的训练评估平台

### 开源社区建设

#### 贡献指南
- **代码规范**：建立清晰的代码贡献标准
- **文档完善**：持续改进技术文档和用户手册
- **测试框架**：建立完整的自动化测试体系
- **社区支持**：活跃的开发者社区和用户支持

#### 生态系统
- **插件架构**：支持第三方插件和扩展
- **API开放**：提供完整的编程接口
- **数据标准**：建立行业数据交换标准
- **工具集成**：与其他科研工具的无缝集成

## 许可证

本项目采用 MIT 许可证开源。详细信息请参阅 [LICENSE](LICENSE) 文件。

### MIT License

```
MIT License

Copyright (c) 2024 TaskTrain Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 贡献指南

我们欢迎社区贡献！请遵循以下指南：

### 如何贡献

1. **Fork 项目**：在GitHub上fork本项目
2. **创建分支**：为你的功能创建一个新分支
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **提交更改**：确保代码符合项目规范
   ```bash
   git commit -m "Add: your feature description"
   ```
4. **推送分支**：将更改推送到你的fork
   ```bash
   git push origin feature/your-feature-name
   ```
5. **创建Pull Request**：在GitHub上创建PR

### 代码规范

- **Python代码**：遵循PEP 8规范
- **注释要求**：关键函数必须有docstring
- **测试覆盖**：新功能需要包含相应测试
- **文档更新**：功能变更需要更新相关文档

### 报告问题

如果发现bug或有功能建议，请：

1. 检查是否已有相关issue
2. 创建新issue，包含：
   - 详细的问题描述
   - 复现步骤
   - 系统环境信息
   - 相关日志或截图

## 致谢

感谢以下项目和社区的支持：

- **Pygame**：提供了优秀的游戏开发框架
- **Python社区**：丰富的生态系统和工具支持
- **开源社区**：持续的反馈和贡献
- **科研社区**：宝贵的需求反馈和测试支持

## 联系方式

- **项目主页**：[GitHub Repository](https://github.com/superxsy/tasktrain)
- **问题反馈**：[GitHub Issues](https://github.com/superxsy/tasktrain/issues)
- **邮件联系**：vetxsy@163.com
- **技术讨论**：[Discussions](https://github.com/superxsy/tasktrain/discussions)

## 引用

如果本项目对您的研究有帮助，请考虑引用：

```bibtex
@software{tasktrain2024,
  title={TaskTrain: A High-Precision Behavioral Training System},
  author={TaskTrain Development Team},
  year={2024},
  url={https://github.com/your-username/tasktrain},
  version={1.8.0}
}
```

---

**TaskTrain** - 专业的行为训练实验平台

*构建精确、可靠、可扩展的行为实验解决方案*
