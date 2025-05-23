#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext

import threading
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

# 导入必要的模块
try:
    from main import check_modules_in_makefile
except ImportError:
    # 如果在当前目录找不到，尝试从同级目录导入
    LOC_COMPILE_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(LOC_COMPILE_dir)
    try:
        from main import check_modules_in_makefile
    except ImportError:
        # 避免循环导入
        check_modules_in_makefile = None

# 避免循环导入update_msys_profile
update_msys_profile = None

class VcuCompilerUI:
    def __init__(self, root, update_path_function=None, mvcu_path=None, svcu_path=None):
        self.root = root
        self.root.title("VCU编译器")

        self.root.geometry("700x600")  # 默认尺寸

        self.root.minsize(600, 500)
        self.root.resizable(True, True)
        
        # 保存路径更新函数
        self.update_path_function = update_path_function
        
        # 保存路径信息
        self.mvcu_path = mvcu_path
        self.svcu_path = svcu_path
        
        # 尝试导入update_msys_profile
        global update_msys_profile
        if update_msys_profile is None:
            try:
                from main import update_msys_profile as ump
                update_msys_profile = ump
            except ImportError:
                pass
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TButton", font=("微软雅黑", 10))
        self.style.configure("TLabel", font=("微软雅黑", 10))
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建源路径选择区域
        path_frame = ttk.Frame(main_frame, padding="5")
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(path_frame, text="源路径:").pack(side=tk.LEFT, padx=5)
        
        self.path_var = tk.StringVar()
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_btn = ttk.Button(path_frame, text="浏览...", command=self.browse_path)
        browse_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加更新路径按钮
        path_update_frame = ttk.Frame(main_frame, padding="5")
        path_update_frame.pack(fill=tk.X, pady=5)
        
        self.update_path_btn = ttk.Button(path_update_frame, text="更新编译器路径", 
                                         command=self.update_compiler_paths)
        self.update_path_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加路径状态标签
        self.path_status_var = tk.StringVar()
        self.path_status_var.set("编译器路径状态: 未检查")
        path_status_label = ttk.Label(path_update_frame, textvariable=self.path_status_var)
        path_status_label.pack(side=tk.LEFT, padx=10)
        
        # 添加MSYS路径信息区域
        msys_path_frame = ttk.LabelFrame(main_frame, text="MSYS路径信息", padding="5")
        msys_path_frame.pack(fill=tk.X, pady=5)
        
        # MVCU路径
        mvcu_frame = ttk.Frame(msys_path_frame, padding="2")
        mvcu_frame.pack(fill=tk.X)
        ttk.Label(mvcu_frame, text="MVCU路径:").pack(side=tk.LEFT, padx=5)
        
        self.mvcu_path_var = tk.StringVar()
        self.mvcu_path_var.set(mvcu_path if mvcu_path else "未设置")
        ttk.Label(mvcu_frame, textvariable=self.mvcu_path_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # SVCU路径
        svcu_frame = ttk.Frame(msys_path_frame, padding="2")
        svcu_frame.pack(fill=tk.X)
        ttk.Label(svcu_frame, text="SVCU路径:").pack(side=tk.LEFT, padx=5)
        
        self.svcu_path_var = tk.StringVar()
        self.svcu_path_var.set(svcu_path if svcu_path else "未设置")
        ttk.Label(svcu_frame, textvariable=self.svcu_path_var).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 显示操作日志的文本框
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, width=70, height=15, font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 底部按钮区域
        btn_frame = ttk.Frame(main_frame, padding="5")
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.compile_btn = ttk.Button(btn_frame, text="开始编译", command=self.start_compile)
        self.compile_btn.pack(side=tk.RIGHT, padx=5)
        
        exit_btn = ttk.Button(btn_frame, text="退出", command=root.destroy)
        exit_btn.pack(side=tk.RIGHT, padx=5)
        
        # 状态条
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 初始化日志
        self.log("VCU编译器已启动，请选择源路径")
        if self.mvcu_path and self.svcu_path:
            self.log(f"MVCU路径: {self.mvcu_path}")
            self.log(f"SVCU路径: {self.svcu_path}")
        
        # 尝试自动更新路径
        if self.update_path_function:
            self.root.after(500, self.update_compiler_paths)
    
    def log(self, message, is_error=False):
        """向日志文本框添加消息"""
        tag = "error" if is_error else "info"

        if "info" not in self.log_text.tag_names():
            self.log_text.tag_configure("info", foreground="black")
        if "error" not in self.log_text.tag_names():
            self.log_text.tag_configure("error", foreground="red")

        if message.startswith("["):
            formatted = message
        else:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted = f"[{timestamp}] {message}"
        self.log_text.insert(tk.END, formatted + "\n", tag)
        self.log_text.see(tk.END)  # 滚动到最新行

    
    def update_compiler_paths(self):
        """更新编译器路径"""
        if not self.update_path_function:
            self.log("更新路径功能不可用", True)
            return
        
        # 禁用更新按钮
        self.update_path_btn.config(state=tk.DISABLED)
        self.path_status_var.set("编译器路径状态: 正在更新...")
        
        # 清空日志区域
        self.log_text.delete(1.0, tk.END)
        self.log("开始更新makefile中编译器路径...")
        
        # 创建回调函数来处理日志
        def path_update_callback(message, is_error=False):
            # 在UI线程中更新UI
            self.root.after(0, lambda: self.log(message, is_error))
        
        # 在新线程中运行路径更新
        threading.Thread(
            target=self._run_path_update, 
            args=(path_update_callback,), 
            daemon=True
        ).start()
    
    def _run_path_update(self, callback):
        """在线程中运行路径更新"""
        try:
            results = self.update_path_function(callback)
            
            # 处理结果
            success = all(item["success"] for item in results) if results else False
            
            # 在UI线程中更新UI
            self.root.after(0, lambda: self._update_ui_after_path_update(success))
            
            # 更新MSYS profile文件并获取路径
            global update_msys_profile
            if update_msys_profile:
                try:
                    success, mvcu_path, svcu_path = update_msys_profile()
                    if success and mvcu_path and svcu_path:
                        self.mvcu_path = mvcu_path
                        self.svcu_path = svcu_path
                        # 在UI线程中更新路径显示
                        self.root.after(0, lambda: self._update_path_display())
                        callback(f"MSYS路径已更新。\nMVCU路径: {mvcu_path}\nSVCU路径: {svcu_path}")
                except Exception as e:
                    callback(f"更新MSYS路径失败: {e}", True)
            else:
                callback("无法更新MSYS路径：函数不可用", True)
            
        except Exception as e:
            error_msg = f"更新路径过程中出错: {e}"
            callback(error_msg, True)
            self.root.after(0, lambda: self._update_ui_after_path_update(False))
    
    def _update_path_display(self):
        """更新路径显示"""
        if self.mvcu_path:
            self.mvcu_path_var.set(self.mvcu_path)
        if self.svcu_path:
            self.svcu_path_var.set(self.svcu_path)
    
    def _update_ui_after_path_update(self, success):
        """更新完路径后更新UI状态"""
        self.update_path_btn.config(state=tk.NORMAL)
        
        if success:
            self.path_status_var.set("编译器路径状态: 已更新")
            self.log("编译器路径更新成功")
            
            # 显示当前的MSYS路径信息
            if self.mvcu_path and self.svcu_path:
                self.log("当前使用的MSYS路径:")
                self.log(f"MVCU路径: {self.mvcu_path}")
                self.log(f"SVCU路径: {self.svcu_path}")
                
                # 更新路径显示
                self._update_path_display()
        else:
            self.path_status_var.set("编译器路径状态: 更新失败")
            self.log("编译器路径更新失败", True)
    
    def browse_path(self):
        """浏览选择源路径"""
        path = filedialog.askdirectory(title="选择源目录") or filedialog.askopenfilename(title="选择源文件")
        if path:
            self.path_var.set(path)
            self.log(f"已选择源路径: {path}")
    
    def start_compile(self):
        """开始编译过程"""
        source_path = self.path_var.get().strip()
        
        if not source_path:
            messagebox.showerror("错误", "请先选择源路径")
            return
        
        if not os.path.exists(source_path):
            messagebox.showerror("错误", "源路径不存在")
            return
        
        # 禁用编译按钮，避免重复操作
        self.compile_btn.config(state=tk.DISABLED)
        self.status_var.set("正在编译...")

        # 清空日志，开始新的编译
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中运行编译过程，避免UI卡顿
        threading.Thread(target=self.compile_process, args=(source_path,), daemon=True).start()
    
    def compile_process(self, source_path):
        """编译处理过程，与auto_compile.py中的逻辑相同"""
        try:
            # 获取当前脚本所在目录
            script_dir = get_application_path()
            
            # 首先确保我们有最新的路径信息
            global update_msys_profile
            if update_msys_profile:
                try:
                    success, mvcu_path, svcu_path = update_msys_profile()
                    if success and mvcu_path and svcu_path:
                        self.mvcu_path = mvcu_path
                        self.svcu_path = svcu_path
                        # 在UI线程中更新路径显示
                        self.root.after(0, lambda: self._update_path_display())
                        self.log(f"MSYS路径已更新。\nMVCU路径: {mvcu_path}\nSVCU路径: {svcu_path}")
                except Exception as e:
                    self.log(f"更新MSYS路径失败: {e}", True)
            
            # 获取文件名（不含扩展名）
            source_name = os.path.splitext(os.path.basename(source_path))[0]
            self.log(f"处理源: {source_name}")
            
            # 调试信息
            self.log(f"正在检查文件名中是否包含MVCU或SVCU。文件名: {source_name}")
            
            # 检查源名称是否包含 "mvcu" 或 "svcu"（不区分大小写）
            source_name_lower = source_name.lower()
            vcu_type = None
            if "mvcu" in source_name_lower:
                vcu_type = "m"
                dest_folder = os.path.join(script_dir, "VCU_compile - selftest", "dev_kernel_mvcu", "src")
                self.log(f"检测到MVCU类型 (在 '{source_name}' 中找到 'mvcu')")
                self.log(f"将使用路径: {self.mvcu_path}")
            elif "svcu" in source_name_lower:
                vcu_type = "s"
                dest_folder = os.path.join(script_dir, "VCU_compile - selftest", "dev_kernel_svcu", "src")
                self.log(f"检测到SVCU类型 (在 '{source_name}' 中找到 'svcu')")
                self.log(f"将使用路径: {self.svcu_path}")
            
            # 如果没有找到匹配的类型，则退出脚本
            if not vcu_type:
                self.log(f"错误: 文件名称 '{source_name}' 未包含 mvcu 或 svcu，无法辨认")
                messagebox.showerror("错误", f"文件名称 '{source_name}' 未包含 mvcu 或 svcu，无法辨认")
                self.compile_done(False)
                return
            
            # 检查目标路径是否存在，如果不存在则创建
            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)
                self.log(f"创建目标文件夹: {dest_folder}")
            
            # 设置 MSYS_FLAG 环境变量
            os.environ["MSYS_FLAG"] = vcu_type
            self.log(f"设置MSYS_FLAG={vcu_type}")
            
            # 使用 robocopy 复制文件
            self.log("开始复制文件...")
            
            # 如果是目录，复制整个目录内容
            if os.path.isdir(source_path):
                self.log(f"复制目录 {source_path} 到 {dest_folder}")
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
                    self.log("错误: 文件复制失败")
                    messagebox.showerror("错误", "文件复制失败")
                    self.compile_done(False)
                    return
                else:
                    self.log("文件复制成功")
            else:
                # 如果是单个文件，直接复制
                try:
                    self.log(f"复制文件 {source_path} 到 {dest_folder}")
                    shutil.copy2(source_path, dest_folder)
                    self.log("文件复制成功")
                except Exception as e:
                    self.log(f"错误: 文件复制失败。{e}")
                    messagebox.showerror("错误", f"文件复制失败: {e}")
                    self.compile_done(False)
                    return
            
            # 检查模块是否都在makefile中
            self.log("检查模块是否都包含在makefile中...")
            if check_modules_in_makefile:
                try:
                    check_modules_in_makefile(vcu_type)
                    self.log("完成模块检查")
                except Exception as e:
                    self.log(f"模块检查过程中出错: {e}")
            else:
                self.log("无法进行模块检查，需要重新运行程序")
            
            # 启动MSYS
            msys_bat_path = os.path.join(script_dir, "MSYS-1.0.10-selftest", "1.0", "msys.bat")
            if os.path.exists(msys_bat_path):
                self.log(f"启动MSYS: {msys_bat_path}")
                subprocess.Popen(["cmd", "/c", "start", "", msys_bat_path])
                self.log("MSYS已启动")

                # 保存vcu_type供编译完成后使用
                self.vcu_type = vcu_type
                
                if vcu_type == "m" and self.mvcu_path:
                    self.log(f"MSYS将使用MVCU路径: {self.mvcu_path}")
                elif vcu_type == "s" and self.svcu_path:
                    self.log(f"MSYS将使用SVCU路径: {self.svcu_path}")
            else:
                self.log(f"错误: 找不到MSYS批处理文件: {msys_bat_path}")
                messagebox.showwarning("警告", f"找不到MSYS批处理文件: {msys_bat_path}")
            
            # 编译完成
            self.compile_done(True)
            
        except Exception as e:
            self.log(f"错误: 处理过程中出现异常: {e}")
            messagebox.showerror("错误", f"处理过程中出现异常: {e}")
            self.compile_done(False)
    
    def compile_done(self, success=True):
        """编译完成后的处理"""
        # 在UI线程中更新UI
        self.root.after(0, lambda: self._update_ui_after_compile(success))
    
    def _update_ui_after_compile(self, success):
        """更新UI状态"""
        self.compile_btn.config(state=tk.NORMAL)
        
        if success:
            self.status_var.set("编译完成")
            self.log("编译过程完成")
            
            # 在编译成功后，打开对应的输出文件夹
            script_dir = get_application_path()
            if hasattr(self, 'vcu_type'):
                if self.vcu_type == "m":
                    output_dir = os.path.join(script_dir, "VCU_compile - selftest", "dev_kernel_mvcu", "build", "out")
                    if os.path.exists(output_dir):
                        self.log(f"打开MVCU输出文件夹: {output_dir}")
                        os.startfile(output_dir)
                elif self.vcu_type == "s":
                    output_dir = os.path.join(script_dir, "VCU_compile - selftest", "dev_kernel_svcu", "build", "out")
                    if os.path.exists(output_dir):
                        self.log(f"打开SVCU输出文件夹: {output_dir}")
                        os.startfile(output_dir)
        else:
            self.status_var.set("编译失败")
            self.log("编译过程失败")

def main():
    root = tk.Tk()
    app = VcuCompilerUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 
