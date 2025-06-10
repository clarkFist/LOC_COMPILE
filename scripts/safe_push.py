import subprocess
import sys
import time
import os

MAX_ATTEMPTS = 100
DELAY_SECONDS = 1


def get_loc_compile_path():
    """获取LOC_COMPILE目录的路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    # 直接使用parent_dir，因为.git目录就在这里
    loc_compile_path = parent_dir
    
    if not os.path.exists(loc_compile_path):
        print(f"错误：找不到LOC_COMPILE目录: {loc_compile_path}")
        sys.exit(1)
    
    git_dir = os.path.join(loc_compile_path, ".git")
    if not os.path.exists(git_dir):
        print(f"错误：LOC_COMPILE目录不是Git仓库: {loc_compile_path}")
        sys.exit(1)
    
    return loc_compile_path


def safe_push(message: str = "更新脚本快速更新") -> None:
    # 获取LOC_COMPILE目录路径
    repo_path = get_loc_compile_path()
    print(f"切换到Git仓库目录: {repo_path}")
    
    # 保存当前工作目录
    original_cwd = os.getcwd()
    
    try:
        # 切换到LOC_COMPILE目录
        os.chdir(repo_path)
        
        # 添加所有更改到暂存区
        subprocess.run(["git", "add", "-A"], check=True)
        result = subprocess.run(["git", "diff", "--cached", "--quiet"])
        has_changes = result.returncode != 0
        
        if has_changes:
            subprocess.run(["git", "commit", "-m", message], check=True)
            print(f"已提交更改: {message}")
        else:
            print("没有需要提交的更改。")
    except subprocess.CalledProcessError as exc:
        print(f"暂存或提交更改失败: {exc}")
        os.chdir(original_cwd)
        sys.exit(1)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(f"第 {attempt} 次尝试拉取并推送更改...")
            subprocess.run(["git", "pull", "--rebase"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("推送成功！")
            os.chdir(original_cwd)
            return
        except subprocess.CalledProcessError as exc:
            print(f"第 {attempt} 次推送失败: {exc}")
            time.sleep(DELAY_SECONDS)
    
    print("所有推送尝试都失败了。")
    os.chdir(original_cwd)
    sys.exit(1)


if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "更新脚本快速更新"
    safe_push(msg)
