import sqlite3

DB_PATH = 'new_user.db'

def init_user_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("User table created successfully.")

if __name__ == "__main__":
    init_user_db()

import sqlite3

SLOT_DB_PATH = 'gloora.db'

def init_slot_db():
    conn = sqlite3.connect(SLOT_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            salon_id INTEGER,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("Slots table created successfully.")

if __name__ == "__main__":
    init_slot_db()


import sqlite3

SALON_DB_PATH = 'salons.db'

def init_salon_db():
    conn = sqlite3.connect(SALON_DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS salons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            lat REAL,
            lng REAL,
            contact TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ON',
            owner_username TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("Salons table created successfully.")

if __name__ == "__main__":
    init_salon_db()


import sqlite3
conn = sqlite3.connect('salons.db')
conn.execute("ALTER TABLE salons ADD COLUMN owner_username TEXT NOT NULL DEFAULT 'unknown'")
conn.commit()
conn.close()
