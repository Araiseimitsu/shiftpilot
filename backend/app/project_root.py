"""PyInstaller 同梱時は展開先 _MEIPASS を、開発時はリポジトリルートを返す。"""
from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass is not None:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    here = Path(__file__).resolve()
    return here.parents[2]
