import os
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, session
from dotenv import load_dotenv
from database import init_db, add_user, check_user
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
# Works even if SECRET_KEY env is missing on Render
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-aps-2026-secure')

# Initialize DB on startup
init_db()

# Load universities - safe if file missing
def load_universities():
    unis = []
    try:
        if os.path.exists('universities.csv'):
            with open('universities.csv', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    unis.append(row)
    except Exception as e:
        print(f"Universities load error: {e}")
    return unis

UNIVERSITIES = load_universities()

def calculate_aps_point(mark):
    """SA APS Points"""
    if mark >= 80: return 7
    if mark >= 70: return 6
    if mark >= 60: return 5
    if mark >= 50: return 4
    if mark >= 40: return 3
    if mark >= 30: return 2
    return 1

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = check_user(username)
        if user and check_password_hash(user['password'], password):
            session['user'] = username
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        if not username or not password:
            flash('Username and password required')
        elif check_user(username):
            flash('Username already exists - please login')
        else:
            hashed = generate_password_hash(password)
            if add_user(username, hashed):
                flash('Registration successful! Please login')
                return redirect(url_for('login'))
            else:
                flash('Failed to register - try again')
    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    aps = 0
    marks = {}
    matched_unis = []
    
    if request.method == 'POST':
        try:
            # Get marks from form
            maths = int(request.form.get('maths', 0) or 0)
            english = int(request.form.get('english', 0) or 0)
            sub3 = int(request.form.get('subject3', 0) or 0)
            sub4 = int(request.form.get('subject4', 0) or 0)
            sub5 = int(request.form.get('subject5', 0) or 0)
            sub6 = int(request.form.get('subject6', 0) or 0)
            
            all_marks = [maths, english, sub3, sub4, sub5, sub6]
            marks = {
                'maths': maths, 'english': english,
                'subject3': sub3, 'subject4': sub4,
                'subject5': sub5, 'subject6': sub6
            }
            
            # Calculate APS (6 subjects)
            aps = sum(calculate_aps_point(m) for m in all_marks)
            
            # Filter universities if CSV exists
            if UNIVERSITIES:
                for uni in UNIVERSITIES:
                    try:
                        req_aps = int(uni.get('aps', uni.get('APS', 0)) or 0)
                        if aps >= req_aps:
                            matched_unis.append(uni)
                    except:
                        pass
            
        except ValueError:
            flash('Please enter valid numbers (0-100)')
    
    return render_template('dashboard.html', 
                         aps=aps, 
                         marks=marks,
                         user=session.get('user'), 
                         universities=matched_unis or UNIVERSITIES)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    # For local testing only - Render uses gunicorn
    app.run(debug=True, host='0.0.0.0', port=5000)
