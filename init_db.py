# All three databases are recreate 
import sqlite3
import os

# Database paths
DB_PATH = 'new_user.db'
SLOT_DB_PATH = 'gloora.db'
SALON_DB_PATH = 'salons.db'

# Function to delete existing database file
def reset_db(db_path):
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted {db_path}")
    else:
        print(f"{db_path} does not exist, no need to delete.")

# Reset all three databases
reset_db(DB_PATH)
reset_db(SLOT_DB_PATH)
reset_db(SALON_DB_PATH)

# Re-initialize databases with proper schema
def init_user_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("User database initialized.")

def init_slot_db():
    conn = sqlite3.connect(SLOT_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            salon_id INTEGER,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    print("Slot database initialized.")

def init_salon_db():
    if not os.path.exists(SALON_DB_PATH):
        with sqlite3.connect(SALON_DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE salons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    lat REAL,
                    lng REAL,
                    contact TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ON',
                    owner_username TEXT NOT NULL,
                    services TEXT,
                    price REAL,
                    pass_key TEXT NOT NULL   -- new: hashed pass key
                )
            """)

    conn.commit()
    conn.close()
    print("Salon database initialized with status and owner_username columns.add pass key also ")


# Initialize all databases
init_user_db()
init_slot_db()
init_salon_db()
print("All databases reset and ready!")
# import sqlite3

# conn = sqlite3.connect("salons.db")
# cursor = conn.cursor()
# cursor.execute("ALTER TABLE salons ADD COLUMN status TEXT DEFAULT 'ON';")
# conn.commit()
# conn.close()
