import sqlite3

DB_FILE = "marks_database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            mark INTEGER NOT NULL,
            level INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, password_hash):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, password_hash))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def check_user(username):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username =?", (username,)).fetchone()
    conn.close()
    return user

if __name__ == "__main__":
    init_db()
    print("Database initialized")    # OPTIMISATION: Speed up profile lookups during index data loops
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_subjects_user_id ON subjects (user_id);
    ''')
    
    conn.commit()
    conn.close()

# Safeguard block allowing Render's build script to invoke table setup cleanly
if __name__ == '__main__':
    print("🚀 Initialising marks_database.db engine tables...")
    init_db()
    print("✅ Schema deployed successfully.")
