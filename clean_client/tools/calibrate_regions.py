"""CLI entry: python -m clean_client.tools.calibrate_regions"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Calibrate Skill/Target/Player/Buff capture regions for clean_client.",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path.cwd(),
        help="Default directory for load/save of *_region.txt (default: cwd)",
    )
    parser.add_argument(
        "--capture",
        default="null",
        choices=("null", "mss", "dxcam", "printwindow"),
        help="Initial capture backend (default: null synthetic frame)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    from clean_client.ui.calibrator import run_calibrator

    return run_calibrator(output_dir=args.dir, capture_mode=args.capture)


if __name__ == "__main__":
    sys.exit(main())
