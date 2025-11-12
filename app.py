# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, flash, session
from markupsafe import Markup
import os
from whitenoise import WhiteNoise
import gspread  # <-- ייבוא חדש
from google.oauth2.service_account import Credentials  # <-- ייבוא חדש
import json  # <-- ייבוא חדש
import logging  # <-- ייבוא חדש לניפוי שגיאות

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", "change-this-key-in-development")
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/') # הגדרת WhiteNoise
logging.basicConfig(level=logging.INFO)  # הדפסת מידע ללוגים

# --- שמות הקבצים בגוגל שיטס (לפי התמונה ששלחת) ---
STUDENT_SHEET_NAME = "שאלון סטודנטים"
MENTOR_SHEET_NAME = "מיפוי מדריכים"

# --- פונקציית חיבור לגוגל ---
def get_google_sheets_client(env_var_name):
    """
    מתחבר ל-Google Sheets API באמצעות משתנה סביבה ספציפי (GCP_CREDS או GCP_CREDS_2)
    """
    try:
        creds_json = os.getenv(env_var_name)
        if not creds_json:
            logging.error(f"משתנה סביבה {env_var_name} לא הוגדר או שהוא ריק.")
            return None
        
        creds_dict = json.loads(creds_json)
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        logging.info(f"התחברות ל-Google Sheets דרך {env_var_name} הצליחה")
        return client
    except json.JSONDecodeError:
        logging.error(f"שגיאה בפענוח ה-JSON מ-{env_var_name}. בדוק שהעתקת את כל הקובץ.")
        return None
    except Exception as e:
        logging.error(f"שגיאה בהתחברות ל-Google דרך {env_var_name}: {e}")
        return None

# --- מצב תחזוקה ---
@app.before_request
def maintenance_mode():
    if not request.path.startswith('/lecturer') and not request.path.startswith('/login'):
        if os.getenv("MAINTENANCE_MODE", "0") == "1":
            html = """
            <html lang="he" dir="rtl">
            <head>
              <meta charset="utf-8">
              <title>האתר סגור</title>
              <style>
                body{ font-family:system-ui,-apple-system,Segoe UI,Heebo,Arial; background:#f8fafc; direction:rtl; text-align:center; margin:0; padding-top:120px; color:#111827; }
                .box{ display:inline-block; padding:32px 40px; border-radius:18px; background:#ffffff; box-shadow:0 10px 30px rgba(15,23,42,.08); border:1px solid #e5e7eb; }
                h1{margin:0 0 12px;font-size:26px;}
                p{margin:0;color:#6b7280;}
              </style>
            </head>
            <body>
              <div class="box">
                <h1>⚙️ האתר סגור כרגע</h1>
                <p>הגישה לטופס סטודנטים הוגבלה זמנית.</p>
              </div>
            </body>
            </html>
            """
            return Markup(html), 503

# --- דפים ציבוריים ---
@app.route("/")
def index():
    return render_template("matching.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("הפנייה נשלחה בהצלחה! נחזור אליך בהקדם.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")

# --- תהליך אימות מרצים ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        flash(f"הרשמה עבור {email} נקלטה (דמו).", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if email and password:
            session['awaiting_secret_auth'] = email
            return redirect(url_for("verify_secret"))
        else:
            flash("נא למלא אימייל וסיסמה.", "error")
    return render_template("login.html")

@app.route("/verify-secret", methods=["GET", "POST"])
def verify_secret():
    if 'awaiting_secret_auth' not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        secret = request.form.get("secret_password")
        LECTURER_SECRET = os.getenv("LECTURER_SECRET")
        if secret == LECTURER_SECRET:
            session['lecturer_email'] = session.get('awaiting_secret_auth', 'lecturer@zefat.ac.il')
            session.pop('awaiting_secret_auth', None)
            flash("התחברת בהצלחה!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("סיסמת מרצים סודית שגויה.", "error")
    return render_template("verify_secret.html")

@app.route("/logout")
def logout():
    session.pop('lecturer_email', None)
    flash("יצאת בהצלחה מהמערכת.", "success")
    return redirect(url_for("index"))

# --- אזור מרצים מחוברים ---
def check_auth():
    if 'lecturer_email' not in session:
        flash("נא להתחבר למערכת המרצים תחילה.", "error")
        return redirect(url_for("login"))
    return None

@app.route("/dashboard")
def dashboard():
    auth_redirect = check_auth()
    if auth_redirect: return auth_redirect
    
    # --- ✨ קריאה לסטודנטים עם חשבון 1 (GCP_CREDS) ✨ ---
    client_students = get_google_sheets_client("GCP_CREDS")
    student_count = 0
    if client_students:
        try:
            student_sheet = client_students.open(STUDENT_SHEET_NAME).sheet1
            student_count = len(student_sheet.get_all_records()) # סופר שורות עם נתונים
            logging.info(f"נמצאו {student_count} סטודנטים")
        except gspread.exceptions.SpreadsheetNotFound:
            logging.error(f"שגיאה: לא ניתן למצוא קובץ סטודנטים בשם '{STUDENT_SHEET_NAME}'")
            flash(f"שגיאה: לא ניתן למצוא את קובץ הסטודנטים '{STUDENT_SHEET_NAME}'.", "error")
        except Exception as e:
            logging.error(f"שגיאה בקריאת קובץ סטודנטים: {e}")
            flash("שגיאה בקריאת קובץ סטודנטים. בדוק הרשאות עבור GCP_CREDS.", "error")

    # --- ✨ קריאה למדריכים עם חשבון 2 (GCP_CREDS_2) ✨ ---
    client_mentors = get_google_sheets_client("GCP_CREDS_2")
    mentor_count = 0
    if client_mentors:
        try:
            mentor_sheet = client_mentors.open(MENTOR_SHEET_NAME).sheet1
            mentor_count = len(mentor_sheet.get_all_records()) # סופר שורות עם נתונים
            logging.info(f"נמצאו {mentor_count} מדריכים")
        except gspread.exceptions.SpreadsheetNotFound:
            logging.error(f"שגיאה: לא ניתן למצוא קובץ מדריכים בשם '{MENTOR_SHEET_NAME}'")
            flash(f"שגיאה: לא ניתן למצוא את קובץ המדריכים '{MENTOR_SHEET_NAME}'.", "error")
        except Exception as e:
            logging.error(f"שגיאה בקריאת קובץ מדריכים: {e}")
            flash("שגיאה בקריאת קובץ מדריכים. בדוק הרשאות עבור GCP_CREDS_2.", "error")

    # (נתוני דמו לשאר המדדים)
    placement_count = 0 
    success_rate_val = 0
    success_rate_str = f"{success_rate_val}%"

    stats = {
        "registered_students": student_count,
        "registered_mentors": mentor_count,
        "success_rate": success_rate_str,
        "placements_done": placement_count
    }
    return render_template("dashboard.html", stats=stats)

@app.route("/analytics", methods=["GET", "POST"])
def analytics():
    auth_redirect = check_auth()
    if auth_redirect: return auth_redirect
    if request.method == "POST":
        results_file = request.files.get('results_file')
        if not results_file:
            return render_template("analytics.html", error="לא נבחר קובץ.")
        
        # ... כאן תהיה הלוגיקה של ניתוח הקובץ ...
        
        # נתוני דמו להצגה
        tables = { "cols": {"site": "מקום הכשרה", "field": "תחום התמחות"}, "by_site": [], "by_field": [], "score_avg": [] }
        charts = { "site_labels": [], "site_values": [], "field_labels": [], "field_values": [], "avg_labels": [], "avg_values": [] }
        return render_template("analytics.html", tables=tables, charts=charts)

    return render_template("analytics.html")

@app.route("/placement-system")
def placement_system():
    auth_redirect = check_auth()
    if auth_redirect: return auth_redirect
    return redirect("https://www.studentsplacement.org/")

# --- דפי דמו ישנים (אם צריך) ---
@app.route("/students-form")
def students_form():
    return "<h2>כאן יהיה שאלון סטודנטים (דף דמו זמני)</h2>"

@app.route("/mentors-form")
def mentors_form():
    return "<h2>כאן יהיה מיפוי מדריכים (דף דמו זמני)</h2>"

if __name__ == "__main__":
    app.run(debug=True)
