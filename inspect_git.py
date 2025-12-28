import subprocess
import os

def run(cmd):
    try:
        return subprocess.check_output(cmd, shell=True).decode().strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

print("--- HEAD COMMIT MSG ---")
print(run("git log -1 --pretty=%B"))
print("\n--- STATUS ---")
print(run("git status --porcelain"))
print("\n--- JUNK FILES ---")
print("last_commit_msg.txt: " + str(os.path.exists("last_commit_msg.txt")))
print("status.txt: " + str(os.path.exists("status.txt")))
