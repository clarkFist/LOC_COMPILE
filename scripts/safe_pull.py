import subprocess
import sys
import time

MAX_ATTEMPTS = 100
DELAY_SECONDS = 1


def safe_pull():
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True,
        ).strip()
    except subprocess.CalledProcessError as exc:
        print(f"Failed to determine current branch: {exc}")
        sys.exit(1)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(f"Attempt {attempt} to clean, fetch and reset...")
            # Discard any local changes to ensure a clean state
            subprocess.run(["git", "reset", "--hard"], check=True)
            subprocess.run(["git", "clean", "-fd"], check=True)

            subprocess.run(["git", "fetch", "--all"], check=True)
            subprocess.run([
                "git",
                "reset",
                "--hard",
                f"origin/{branch}",
            ], check=True)
            print("Pull successful.")
            return
        except subprocess.CalledProcessError as exc:
            print(f"Pull failed on attempt {attempt}: {exc}")
            time.sleep(DELAY_SECONDS)
    print("All pull attempts failed.")
    sys.exit(1)


if __name__ == "__main__":
    safe_pull()
