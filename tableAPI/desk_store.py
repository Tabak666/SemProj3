import os
import json
import threading
import random

BASE_DIR = os.path.dirname(__file__)
DESKS_PATH = os.path.join(BASE_DIR, "desks.json")
_LOCK = threading.RLock()

def generate_mac_address():
    """Generate a random MAC address."""
    return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))

def _default_desks(n=20):
    return [
        {
            "id": i + 1,
            "name": f"Table {i + 1}",
            "floor": f"Floor {(i % 3) + 1}",
            "room": chr(65 + (i % 4)),  # A, B, C, D
            "mac": generate_mac_address()
        }
        for i in range(n)
    ]

def _load_desks_no_lock():
    """Load desks from JSON file, create with defaults if missing."""
    if not os.path.exists(DESKS_PATH):
        desks = _default_desks()
        _save_desks_no_lock(desks)
        return desks
    
    try:
        with open(DESKS_PATH, "r", encoding="utf-8") as f:
            desks = json.load(f)
        
        if not isinstance(desks, list) or len(desks) == 0:
            desks = _default_desks()
            _save_desks_no_lock(desks)
            return desks
        
        # Ensure all desks have a MAC address
        modified = False
        for desk in desks:
            if not desk.get("mac"):
                desk["mac"] = generate_mac_address()
                modified = True
        
        # If any desks were missing MAC addresses, save the updated list
        if modified:
            _save_desks_no_lock(desks)
        
        return desks
    except Exception:
        desks = _default_desks()
        _save_desks_no_lock(desks)
        return desks

def load_desks():
    """Thread-safe desk loading."""
    with _LOCK:
        return _load_desks_no_lock()

def save_desks(desks):
    """Thread-safe desk saving."""
    with _LOCK:
        _save_desks_no_lock(desks)

def _save_desks_no_lock(desks):
    """Save desks to JSON file with atomic write."""
    try:
        os.makedirs(os.path.dirname(DESKS_PATH), exist_ok=True)
        tmp = DESKS_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(desks, f, indent=2, ensure_ascii=False)
        os.replace(tmp, DESKS_PATH)
    except Exception as e:
        raise

def add_desk(name="New Table", extra=None):
    """Add a new desk with optional extra fields. Auto-generates MAC if not provided."""
    with _LOCK:
        desks = _load_desks_no_lock()
        max_id = max((d.get("id", 0) for d in desks), default=0)
        new = {"id": max_id + 1, "name": name}
        
        # Always ensure a MAC address exists
        if extra and isinstance(extra, dict):
            new.update(extra)
        
        if not new.get("mac"):
            new["mac"] = generate_mac_address()
        
        desks.append(new)
        _save_desks_no_lock(desks)
        return new

def remove_desk(desk_id):
    """Remove a desk by ID."""
    with _LOCK:
        desks = _load_desks_no_lock()
        orig_len = len(desks)
        desks = [d for d in desks if str(d.get("id")) != str(desk_id)]
        if len(desks) == orig_len:
            return False
        _save_desks_no_lock(desks)
        return True

# Force initialization on import
load_desks()
