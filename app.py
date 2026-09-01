import csv
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_db_connection

app = Flask(__name__)
app.secret_key = "super_secret_south_africa_varsity_key_123"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE_PATH = os.path.join(BASE_DIR, 'universities.csv')

def load_courses_from_csv():
    courses_list = []
    if not os.path.exists(CSV_FILE_PATH):
        return courses_list
    with open(CSV_FILE_PATH, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                courses_list.append({
                    "varsity": row['University'].strip(),
                    "name": row['Course'].strip(),
                    "min_aps": int(row['Min_APS']),
                    "min_avg": int(row['Min_Avg']),
                    "req_math": int(row['Req_Math']),
                    "req_sci": int(row['Req_Science'])
                })
            except (ValueError, KeyError):
                continue
    return courses_list

def calculate_aps(mark):
    if mark >= 80: return 7
    if mark >= 70: return 6
    if mark >= 60: return 5
    if mark >= 50: return 4
    if mark >= 40: return 3
    if mark >= 30: return 2
    return 1

def is_life_orientation(subject_name):
    """Helper function to cleanly standardise South African Life Orientation matching rules."""
    name_clean = subject_name.strip().lower()
    return "life orientation" in name_clean or name_clean == "lo"

# --- AUTHENTICATION ROUTES ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        if not username or not password:
            return "Please fill in all fields", 400
            
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            
            user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
            session['user_id'] = user['id']
            session['username'] = username
            conn.close()
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already exists! Go back and choose another.", 400
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = username
            return redirect(url_for('index'))
        
        return "Invalid credentials! Go back and try again.", 401
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- PROTECTED PROFILE APPLICATION ROUTES ---

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    subjects = conn.execute("SELECT id, subject, mark, level FROM subjects WHERE user_id = ?", (session['user_id'],)).fetchall()
    conn.close()

    total_marks = sum(row['mark'] for row in subjects)
    count = len(subjects)
    avg_mark = total_marks / count if count > 0 else 0
    total_aps = sum(row['level'] for row in subjects if not is_life_orientation(row['subject']))

    math_mark = 0
    sci_mark = 0
    for row in subjects:
        subj_name = row['subject'].lower()
        if "mathematics" in subj_name and "literacy" not in subj_name:
            math_mark = max(math_mark, row['mark'])
        if "physical science" in subj_name or "life science" in subj_name:
            sci_mark = max(sci_mark, row['mark'])

    result_text = (
        f"📊 Profile Stats ({session['username']}):\n"
        f"• Total Registered NSC Subjects: {count} / 7 Recommended\n"
        f"• Group Academic Average: {avg_mark:.2f}%\n"
        f"• Active Entry APS Score (Excl. LO): {total_aps} Points\n"
        f"• Pure Mathematics Tracker: {math_mark}% | Science Gateway Tracker: {sci_mark}%"
    )

    qualified_courses = []
    if count > 0:
        csv_courses = load_courses_from_csv()
        for course in csv_courses:
            if (total_aps >= course["min_aps"] and 
                avg_mark >= course["min_avg"] and 
                math_mark >= course["req_math"] and 
                sci_mark >= course["req_sci"]):
                qualified_courses.append(course)

    return render_template('index.html', subjects=subjects, result=result_text, courses=qualified_courses)

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    subject = request.form['subject']
    mark = int(request.form['mark'])
    level = 0 if is_life_orientation(subject) else calculate_aps(mark)

    conn = get_db_connection()
    conn.execute("INSERT INTO subjects (user_id, subject, mark, level) VALUES (?, ?, ?, ?)", 
                 (session['user_id'], subject, mark, level))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    conn.execute("DELETE FROM subjects WHERE id = ? AND user_id = ?", (id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
else:
    # Safely init database on production bootup via Gunicorn
    init_db()
