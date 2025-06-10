#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LOC_COMPILE 项目环境设置脚本
自动检测并安装运行环境依赖
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_info(message):
    """打印信息"""
    print(f"[信息] {message}")


def print_error(message):
    """打印错误"""
    print(f"[错误] {message}")


def print_success(message):
    """打印成功"""
    print(f"[成功] {message}")


def check_python_version():
    """检查Python版本"""
    print_info("检查Python版本...")
    version = sys.version_info
    if version.major < 3:
        print_error(f"Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print_error("本项目需要Python 3.6或更高版本")
        return False
    elif version.major == 3 and version.minor < 6:
        print_error(f"Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print_error("本项目需要Python 3.6或更高版本")
        return False
    else:
        print_success(f"Python版本: {version.major}.{version.minor}.{version.micro} ✓")
        return True


def check_tkinter():
    """检查tkinter可用性"""
    print_info("检查tkinter GUI库...")
    try:
        import tkinter
        import tkinter.ttk
        import tkinter.filedialog
        import tkinter.messagebox
        import tkinter.scrolledtext
        print_success("tkinter GUI库可用 ✓")
        return True
    except ImportError as e:
        print_error(f"tkinter不可用: {e}")
        if platform.system() == "Linux":
            print_info("Linux系统请安装: sudo apt-get install python3-tk")
        elif platform.system() == "Darwin":
            print_info("macOS系统请使用Homebrew安装Python，或安装tkinter包")
        return False


def check_pip():
    """检查pip可用性"""
    print_info("检查pip包管理器...")
    try:
        import pip
        print_success("pip可用 ✓")
        return True
    except ImportError:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "--version"], 
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print_success("pip可用 ✓")
            return True
        except subprocess.CalledProcessError:
            print_error("pip不可用，请先安装pip")
            return False


def install_dependencies(minimal=True):
    """安装依赖包"""
    requirements_file = "requirements-minimal.txt" if minimal else "requirements.txt"
    
    if not Path(requirements_file).exists():
        print_error(f"依赖文件不存在: {requirements_file}")
        return False
    
    print_info(f"安装依赖包 ({requirements_file})...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", requirements_file
        ])
        print_success("依赖包安装完成 ✓")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"依赖包安装失败: {e}")
        return False


def check_installed_packages():
    """检查已安装的包"""
    print_info("检查已安装的关键包...")
    
    packages_to_check = [
        ("pyinstaller", "打包工具"),
    ]
    
    if platform.system() == "Windows":
        packages_to_check.append(("pywin32", "Windows系统增强"))
    
    all_good = True
    for package, description in packages_to_check:
        try:
            __import__(package)
            print_success(f"{package} ({description}) ✓")
        except ImportError:
            print_error(f"{package} ({description}) 未安装")
            all_good = False
    
    return all_good


def test_basic_functionality():
    """测试基本功能"""
    print_info("测试基本功能...")
    
    try:
        # 测试路径工具
        from path_utils import get_application_path, get_resource_path
        app_path = get_application_path()
        resource_path = get_resource_path()
        print_success(f"路径工具测试通过 - 应用路径: {app_path}")
        
        # 测试GUI导入
        if check_tkinter():
            print_success("GUI库测试通过")
        
        return True
    except Exception as e:
        print_error(f"功能测试失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("LOC_COMPILE 项目环境设置")
    print("=" * 50)
    
    # 检查基本环境
    if not check_python_version():
        sys.exit(1)
    
    if not check_tkinter():
        print_error("tkinter不可用，GUI功能将无法使用")
        response = input("是否继续安装其他依赖? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    if not check_pip():
        sys.exit(1)
    
    # 询问安装类型
    print("\n安装选项:")
    print("1. 最小安装 (仅运行时依赖)")
    print("2. 完整安装 (包含开发工具)")
    
    choice = input("请选择 (1/2, 默认为1): ").strip()
    minimal = choice != '2'
    
    # 安装依赖
    if not install_dependencies(minimal):
        sys.exit(1)
    
    # 检查安装结果
    if not check_installed_packages():
        print_error("部分包安装失败，但可能不影响基本功能")
    
    # 测试功能
    if test_basic_functionality():
        print_success("\n环境设置完成！")
        print_info("现在可以运行: python main.py")
    else:
        print_error("\n环境设置可能有问题，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main() 