"""Lanzador simple para desarrollo.
Permite iniciar Admin o Vendedor sin generar .exe.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

APPS = {
    "1": {
        "key": "admin",
        "label": "Programa Administrador",
        "module": "plotmaster.apps.admin.main",
    },
    "2": {
        "key": "vendor",
        "label": "Programa Vendedor",
        "module": "plotmaster.apps.vendor.main",
    },
}


def _print_menu() -> None:
    print("\n=== Plot Master (desarrollo) ===")
    for option, cfg in APPS.items():
        print(f" {option} - {cfg['label']}")
    print(" 0 - Salir")


def _select_app() -> dict:
    choice = input("Elegir opción: ").strip().lower()
    if choice in {"0", "salir", "exit"}:
        sys.exit(0)

    # Permitir elegir por número o por clave
    for option, cfg in APPS.items():
        if choice in {option, cfg["key"], cfg["key"][:1]}:
            return cfg

    print("Opción inválida. Usa 1 (Admin) o 2 (Vendedor).")
    sys.exit(1)


def _run_module(module: str) -> int:
    cmd = [sys.executable, "-m", module]
    print(f"\n-> Iniciando {module} ...\n")
    try:
        return subprocess.call(cmd, cwd=ROOT)
    except KeyboardInterrupt:
        return 130


def main() -> None:
    _print_menu()
    app_cfg = _select_app()
    exit_code = _run_module(app_cfg["module"])
    if exit_code:
        print(f"El proceso terminó con código {exit_code}.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
