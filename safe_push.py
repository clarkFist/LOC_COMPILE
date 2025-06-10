import subprocess
import sys
import os
from pathlib import Path


def run_cmd(command):
    """运行命令并打印输出，出错时抛出异常"""
    result = subprocess.run(command, shell=True, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        # 传递错误输出到异常中
        error = subprocess.CalledProcessError(result.returncode, command)
        error.output = result.stdout  # 保存错误输出
        raise error
    return result


def find_git_repo():
    """查找git仓库目录"""
    current_dir = Path.cwd()
    
    # 首先检查当前目录
    if (current_dir / '.git').exists():
        return current_dir
    
    # 检查父目录
    for parent in current_dir.parents:
        if (parent / '.git').exists():
            return parent
    
    # 检查子目录（只检查一级子目录）
    for item in current_dir.iterdir():
        if item.is_dir() and (item / '.git').exists():
            return item
    
    # 特别检查常见的项目结构
    possible_dirs = [
        current_dir / current_dir.name,  # 同名子目录
        current_dir / 'src',
        current_dir / 'project',
    ]
    
    for dir_path in possible_dirs:
        if dir_path.exists() and (dir_path / '.git').exists():
            return dir_path
    
    return None


def ensure_in_git_repo():
    """确保在git仓库中，如果不在则尝试切换到正确目录"""
    try:
        # 先尝试直接检查
        subprocess.run("git rev-parse --is-inside-work-tree", 
                      shell=True, check=True,
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"✓ 当前目录已是git仓库: {Path.cwd()}")
        return True
    except subprocess.CalledProcessError:
        print(f"⚠ 当前目录不是git仓库: {Path.cwd()}")
        
        # 尝试查找git仓库
        git_repo = find_git_repo()
        if git_repo:
            print(f"✓ 找到git仓库: {git_repo}")
            os.chdir(git_repo)
            print(f"✓ 已切换到git仓库目录: {Path.cwd()}")
            return True
        else:
            print("❌ 错误：未找到git仓库！")
            print("请确保以下之一：")
            print("  1. 在git仓库目录中运行脚本")
            print("  2. 在包含git仓库子目录的父目录中运行脚本")
            print("  3. 先初始化git仓库 (git init)")
            return False


def has_changes():
    """检查是否有需要提交的更改"""
    result = subprocess.run("git status --porcelain", shell=True,
                           stdout=subprocess.PIPE, text=True)
    return bool(result.stdout.strip())


def safe_push(message="更新脚本快速更新"):
    """安全地将本地更改推送到远程仓库"""
    try:
        # 确保在git仓库中
        if not ensure_in_git_repo():
            return
        
        print("📥 正在拉取最新代码...")
        # 拉取最新代码，先处理可能的冲突
        try:
            run_cmd("git pull --rebase")
        except subprocess.CalledProcessError as e:
            # 获取实际的错误输出
            error_output = getattr(e, 'output', str(e))
            if "unstaged changes" in error_output or "uncommitted changes" in error_output or "cannot pull with rebase" in error_output:
                print("⚠ 检测到未提交的更改，先进行提交...")
                if has_changes():
                    run_cmd("git add -A")
                    run_cmd(f"git commit -m \"{message}\"")
                    print("✓ 更改已提交，重新尝试拉取...")
                    try:
                        run_cmd("git pull --rebase")
                    except subprocess.CalledProcessError:
                        print("⚠ rebase失败，尝试普通pull...")
                        run_cmd("git pull")
                else:
                    print("⚠ 尝试使用stash处理...")
                    run_cmd("git stash")
                    run_cmd("git pull --rebase")
                    run_cmd("git stash pop")
            else:
                raise
        
        # 检查是否还有新的更改需要提交
        if has_changes():
            print("📝 发现新的更改，正在提交...")
            run_cmd("git add -A")
            run_cmd(f"git commit -m \"{message}\"")
        else:
            print("✓ 没有新的更改需要提交")
        
        print("📤 正在推送到远程仓库...")
        run_cmd("git push")
        print("✅ 推送完成！")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
        print("请检查网络连接和git配置")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")


if __name__ == "__main__":
    commit_message = " ".join(sys.argv[1:]) or "更新脚本快速更新"
    print(f"🚀 开始安全推送，提交信息: {commit_message}")
    safe_push(commit_message)
