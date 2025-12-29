"""Command-line stub that exposes the shared updater manager."""
from __future__ import annotations

import argparse
import sys

from .manager import check_for_updates


def main() -> int:
    parser = argparse.ArgumentParser(description="Plot Master updater check")
    parser.add_argument("--app", choices=("admin", "vendor"), default="admin")
    args = parser.parse_args()

    success, message = check_for_updates(args.app)
    print(message)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
