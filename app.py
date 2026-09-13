import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import init_db, add_user, check_user, add_subject, get_subjects, delete_subject
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'thembas-tracker-2026-secure-key')

init_db()

def get_level(mark):
    mark = int(mark)
    if mark >= 80: return 7
    if mark >= 70: return 6
    if mark >= 60: return 5
    if mark >= 50: return 4
    if mark >= 40: return 3
    if mark >= 30: return 2
    return 1

def calculate_stats(subjects):
    if not subjects:
        return "NO DATA - ADD SUBJECTS", 0, 0
    total_aps = sum([s['level'] for s in subjects])
    avg = sum([s['mark'] for s in subjects]) / len(subjects)
    result = f"TOTAL SUBJECTS: {len(subjects)}\nTOTAL APS: {total_aps}\nAVERAGE: {avg:.1f}%\nSTATUS: CALCULATED"
    return result, total_aps, avg

def get_qualified_courses(total_aps, avg):
    all_courses = [
        {"varsity":"UJ","name":"BSc Computer Science","min_aps":26,"min_avg":60,"req_math":60,"req_sci":50},
        {"varsity":"WITS","name":"BSc Engineering","min_aps":32,"min_avg":70,"req_math":70,"req_sci":65},
        {"varsity":"UP","name":"BCom Informatics","min_aps":30,"min_avg":60,"req_math":60,"req_sci":0},
        {"varsity":"UCT","name":"BSc IT","min_aps":28,"min_avg":65,"req_math":65,"req_sci":50},
        {"varsity":"NWU","name":"BSc Physics","min_aps":24
