import json
import os
from threading import Lock
from uuid import uuid4

STORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'tables.json')
STORE_PATH = os.path.normpath(STORE_PATH)

_lock = Lock()

def _ensure_store():
    dirpath = os.path.dirname(STORE_PATH)
    if not os.path.isdir(dirpath):
        os.makedirs(dirpath, exist_ok=True)
    if not os.path.isfile(STORE_PATH):
        with open(STORE_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f)

def load_tables():
    _ensure_store()
    with _lock:
        with open(STORE_PATH, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception:
                return []

def save_tables(tables):
    _ensure_store()
    with _lock:
        with open(STORE_PATH, 'w', encoding='utf-8') as f:
            json.dump(tables, f, indent=2)

def get_tables():
    return load_tables()

def add_table(data):
    tables = load_tables()
    new_table = {
        "id": data.get("id") or str(uuid4()),
        "name": data.get("name", "Untitled"),
        "meta": data.get("meta", {})
    }
    tables.append(new_table)
    save_tables(tables)
    return new_table

def remove_table(table_id):
    tables = load_tables()
    new_tables = [t for t in tables if str(t.get("id")) != str(table_id)]
    if len(new_tables) == len(tables):
        return False
    save_tables(new_tables)
    return True
