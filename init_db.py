from database import get_db_connection

def init_all_databases():
    with get_db_connection() as conn:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS slot_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            salon_id INTEGER NOT NULL,
            slot_datetime TEXT NOT NULL,
            reminder_time TEXT NOT NULL,
            sent INTEGER DEFAULT 0
        )
        """)

        conn.commit()   # 👈 ADD THIS
        print("✅ slot_reminders table created successfully!")

if __name__ == "__main__":
    init_all_databases()
