import sqlite3
import os
from datetime import datetime

DB_FILE = 'stockbot.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # History Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            date_analyzed TEXT NOT NULL,
            status TEXT NOT NULL,
            ai_engine TEXT NOT NULL,
            report_html TEXT NOT NULL
        )
    ''')
    # Settings Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            groq_api_key TEXT,
            temperature REAL,
            username TEXT DEFAULT 'Vishal Raj',
            password TEXT DEFAULT 'admin'
        )
    ''')
    
    # Safe Migrations for existing databases
    try:
        c.execute("ALTER TABLE settings ADD COLUMN username TEXT DEFAULT 'Vishal Raj'")
    except sqlite3.OperationalError:
        pass # Column already exists
        
    try:
        c.execute("ALTER TABLE settings ADD COLUMN password TEXT DEFAULT 'admin'")
    except sqlite3.OperationalError:
        pass # Column already exists
    
    # Check if settings exist, if not create default
    c.execute('SELECT COUNT(*) FROM settings')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO settings (groq_api_key, temperature, username, password) VALUES (?, ?, ?, ?)', 
                  (os.environ.get('GROQ_API_KEY', ''), 0.2, 'Vishal Raj', 'admin'))
        
    conn.commit()
    conn.close()

def save_analysis(filename, html_report):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO history (filename, date_analyzed, status, ai_engine, report_html)
        VALUES (?, ?, ?, ?, ?)
    ''', (filename, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Completed', 'Llama 3.3', html_report))
    conn.commit()
    conn.close()

def get_all_history():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, filename, date_analyzed, status, ai_engine FROM history ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_settings():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT groq_api_key, temperature, username, password FROM settings LIMIT 1')
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {'groq_api_key': '', 'temperature': 0.2, 'username': 'Vishal Raj', 'password': 'admin'}

def update_settings(api_key, temperature, username, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE settings SET groq_api_key = ?, temperature = ?, username = ?, password = ? WHERE id = 1', 
              (api_key, temperature, username, password))
    conn.commit()
    
    # Also update environment var for immediate effect
    if api_key:
        os.environ['GROQ_API_KEY'] = api_key
        
    conn.close()
