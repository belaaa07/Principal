"""Helpers to interrogate GitHub releases for updates."""
from __future__ import annotations

import json
import urllib.request
from typing import Any, Mapping, Optional

GITHUB_RELEASES_ENDPOINT = "https://api.github.com/repos/{repo}/releases/latest"
DEFAULT_HEADERS = {
    "User-Agent": "PlotMaster-Updater",
    "Accept": "application/vnd.github+json",
}


def fetch_latest_release(repo: str, token: Optional[str] = None) -> Mapping[str, Any]:
    if not repo:
        raise ValueError("github repo is required to fetch releases")

    url = GITHUB_RELEASES_ENDPOINT.format(repo=repo)
    request = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    if token:
        request.add_header("Authorization", f"token {token}")

    with urllib.request.urlopen(request, timeout=15) as response:
        payload = response.read().decode("utf-8")

    return json.loads(payload)


def guess_asset_download_url(
    release: Mapping[str, Any],
    template: Optional[str],
    app_key: str,
    version: str,
) -> Optional[str]:
    assets = list(release.get("assets", []))
    if not assets:
        return None

    def _best_match(name: str) -> bool:
        normalized = name.strip().lower()
        if template:
            try:
                candidate = template.format(app=app_key, version=version)
            except Exception:
                candidate = template
            if normalized == candidate.strip().lower():
                return True
        if normalized.endswith(".exe") and app_key in normalized:
            return True
        return False

    if template:
        try:
            expected_name = template.format(app=app_key, version=version)
        except Exception:
            expected_name = template
        for asset in assets:
            if asset.get("name", "").strip().lower() == expected_name.strip().lower():
                return asset.get("browser_download_url")

    for asset in assets:
        name = asset.get("name", "")
        if _best_match(name):
            return asset.get("browser_download_url")

    return assets[0].get("browser_download_url")
