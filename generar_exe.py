"""Herramienta mínima para empaquetar cada aplicación con PyInstaller."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST_ROOT = ROOT / "dist"
BUILD_ROOT = ROOT / "build"

APP_TARGETS = {
    "1": {
        "key": "admin",
        "label": "Programa Administrador",
        "entry": ROOT / "plotmaster" / "apps" / "admin" / "main.py",
        "name": "PlotMaster_Admin",
    },
    "2": {
        "key": "vendor",
        "label": "Programa Vendedor",
        "entry": ROOT / "plotmaster" / "apps" / "vendor" / "main.py",
        "name": "PlotMaster_Vendor",
    },
}


def _print_menu() -> None:
    print("\n=== Generar .exe ===")
    for option, target in APP_TARGETS.items():
        print(f" {option} - {target['label']}")
    print(" 0 - Salir")


def _select_target() -> dict:
    choice = input("Elegir opción: ").strip().lower()
    if choice in {"0", "salir", "exit"}:
        sys.exit(0)
    target = APP_TARGETS.get(choice)
    if not target:
        print("Opción inválida. Usa 1 (Admin) o 2 (Vendedor).")
        sys.exit(1)
    return target


def _run_pyinstaller(target: dict) -> Path:
    dist_path = DIST_ROOT / target["key"]
    build_path = BUILD_ROOT / target["key"]
    dist_path.mkdir(parents=True, exist_ok=True)
    build_path.mkdir(parents=True, exist_ok=True)
    entry = target["entry"]
    if not entry.exists():
        print(f"No se encontró el archivo de entrada: {entry}")
        sys.exit(1)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--name",
        target["name"],
        "--distpath",
        str(dist_path),
        "--workpath",
        str(build_path),
        str(entry),
    ]

    print(f"\n-> Ejecutando PyInstaller para {target['label']}...\n")
    subprocess.run(cmd, check=True)
    exe_path = dist_path / f"{target['name']}.exe"
    return exe_path


def main() -> None:
    _print_menu()
    target = _select_target()
    try:
        exe_path = _run_pyinstaller(target)
    except subprocess.CalledProcessError as exc:
        print(f"PyInstaller falló con código {exc.returncode}.")
        sys.exit(exc.returncode)
    print("\nListo.")
    print(f" - Ejecutable: {exe_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
