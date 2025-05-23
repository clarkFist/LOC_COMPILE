# LOC_COMPILE

本项目提供一个用于辅助编译 VCU (MVCU 与 SVCU) 项目的工具集，支持图形界面与命令行两种模式。核心功能包括自动更新 makefile 中的编译器路径、生成 MSYS profile 配置以及一键启动编译流程。

## 目录
- [功能特点](#功能特点)
- [环境要求](#环境要求)
- [使用说明](#使用说明)
- [目录结构](#目录结构)
- [贡献与开发](#贡献与开发)
- [快速开始](#快速开始)
- [常见问题](#常见问题)

---

## 功能特点

- **目录结构自动校验**：启动时确保项目根目录及其子目录存在。
- **makefile 路径更新**：根据实际路径自动替换编译器 (CW/GCC) 配置。
- **MSYS profile 生成**：根据所选模式自动配置 `MSYS_FLAG` 以及相关脚本执行。
- **图形化界面**：提供基于 `tkinter` 的操作界面，可查看实时日志并进行源路径选择。
- **命令行模式**：支持在终端直接指定源码路径并触发编译。

---

## 环境要求

> ⚠ **注意**：当前工具仅在 Windows 环境下经过验证。

- Python 3.6 及以上版本
- Windows 环境（需提前安装 CW 与 GCC 编译链，以及 MSYS 环境）
- 运行 GUI 模式需确保 `tkinter` 模块可用

---

## 使用说明

1. **安装依赖**
   ```bash
   pip install -r requirements.txt  # 如有依赖项
   ```

2. **启动图形界面**
   ```bash
   python main.py --gui
   ```

3. **命令行编译**
   ```bash
   python main.py --console <源文件或目录路径>
   ```

4. **仅更新编译器路径**
   ```bash
   python main.py --update-paths
   ```

---

## 目录结构

运行前程序会在当前目录下创建如下结构（如不存在将自动生成）：

```
VCU_compile - selftest/
├── dev_kernel_mvcu/
│   ├── src/
│   └── build/
│       └── out/
└── dev_kernel_svcu/
    ├── src/
    └── build/
        └── out/
```

---

## 贡献与开发

欢迎提交 Issue 或 Pull Request 以改进此工具。开发者可直接运行 `main.py` 以调试功能，或查看 `vcu_compiler_ui.py` 获取界面实现细节。

---

## 快速开始

在命令行中直接运行 `python main.py` 会自动检测是否拖入文件或目录：
- 如果提供了路径，程序将以命令行模式运行并启动自动编译。
- 否则默认启动图形界面，可在界面中选择源路径并执行编译。

---

## 常见问题

1. **无法找到 MSYS 或编译器**
   - 请确保 `CW/ColdFire_Tools/Command_Line_Tools` 和 `GCC/bin` 位于项目根目录同级或相应位置。
   - 确认环境变量设置正确，或使用 `--update-paths` 自动更新。

2. **GUI 无法显示**
   - 请确认 Python 已安装 `tkinter` 模块。部分精简版 Python 可能不包含该模块，可重新安装完整版本。

