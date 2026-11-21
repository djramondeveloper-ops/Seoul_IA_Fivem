from __future__ import annotations
import os
import sys

try:
    if os.name == 'nt':
        os.system('chcp 65001 >nul')
except Exception:
    pass

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

from mz_ai_fivem import run

if __name__ == '__main__':
    run()
