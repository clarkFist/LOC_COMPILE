#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
VCU编译器图形界面
基于tkinter的现代化GUI，用于辅助VCU项目编译
"""

import os
import sys
import subprocess
import shutil
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk, scrolledtext
import threading
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入工具模块
try:
    from path_utils import get_application_path, get_resource_path
except ImportError:
    logger.warning("path_utils模块导入失败，使用默认实现")
    def get_application_path():
        return os.path.dirname(os.path.abspath(__file__))
    
    def get_resource_path():
        return get_application_path()


class ModuleImporter:
    """模块导入管理器，负责动态导入main模块中的函数"""
    
    def __init__(self):
        self.check_modules_in_makefile = None
        self.archive_output_files = None
        self.update_msys_profile = None
        self._import_functions()
    
    def _import_functions(self):
        """尝试多种方式导入main模块中的函数"""
        import_strategies = [
            self._direct_import,
            self._path_based_import,
            self._dynamic_import
        ]
        
        for strategy in import_strategies:
            try:
                if strategy():
                    logger.info("成功导入main模块函数")
                    return
            except Exception as e:
                logger.debug(f"导入策略失败: {strategy.__name__}, 错误: {e}")
        
        logger.warning("所有导入策略失败，使用备用实现")
        self._use_backup_functions()
    
    def _direct_import(self) -> bool:
        """直接导入策略"""
        from main import check_modules_in_makefile, archive_output_files, update_msys_profile
        self.check_modules_in_makefile = check_modules_in_makefile
        self.archive_output_files = archive_output_files
        self.update_msys_profile = update_msys_profile
        return True
    
    def _path_based_import(self) -> bool:
        """基于路径的导入策略"""
        search_paths = [
            os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else None,
            os.path.join(os.path.dirname(sys.executable), "LOC_COMPILE") if getattr(sys, 'frozen', False) else None,
            getattr(sys, '_MEIPASS', None),
            os.path.join(getattr(sys, '_MEIPASS', ''), "LOC_COMPILE") if hasattr(sys, '_MEIPASS') else None,
            os.path.dirname(os.path.abspath(__file__)),
        ]
        
        for path in filter(None, search_paths):
            if os.path.exists(path):
                sys.path.insert(0, path)
        
        from main import check_modules_in_makefile, archive_output_files, update_msys_profile
        self.check_modules_in_makefile = check_modules_in_makefile
        self.archive_output_files = archive_output_files
        self.update_msys_profile = update_msys_profile
        return True
    
    def _dynamic_import(self) -> bool:
        """动态导入策略"""
        import importlib.util
        
        search_paths = [
            os.path.dirname(sys.executable),
            os.path.join(os.path.dirname(sys.executable), "LOC_COMPILE"),
            getattr(sys, '_MEIPASS', None),
            os.path.join(getattr(sys, '_MEIPASS', ''), "LOC_COMPILE") if hasattr(sys, '_MEIPASS') else None,
            os.path.dirname(os.path.abspath(__file__)),
        ]
        
        for path in filter(None, search_paths):
            main_file = Path(path) / "main.py"
            if main_file.exists():
                spec = importlib.util.spec_from_file_location("main", str(main_file))
                main_module = importlib.util.module_from_spec(spec)
                sys.modules["main"] = main_module
                spec.loader.exec_module(main_module)
                
                self.check_modules_in_makefile = getattr(main_module, 'check_modules_in_makefile', None)
                self.archive_output_files = getattr(main_module, 'archive_output_files', None)
                self.update_msys_profile = getattr(main_module, 'update_msys_profile', None)
                return True
        
        return False
    
    def _use_backup_functions(self):
        """使用备用函数实现"""
        def check_modules_in_makefile(vcu_type):
            logger.info(f"执行基本的模块检查 (VCU类型: {vcu_type})")
            return True
        
        def archive_output_files(output_dir):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_dir = Path(output_dir) / f"out_{timestamp}"
            dest_dir.mkdir(exist_ok=True)
            
            for file_path in Path(output_dir).glob("*"):
                if file_path.suffix.lower() in [".s19", ".lze"]:
                    shutil.copy2(file_path, dest_dir / file_path.name)
            
            return str(dest_dir)
        
        def update_msys_profile():
            return False, None, None
        
        self.check_modules_in_makefile = check_modules_in_makefile
        self.archive_output_files = archive_output_files
        self.update_msys_profile = update_msys_profile


class VcuCompilerUI:
    """VCU编译器主界面类"""
    
    # 常量定义
    WINDOW_TITLE = "VCU编译器 v2.0"
    WINDOW_SIZE = "800x600"
    MIN_WINDOW_SIZE = (600, 500)
    
    # VCU类型映射
    VCU_TYPES = {
        'mvcu': {
            'code': 'm',
            'name': 'MVCU',
            'folder': 'dev_kernel_mvcu'
        },
        'svcu': {
            'code': 's',
            'name': 'SVCU', 
            'folder': 'dev_kernel_svcu'
        }
    }
    
    def __init__(self, root: tk.Tk, update_path_function: Optional[Callable] = None, 
                 mvcu_path: Optional[str] = None, svcu_path: Optional[str] = None):
        """
        初始化VCU编译器界面
        
        Args:
            root: Tk根窗口实例
            update_path_function: 更新makefile路径的回调函数
            mvcu_path: MSYS环境下MVCU的编译路径
            svcu_path: MSYS环境下SVCU的编译路径
        """
        self.root = root
        self.update_path_function = update_path_function
        self.mvcu_path = mvcu_path
        self.svcu_path = svcu_path
        self.current_vcu_type = None
        
        # 导入必要的函数
        self.importer = ModuleImporter()
        
        # 初始化界面
        self._setup_window()
        self._setup_styles()
        self._create_widgets()
        self._initialize_logging()
        
        # 自动更新路径
        if self.update_path_function:
            self.root.after(500, self.update_compiler_paths)
    
    def _setup_window(self):
        """配置主窗口"""
        self.root.title(self.WINDOW_TITLE)
        self.root.geometry(self.WINDOW_SIZE)
        self.root.minsize(*self.MIN_WINDOW_SIZE)
        self.root.resizable(True, True)
        
        # 居中显示窗口
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    def _setup_styles(self):
        """配置UI样式"""
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            logger.warning("无法设置clam主题，使用默认主题")
        
        # 配置字体和样式
        font_config = ("Microsoft YaHei UI", 10)
        self.style.configure("TButton", font=font_config)
        self.style.configure("TLabel", font=font_config)
        self.style.configure("TLabelFrame.Label", font=("Microsoft YaHei UI", 10, "bold"))
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        
        # 创建各个区域
        self._create_path_selection_area(main_frame, row=0)
        self._create_path_update_area(main_frame, row=1)
        self._create_msys_path_area(main_frame, row=2)
        self._create_makefile_path_area(main_frame, row=3)
        self._create_log_area(main_frame, row=4)
        self._create_button_area(main_frame, row=5)
        self._create_status_bar()
        
        # 配置行权重
        main_frame.rowconfigure(4, weight=1)
    
    def _create_path_selection_area(self, parent: ttk.Frame, row: int):
        """创建路径选择区域"""
        path_frame = ttk.LabelFrame(parent, text="源路径选择", padding="5")
        path_frame.grid(row=row, column=0, sticky="ew", pady=5)
        path_frame.columnconfigure(1, weight=1)
        
        ttk.Label(path_frame, text="源路径:").grid(row=0, column=0, padx=5, sticky="w")
        
        self.path_var = tk.StringVar()
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        path_entry.grid(row=0, column=1, padx=5, sticky="ew")
        
        browse_btn = ttk.Button(path_frame, text="浏览...", command=self._browse_path)
        browse_btn.grid(row=0, column=2, padx=5)
    
    def _create_path_update_area(self, parent: ttk.Frame, row: int):
        """创建路径更新区域"""
        update_frame = ttk.Frame(parent, padding="5")
        update_frame.grid(row=row, column=0, sticky="ew", pady=5)
        update_frame.columnconfigure(1, weight=1)
        
        self.update_path_btn = ttk.Button(
            update_frame, 
            text="更新编译器路径",
            command=self.update_compiler_paths
        )
        self.update_path_btn.grid(row=0, column=0, padx=5, sticky="w")
        
        # 路径状态标签
        self.path_status_var = tk.StringVar(value="编译器路径状态: 未检查")
        status_label = ttk.Label(update_frame, textvariable=self.path_status_var)
        status_label.grid(row=0, column=1, padx=10, sticky="w")
    
    def _create_msys_path_area(self, parent: ttk.Frame, row: int):
        """创建MSYS路径信息区域"""
        msys_frame = ttk.LabelFrame(parent, text="MSYS配置", padding="5")
        msys_frame.grid(row=row, column=0, sticky="ew", pady=5)
        msys_frame.columnconfigure(1, weight=1)
        
        # MVCU路径
        self._create_path_display(msys_frame, "MVCU路径:", 0, self.mvcu_path)
        
        # SVCU路径  
        self._create_path_display(msys_frame, "SVCU路径:", 1, self.svcu_path)
    
    def _create_path_display(self, parent: ttk.Frame, label_text: str, row: int, path_value: Optional[str]):
        """创建路径显示行"""
        frame = ttk.Frame(parent, padding="2")
        frame.grid(row=row, column=0, sticky="ew")
        frame.columnconfigure(1, weight=1)
        
        ttk.Label(frame, text=label_text).grid(row=0, column=0, padx=5, sticky="w")
        
        path_var = tk.StringVar(value=path_value or "未设置")
        ttk.Label(frame, textvariable=path_var).grid(row=0, column=1, padx=5, sticky="ew")
        
        # 保存变量引用
        if "MVCU" in label_text:
            self.mvcu_path_var = path_var
        else:
            self.svcu_path_var = path_var
    
    def _create_makefile_path_area(self, parent: ttk.Frame, row: int):
        """创建Makefile路径显示区域"""
        makefile_frame = ttk.LabelFrame(parent, text="Makefile路径", padding="5")
        makefile_frame.grid(row=row, column=0, sticky="ew", pady=5)
        makefile_frame.columnconfigure(1, weight=1)
        
        # MVCU makefile路径
        self.mvcu_makefile_var = tk.StringVar(value="-")
        self._create_makefile_display(makefile_frame, "MVCU makefile:", 0, self.mvcu_makefile_var)
        
        # SVCU makefile路径
        self.svcu_makefile_var = tk.StringVar(value="-")
        self._create_makefile_display(makefile_frame, "SVCU makefile:", 1, self.svcu_makefile_var)
    
    def _create_makefile_display(self, parent: ttk.Frame, label_text: str, row: int, text_var: tk.StringVar):
        """创建makefile路径显示行"""
        ttk.Label(parent, text=label_text).grid(row=row, column=0, padx=5, sticky="w")
        ttk.Label(parent, textvariable=text_var).grid(row=row, column=1, padx=5, sticky="ew")
    
    def _create_log_area(self, parent: ttk.Frame, row: int):
        """创建日志显示区域"""
        log_frame = ttk.LabelFrame(parent, text="操作日志", padding="5")
        log_frame.grid(row=row, column=0, sticky="nsew", pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            font=("Consolas", 9),
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 配置日志颜色标签
        self._setup_log_tags()
    
    def _setup_log_tags(self):
        """设置日志文本标签"""
        tag_configs = {
            "info": {"foreground": "black"},
            "error": {"foreground": "red"},
            "success": {"foreground": "green"},
            "warning": {"foreground": "orange"},
            "debug": {"foreground": "gray"}
        }
        
        for tag, config in tag_configs.items():
            self.log_text.tag_configure(tag, **config)
    
    def _create_button_area(self, parent: ttk.Frame, row: int):
        """创建按钮区域"""
        btn_frame = ttk.Frame(parent, padding="5")
        btn_frame.grid(row=row, column=0, sticky="e", pady=10)
        
        # 退出按钮
        exit_btn = ttk.Button(btn_frame, text="退出", command=self.root.destroy)
        exit_btn.grid(row=0, column=0, padx=5)
        
        # 编译按钮
        self.compile_btn = ttk.Button(
            btn_frame, 
            text="开始编译", 
            command=self._start_compile,
            style="Accent.TButton"
        )
        self.compile_btn.grid(row=0, column=1, padx=5)
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        status_bar.grid(row=1, column=0, sticky="ew")
    
    def _initialize_logging(self):
        """初始化日志"""
        self._log("VCU编译器已启动，请选择源路径")
        if self.mvcu_path and self.svcu_path:
            self._log(f"MVCU路径: {self.mvcu_path}")
            self._log(f"SVCU路径: {self.svcu_path}")
    
    def _log(self, message: str, level: str = "info"):
        """
        向日志文本框添加消息
        
        Args:
            message: 日志消息
            level: 日志级别 (info, error, success, warning, debug)
        """
        # 自动判断日志级别
        if level == "info":
            if any(keyword in message for keyword in ["错误", "失败", "异常"]):
                level = "error"
            elif "警告" in message:
                level = "warning"
            elif any(keyword in message for keyword in ["成功", "完成"]):
                level = "success"
        
        # 格式化消息
        if not message.startswith("["):
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
        else:
            formatted_message = message
        
        # 更新日志文本框
        def update_log():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, formatted_message + "\n", level)
            self.log_text.config(state=tk.DISABLED)
            self.log_text.see(tk.END)
        
        if threading.current_thread() is threading.main_thread():
            update_log()
        else:
            self.root.after(0, update_log)
    
    def _browse_path(self):
        """浏览选择源路径"""
        # 支持选择文件夹或文件
        path = filedialog.askdirectory(title="选择源目录")
        if not path:
            path = filedialog.askopenfilename(
                title="选择源文件",
                filetypes=[("所有文件", "*.*"), ("C文件", "*.c"), ("头文件", "*.h")]
            )
        
        if path:
            self.path_var.set(path)
            self._log(f"已选择源路径: {path}")
            
            # 自动检测VCU类型
            self._detect_vcu_type(path)
    
    def _detect_vcu_type(self, path: str):
        """检测VCU类型"""
        filename = Path(path).stem.lower()
        detected_type = None
        
        for vcu_key in self.VCU_TYPES:
            if vcu_key in filename:
                detected_type = self.VCU_TYPES[vcu_key]['name']
                break
        
        if detected_type:
            self._log(f"检测到{detected_type}项目", "success")
        else:
            self._log("未能自动检测VCU类型，请确认文件名包含mvcu或svcu", "warning")
    
    def update_compiler_paths(self):
        """更新编译器路径"""
        if not self.update_path_function:
            self._log("更新路径功能不可用", "error")
            return
        
        # 禁用更新按钮并更新状态
        self.update_path_btn.config(state=tk.DISABLED)
        self.path_status_var.set("编译器路径状态: 正在更新...")
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        self._log("开始更新makefile中编译器路径...")
        
        # 在新线程中执行更新
        def update_thread():
            try:
                results = self.update_path_function(self._log)
                self._process_path_update_results(results)
            except Exception as e:
                self._log(f"更新路径过程中出错: {e}", "error")
                self.root.after(0, lambda: self._update_ui_after_path_update(False))
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def _process_path_update_results(self, results: List[Dict[str, Any]]):
        """处理路径更新结果"""
        if not results:
            self.root.after(0, lambda: self._update_ui_after_path_update(False))
            return
        
        success = all(item.get("success", False) for item in results)
        
        # 更新makefile路径显示
        for item in results:
            if item.get("success") and item.get("path"):
                if item["type"] == "MVCU":
                    self.mvcu_makefile_var.set(item["path"])
                elif item["type"] == "SVCU":
                    self.svcu_makefile_var.set(item["path"])
        
        # 更新MSYS profile
        self._update_msys_profile()
        
        # 更新UI
        self.root.after(0, lambda: self._update_ui_after_path_update(success))
    
    def _update_msys_profile(self):
        """更新MSYS profile文件"""
        if not self.importer.update_msys_profile:
            self._log("无法更新MSYS路径：函数不可用", "warning")
            return
        
        try:
            success, mvcu_path, svcu_path = self.importer.update_msys_profile()
            if success and mvcu_path and svcu_path:
                self.mvcu_path = mvcu_path
                self.svcu_path = svcu_path
                self.root.after(0, self._update_path_display)
                self._log(f"MSYS路径已更新\nMVCU路径: {mvcu_path}\nSVCU路径: {svcu_path}", "success")
            else:
                self._log("MSYS路径更新失败", "warning")
        except Exception as e:
            self._log(f"更新MSYS路径失败: {e}", "error")
    
    def _update_path_display(self):
        """更新路径显示"""
        if hasattr(self, 'mvcu_path_var') and self.mvcu_path:
            self.mvcu_path_var.set(self.mvcu_path)
        if hasattr(self, 'svcu_path_var') and self.svcu_path:
            self.svcu_path_var.set(self.svcu_path)
    
    def _update_ui_after_path_update(self, success: bool):
        """更新完路径后更新UI状态"""
        self.update_path_btn.config(state=tk.NORMAL)
        
        if success:
            self.path_status_var.set("编译器路径状态: 已更新")
            self._log("编译器路径更新成功", "success")
        else:
            self.path_status_var.set("编译器路径状态: 更新失败")
            self._log("编译器路径更新失败", "error")
    
    def _start_compile(self):
        """开始编译过程"""
        source_path = self.path_var.get().strip()
        
        # 输入验证
        if not source_path:
            messagebox.showerror("错误", "请先选择源路径")
            return
        
        if not Path(source_path).exists():
            messagebox.showerror("错误", "源路径不存在")
            return
        
        # 禁用编译按钮并更新状态
        self.compile_btn.config(state=tk.DISABLED)
        self.status_var.set("正在编译...")
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中执行编译
        threading.Thread(
            target=self._compile_process, 
            args=(source_path,), 
            daemon=True
        ).start()
    
    def _compile_process(self, source_path: str):
        """编译处理过程"""
        try:
            # 检测VCU类型
            vcu_info = self._get_vcu_info(source_path)
            if not vcu_info:
                return
            
            # 准备编译环境
            if not self._prepare_compile_environment(source_path, vcu_info):
                return
            
            # 检查模块
            self._check_modules(vcu_info['code'])
            
            # 启动MSYS
            self._launch_msys(vcu_info)
            
            # 编译完成
            self._compile_done(True, vcu_info['code'])
            
        except Exception as e:
            self._log(f"编译过程中出现异常: {e}", "error")
            messagebox.showerror("错误", f"编译过程中出现异常: {e}")
            self._compile_done(False)
    
    def _get_vcu_info(self, source_path: str) -> Optional[Dict[str, str]]:
        """获取VCU信息"""
        source_name = Path(source_path).stem.lower()
        self._log(f"处理源: {Path(source_path).stem}")
        
        for vcu_key, vcu_info in self.VCU_TYPES.items():
            if vcu_key in source_name:
                self._log(f"检测到{vcu_info['name']}类型", "success")
                return vcu_info
        
        self._log(f"错误: 文件名称未包含mvcu或svcu，无法识别", "error")
        messagebox.showerror("错误", f"文件名称未包含mvcu或svcu，无法识别")
        self._compile_done(False)
        return None
    
    def _prepare_compile_environment(self, source_path: str, vcu_info: Dict[str, str]) -> bool:
        """准备编译环境"""
        try:
            # 创建目标文件夹
            script_dir = get_application_path()
            dest_folder = Path(script_dir) / "VCU_compile - selftest" / vcu_info['folder'] / "src"
            dest_folder.mkdir(parents=True, exist_ok=True)
            
            self._log(f"目标文件夹: {dest_folder}")
            
            # 设置环境变量
            os.environ["MSYS_FLAG"] = vcu_info['code']
            self._log(f"设置MSYS_FLAG={vcu_info['code']}")
            
            # 复制文件
            return self._copy_source_files(source_path, dest_folder)
            
        except Exception as e:
            self._log(f"准备编译环境失败: {e}", "error")
            return False
    
    def _copy_source_files(self, source_path: str, dest_folder: Path) -> bool:
        """复制源文件"""
        self._log("开始复制文件...")
        
        try:
            source_path_obj = Path(source_path)
            
            if source_path_obj.is_dir():
                # 复制目录
                self._log(f"复制目录 {source_path} 到 {dest_folder}")
                result = subprocess.run([
                    "robocopy", str(source_path_obj), str(dest_folder),
                    "/MIR", "/NFL", "/NDL", "/NJH", "/NC", "/NJS", "/NP"
                ], capture_output=True, text=True)
                
                # robocopy返回值大于等于8表示错误
                if result.returncode >= 8:
                    self._log(f"文件复制失败: {result.stderr}", "error")
                    return False
                else:
                    self._log("目录复制成功", "success")
            else:
                # 复制单个文件
                self._log(f"复制文件 {source_path} 到 {dest_folder}")
                shutil.copy2(source_path_obj, dest_folder / source_path_obj.name)
                self._log("文件复制成功", "success")
            
            return True
            
        except Exception as e:
            self._log(f"文件复制失败: {e}", "error")
            messagebox.showerror("错误", f"文件复制失败: {e}")
            return False
    
    def _check_modules(self, vcu_code: str):
        """检查模块"""
        if not self.importer.check_modules_in_makefile:
            self._log("无法进行模块检查，需要重新运行程序", "warning")
            return
        
        try:
            self._log("检查模块是否都包含在makefile中...")
            self.importer.check_modules_in_makefile(vcu_code)
            self._log("完成模块检查", "success")
        except Exception as e:
            self._log(f"模块检查过程中出错: {e}", "error")
    
    def _launch_msys(self, vcu_info: Dict[str, str]):
        """启动MSYS"""
        resource_dir = get_resource_path()
        msys_bat_path = Path(resource_dir) / "MSYS-1.0.10-selftest" / "1.0" / "msys.bat"
        
        if msys_bat_path.exists():
            self._log(f"启动MSYS: {msys_bat_path}")
            try:
                subprocess.Popen(["cmd", "/c", "start", "", str(msys_bat_path)])
                self._log("MSYS已启动", "success")
                
                # 显示将要使用的路径
                if vcu_info['code'] == "m" and self.mvcu_path:
                    self._log(f"MSYS将使用MVCU路径: {self.mvcu_path}")
                elif vcu_info['code'] == "s" and self.svcu_path:
                    self._log(f"MSYS将使用SVCU路径: {self.svcu_path}")
                    
            except Exception as e:
                self._log(f"启动MSYS失败: {e}", "error")
        else:
            self._log(f"找不到MSYS批处理文件: {msys_bat_path}", "error")
            messagebox.showwarning("警告", f"找不到MSYS批处理文件: {msys_bat_path}")
    
    def _compile_done(self, success: bool, vcu_code: Optional[str] = None):
        """编译完成后的处理"""
        self.current_vcu_type = vcu_code
        self.root.after(0, lambda: self._update_ui_after_compile(success))
    
    def _update_ui_after_compile(self, success: bool):
        """更新编译完成后的UI状态"""
        self.compile_btn.config(state=tk.NORMAL)
        
        if success:
            self.status_var.set("编译完成")
            self._log("编译过程完成", "success")
            self._open_output_folder()
        else:
            self.status_var.set("编译失败")
            self._log("编译过程失败", "error")
    
    def _open_output_folder(self):
        """打开输出文件夹"""
        if not self.current_vcu_type:
            return
        
        try:
            script_dir = get_application_path()
            folder_name = "dev_kernel_mvcu" if self.current_vcu_type == "m" else "dev_kernel_svcu"
            output_dir = Path(script_dir) / "VCU_compile - selftest" / folder_name / "build" / "out"
            
            if output_dir.exists() and self.importer.archive_output_files:
                archived_dir = self.importer.archive_output_files(str(output_dir))
                self._log(f"输出文件已归档到: {archived_dir}", "success")
                
                # 打开归档文件夹
                if Path(archived_dir).exists():
                    os.startfile(archived_dir)
                    self._log("已打开输出文件夹", "success")
            else:
                self._log("输出目录不存在或归档功能不可用", "warning")
                
        except Exception as e:
            self._log(f"打开输出文件夹失败: {e}", "error")


class VcuCompilerApp:
    """VCU编译器应用程序类"""
    
    def __init__(self):
        self.root = None
        self.ui = None
    
    def run(self, update_path_function: Optional[Callable] = None, 
            mvcu_path: Optional[str] = None, svcu_path: Optional[str] = None):
        """
        运行应用程序
        
        Args:
            update_path_function: 更新路径的回调函数
            mvcu_path: MVCU路径
            svcu_path: SVCU路径
        """
        try:
            self.root = tk.Tk()
            
            # 设置应用程序图标（如果存在）
            self._set_app_icon()
            
            # 创建UI
            self.ui = VcuCompilerUI(
                self.root, 
                update_path_function, 
                mvcu_path, 
                svcu_path
            )
            
            # 设置关闭事件处理
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # 启动主循环
            self.root.mainloop()
            
        except Exception as e:
            logger.error(f"应用程序启动失败: {e}")
            messagebox.showerror("启动错误", f"应用程序启动失败: {e}")
    
    def _set_app_icon(self):
        """设置应用程序图标"""
        try:
            # 尝试设置图标（如果图标文件存在）
            icon_path = Path(get_resource_path()) / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            # 图标设置失败不影响程序运行
            pass
    
    def _on_closing(self):
        """应用程序关闭事件处理"""
        try:
            # 可以在这里添加保存设置等逻辑
            self.root.destroy()
        except Exception as e:
            logger.error(f"应用程序关闭时出错: {e}")


def main():
    """主函数"""
    try:
        # 设置DPI感知（Windows）
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (ImportError, AttributeError, OSError):
            pass
        
        # 创建并运行应用程序
        app = VcuCompilerApp()
        app.run()
        
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        messagebox.showerror("程序错误", f"程序运行出错: {e}")


if __name__ == "__main__":
    main()