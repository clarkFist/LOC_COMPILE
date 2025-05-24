import os
import sys

"""封装路径相关的辅助函数，兼容打包和开发两种环境。"""

def get_application_path():
    """获取应用程序运行目录，用于存放输出等可写文件"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    loc_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(loc_dir)


def get_resource_path(*path_parts):
    """获取资源文件所在目录，兼容 PyInstaller"""
    base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else get_application_path()
    return os.path.normpath(os.path.join(base, *path_parts)) if path_parts else os.path.normpath(base)

