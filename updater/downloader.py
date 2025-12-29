"""Placeholder downloader for updates.
- download_file(url, target_path)
"""
from pathlib import Path
import urllib.request

def download_file(url: str, target_path: Path) -> bool:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url) as resp, open(target_path, 'wb') as f:
            f.write(resp.read())
        return True
    except Exception:
        return False
