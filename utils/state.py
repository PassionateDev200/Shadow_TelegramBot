import json
import os
import sys
from typing import Any, Dict, List
from models.pool import Pool

def get_base_dir():
    """Get the base directory for the application (handles both development and executable)"""
    if getattr(sys, 'frozen', False):
        # Running as executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

STATE_DIR = os.path.join(get_base_dir(), "data")
STATE_FILE = os.path.join(STATE_DIR, "state.json")


def _ensure_dir() -> None:
    os.makedirs(STATE_DIR, exist_ok=True)


def save_state(pools: List[Pool], settings: Dict[str, Any]) -> None:
    _ensure_dir()
    data = {
        "pools": [
            {
                "link": p.link,
                "range": p.range,
                "token": p.token,
                "amount": p.amount,
                "upper_range": p.upper_range,
                "lower_range": p.lower_range,
                "owner_chat_id": p.owner_chat_id,
                "last_status": p.last_status,
                "meta": p.meta,
            }
            for p in pools
        ],
        "settings": settings,
    }
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, STATE_FILE)


def load_state() -> Dict[str, Any]:
    if not os.path.exists(STATE_FILE):
        # Create default state.json if it doesn't exist
        default_state = {
            "pools": [],
            "settings": {
                "threshold": 90,
                "balance_tolerance": 2
            }
        }
        save_state([], default_state["settings"])
        return default_state
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Corrupt state; start fresh but do not delete file
        return {
            "pools": [],
            "settings": {
                "threshold": 90,
                "balance_tolerance": 2
            }
        }
