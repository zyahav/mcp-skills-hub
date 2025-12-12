
import sys
import os
from pathlib import Path

# Add the directory containing server.py to the python path
current_dir = Path.cwd()
sys.path.append(str(current_dir / "mcps/git-manager"))

try:
    import server
except ImportError as e:
    print(f"Error importing server: {e}")
    sys.exit(1)

def perform_real_commit():
    print(f"\n>>> Calling git_add_commit_push(message=None, push=True)...")
    try:
        # Utilizing the auto-message generation and default push behavior
        res = server.do_git_add_commit_push(message=None, worktree=None, push=True)
        print("RESULT:")
        print(res)
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    perform_real_commit()
