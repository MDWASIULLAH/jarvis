from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
AGENT_DIR = ROOT_DIR / "agent"

if AGENT_DIR.exists() and str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))
