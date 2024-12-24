# multi_install

## 简介

`multi_install`是一个使用PyQt5构建图形用户界面（GUI）的Python应用程序，它可以帮助您快速在多个设备上同时安装APK文件。

## 快速开始

### 环境要求

- python3.9
- Pyqt5
- adb

### 安装步骤

1. 克隆仓库到本地

   ```
   git clone https://github.com/Qiuyang-Pan/multi_install.git
   ```
2. 进入项目目录

   ```
   cd multi_install
   ```
3. 创建虚拟环境并激活（推荐）

   ``` 
   python -m venv .venv
   source .venv/bin/activate  # Unix 或 macOS
   .venv\Scripts\activate     # Windows
   ```
4. 安装依赖

   ```
   pip install -r requirements.txt
   ```
5. 运行main.py

   ```
   python main.py
   ```
### 使用方法

1. 本地安装 [adb](https://developer.android.com/tools/releases/platform-tools?hl=zh-cn) 工具
2. 连接手机，选择apk
3. 选择设备安装或全部安装
