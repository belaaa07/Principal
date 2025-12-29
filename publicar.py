"""Automatiza el build y empaquetado de Plot Master.

Flujo:
1) Pregunta qué app compilar (Admin/Vendedor).
2) Pide la versión (v1.4.0 / 1.4.0).
3) Actualiza archivos de versión locales y remotos.
4) Ejecuta PyInstaller con el spec correspondiente.
5) Renombra el .exe con la versión y lo copia a releases/access listo para subir a GitHub.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent
RELEASES_DIR = ROOT / "releases" / "access"


@dataclass(frozen=True)
class AppTarget:
    key: str
    label: str
    spec_path: Path
    dist_dir: Path
    exe_name: str
    release_name_template: str
    local_version_file: Path
    remote_version_file: Path

    def source_exe(self) -> Path:
        return self.dist_dir / self.exe_name

    def release_filename(self, version: str) -> str:
        return self.release_name_template.format(version=version)


APP_TARGETS: Dict[str, AppTarget] = {
    "1": AppTarget(
        key="admin",
        label="Administrador",
        spec_path=ROOT / "scripts" / "pyinstaller_admin.spec",
        dist_dir=ROOT / "dist",
        exe_name="PlotMaster_Admin.exe",
        release_name_template="PlotMaster_Admin_v{version}.exe",
        local_version_file=ROOT / "config" / "admin_version.json",
        remote_version_file=ROOT / "config" / "remote_versions" / "admin_version.json",
    ),
    "2": AppTarget(
        key="vendor",
        label="Vendedor",
        spec_path=ROOT / "scripts" / "pyinstaller_vendor.spec",
        dist_dir=ROOT / "dist",
        exe_name="PlotMaster_Vendor.exe",
        release_name_template="PlotMaster_Vendedor_v{version}.exe",
        local_version_file=ROOT / "config" / "vendor_version.json",
        remote_version_file=ROOT / "config" / "remote_versions" / "vendor_version.json",
    ),
}


def _print_menu() -> None:
    print("\n=== Build / Publicación ===")
    for option, target in APP_TARGETS.items():
        print(f" {option} - {target.label}")
    print(" 0 - Salir")


def _select_target() -> AppTarget:
    choice = input("Elegir opción: ").strip().lower()
    if choice in {"0", "salir", "exit"}:
        sys.exit(0)

    for option, target in APP_TARGETS.items():
        if choice in {option, target.key, target.key[:1]}:
            return target

    print("Opción inválida. Usa 1 (Admin) o 2 (Vendedor).")
    sys.exit(1)


def _clean_version(raw: str) -> str:
    value = (raw or "").strip()
    if value.lower().startswith("v"):
        value = value[1:]
    return value.strip()


def _ask_version() -> str:
    version = _clean_version(input("Versión (ej. v1.4.0): "))
    if not version:
        print("La versión no puede estar vacía.")
        sys.exit(1)
    return version


def _load_json(path: Path) -> Dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def _write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_versions(target: AppTarget, version: str) -> List[Path]:
    updated: List[Path] = []
    for path in [target.local_version_file, target.remote_version_file]:
        payload = _load_json(path)
        payload["version"] = version
        _write_json(path, payload)
        updated.append(path)
    return updated


def _run_pyinstaller(target: AppTarget) -> None:
    if not target.spec_path.exists():
        print(f"No se encontró el spec: {target.spec_path}")
        sys.exit(1)

    work_dir = ROOT / "build" / target.key
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--distpath",
        str(target.dist_dir),
        "--workpath",
        str(work_dir),
        str(target.spec_path),
    ]
    print(f"\n-> Ejecutando PyInstaller: {' '.join(cmd)}\n")
    try:
        subprocess.run(cmd, cwd=ROOT, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"PyInstaller falló (código {exc.returncode}).")
        sys.exit(exc.returncode)


def _clean_previous_build(target: AppTarget) -> None:
    try:
        exe_path = target.source_exe()
        if exe_path.exists():
            exe_path.unlink()
    except Exception:
        pass
    build_path = ROOT / "build" / target.key
    if build_path.exists():
        shutil.rmtree(build_path, ignore_errors=True)


def _stage_release(target: AppTarget, version: str) -> Path:
    src = target.source_exe()
    if not src.exists():
        print(f"No se encontró el ejecutable generado: {src}")
        sys.exit(1)

    RELEASES_DIR.mkdir(parents=True, exist_ok=True)
    dest = RELEASES_DIR / target.release_filename(version)
    if dest.exists():
        dest.unlink()
    shutil.copy2(src, dest)
    return dest


def main() -> None:
    _print_menu()
    target = _select_target()
    version = _ask_version()

    print(f"\nPreparando {target.label} v{version} ...")
    updated_files = _update_versions(target, version)
    print("Archivos de versión actualizados:")
    for path in updated_files:
        print(f" - {path.relative_to(ROOT)}")

    _clean_previous_build(target)
    _run_pyinstaller(target)
    staged_path = _stage_release(target, version)

    print("\nListo. Archivos generados:")
    print(f" - EXE: {target.source_exe().relative_to(ROOT)}")
    print(f" - Release: {staged_path.relative_to(ROOT)}")
    print(f"\nSiguiente paso: subir el .exe versionado a GitHub Releases con tag v{version}.")


if __name__ == "__main__":
    main()
