#!/usr/bin/env python3
"""Deploy helper: prints commands to run in hosting console."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sync = ROOT / "scripts" / "sync_deploy_configs.py"
subprocess.run([sys.executable, str(sync)], check=True)
