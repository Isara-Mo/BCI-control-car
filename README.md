# BCI-control-car

# 脑机接口 SSVEP 控制无人机/小车系统

## 项目简介

本项目实现了基于 SSVEP（稳态视觉诱发电位）的脑机接口系统，用于通过脑电信号控制无人机或小车。系统集成了脑电信号采集、信号处理、特征提取与分类（FBCCA 算法）、以及对下位机（如无人机/小车）的指令控制。

## 主要功能

- 实时采集 EEG 脑电信号（通过 LSL 协议）
- SSVEP 信号处理与特征提取（FBCCA 算法）
- 支持多种指令（如前进、后退、左转、右转、亮灯、鸣笛等）
- 通过串口或 WiFi 控制无人机/小车
- 实验界面基于 PsychoPy，支持全屏刺激呈现
- 数据自动保存为 CSV 文件

## 目录结构

- `ssvep_car.py`：主程序，包含界面、流程与控制逻辑
- `model.py`：SSVEP 信号处理与分类算法
- `lsl_received_data.py`：脑电数据采集（LSL）
- `eeg_data/`：实验采集到的脑电数据（CSV 格式）
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

安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 运行主程序


```bash
python ssvep_car.py
```

### 2. 数据采集与实验流程

- 启动程序后，填写被试信息和小车端口号（如 COM3）
- 按提示进行脑控实验，数据将自动保存到 `eeg_data/` 目录下

### 3. 数据说明

- 实验采集的数据以 CSV 格式保存在 `eeg_data/` 目录
- 每行为一次采样的多通道 EEG 数据

## 算法说明

- 本项目采用 FBCCA（Filter Bank Canonical Correlation Analysis）算法进行 SSVEP 信号的特征提取与分类，详见 `model.py`。


## 致谢

- 本项目部分代码参考了开源社区相关实现，感谢各位作者的贡献。

---

