# ══════════════════════════════════════════════════════════
#  database.py  —  Saves all pump readings to SQLite
# ══════════════════════════════════════════════════════════

import sqlite3
import config

def init_db():
    """Create the readings table if it doesn't exist yet"""
    conn = sqlite3.connect(config.DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS readings (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp    TEXT,
            rpm          REAL,
            torque       REAL,
            air_temp     REAL,
            tool_wear    INTEGER,
            fault_status TEXT,
            fault_type   TEXT,
            rul_hours    REAL
        )
    ''')
    # Try adding fault_type column if table already exists from older run
    try:
        c.execute('ALTER TABLE readings ADD COLUMN fault_type TEXT')
    except Exception:
        pass
    conn.commit()
    conn.close()

def save_reading(state):
    """Save one reading to the database"""
    conn = sqlite3.connect(config.DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO readings (timestamp, rpm, torque, air_temp, tool_wear, fault_status, fault_type, rul_hours)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        state.get('timestamp', ''),
        state.get('rpm', 0),
        state.get('torque', 0),
        state.get('air_temp', 0),
        state.get('tool_wear', 0),
        state.get('fault_status', ''),
        state.get('fault_type', 'NORMAL'),
        state.get('rul_hours', 0)
    ))
    conn.commit()
    conn.close()

def get_recent(limit=10):
    """Get the last N readings (for the dashboard table)"""
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM readings ORDER BY id DESC LIMIT ?', (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return list(reversed(rows))  # oldest first
