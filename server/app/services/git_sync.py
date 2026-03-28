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
