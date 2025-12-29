"""Utilities that read the current version and resolve releases."""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple

from . import github


def _clean_version_label(raw: str, prefix: Optional[str] = None) -> str:
    label = (raw or "").strip()
    if prefix and label.startswith(prefix):
        label = label[len(prefix) :].lstrip()
    return label.lstrip("vV").strip()


def _split_version(value: str) -> Tuple[Any, ...]:
    if not value:
        return ()
    parts: list[Any] = []
    for chunk in value.replace("-", ".").split("."):
        cleaned = chunk.strip()
        if not cleaned:
            parts.append(0)
            continue
        if cleaned.isdigit():
            parts.append(int(cleaned))
        else:
            parts.append(cleaned.lower())
    return tuple(parts)


def is_remote_newer(local: str, remote: str) -> bool:
    if not remote:
        return False
    if not local:
        return True
    return _split_version(remote) > _split_version(local)


@dataclass
class RemoteVersionInfo:
    version: str
    download_url: Optional[str]
    source: str


def fetch_remote_version_from_json(uri: str) -> RemoteVersionInfo:
    with urllib.request.urlopen(uri, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))

    version = _clean_version_label(payload.get("version", ""))
    download_url = payload.get("download_url")
    return RemoteVersionInfo(version=version, download_url=download_url, source=uri)


def fetch_remote_version_from_github(github_cfg: Mapping[str, Any], app_key: str) -> RemoteVersionInfo:
    repo = (github_cfg or {}).get("repo")
    if not repo:
        raise ValueError("github.repo is required in updater config")

    release = github.fetch_latest_release(repo, token=github_cfg.get("token"))
    version = _clean_version_label(
        release.get("tag_name") or release.get("name") or "",
        github_cfg.get("tag_prefix"),
    )
    download_url = github.guess_asset_download_url(
        release,
        github_cfg.get("asset_name_template"),
        app_key,
        version,
    )
    return RemoteVersionInfo(version=version, download_url=download_url, source=f"github:{repo}")


def read_local_version(path: Path) -> str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("version", "").strip()
    except FileNotFoundError:
        return ""
    except Exception:
        return ""
