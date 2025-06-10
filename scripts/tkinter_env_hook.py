import os
import sys


def _set_tcl_tk_env():
    """Ensure Tcl/Tk library paths are set at runtime."""
    if hasattr(sys, 'frozen'):
        # 在打包后的应用中
        base_dir = os.path.dirname(sys.executable)
        
        # 设置 Tcl/Tk 库路径
        tcl_dir = os.path.join(base_dir, 'tcl')
        tk_dir = os.path.join(base_dir, 'tk')
        
        if os.path.isdir(tcl_dir):
            os.environ['TCL_LIBRARY'] = tcl_dir
        if os.path.isdir(tk_dir):
            os.environ['TK_LIBRARY'] = tk_dir
            
        # 确保当前目录在 PATH 中，以便找到 DLL 文件
        current_path = os.environ.get('PATH', '')
        if base_dir not in current_path:
            os.environ['PATH'] = base_dir + os.pathsep + current_path
            
        # 对于 Windows，还需要设置一些额外的环境变量
        if sys.platform.startswith('win'):
            # 确保 tkinter 能找到必要的 DLL
            os.environ.setdefault('TK_SILENCE_DEPRECATION', '1')
    else:
        # 在开发环境中
        base_dir = os.path.dirname(os.path.abspath(__file__))

        tcl_dir = os.path.join(base_dir, 'tcl')
        tk_dir = os.path.join(base_dir, 'tk')

        if os.path.isdir(tcl_dir):
            os.environ.setdefault('TCL_LIBRARY', tcl_dir)
        if os.path.isdir(tk_dir):
            os.environ.setdefault('TK_LIBRARY', tk_dir)


_set_tcl_tk_env()
