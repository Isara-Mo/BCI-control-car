<div id="language-switch" style="text-align: right; margin-bottom: 20px;">
  <button id="en-btn" style="padding: 8px 15px; margin-right: 5px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">English</button>
  <button id="zh-btn" style="padding: 8px 15px; background-color: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">中文</button>
</div>

<!-- English Version -->
<div id="en-content">

# BCI-control-car

## Brain-Computer Interface (BCI) SSVEP Control System for Drones/Cars

### Project Overview

This project implements a brain-computer interface system based on SSVEP (Steady-State Visual Evoked Potential) for controlling drones or cars through EEG brain signals. The system integrates EEG signal acquisition, signal processing, feature extraction and classification (FBCCA algorithm), and command control for lower-level devices (such as drones/cars).

### Key Features

- Real-time EEG signal acquisition (via LSL protocol)
- SSVEP signal processing and feature extraction (FBCCA algorithm)
- Support for multiple commands (forward, backward, left turn, right turn, lights, horn, etc.)
- **New: Auto-cruise functionality** - Trigger preset action sequences via BCI
- Control drones/cars via serial port or WiFi
- Experimental interface based on PsychoPy with full-screen stimulus presentation
- Automatic data saving in CSV format

### Directory Structure

- `ssvep_car.py`: Main program containing interface, workflow, and control logic
- `model.py`: SSVEP signal processing and classification algorithm
- `lsl_received_data.py`: EEG data acquisition (LSL)
- `eeg_data/`: Collected EEG data from experiments (CSV format)
- `simple_car_test.py`: **New** - Simplified car testing program
- `dist/ssvep_car.exe`: Packaged executable file (Windows)
- `requirements.txt`: Python dependencies list

### Environment Requirements

- Python 3.7+
- Main dependencies (see requirements.txt):
  - psychopy
  - mne
  - pandas
  - numpy
  - scikit-learn
  - pylsl
  - djitellopy
  - pyserial (for serial communication)
  - **New**: tkinter (for test program interface)

### Usage

#### 1. Run Main Program

```bash
python ssvep_car.py
```

#### 2. Data Collection and Experiment Workflow

- After starting the program, enter subject information and car COM port (e.g., COM3)
- Follow the prompts to conduct the BCI experiment; data will be automatically saved to `eeg_data/` directory

#### 3. Auto-Cruise Functionality

**Feature Description:**
- When the BCI recognizes a "backward" command, the system enters auto-cruise mode
- Auto-cruise executes a preset sequence of actions in order
- The system automatically returns to normal BCI control after sequence completion

**Configure Auto-Cruise Sequence:**
Modify the `auto_cruise_sequence` array in `ssvep_car.py`:
```python
auto_cruise_sequence = [2, 3, 4, 2, 3, 4, 2, 3, 4, 2, 3, 4]
```
Number meanings: 2=forward, 3=left turn, 4=right turn, 5=lights, 6=horn

#### 4. Car Testing Programs

**Simplified Testing Program:**
```bash
python simple_car_test.py
```

**Features:**
- Serial port connection management
- Individual action testing
- Action sequence recording
- One-click sequence execution
- Copy sequence to clipboard

**Testing Workflow:**
1. Run the testing program
2. Set serial port (default COM3)
3. Connect to the car
4. Start recording
5. Click buttons to test actions in sequence
6. Stop recording
7. Copy sequence or save to file
8. Apply sequence to main program's `auto_cruise_sequence`

#### 5. Data Information

- Experimental collected data is saved in CSV format in `eeg_data/` directory
- Each row contains multi-channel EEG data from one sampling

### Algorithm Explanation

- This project uses FBCCA (Filter Bank Canonical Correlation Analysis) algorithm for SSVEP signal feature extraction and classification. See `model.py` for details.

### Control Command Reference

| Command | Code | Description |
|---------|------|-------------|
| Lights | 5 | Control car lights |
| Forward | 2 | Car moves forward (send command twice with 0.3s interval) |
| Left Turn | 3 | Car turns left |
| Right Turn | 4 | Car turns right |
| Backward | 1 | Trigger auto-cruise mode |
| Horn | 6 | Car horn |

### Changelog

#### v2.0 (Latest)
- Added auto-cruise functionality
- Added car testing program
- Optimized control logic
- Fixed variable definition order issue

#### v1.0
- Basic SSVEP BCI functionality
- Support for multiple control commands
- Data acquisition and saving

### Acknowledgments

- This project references some implementations from the open-source community. Thanks to all contributors.

---

</div>

<!-- Chinese Version -->
<div id="zh-content" style="display: none;">

# BCI-control-car

# 脑机接口 SSVEP 控制无人机/小车系统

## 项目简介

本项目实现了基于 SSVEP（稳态视觉诱发电位）的脑机接口系统，用于通过脑电信号控制无人机或小车。系统集成了脑电信号采集、信号处理、特征提取与分类（FBCCA 算法）、以及对下位机（如无人机/小车）的指令控制。

## 主要功能

- 实时采集 EEG 脑电信号（通过 LSL 协议）
- SSVEP 信号处理与特征提取（FBCCA 算法）
- 支持多种指令（如前进、后退、左转、右转、亮灯、鸣笛等）
- **新增：自动巡航功能** - 通过脑机接口触发预设动作序列
- 通过串口或 WiFi 控制无人机/小车
- 实验界面基于 PsychoPy，支持全屏刺激呈现
- 数据自动保存为 CSV 文件

## 目录结构

- `ssvep_car.py`：主程序，包含界面、流程与控制逻辑
- `model.py`：SSVEP 信号处理与分类算法
- `lsl_received_data.py`：脑电数据采集（LSL）
- `eeg_data/`：实验采集到的脑电数据（CSV 格式）
- `simple_car_test.py`：**新增** - 简化版小车测试程序
- `dist/ssvep_car.exe`：已打包的可执行文件（Windows）
- `requirements.txt`：Python 依赖库列表

## 环境依赖

- Python 3.7+
- 主要依赖库（详见 requirements.txt）：
  - psychopy
  - mne
  - pandas
  - numpy
  - scikit-learn
  - pylsl
  - djitellopy
  - pyserial（用于串口通信）
  - **新增**：tkinter（用于测试程序界面）

## 使用方法

### 1. 运行主程序

```bash
python ssvep_car.py
```

### 2. 数据采集与实验流程

- 启动程序后，填写被试信息和小车端口号（如 COM3）
- 按提示进行脑控实验，数据将自动保存到 `eeg_data/` 目录下

### 3. 自动巡航功能

**功能说明：**
- 当脑机接口识别到"后退"指令时，系统会启动自动巡航模式
- 自动巡航会依次执行预设的动作序列
- 序列执行完毕后自动恢复正常脑机控制

**配置自动巡航序列：**
在 `ssvep_car.py` 中修改 `auto_cruise_sequence` 数组：
```python
auto_cruise_sequence = [2, 3, 4, 2, 3, 4, 2, 3, 4, 2, 3, 4]
```
数字含义：2=前进，3=左转，4=右转，5=亮灯，6=鸣笛

### 4. 小车测试程序

**简化版测试程序：**
```bash
python simple_car_test.py
```

**功能：**
- 串口连接管理
- 单个动作测试
- 动作序列记录
- 一键执行序列
- 复制序列到剪贴板

**测试流程：**
1. 运行测试程序
2. 设置串口（默认COM3）
3. 连接小车
4. 开始记录
5. 依次点击按钮测试动作
6. 停止记录
7. 复制序列或保存到文件
8. 将序列应用到主程序的 `auto_cruise_sequence`

### 5. 数据说明

- 实验采集的数据以 CSV 格式保存在 `eeg_data/` 目录
- 每行为一次采样的多通道 EEG 数据

## 算法说明

- 本项目采用 FBCCA（Filter Bank Canonical Correlation Analysis）算法进行 SSVEP 信号的特征提取与分类，详见 `model.py`。

## 控制指令说明

| 指令 | 代码 | 说明 |
|------|------|------|
| 亮灯 | 5 | 控制小车灯光 |
| 前进 | 2 | 小车前进（发送两次命令，间隔0.3秒） |
| 左转 | 3 | 小车左转 |
| 右转 | 4 | 小车右转 |
| 后退 | 1 | 触发自动巡航模式 |
| 鸣笛 | 6 | 小车鸣笛 |

## 更新日志

### v2.0 (最新)
- 新增自动巡航功能
- 新增小车测试程序
- 优化控制逻辑
- 修复变量定义顺序问题

### v1.0
- 基础SSVEP脑机接口功能
- 支持多种控制指令
- 数据采集与保存

## 致谢

- 本项目部分代码参考了开源社区相关实现，感谢各位作者的贡献。

---

</div>

<script>
document.getElementById('en-btn').addEventListener('click', function() {
  document.getElementById('en-content').style.display = 'block';
  document.getElementById('zh-content').style.display = 'none';
  document.getElementById('en-btn').style.backgroundColor = '#007bff';
  document.getElementById('zh-btn').style.backgroundColor = '#6c757d';
});

document.getElementById('zh-btn').addEventListener('click', function() {
  document.getElementById('en-content').style.display = 'none';
  document.getElementById('zh-content').style.display = 'block';
  document.getElementById('en-btn').style.backgroundColor = '#6c757d';
  document.getElementById('zh-btn').style.backgroundColor = '#007bff';
});
</script>

