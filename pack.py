#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""打包脚本：将項目打包为單個可執行文件"""

import os
import shutil
import subprocess
import sys
from datetime import datetime
import time


def build_executable():
    """使用 PyInstaller 打包項目"""
    loc_dir = os.path.dirname(os.path.abspath(__file__))
    # 与 main.py 中的 get_application_path() 保持一致，资源目录位于上级
    project_root = os.path.dirname(loc_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exe_name = f"LOC_COMPILE_{timestamp}"

    dist_dir = os.path.join(project_root, "dist")
    build_dir = os.path.join(project_root, "build")
    release_dir = os.path.join(project_root, "release")

    # 清理舊的輸出
    for d in (dist_dir, build_dir):
        if os.path.exists(d):
            shutil.rmtree(d)

    # 基础 PyInstaller 命令
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--onefile",
        "--noconsole",
        "--name",
        exe_name,
        # 主入口文件
        os.path.join(loc_dir, "main.py"),
    ]

    # 确保包含 vcu_compiler_ui 模块
    ui_module_path = os.path.join(loc_dir, "vcu_compiler_ui.py")
    if os.path.exists(ui_module_path):
        print(f"找到UI模块: {ui_module_path}")
        cmd.extend(["--hidden-import", "vcu_compiler_ui"])
        # 也可以直接添加为额外文件
        cmd.extend(["--add-data", f"{ui_module_path}{os.pathsep}LOC_COMPILE"])
    else:
        print(f"警告: UI模块不存在: {ui_module_path}")

    # 添加其他可能需要的Python模块
    hidden_imports = [
        "tkinter",
        "tkinter.ttk", 
        "tkinter.filedialog",
        "tkinter.messagebox",
        "tkinter.scrolledtext",
        "threading",
        "subprocess",
        "shutil",
        "argparse",
        "re",
        "datetime"
    ]
    
    for module in hidden_imports:
        cmd.extend(["--hidden-import", module])

    # 将整个LOC_COMPILE目录作为数据包含
    cmd.extend(["--add-data", f"{loc_dir}{os.pathsep}LOC_COMPILE"])

    # 搜索可能需要打包的数据目录
    data_dirs = [
        "CW",
        "GCC", 
        "MSYS-1.0.10-selftest",
    ]
    
    # VCU_compile目录需要特殊处理，只包含必要的文件
    vcu_compile_dir = os.path.join(project_root, "VCU_compile - selftest")
    if os.path.exists(vcu_compile_dir):
        print(f"找到VCU项目目录: {vcu_compile_dir}")
        # 不直接添加整个目录，而是在后面的复制过程中特殊处理
    else:
        print(f"警告: VCU项目目录不存在: {vcu_compile_dir}")

    for d in data_dirs:
        abs_path = os.path.join(project_root, d)
        abs_path = os.path.normpath(abs_path)  # 规范化路径
        if os.path.exists(abs_path):
            print(f"找到数据目录: {abs_path}")
            # PyInstaller 的 --add-data 格式为 '源路径;目标路径' (Windows) 或 '源路径:目标路径' (Linux/Mac)
            cmd.extend(["--add-data", f"{abs_path}{os.pathsep}{d}"])
        else:
            print(f"警告: 数据目录不存在: {abs_path}")

    # 添加图标文件（如果存在）
    icon_path = os.path.join(loc_dir, "icon.ico")
    if os.path.exists(icon_path):
        cmd.extend(["--icon", icon_path])

    print("执行打包命令:", " ".join(cmd))
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"打包失败，错误代码: {e.returncode}")
        raise

    exe_path = os.path.join(dist_dir, f"{exe_name}.exe")
    if not os.path.exists(exe_path):
        raise FileNotFoundError(f"生成的exe文件不存在: {exe_path}")
    
    os.makedirs(release_dir, exist_ok=True)
    final_path = os.path.join(release_dir, f"{exe_name}.exe")
    shutil.move(exe_path, final_path)

    # 复制数据目录到release目录，确保exe与数据目录在同一目录
    for d in data_dirs:
        src_path = os.path.join(project_root, d)
        if os.path.exists(src_path):
            dest_path = os.path.join(release_dir, d)
            if os.path.exists(dest_path):
                try:
                    shutil.rmtree(dest_path)
                except Exception as e:
                    print(f"警告: 删除现有目录失败 {dest_path}: {e}")
                    continue
            
            try:
                if os.path.isdir(src_path):
                    # 使用自定义复制函数，排除不需要的文件
                    copy_directory_safe(src_path, dest_path)
                    print(f"复制目录: {src_path} -> {dest_path}")
                else:
                    shutil.copy2(src_path, dest_path)
                    print(f"复制文件: {src_path} -> {dest_path}")
            except Exception as e:
                print(f"警告: 复制失败 {src_path}: {e}")
                continue

    # 特殊处理VCU_compile目录，只复制必要的文件和目录结构
    vcu_src_path = os.path.join(project_root, "VCU_compile - selftest")
    if os.path.exists(vcu_src_path):
        vcu_dest_path = os.path.join(release_dir, "VCU_compile - selftest")
        print(f"特殊处理VCU项目目录: {vcu_src_path}")
        
        try:
            # 创建基本目录结构
            basic_dirs = [
                "dev_kernel_mvcu/src",
                "dev_kernel_mvcu/build", 
                "dev_kernel_mvcu/build/out",
                "dev_kernel_svcu/src",
                "dev_kernel_svcu/build",
                "dev_kernel_svcu/build/out",
            ]
            
            for basic_dir in basic_dirs:
                full_dir = os.path.join(vcu_dest_path, basic_dir)
                os.makedirs(full_dir, exist_ok=True)
                print(f"创建目录: {full_dir}")
            
            # 只复制重要的文件（makefile等）
            for root, dirs, files in os.walk(vcu_src_path):
                # 跳过问题目录
                dirs[:] = [d for d in dirs if not any(skip in d.lower() for skip in 
                          ['.metadata', '.settings', 'debug', 'release', 'remotesystemstempfiles'])]
                
                rel_path = os.path.relpath(root, vcu_src_path)
                if rel_path == '.':
                    continue
                    
                dest_dir = os.path.join(vcu_dest_path, rel_path)
                
                for file in files:
                    # 只复制重要文件
                    if (file.lower() in ['makefile', 'readme.txt', 'readme.md'] or 
                        file.lower().endswith(('.c', '.h', '.s', '.bat', '.sh', '.py', '.txt'))):
                        try:
                            src_file = os.path.join(root, file)
                            os.makedirs(dest_dir, exist_ok=True)
                            dest_file = os.path.join(dest_dir, file)
                            shutil.copy2(src_file, dest_file)
                            print(f"复制VCU文件: {rel_path}/{file}")
                        except Exception as e:
                            print(f"复制VCU文件失败 {file}: {e}")
                            
        except Exception as e:
            print(f"特殊处理VCU目录失败: {e}")
            # 如果特殊处理失败，尝试使用安全复制
            try:
                copy_important_files_only(vcu_src_path, vcu_dest_path)
                print(f"使用安全复制模式处理VCU目录")
            except Exception as e2:
                print(f"安全复制VCU目录也失败: {e2}")

    # 创建启动脚本（可选）
    create_batch_launcher(release_dir, f"{exe_name}.exe")

    print(f"打包完成，生成文件: {final_path}")
    print(f"release目录: {release_dir}")
    print("目录结构:")
    for item in os.listdir(release_dir):
        item_path = os.path.join(release_dir, item)
        if os.path.isdir(item_path):
            print(f"  [目录] {item}/")
        else:
            size = os.path.getsize(item_path) / 1024 / 1024  # MB
            print(f"  [文件] {item} ({size:.1f} MB)")

    return final_path


def create_batch_launcher(release_dir, exe_name):
    """创建批处理启动脚本"""
    batch_content = f'''@echo off
title VCU编译器
echo 启动VCU编译器...
echo.

REM 设置当前目录为脚本所在目录
cd /d "%~dp0"

REM 启动主程序
"{exe_name}"

REM 如果程序异常退出，暂停显示错误信息
if errorlevel 1 (
    echo.
    echo 程序运行出错，错误代码: %errorlevel%
    echo 请检查相关配置文件和依赖项
    pause
)
'''
    
    batch_path = os.path.join(release_dir, "启动VCU编译器.bat")
    try:
        with open(batch_path, 'w', encoding='gbk') as f:
            f.write(batch_content)
        print(f"创建启动脚本: {batch_path}")
    except Exception as e:
        print(f"创建启动脚本失败: {e}")


def copy_directory_safe(src, dest, ignore_patterns=None):
    """安全复制目录，排除特定模式的文件和目录"""
    if ignore_patterns is None:
        ignore_patterns = [
            '.git',           # Git 仓库
            '.gitignore',     # Git 忽略文件
            '__pycache__',    # Python 缓存
            '*.pyc',          # Python 编译文件
            '*.pyo',          # Python 优化文件
            '.vs',            # Visual Studio
            '.vscode',        # VS Code
            'Thumbs.db',      # Windows 缩略图
            '.DS_Store',      # macOS 文件
            '*.tmp',          # 临时文件
            '*.temp',         # 临时文件
            '*.log',          # 日志文件
            'dist',           # 构建输出目录
            'build',          # 构建临时目录
            '.metadata',      # Eclipse 元数据目录
            '.settings',      # Eclipse 设置目录
            '.project',       # Eclipse 项目文件
            '.cproject',      # Eclipse C/C++ 项目文件
            '.classpath',     # Eclipse Java 类路径文件
            '*.launch',       # Eclipse 启动配置文件
            '.history',       # Eclipse 历史目录
            'RemoteSystemsTempFiles', # Eclipse 远程系统临时文件
            '*.d',            # 依赖文件
            '*.o',            # 目标文件
            '*.obj',          # 目标文件
            '*.elf',          # 可执行文件
            '*.bin',          # 二进制文件
            '*.hex',          # 十六进制文件
            '*.map',          # 映射文件
            '*.lst',          # 列表文件
            'Debug',          # Debug 目录
            'Release',        # Release 目录
            '*.workspace',    # 工作空间文件
        ]
    
    def ignore_function(directory, files):
        """自定义忽略函数"""
        ignored = []
        for f in files:
            # 检查是否匹配忽略模式
            should_ignore = False
            for pattern in ignore_patterns:
                if pattern.startswith('.') and not pattern.startswith('*.'):
                    # 目录名或文件名精确匹配
                    if f == pattern or f == pattern[1:]:
                        should_ignore = True
                        break
                elif pattern.startswith('*.'):
                    # 文件扩展名匹配
                    if f.lower().endswith(pattern[1:].lower()):
                        should_ignore = True
                        break
                elif pattern in f.lower():
                    # 包含匹配（不区分大小写）
                    should_ignore = True
                    break
            
            # 额外检查：排除包含特殊字符或过长的文件名
            if len(f) > 200:  # 文件名过长
                should_ignore = True
            
            # 检查是否包含可能有问题的字符
            problematic_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
            if any(char in f for char in problematic_chars if char not in ['\\', '/']):
                should_ignore = True
            
            if should_ignore:
                ignored.append(f)
                print(f"跳过: {os.path.join(directory, f)}")
        
        return ignored
    
    try:
        shutil.copytree(src, dest, ignore=ignore_function)
    except Exception as e:
        print(f"目录复制失败: {e}")
        # 尝试手动复制重要文件
        try:
            os.makedirs(dest, exist_ok=True)
            copy_important_files_only(src, dest)
        except Exception as e2:
            print(f"手动复制也失败: {e2}")
            raise


def copy_important_files_only(src, dest):
    """仅复制重要文件，避免复制可能有问题的文件"""
    important_extensions = ['.c', '.h', '.s', '.S', '.asm', '.txt', '.md', '.bat', '.sh', '.py']
    important_dirs = ['src', 'inc', 'include', 'scripts', 'tools']
    
    for root, dirs, files in os.walk(src):
        # 过滤目录
        dirs[:] = [d for d in dirs if not any(ignore in d.lower() for ignore in 
                   ['.metadata', '.settings', 'debug', 'release', '.git', '__pycache__'])]
        
        # 计算相对路径
        rel_path = os.path.relpath(root, src)
        if rel_path == '.':
            dest_dir = dest
        else:
            dest_dir = os.path.join(dest, rel_path)
        
        # 创建目标目录
        os.makedirs(dest_dir, exist_ok=True)
        
        # 复制重要文件
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in important_extensions or file.lower() in ['makefile', 'readme']:
                try:
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_dir, file)
                    shutil.copy2(src_file, dest_file)
                    print(f"复制: {src_file} -> {dest_file}")
                except Exception as e:
                    print(f"复制文件失败 {file}: {e}")
                    continue


def verify_dependencies():
    """验证打包依赖项"""
    print("验证打包环境...")
    
    # 检查PyInstaller
    try:
        result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ PyInstaller 版本: {result.stdout.strip()}")
        else:
            raise subprocess.CalledProcessError(result.returncode, "PyInstaller")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ PyInstaller 未安装或版本过低")
        print("请运行: pip install pyinstaller>=5.0")
        return False
    
    # 检查必要的Python模块
    required_modules = ['tkinter', 'threading', 'subprocess', 'shutil', 'argparse']
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} 模块可用")
        except ImportError:
            print(f"✗ {module} 模块不可用")
            return False
    
    # 检查源文件
    loc_dir = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(loc_dir, "main.py")
    ui_py = os.path.join(loc_dir, "vcu_compiler_ui.py")
    
    if os.path.exists(main_py):
        print(f"✓ 找到主程序: {main_py}")
    else:
        print(f"✗ 主程序不存在: {main_py}")
        return False
    
    if os.path.exists(ui_py):
        print(f"✓ 找到UI模块: {ui_py}")
    else:
        print(f"✗ UI模块不存在: {ui_py}")
        return False
    
    return True


def main():
    try:
        print("=" * 50)
        print("VCU编译器打包脚本")
        print("=" * 50)
        
        # 验证依赖
        if not verify_dependencies():
            print("✗ 依赖项检查失败，请解决上述问题后重试")
            input("按任意键退出...")
            sys.exit(1)
        
        print("\n开始打包...")
        exe_path = build_executable()
        print("\n" + "=" * 50)
        print("✓ 打包成功完成！")
        print(f"✓ 生成文件: {exe_path}")
        print("=" * 50)
        
        # 询问是否打开release目录
        try:
            import msvcrt
            print("\n按任意键打开release目录，或等待5秒自动退出...")
            i = 0
            while i < 50:  # 5秒 = 50 * 0.1秒
                if msvcrt.kbhit():
                    msvcrt.getch()
                    release_dir = os.path.dirname(exe_path)
                    os.startfile(release_dir)
                    break
                time.sleep(0.1)
                i += 1
        except ImportError:
            input("按回车键退出...")
            
    except FileNotFoundError as e:
        if "PyInstaller" in str(e):
            print("✗ 错误: 未找到 PyInstaller，请先安装: pip install pyinstaller")
        else:
            print(f"✗ 文件不存在错误: {e}")
        input("按任意键退出...")
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        print(f"✗ 打包过程出错，返回码: {exc.returncode}")
        print("请检查上述错误信息并修复相关问题")
        input("按任意键退出...")
        sys.exit(exc.returncode)
    except Exception as e:
        print(f"✗ 未预期的错误: {e}")
        print("请检查项目配置和依赖项")
        input("按任意键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()
