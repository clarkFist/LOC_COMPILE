# 🔌 LOC_COMPILE API 文档

> 📘 **接口规范**: 核心API详细说明  
> 👨‍💻 **目标用户**: 开发者、集成人员  
> 📅 **版本**: v2.0  

---

## 📚 API 概览

LOC_COMPILE 提供了一套完整的API用于VCU编译器管理，主要包括：

- **路径管理API**: 处理应用程序和资源路径
- **编译器控制API**: 管理makefile和编译流程
- **UI组件API**: 图形界面组件和事件处理
- **环境配置API**: MSYS环境和系统配置

---

## 🛠️ 核心模块

### path_utils 模块

#### get_application_path()

```python
def get_application_path() -> str:
    """
    获取应用程序根路径
    
    Returns:
        str: 应用程序根目录的绝对路径
        
    Note:
        - 开发环境: 返回脚本所在目录
        - 打包环境: 返回可执行文件所在目录
        
    Examples:
        >>> import path_utils
        >>> app_path = path_utils.get_application_path()
        >>> print(app_path)
        'C:\\LOC_COMPILE'
    """
```

#### get_resource_path(relative_path="")

```python
def get_resource_path(relative_path: str = "") -> str:
    """
    获取资源文件路径
    
    Args:
        relative_path (str): 相对于资源根目录的路径
        
    Returns:
        str: 资源文件的绝对路径
        
    Examples:
        >>> gcc_path = path_utils.get_resource_path("GCC/bin")
        >>> cw_path = path_utils.get_resource_path("CW/ColdFire_Tools")
        >>> print(gcc_path)
        'C:\\LOC_COMPILE\\GCC\\bin'
    """
```

---

### main 模块

#### ensure_project_structure()

```python
def ensure_project_structure() -> None:
    """
    确保项目的基本目录结构在应用程序目录下正确存在
    
    Creates:
        - VCU_compile - selftest/
        - dev_kernel_mvcu/src/
        - dev_kernel_mvcu/build/out/
        - dev_kernel_svcu/src/
        - dev_kernel_svcu/build/out/
        
    Raises:
        Exception: 创建目录失败时抛出异常
        
    Examples:
        >>> import main
        >>> main.ensure_project_structure()
        创建项目根目录: C:\\LOC_COMPILE\\VCU_compile - selftest
    """
```

#### update_makefiles_with_correct_paths(callback=None)

```python
def update_makefiles_with_correct_paths(callback: Optional[Callable[[str, bool], None]] = None) -> List[Dict[str, Any]]:
    """
    更新makefile中的编译器路径为Windows格式的绝对路径
    
    Args:
        callback: 进度回调函数
            - message (str): 进度信息
            - is_error (bool): 是否为错误信息
            
    Returns:
        List[Dict]: 更新结果列表，每个元素包含:
        {
            "type": "MVCU" | "SVCU",
            "success": bool,
            "message": str,
            "path": str  # 仅成功时包含
        }
        
    Examples:
        >>> def progress_callback(msg, is_error=False):
        ...     print(f"{'ERROR' if is_error else 'INFO'}: {msg}")
        >>> results = main.update_makefiles_with_correct_paths(progress_callback)
        >>> all_success = all(r['success'] for r in results)
    """
```

#### update_msys_profile()

```python
def update_msys_profile() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    更新MSYS的profile文件，配置环境变量和路径
    
    Returns:
        Tuple[bool, str, str]: (成功标志, MVCU路径, SVCU路径)
        
    Examples:
        >>> success, mvcu_path, svcu_path = main.update_msys_profile()
        >>> if success:
        ...     print(f"MVCU路径: {mvcu_path}")
        ...     print(f"SVCU路径: {svcu_path}")
    """
```

#### process_in_console_mode(source_path)

```python
def process_in_console_mode(source_path: str) -> bool:
    """
    命令行模式下的项目处理逻辑
    
    Args:
        source_path (str): 源项目路径
        
    Returns:
        bool: 处理是否成功
        
    Process:
        1. 验证源路径存在性
        2. 识别VCU项目类型 (MVCU/SVCU)
        3. 复制源文件到目标目录
        4. 设置环境变量
        5. 启动MSYS编译环境
        
    Examples:
        >>> success = main.process_in_console_mode("C:\\Projects\\MVCU_v1.0")
        >>> if success:
        ...     print("项目处理成功")
    """
```

---

### vcu_compiler_ui 模块

#### VcuCompilerUI 类

```python
class VcuCompilerUI:
    """VCU编译器主界面类"""
    
    # 常量定义
    WINDOW_TITLE = "VCU编译器 v2.0"
    WINDOW_SIZE = "800x600"
    MIN_WINDOW_SIZE = (600, 500)
    
    # VCU类型映射
    VCU_TYPES = {
        'mvcu': {'code': 'm', 'name': 'MVCU', 'folder': 'dev_kernel_mvcu'},
        'svcu': {'code': 's', 'name': 'SVCU', 'folder': 'dev_kernel_svcu'}
    }
```

##### 构造方法

```python
def __init__(self, root: tk.Tk, 
             update_path_function: Optional[Callable] = None,
             mvcu_path: Optional[str] = None,
             svcu_path: Optional[str] = None) -> None:
    """
    初始化VCU编译器界面
    
    Args:
        root: Tk根窗口实例
        update_path_function: 更新makefile路径的回调函数
        mvcu_path: MSYS环境下MVCU的编译路径
        svcu_path: MSYS环境下SVCU的编译路径
    """
```

##### 核心方法

```python
def _log(self, message: str, level: str = "info") -> None:
    """
    向日志文本框添加消息
    
    Args:
        message: 日志消息
        level: 日志级别 ("info", "error", "success", "warning", "debug")
        
    Auto-detection:
        - "错误", "失败", "异常" → error
        - "警告" → warning  
        - "成功", "完成" → success
    """

def update_compiler_paths(self) -> None:
    """
    更新编译器路径配置
    
    Process:
        1. 禁用更新按钮
        2. 清空日志显示
        3. 在新线程中调用更新函数
        4. 处理更新结果
        5. 更新UI状态
    """

def _start_compile(self) -> None:
    """
    开始编译流程
    
    Validation:
        - 检查源路径是否选择
        - 验证VCU类型识别
        - 确认编译环境就绪
        
    Process:
        1. 准备编译环境
        2. 复制源文件
        3. 检查模块完整性
        4. 启动MSYS编译
    """
```

#### ModuleImporter 类

```python
class ModuleImporter:
    """模块导入管理器，负责动态导入main模块中的函数"""
    
    def __init__(self) -> None:
        """初始化并尝试导入必要的函数"""
        
    def _direct_import(self) -> bool:
        """直接导入策略"""
        
    def _path_based_import(self) -> bool:
        """基于路径的导入策略"""
        
    def _dynamic_import(self) -> bool:
        """动态导入策略"""
        
    def _use_backup_functions(self) -> None:
        """使用备用函数实现"""
```

---

## 🔄 事件处理

### 回调函数规范

#### 进度回调函数

```python
def progress_callback(message: str, is_error: bool = False) -> None:
    """
    进度回调函数规范
    
    Args:
        message: 进度信息或错误消息
        is_error: 是否为错误信息
        
    Usage:
        用于update_makefiles_with_correct_paths()等函数的进度反馈
    """
```

#### UI事件回调

```python
def ui_event_handler(event_type: str, data: Dict[str, Any]) -> None:
    """
    UI事件处理器规范
    
    Args:
        event_type: 事件类型 ("path_selected", "compile_started", etc.)
        data: 事件数据
        
    Events:
        - "path_selected": 用户选择了源路径
        - "compile_started": 编译开始
        - "compile_finished": 编译完成
        - "error_occurred": 发生错误
    """
```

---

## 📊 数据结构

### 编译结果结构

```python
CompileResult = TypedDict('CompileResult', {
    'success': bool,           # 编译是否成功
    'vcu_type': str,          # VCU类型 ("MVCU" | "SVCU")
    'output_path': str,       # 输出文件路径
    'duration': float,        # 编译耗时(秒)
    'errors': List[str],      # 错误信息列表
    'warnings': List[str]     # 警告信息列表
})
```

### 路径更新结果

```python
PathUpdateResult = TypedDict('PathUpdateResult', {
    'type': str,              # "MVCU" | "SVCU"
    'success': bool,          # 更新是否成功
    'message': str,           # 详细消息
    'path': str              # makefile路径 (可选)
})
```

### VCU项目信息

```python
VcuProjectInfo = TypedDict('VcuProjectInfo', {
    'type': str,              # "mvcu" | "svcu"
    'code': str,              # "m" | "s"
    'name': str,              # "MVCU" | "SVCU"
    'folder': str,            # "dev_kernel_mvcu" | "dev_kernel_svcu"
    'source_path': str,       # 源项目路径
    'dest_path': str         # 目标路径
})
```

---

## 🔧 扩展接口

### 自定义编译器支持

```python
class CompilerInterface:
    """编译器接口基类"""
    
    def detect_compiler(self, path: str) -> bool:
        """检测编译器是否存在"""
        raise NotImplementedError
        
    def update_config(self, config_path: str, compiler_path: str) -> bool:
        """更新编译器配置"""
        raise NotImplementedError
        
    def compile_project(self, project_path: str) -> CompileResult:
        """编译项目"""
        raise NotImplementedError

class GccCompiler(CompilerInterface):
    """GCC编译器实现"""
    pass

class ColdFireCompiler(CompilerInterface):
    """ColdFire编译器实现"""
    pass
```

### 插件系统接口

```python
class PluginInterface:
    """插件接口基类"""
    
    def get_name(self) -> str:
        """获取插件名称"""
        raise NotImplementedError
        
    def get_version(self) -> str:
        """获取插件版本"""
        raise NotImplementedError
        
    def initialize(self, context: Dict[str, Any]) -> None:
        """初始化插件"""
        raise NotImplementedError
        
    def execute(self, command: str, params: Dict[str, Any]) -> Any:
        """执行插件命令"""
        raise NotImplementedError
```

---

## 📋 使用示例

### 基本用法示例

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from main import update_makefiles_with_correct_paths, ensure_project_structure
from vcu_compiler_ui import VcuCompilerUI

def main():
    # 1. 确保项目结构
    ensure_project_structure()
    
    # 2. 更新编译器路径
    def progress_callback(msg, is_error=False):
        print(f"{'[ERROR]' if is_error else '[INFO]'} {msg}")
    
    results = update_makefiles_with_correct_paths(progress_callback)
    success = all(r['success'] for r in results)
    
    if success:
        print("编译器路径更新成功")
        
        # 3. 启动GUI
        root = tk.Tk()
        app = VcuCompilerUI(root, update_makefiles_with_correct_paths)
        root.mainloop()
    else:
        print("编译器路径更新失败")

if __name__ == '__main__':
    main()
```

### 命令行集成示例

```python
import sys
from main import process_in_console_mode

def batch_compile(project_paths):
    """批量编译多个项目"""
    results = []
    
    for project_path in project_paths:
        print(f"正在处理: {project_path}")
        success = process_in_console_mode(project_path)
        results.append({
            'path': project_path,
            'success': success
        })
    
    # 输出结果统计
    success_count = sum(1 for r in results if r['success'])
    print(f"批量编译完成: {success_count}/{len(results)} 成功")
    
    return results

# 使用示例
if __name__ == '__main__':
    projects = [
        "C:\\Projects\\MVCU_Project_v1.0",
        "C:\\Projects\\SVCU_Project_v2.0"
    ]
    batch_compile(projects)
```

---

## 🚨 错误处理

### 异常类型

```python
class LOCCompileError(Exception):
    """LOC_COMPILE基础异常类"""
    pass

class CompilerNotFoundError(LOCCompileError):
    """编译器未找到异常"""
    pass

class ProjectStructureError(LOCCompileError):
    """项目结构错误异常"""
    pass

class MSYSEnvironmentError(LOCCompileError):
    """MSYS环境错误异常"""
    pass
```

### 错误处理示例

```python
try:
    ensure_project_structure()
    results = update_makefiles_with_correct_paths()
except CompilerNotFoundError as e:
    print(f"编译器配置错误: {e}")
    # 处理编译器缺失的情况
except ProjectStructureError as e:
    print(f"项目结构错误: {e}")
    # 处理目录结构问题
except Exception as e:
    print(f"未知错误: {e}")
    # 通用错误处理
```

---

## 📞 技术支持

### API问题排查

1. **导入问题**
   - 检查模块路径是否正确
   - 验证Python版本兼容性
   - 确认依赖包已安装

2. **调用问题**
   - 验证参数类型和格式
   - 检查返回值处理
   - 查看异常信息

3. **性能问题**
   - 监控函数执行时间
   - 检查内存使用情况
   - 优化调用频率

### 获取帮助

- 📖 [用户指南](../user_guide/README.md) - 基本使用方法
- 🛠️ [开发者文档](../developer/README.md) - 开发指南
- 🔧 [故障排除](../troubleshooting/README.md) - 问题解决

---

*📅 最后更新: 2025年1月*  
*📘 API版本: v2.0* 