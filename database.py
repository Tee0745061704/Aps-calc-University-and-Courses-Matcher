import sqlite3
DB_FILE = "marks_database.db"
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS subjects (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, subject TEXT NOT NULL, mark INTEGER NOT NULL, level INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)')
    conn.commit()
    conn.close()
def add_user(u,p):
    conn=get_db_connection()
    try:
        conn.execute("INSERT INTO users (username,password) VALUES (?,?)",(u,p))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()
def check_user(u):
    conn=get_db_connection()
    user=conn.execute("SELECT * FROM users WHERE username=?",(u,)).fetchone()
    conn.close()
    return user
if __name__=="__main__":
    init_db()
