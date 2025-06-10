import subprocess
import sys


def run_cmd(command):
    """运行命令并打印输出，出错时抛出异常"""
    result = subprocess.run(command, shell=True, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command)
    return result


def has_changes():
    """检查是否有需要提交的更改"""
    result = subprocess.run("git status --porcelain", shell=True,
                           stdout=subprocess.PIPE, text=True)
    return bool(result.stdout.strip())


def safe_push(message="更新脚本快速更新"):
    """安全地将本地更改推送到远程仓库"""
    # 确保在git仓库中
    run_cmd("git rev-parse --is-inside-work-tree")

    # 拉取最新代码
    run_cmd("git pull --rebase")

    if not has_changes():
        print("没有需要提交的更改")
        return

    # 添加并提交
    run_cmd("git add -A")
    run_cmd(f"git commit -m \"{message}\"")

    # 推送到远端
    run_cmd("git push")


if __name__ == "__main__":
    commit_message = " ".join(sys.argv[1:]) or "更新脚本快速更新"
    safe_push(commit_message)
