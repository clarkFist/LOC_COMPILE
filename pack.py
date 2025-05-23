#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""打包脚本：将項目打包為單個可執行文件"""

import os
import shutil
import subprocess
import sys
from datetime import datetime


def build_executable():
    """使用 PyInstaller 打包項目"""
    project_root = os.path.dirname(os.path.abspath(__file__))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exe_name = f"LOC_COMPILE_{timestamp}"

    dist_dir = os.path.join(project_root, "dist")
    build_dir = os.path.join(project_root, "build")
    release_dir = os.path.join(project_root, "release")

    # 清理舊的輸出
    for d in (dist_dir, build_dir):
        if os.path.exists(d):
            shutil.rmtree(d)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--onefile",
        "--noconsole",
        "--name",
        exe_name,
        os.path.join(project_root, "main.py"),
    ]

    # 搜索可能需要打包的數據目錄
    data_dirs = [
        "CW",
        "GCC",
        "MSYS-1.0.10-selftest",
        "VCU_compile - selftest",
    ]

    for d in data_dirs:
        abs_path = os.path.join(project_root, d)
        if os.path.exists(abs_path):
            # PyInstaller 的 --add-data 格式為 '源路徑;目標路徑'
            cmd.extend(["--add-data", f"{abs_path}{os.pathsep}{d}"])

    print("執行打包命令:", " ".join(cmd))
    subprocess.check_call(cmd)

    exe_path = os.path.join(dist_dir, f"{exe_name}.exe")
    os.makedirs(release_dir, exist_ok=True)
    final_path = os.path.join(release_dir, f"{exe_name}.exe")
    shutil.move(exe_path, final_path)

    print(f"打包完成，生成文件: {final_path}")


def main():
    try:
        build_executable()
    except FileNotFoundError:
        print("未找到 PyInstaller，請先安裝: pip install pyinstaller")
    except subprocess.CalledProcessError as exc:
        print("打包過程出錯，返回碼:", exc.returncode)
        sys.exit(exc.returncode)


if __name__ == "__main__":
    main()
