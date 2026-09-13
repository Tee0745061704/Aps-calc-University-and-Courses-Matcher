import csv, os, sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_db_connection

app = Flask(__name__)
app.secret_key = "super_secret_south_africa_varsity_key_123"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE_PATH = os.path.join(BASE_DIR, 'universities.csv')
init_db()

def load_courses_from_csv():
    courses_list = []
    if not os.path.exists(CSV_FILE_PATH): return courses_list
    import csv
    with open(CSV_FILE_PATH, 'r', encoding='utf-8') as file:
        for row in csv.DictReader(file):
            try:
                courses_list.append({"varsity": row['University'].strip(), "name": row['Course'].strip(), "min_aps": int(row['Min_APS']), "min_avg": int(row['Min_Avg']), "req_math": int(row['Req_Math']), "req_sci": int(row['Req_Science'])})
            except: continue
    return courses_list

def calculate_aps(mark):
    if mark >= 80: return 7
    if mark >= 70: return 6
    if mark >= 60: return 5
    if mark >= 50: return 4
    if mark >= 40: return 3
    if mark >= 30: return 2
    return 1

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?,?)", (username, generate_password_hash(request.form['password'])))
            conn.commit()
            user = conn.execute("SELECT id FROM users WHERE username =?", (username,)).fetchone()
            session['user_id'] = user['id']; session['username'] = username
            conn.close()
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            conn.close()
            return "Username exists!", 400
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username =?", (request.form['username'].strip(),)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'] = user['id']; session['username'] = request.form['username'].strip()
            return redirect(url_for('index'))
        return "Invalid credentials!", 401
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    if not conn.execute("SELECT id FROM users WHERE id =?", (session['user_id'],)).fetchone():
        conn.close(); session.clear(); return redirect(url_for('login'))
    subjects = conn.execute("SELECT id, subject, mark, level FROM subjects WHERE user_id =?", (session['user_id'],)).fetchall()
    conn.close()
    count = len(subjects)
    avg_mark = sum(r['mark'] for r in subjects)/count if count else 0
    total_aps = sum(r['level'] for r in subjects if "life orientation" not in r['subject'].lower())
    math_mark = max([r['mark'] for r in subjects if "mathematics" in r['subject'].lower() and "literacy" not in r['subject'].lower()] + [0])
    sci_mark = max([r['mark'] for r in subjects if "physical science" in r['subject'].lower() or "life science" in r['subject'].lower()] + [0])
    result_text = f"📊 {session['username']} | Subjects: {count}/7 | Avg: {avg_mark:.1f}% | APS: {total_aps} | Math: {math_mark}% | Sci: {sci_mark}%"
    qualified = [c for c in load_courses_from_csv() if count and total_aps >= c["min_aps"] and avg_mark >= c["min_avg"] and math_mark >= c["req_math"] and sci_mark >= c["req_sci"]] if count else []
    return render_template('index.html', subjects=subjects, result=result_text, courses=qualified)

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session: return redirect(url_for('login'))
    subject = request.form['subject']; mark = int(request.form['mark'])
    level = 0 if "life orientation" in subject.lower() else calculate_aps(mark)
    conn = get_db_connection()
    if not conn.execute("SELECT id FROM users WHERE id =?", (session['user_id'],)).fetchone():
        conn.close(); session.clear(); return redirect(url_for('login'))
    conn.execute("INSERT INTO subjects (user_id, subject, mark, level) VALUES (?,?,?,?)", (session['user_id'], subject, mark, level))
    conn.commit(); conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute("DELETE FROM subjects WHERE id =? AND user_id =?", (id, session['user_id']))
    conn.commit(); conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
