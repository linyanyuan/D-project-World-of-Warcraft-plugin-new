"""Resolve package root for source runs and PyInstaller freezes."""

from __future__ import annotations

import sys
from pathlib import Path


def package_root() -> Path:
    """Directory that contains ``config/`` and ``profiles/``.

    - Source: ``.../clean_client``
    - PyInstaller: ``sys._MEIPASS / clean_client`` (bundled datas)
    """
    if getattr(sys, "frozen", False):
        meipass = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        bundled = meipass / "clean_client"
        if (bundled / "config" / "default.json").exists():
            return bundled
        if (meipass / "config" / "default.json").exists():
            return meipass
        return bundled
    return Path(__file__).resolve().parent
