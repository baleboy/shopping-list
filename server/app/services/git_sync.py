import subprocess
from app.config import settings


def git_pull() -> bool:
    try:
        subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=settings.data_dir,
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def git_push(message: str = "Update lists") -> bool:
    try:
        subprocess.run(
            ["git", "add", "."],
            cwd=settings.data_dir,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=settings.data_dir,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "push"],
            cwd=settings.data_dir,
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError:
        return False
