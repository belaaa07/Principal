"""Placeholder swapper: swap downloaded exe on restart."""
from pathlib import Path
import shutil

def swap_executable(new_file: Path, current_file: Path) -> bool:
    try:
        backup = current_file.with_suffix(current_file.suffix + '.bak')
        if backup.exists():
            backup.unlink()
        if current_file.exists():
            current_file.rename(backup)
        shutil.move(str(new_file), str(current_file))
        return True
    except Exception:
        return False
