# 小鼠序列训练任务 - MATLAB版

这是原Python版本小鼠序列训练任务的MATLAB移植版本，提供了完整的硬件控制、数据记录和用户界面功能。

## 项目概述

本项目实现了一个用于小鼠行为训练的序列按压任务系统，支持两种主要模式：
- **Sequence-3模式**: 小鼠需要按顺序按压L1→L2→L3三个按钮
- **Shaping-1模式**: 小鼠只需按压指定LED对应的按钮

## 主要特性

### 🎯 核心功能
- **状态机管理**: 完整的任务状态控制（ITI、等待、奖励等）
- **硬件抽象**: 支持Arduino Due和模拟键盘两种输入模式
- **数据记录**: 自动记录试次数据到JSON和CSV格式
- **自适应调整**: 根据表现自动调整任务难度
- **实时监控**: 图形化界面显示任务状态和统计信息

### 🔧 技术特性
- **模块化设计**: 使用MATLAB包结构组织代码
- **配置管理**: JSON格式的配置文件
- **错误处理**: 完善的错误检测和处理机制
- **扩展性**: 易于添加新的硬件后端和任务模式

## 系统要求

### 软件要求
- **MATLAB**: R2018a或更高版本
- **推荐工具箱**:
  - Instrument Control Toolbox（Arduino支持）
  - MATLAB Support Package for Arduino Hardware

### 硬件要求
- **Arduino Due**（可选）
- **LED指示灯** x3
- **按钮开关** x3
- **电磁阀**（奖励给予）
- **连接线缆**

## 快速开始

### 1. 安装和配置

```matlab
% 1. 克隆或下载项目到本地
% 2. 在MATLAB中导航到项目目录
cd('path/to/tasktrain')

% 3. 运行启动脚本
run_task()
```

### 2. 基本使用

1. **选择硬件模式**:
   - 模拟键盘：用于测试和演示
   - Arduino Due：用于实际实验

2. **配置参数**:
   - 点击"配置"按钮修改实验参数
   - 或直接编辑`config.json`文件

3. **开始实验**:
   - 点击"开始"按钮启动会话
   - 使用"暂停"和"重置"控制实验进程

### 3. 模拟模式操作

在模拟键盘模式下，使用以下按键：
- **J键**: 模拟按钮1
- **K键**: 模拟按钮2
- **L键**: 模拟按钮3
- **空格键**: 暂停/继续
- **R键**: 重置会话
- **M键**: 切换模式

## 项目结构

```
tasktrain/
├── +core/                  # 核心功能包
│   ├── TaskState.m         # 任务状态枚举
│   ├── Config.m            # 配置管理类
│   ├── TrialLogger.m       # 数据记录类
│   └── TaskStateMachine.m  # 状态机类
├── +io/                    # 输入输出包
│   ├── IOBackend.m         # IO抽象基类
│   ├── ArduinoBackend.m    # Arduino硬件后端
│   └── SimKeyboardBackend.m # 模拟键盘后端
├── MouseSequenceTaskApp.m  # 主应用程序
├── run_task.m              # 启动脚本
├── config.json             # 配置文件
├── data/                   # 数据目录（自动创建）
└── README_MATLAB.md        # 说明文档
```

## 配置说明

### 主要配置参数

```json
{
  "subject_id": "M001",           // 被试ID
  "mode": "sequence3",            // 任务模式
  "max_trials": 500,             // 最大试次数
  "iti_min": 3.0,                // ITI最小时间
  "iti_max": 7.0,                // ITI最大时间
  "wait_L1": 5.0,                // L1等待时间
  "wait_L2": 5.0,                // L2等待时间
  "wait_L3": 5.0,                // L3等待时间
  "release_window": 0.5,         // 松开窗口时间
  "reward_duration": 0.1,        // 奖励持续时间
  "adaptive_enabled": true       // 是否启用自适应
}
```

### 硬件引脚配置

```json
{
  "pins": {
    "led1": 2,      // LED1引脚
    "led2": 3,      // LED2引脚
    "led3": 4,      // LED3引脚
    "button1": 5,   // 按钮1引脚
    "button2": 6,   // 按钮2引脚
    "button3": 7,   // 按钮3引脚
    "valve": 8      // 电磁阀引脚
  }
}
```

## 数据格式

### 试次数据（JSON格式）

```json
{
  "trial_index": 1,
  "timestamp": "2024-01-01T12:00:00",
  "state_sequence": ["ITI", "L1_WAIT", "L2_WAIT", "L3_WAIT", "REWARD"],
  "button_events": [
    {
      "timestamp": 1234567890.123,
      "button": 1,
      "action": "press"
    }
  ],
  "result_code": 0,
  "config_snapshot": {...}
}
```

### 会话汇总（CSV格式）

| trial_index | timestamp | result_code | reaction_time | sequence_time | errors |
|-------------|-----------|-------------|---------------|---------------|---------|
| 1 | 2024-01-01T12:00:00 | 0 | 0.523 | 1.234 | 0 |

## 错误代码

- **0**: 正确完成
- **1**: 未按压（超时）
- **2**: 按错按钮
- **3**: 按住时间过长
- **4**: 过早按压（ITI期间）

## 开发指南

### 添加新的硬件后端

1. 继承`io.IOBackend`抽象类
2. 实现所有抽象方法
3. 在主应用程序中添加选项

```matlab
classdef MyBackend < io.IOBackend
    methods
        function obj = MyBackend(config)
            obj@io.IOBackend(config);
            % 初始化代码
        end
        
        function success = initialize(obj)
            % 实现初始化逻辑
        end
        
        % 实现其他抽象方法...
    end
end
```

### 添加新的任务模式

1. 在`core.TaskState`中添加新状态
2. 在`core.TaskStateMachine`中添加状态转换逻辑
3. 更新配置文件和UI

## 故障排除

### 常见问题

1. **Arduino连接失败**
   - 检查USB连接
   - 确认Arduino驱动已安装
   - 检查端口权限

2. **配置文件错误**
   - 验证JSON格式
   - 检查参数范围
   - 使用默认配置测试

3. **数据记录失败**
   - 检查磁盘空间
   - 确认写入权限
   - 检查文件路径

### 调试模式

```matlab
% 启用详细日志
config.debug_mode = true;

% 查看状态机状态
stateMachine.getCurrentState()

% 检查IO后端连接
ioBackend.isConnected()
```

## 性能优化

- **定时器频率**: 默认100Hz，可根据需要调整
- **数据缓存**: 批量写入减少IO开销
- **内存管理**: 及时清理大型数据结构

## 版本历史

### v1.0.0 (2024-01-01)
- 初始MATLAB移植版本
- 完整的状态机实现
- Arduino和模拟键盘支持
- 图形化用户界面
- 数据记录和分析功能

## 许可证

本项目基于原Python版本移植，遵循相同的许可证条款。

## 联系方式

如有问题或建议，请联系开发团队。

---

**注意**: 这是从Python版本移植的MATLAB实现，保持了原有的核心功能和数据格式兼容性。