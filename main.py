#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import subprocess
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import re
from datetime import datetime

# 添加获取应用程序路径的函数
def get_application_path():
    """获取应用程序的实际路径，适用于打包后的EXE文件"""
    if getattr(sys, 'frozen', False):
        # 如果应用程序已被打包
        return os.path.dirname(sys.executable)
    else:
        # 如果是直接运行脚本
        # 获取当前脚本所在的LOC_COMPILE目录
        LOC_COMPILE_dir = os.path.dirname(os.path.abspath(__file__))
        # 返回项目根目录
        return os.path.dirname(LOC_COMPILE_dir)

# 确保项目目录结构正确存在
def ensure_project_structure():
    """确保项目的基本目录结构在EXE所在目录正确存在"""
    app_path = get_application_path()
    
    # 项目根目录
    vcu_project_dir = os.path.join(app_path, "VCU_compile - selftest")
    
    # 检查并创建项目根目录
    if not os.path.exists(vcu_project_dir):
        os.makedirs(vcu_project_dir)
        print(f"创建项目根目录: {vcu_project_dir}")
    
    # 确保MVCU和SVCU目录结构存在
    mvcu_src_dir = os.path.join(vcu_project_dir, "dev_kernel_mvcu", "src")
    mvcu_build_dir = os.path.join(vcu_project_dir, "dev_kernel_mvcu", "build")
    mvcu_out_dir = os.path.join(mvcu_build_dir, "out")
    
    svcu_src_dir = os.path.join(vcu_project_dir, "dev_kernel_svcu", "src")
    svcu_build_dir = os.path.join(vcu_project_dir, "dev_kernel_svcu", "build")
    svcu_out_dir = os.path.join(svcu_build_dir, "out")
    
    # 创建必要的目录
    for directory in [mvcu_src_dir, mvcu_build_dir, mvcu_out_dir, svcu_src_dir, svcu_build_dir, svcu_out_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"创建目录: {directory}")

# 导入UI组件
try:
    from vcu_compiler_ui import VcuCompilerUI
except ImportError:
    # 如果在同一目录下找不到，定义一个路径变量
    script_dir = get_application_path()
    LOC_COMPILE_dir = os.path.join(script_dir, "LOC_COMPILE")
    sys.path.append(LOC_COMPILE_dir)
    try:
        from vcu_compiler_ui import VcuCompilerUI
    except ImportError:
        # 如果还是导入失败，会在后面处理
        pass

def update_makefiles_with_correct_paths(callback=None):
    """
    更新makefile中的编译器路径为Windows格式的绝对路径
    
    参数:
        callback: 回调函数，用于将进度和信息显示在UI上
                 格式为 callback(message, is_error=False)
    """
    # 用于记录和显示信息的帮助函数
    def show_message(message, is_error=False):
        """按照统一格式记录并发送日志信息"""

        # 确保消息带有时间戳前缀
        if not message.startswith("["):
            timestamp = datetime.now().strftime("%H:%M:%S")
            message = f"[{timestamp}] {message}"

        print(message)

        # 回调给UI时应传递当前消息
        if callback:
            callback(message, is_error)
    
    # 使用新的应用程序路径获取函数
    script_dir = get_application_path()
    
    # 确保盘符是大写的
    if script_dir.startswith("c:"):
        script_dir = "C:" + script_dir[2:]
    
    # 获取CW和GCC的绝对路径
    cw_path = os.path.join(script_dir, "CW", "ColdFire_Tools", "Command_Line_Tools")
    gcc_path = os.path.join(script_dir, "GCC", "bin")
    
    # 转换为Windows格式的路径 (使用正斜杠，如C:/Users/...)
    win_cw_path = cw_path.replace("\\", "/")
    win_gcc_path = gcc_path.replace("\\", "/")
    
    # 确保路径中的盘符是大写的
    if win_cw_path.startswith("c:/"):
        win_cw_path = "C:" + win_cw_path[1:]
    if win_gcc_path.startswith("c:/"):
        win_gcc_path = "C:" + win_gcc_path[1:]
    
    show_message("Current directory: {}".format(script_dir))
    show_message("Setting compiler paths:")
    show_message("CW path = {}".format(win_cw_path))
    show_message("GCC path = {}".format(win_gcc_path))
    
    # 项目根目录
    vcu_project_dir = os.path.join(script_dir, "VCU_compile - selftest")
    
    # 需要更新的makefile路径列表
    makefile_paths = [
        os.path.join(vcu_project_dir, "dev_kernel_mvcu", "build", "makefile"),
        os.path.join(vcu_project_dir, "dev_kernel_svcu", "build", "makefile")
    ]
    
    # 尝试可能的编码列表
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    results = []  # 用于收集结果报告
    
    for makefile_path in makefile_paths:
        if os.path.exists(makefile_path):
            # 判断是哪个makefile
            makefile_type = "MVCU" if "dev_kernel_mvcu" in makefile_path else "SVCU"
            show_message("Processing {} makefile...".format(makefile_type))
            
            # 尝试不同的编码
            content = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    with open(makefile_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    used_encoding = encoding
                    show_message("Successfully read file with {} encoding".format(encoding))
                    break
                except UnicodeDecodeError:
                    show_message("Cannot read file with {} encoding, trying next...".format(encoding))
                    continue
            
            if content is None:
                error_msg = "Cannot read file with any supported encoding: {}".format(makefile_path)
                show_message(error_msg, is_error=True)
                results.append({"type": makefile_type, "success": False, "message": error_msg})
                continue
            
            try:
                # 使用正则表达式进行替换，确保路径使用双引号正确转义
                # 替换CW路径
                content = re.sub(r'CW_PATH\s*=\s*[^\n]*', 'CW_PATH = {}'.format(win_cw_path), content)
                # 替换GCC路径
                content = re.sub(r'GCC_PATH\s*=\s*[^\n]*', 'GCC_PATH = {}'.format(win_gcc_path), content)
                
                # 修改all目标中的中文为英文
                content = re.sub(r'@echo\s+"?========== 编译信息 ==========="?', '@echo "========== Compilation Info =========="', content)
                content = re.sub(r'@echo\s+"?当前路径: \$\(shell pwd\)"?', '@echo "Current directory: $(shell pwd)"', content)
                content = re.sub(r'@echo\s+"?编译器路径:"?', '@echo "Compiler paths:"', content)
                content = re.sub(r'@echo\s+"?=============================="?', '@echo "=============================="', content)
                
                # 保存修改后的内容，使用相同的编码
                with open(makefile_path, 'w', encoding=used_encoding) as f:
                    f.write(content)
                
                success_msg = "Successfully updated {} makefile: {}".format(makefile_type, makefile_path)
                show_message(success_msg)
                results.append({"type": makefile_type, "success": True, "message": success_msg})
            except Exception as e:
                error_msg = "Failed to update makefile content: {}, error: {}".format(makefile_path, e)
                show_message(error_msg, is_error=True)
                results.append({"type": makefile_type, "success": False, "message": error_msg})
        else:
            error_msg = "Makefile not found: {}".format(makefile_path)
            show_message(error_msg, is_error=True)
            results.append({"type": makefile_type, "success": False, "message": error_msg})
    
    # 返回更新结果，可在UI中使用
    return results

def update_msys_profile():
    """更新MSYS的profile文件，使用简单的路径指定方式"""
    # 获取当前脚本所在目录
    script_dir = get_application_path()
    
    # 确保盘符是大写的
    if script_dir.startswith("c:"):
        script_dir = "C:" + script_dir[2:]
    
    # 构建项目路径
    vcu_dir = os.path.join(script_dir, "VCU_compile - selftest")
    
    # 构建MSYS profile路径
    profile_path = os.path.join(script_dir, "MSYS-1.0.10-selftest", "1.0", "etc", "profile")
    
    if not os.path.exists(profile_path):
        print(f"警告: MSYS profile文件不存在: {profile_path}")
        return False, None, None
    
    # 将Windows路径转换为MSYS路径格式
    msys_path_format = script_dir.replace("\\", "/").replace("C:", "/c")
    vcu_path_format = vcu_dir.replace("\\", "/").replace("C:", "/c")
    
    # 构建MSYS脚本内容
    mvcu_path = f"{vcu_path_format}/dev_kernel_mvcu/build"
    svcu_path = f"{vcu_path_format}/dev_kernel_svcu/build"
    
    # 创建最简单的profile头部
    profile_header = '''# Copyright (C) 2001, 2002  Earnie Boyd  <earnie@users.sf.net>
# This file is part of the Minimal SYStem.
#   http://www.mingw.org/msys.shtml
# 
#         File:	profile
#  Description:	Shell environment initialization script
# Last Revised:	2002.05.04

if [ -z "$MSYSTEM" ]; then
  MSYSTEM=MINGW32
fi

# PATH setup
if [ $MSYSTEM == MINGW32 ]; then
  export PATH=".:/usr/local/bin:/mingw/bin:/bin:$PATH"
else
  export PATH=".:/usr/local/bin:/bin:/mingw/bin:$PATH"
fi

if [ -z "$USERNAME" ]; then
  LOGNAME="`id -un`"
else
  LOGNAME="$USERNAME"
fi

# Set up USER's home directory
if [ -z "$HOME" ]; then
  HOME="/home/$LOGNAME"
fi

if [ ! -d "$HOME" ]; then
  mkdir -p "$HOME"
fi

if [ "x$HISTFILE" == "x/.bash_history" ]; then
  HISTFILE=$HOME/.bash_history
fi

export HOME LOGNAME MSYSTEM HISTFILE

for i in /etc/profile.d/*.sh ; do
  if [ -f $i ]; then
    . $i
  fi
done

export MAKE_MODE=unix
export PS1='\\[\\033]0;$MSYSTEM:\\w\\007
\\033[32m\\]\\u@\\h \\[\\033[33m\\w\\033[0m\\]
$ '

alias clear=clsb
'''

    # 创建处理MSYS_FLAG的部分，包含硬编码的路径
    msys_flag_handler = f'''
# 处理MSYS_FLAG
if [ -n "$MSYS_FLAG" ]; then
  # 将MSYS_FLAG变量的值赋值给user_input变量
  user_input="$MSYS_FLAG"
  echo "Current MSYS_FLAG: $user_input"

  # 根据user_input变量的值执行不同的操作
  if [ "$user_input" = "m" ]; then
    # MVCU
    echo "Switching to MVCU directory"
    cd "{mvcu_path}"
    script_name="make_com.sh"
  elif [ "$user_input" = "s" ]; then
    # SVCU
    echo "Switching to SVCU directory"
    cd "{svcu_path}"
    script_name="make_voob.sh"
  else
    echo "Unknown mode: $user_input"
    exit 1
  fi

  # 检查当前目录
  echo "Current directory: $(pwd)"
  
  # 检查脚本是否存在并执行
  if [ -f "$script_name" ]; then
    echo "Executing script: $script_name"
    sh "$script_name"
  else
    echo "Script $script_name not found in current directory."
    echo "Available files:"
    ls -la *.sh 2>/dev/null || echo "No .sh files found."
  fi
fi
'''

    # 组合完整的profile内容
    profile_content = profile_header + msys_flag_handler
    
    # 写入文件
    try:
        with open(profile_path, 'w', encoding='utf-8') as f:
            f.write(profile_content)
        print(f"MSYS profile文件已更新: {profile_path}")
        return True, mvcu_path, svcu_path
    except Exception as e:
        print(f"更新MSYS profile文件失败: {e}")
        return False, None, None

def process_in_console_mode(source_path):
    
    """命令行模式下的处理逻辑"""
    # 获取当前脚本所在目录
    script_dir = get_application_path()
    
    # 项目根目录
    vcu_project_dir = os.path.join(script_dir, "VCU_compile - selftest")
    
    # 首先更新makefiles中的编译器路径配置
    update_makefiles_with_correct_paths()
    
    # 检查源路径是否存在
    if not os.path.exists(source_path):
        print("错误: 源路径不存在。")
        input("按任意键继续...")
        return False
    
    # 获取文件名（不含扩展名）
    source_name = os.path.splitext(os.path.basename(source_path))[0]
    print(f"处理源: {source_name}")
    
    # 调试信息
    print(f"正在检查文件名中是否包含mvcu或svcu。文件名: {source_name}")
    
    # 检查源名称是否包含 "mvcu" 或 "svcu"（不区分大小写）
    source_name_lower = source_name.lower()
    vcu_type = None
    
    if "mvcu" in source_name_lower:
        vcu_type = "m"
        dest_folder = os.path.join(vcu_project_dir, "dev_kernel_mvcu", "src")
        print(f"检测到MVCU类型 (在 '{source_name}' 中找到 'mvcu')")
    elif "svcu" in source_name_lower:
        vcu_type = "s"
        dest_folder = os.path.join(vcu_project_dir, "dev_kernel_svcu", "src")
        print(f"检测到SVCU类型 (在 '{source_name}' 中找到 'svcu')")
    
    # 如果没有找到匹配的类型，则退出脚本
    if not vcu_type:
        print(f"错误: 文件名称 '{source_name}' 未包含 mvcu 或 svcu，无法辨认。")
        input("按任意键继续...")
        return False
    
    # 检查目标路径是否存在，如果不存在则创建
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
        print(f"创建目标文件夹: {dest_folder}")
    
    # 设置 MSYS_FLAG 环境变量
    os.environ["MSYS_FLAG"] = vcu_type
    print(f"设置MSYS_FLAG={vcu_type}")
    
    try:
        # 使用 robocopy 复制文件
        print("开始复制文件...")
        
        # 如果是目录，复制整个目录内容
        if os.path.isdir(source_path):
            print(f"复制目录 {source_path} 到 {dest_folder}")
            # 使用subprocess调用robocopy
            result = subprocess.run([
                "robocopy", 
                source_path, 
                dest_folder, 
                "/MIR", 
                "/NFL", "/NDL", "/NJH", "/NC", "/NJS", "/NP"
            ], check=False)
            
            # robocopy 返回值大于等于8表示错误
            if result.returncode >= 8:
                print("错误: 文件复制失败。")
                input("按任意键继续...")
                return False
            else:
                print("文件复制成功")
        else:
            # 如果是单个文件，直接复制
            try:
                print(f"复制文件 {source_path} 到 {dest_folder}")
                shutil.copy2(source_path, dest_folder)
                print("文件复制成功")
            except Exception as e:
                print(f"错误: 文件复制失败。{e}")
                input("按任意键继续...")
                return False
        
        # 启动MSYS
        msys_bat_path = os.path.join(script_dir, "MSYS-1.0.10-selftest", "1.0", "msys.bat")
        if os.path.exists(msys_bat_path):
            print(f"启动MSYS: {msys_bat_path}")
            subprocess.Popen(["cmd", "/c", "start", "", msys_bat_path])
            print("MSYS已启动")
            
            # 编译完成后，打开对应的输出文件夹
            if vcu_type == "m":
                output_dir = os.path.join(vcu_project_dir, "dev_kernel_mvcu", "build", "out")
                if os.path.exists(output_dir):
                    print(f"打开MVCU输出文件夹: {output_dir}")
                    os.startfile(output_dir)
            elif vcu_type == "s":
                output_dir = os.path.join(vcu_project_dir, "dev_kernel_svcu", "build", "out")
                if os.path.exists(output_dir):
                    print(f"打开SVCU输出文件夹: {output_dir}")
                    os.startfile(output_dir)
            
            return True
        else:
            print(f"错误: 找不到MSYS批处理文件: {msys_bat_path}")
            input("按任意键继续...")
            return False
    
    except Exception as e:
        print(f"错误: 处理过程中出现异常: {e}")
        input("按任意键继续...")
        return False

def start_gui_mode():
    """启动GUI模式"""
    try:
        # 首先确保项目目录结构正确
        ensure_project_structure()
        
        # 更新MSYS的profile文件，并获取路径信息
        success, mvcu_path, svcu_path = update_msys_profile()
        
        # 尝试导入UI模块
        try:
            from vcu_compiler_ui import VcuCompilerUI
        except ImportError:
            print("错误: 无法导入VcuCompilerUI模块，请确保vcu_compiler_ui.py文件存在。")
            return False
        
        # 检查tkinter是否可用
        try:
            import tkinter as tk
        except ImportError:
            print("错误: 无法导入tkinter模块，请确保安装了带有tkinter的Python。")
            return False
        
        # 启动GUI，传递路径信息
        root = tk.Tk()
        app = VcuCompilerUI(root, update_makefiles_with_correct_paths, mvcu_path, svcu_path)
        root.mainloop()
        return True
    
    except Exception as e:
        print(f"启动GUI时出错: {e}")
        return False

def main():
    """主函数，处理命令行参数并启动相应的模式"""
    # 确保项目目录结构正确
    ensure_project_structure()
    
    # 更新MSYS的profile文件
    success, mvcu_path, svcu_path = update_msys_profile()
    
    parser = argparse.ArgumentParser(description="VCU编译器启动器")
    parser.add_argument("--gui", action="store_true", help="启动图形界面模式")
    parser.add_argument("--console", action="store_true", help="启动命令行模式")
    parser.add_argument("--update-paths", action="store_true", help="仅更新makefile中的编译器路径")
    parser.add_argument("source_path", nargs="?", help="源文件或目录的路径")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 如果只是更新路径
    if args.update_paths:
        update_makefiles_with_correct_paths()
        if success:
            print("编译器路径更新完成。")
            print(f"MVCU路径: {mvcu_path}")
            print(f"SVCU路径: {svcu_path}")
        else:
            print("编译器路径更新失败。")
        return 0
    
    # 判断运行模式
    if args.gui:
        # 启动GUI模式
        start_gui_mode()
    elif args.console or args.source_path:
        # 命令行模式
        if not args.source_path:
            parser.print_help()
            print("\n错误: 命令行模式下必须指定源路径。")
            return 1
        
        # 处理文件
        success = process_in_console_mode(args.source_path)
        return 0 if success else 1
    else:
        # 没有指定模式或参数，默认启动GUI
        # 但先检查是否有拖放的文件
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            # 有拖放的文件，使用命令行模式处理
            success = process_in_console_mode(sys.argv[1])
            return 0 if success else 1
        else:
            # 启动GUI模式
            start_gui_mode()
    
    return 0

def no_console_main():
    """无控制台版本的主函数，用于打包时不显示控制台窗口"""
    try:
        sys.exit(main())
    except Exception as e:
        # 捕获所有异常，避免在无控制台模式时崩溃而无法看到错误信息
        messagebox.showerror("错误", f"程序运行时发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        # 打包后的应用程序入口点
        no_console_main()
    else:
        # 开发环境入口点
        sys.exit(main())
