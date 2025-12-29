"""Manager that coordinates version checks, downloads, and staging."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .downloader import download_file
from .version_checker import (
    RemoteVersionInfo,
    fetch_remote_version_from_github,
    fetch_remote_version_from_json,
    is_remote_newer,
    read_local_version,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "update_config.json"


def _load_update_config() -> Dict[str, Any]:
    try:
        payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except FileNotFoundError:
        print(f"[Updater] Config not found at {CONFIG_PATH}; skipping checks.")
        return {}
    except Exception as exc:  # pragma: no cover - logging only
        print(f"[Updater] Failed to read config: {exc}")
        return {}


def _skip_updates() -> bool:
    return os.getenv("PLOTMASTER_SKIP_UPDATES", "0").lower() in {"1", "true", "yes"}


def _resolve_local_path(relative: str, default_name: str) -> Path:
    base = (relative or default_name).strip()
    return (ROOT / base).resolve()


def _resolve_remote_uri(candidate: str) -> str:
    trimmed = (candidate or "").strip()
    if not trimmed:
        return ""
    if trimmed.startswith(("http://", "https://", "file://")):
        return trimmed
    return (ROOT / trimmed).resolve().as_uri()


def _pending_metadata_path(temp_dir: Path, app_key: str) -> Path:
    return temp_dir / f"pending_{app_key}.json"


def _read_pending_metadata(temp_dir: Path, app_key: str) -> Optional[Dict[str, Any]]:
    meta_path = _pending_metadata_path(temp_dir, app_key)
    if not meta_path.exists():
        return None
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_pending_metadata(
    temp_dir: Path,
    app_key: str,
    meta: Dict[str, Any],
) -> None:
    temp_dir.mkdir(parents=True, exist_ok=True)
    meta_path = _pending_metadata_path(temp_dir, app_key)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")


def _build_download_url(app_cfg: Dict[str, Any], remote_info: RemoteVersionInfo, app_key: str) -> Optional[str]:
    if remote_info.download_url:
        return remote_info.download_url

    template = (app_cfg.get("download_url_template") or "").strip()
    if not template:
        return None

    try:
        return template.format(app=app_key, version=remote_info.version)
    except Exception:
        return template


def _resolve_remote_info(app_cfg: Dict[str, Any], app_key: str) -> RemoteVersionInfo:
    github_cfg = app_cfg.get("github") or {}
    if github_cfg.get("repo"):
        return fetch_remote_version_from_github(github_cfg, app_key)

    remote_uri = _resolve_remote_uri(app_cfg.get("remote_version_url", ""))
    if not remote_uri:
        raise ValueError("no remote_version_url or github repo provided")

    return fetch_remote_version_from_json(remote_uri)


def check_for_updates(app_key: str) -> Tuple[bool, str]:
    if _skip_updates():
        return False, "actualizaciones deshabilitadas por PLOTMASTER_SKIP_UPDATES"

    config = _load_update_config()
    apps = config.get("apps", {})
    app_cfg = apps.get(app_key)

    if not app_cfg:
        return False, f"sin configuración de actualizador para '{app_key}'"

    local_path = _resolve_local_path(app_cfg.get("local_version_file", ""), f"config/{app_key}_version.json")
    local_version = read_local_version(local_path)

    try:
        remote_info = _resolve_remote_info(app_cfg, app_key)
    except Exception as exc:
        return False, f"no se pudo resolver la versión remota: {exc}"

    if not remote_info.version:
        return False, f"la versión remota en {remote_info.source} está vacía"

    if not is_remote_newer(local_version, remote_info.version):
        temp_dir = Path(ROOT / app_cfg.get("update_temp_dir", "build/updates"))
        pending = _read_pending_metadata(temp_dir, app_key)
        if pending and pending.get("version") == remote_info.version:
            return True, f"actualización {remote_info.version} ya descargada en {pending.get('staged_path')}"
        return False, f"ya está en la versión {local_version or '0.0.0'}"

    temp_dir = Path(ROOT / app_cfg.get("update_temp_dir", "build/updates"))
    staged_path = temp_dir / f"{app_key}_{remote_info.version}.exe"
    download_url = _build_download_url(app_cfg, remote_info, app_key)
    downloaded = False

    if download_url:
        if staged_path.exists():
            downloaded = True
        else:
            downloaded = download_file(download_url, staged_path)

    details = (
        f"versión {remote_info.version} disponible (actual {local_version or '0.0.0'}) desde {remote_info.source}"
        + (f"; se preparó {staged_path}" if staged_path.exists() else "")
    )

    if download_url:
        details += f"; url: {download_url}"

    if download_url and downloaded:
        metadata = {
            "app": app_key,
            "version": remote_info.version,
            "staged_path": str(staged_path),
            "source": remote_info.source,
            "download_url": download_url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _write_pending_metadata(temp_dir, app_key, metadata)
    elif download_url and not downloaded:
        details += " (descarga fallida)"
    else:
        details += " (sin URL de descarga)"

    print(f"[Updater] {details}")
    return True, details
