#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""路径配置测试脚本"""

import os
import sys

# 导入路径函数
from main import get_application_path, get_resource_path

def test_paths():
    """测试所有路径配置"""
    print("="*60)
    print("路径配置测试")
    print("="*60)
    
    # 基本路径信息
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    print(f"脚本文件: {__file__}")
    print(f"是否为打包状态: {getattr(sys, 'frozen', False)}")
    
    print("\n" + "-"*40)
    print("应用程序路径测试")
    print("-"*40)
    
    try:
        app_path = get_application_path()
        print(f"应用程序路径: {app_path}")
        print(f"路径是否存在: {os.path.exists(app_path)}")
        
        if os.path.exists(app_path):
            print("应用程序目录内容:")
            for item in sorted(os.listdir(app_path)):
                item_path = os.path.join(app_path, item)
                item_type = "[目录]" if os.path.isdir(item_path) else "[文件]"
                print(f"  {item_type} {item}")
                
    except Exception as e:
        print(f"获取应用程序路径失败: {e}")
    
    print("\n" + "-"*40)
    print("资源路径测试")
    print("-"*40)
    
    try:
        resource_path = get_resource_path()
        print(f"资源路径: {resource_path}")
        print(f"路径是否存在: {os.path.exists(resource_path)}")
        
        # 测试关键资源目录
        key_resources = ["GCC", "CW", "MSYS-1.0.10-selftest", "VCU_compile - selftest"]
        
        print("\n关键资源目录检查:")
        for resource in key_resources:
            res_path = get_resource_path(resource)
            exists = os.path.exists(res_path)
            status = "✓" if exists else "✗"
            print(f"  {status} {resource}: {res_path}")
            
            if exists and os.path.isdir(res_path):
                # 显示子目录（仅第一级）
                try:
                    items = os.listdir(res_path)[:5]  # 限制显示前5个
                    if items:
                        for item in items:
                            item_path = os.path.join(res_path, item)
                            item_type = "[目录]" if os.path.isdir(item_path) else "[文件]"
                            print(f"    {item_type} {item}")
                        if len(os.listdir(res_path)) > 5:
                            print(f"    ... 还有 {len(os.listdir(res_path)) - 5} 个项目")
                except PermissionError:
                    print("    无法访问目录内容")
                    
    except Exception as e:
        print(f"获取资源路径失败: {e}")
    
    print("\n" + "-"*40)
    print("编译器路径测试")
    print("-"*40)
    
    try:
        # 测试编译器路径
        gcc_path = get_resource_path("GCC", "bin")
        cw_path = get_resource_path("CW", "ColdFire_Tools", "Command_Line_Tools")
        
        print(f"GCC路径: {gcc_path}")
        print(f"GCC存在: {os.path.exists(gcc_path)}")
        
        print(f"CW路径: {cw_path}")
        print(f"CW存在: {os.path.exists(cw_path)}")
        
        # 查找具体的编译器可执行文件
        if os.path.exists(gcc_path):
            gcc_files = [f for f in os.listdir(gcc_path) if f.endswith('.exe')]
            print(f"GCC可执行文件: {gcc_files[:3]}...")  # 显示前3个
            
        if os.path.exists(cw_path):
            cw_files = [f for f in os.listdir(cw_path) if f.endswith('.exe')]
            print(f"CW可执行文件: {cw_files[:3]}...")  # 显示前3个
            
    except Exception as e:
        print(f"测试编译器路径失败: {e}")
    
    print("\n" + "-"*40)
    print("MSYS路径测试")
    print("-"*40)
    
    try:
        msys_path = get_resource_path("MSYS-1.0.10-selftest")
        print(f"MSYS路径: {msys_path}")
        print(f"MSYS存在: {os.path.exists(msys_path)}")
        
        if os.path.exists(msys_path):
            msys_bat = os.path.join(msys_path, "1.0", "msys.bat")
            print(f"MSYS批处理文件: {msys_bat}")
            print(f"批处理文件存在: {os.path.exists(msys_bat)}")
            
            profile_path = os.path.join(msys_path, "1.0", "etc", "profile")
            print(f"Profile文件: {profile_path}")
            print(f"Profile文件存在: {os.path.exists(profile_path)}")
            
    except Exception as e:
        print(f"测试MSYS路径失败: {e}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    test_paths() 