# -*- coding: utf-8 -*-
import os
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from markupsafe import Markup
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "change-this-key")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

# ============== תחזוקה ==============
@app.before_request
def maintenance_mode():
    if os.getenv("MAINTENANCE_MODE", "0") == "1":
        html = """
        <html lang="he" dir="rtl">
        <head>
          <meta charset="utf-8">
          <title>האתר סגור</title>
          <style>
            body{font-family:system-ui,-apple-system,Segoe UI,Heebo,Arial;background:#f8fafc;direction:rtl;text-align:center;margin:0;padding-top:120px;color:#111827;}
            .box{display:inline-block;padding:32px 40px;border-radius:18px;background:#ffffff;box-shadow:0 10px 30px rgba(15,23,42,.08);border:1px solid #e5e7eb;}
            h1{margin:0 0 12px;font-size:26px;} p{margin:0;color:#6b7280;}
          </style>
        </head>
        <body><div class="box"><h1>⚙️ האתר סגור כרגע</h1><p>הגישה לטופס סטודנטים הוגבלה זמנית.</p></div></body></html>
        """
        return Markup(html), 503

# ============== עזר ==============
def login_required(view):
    def wrapper(*args, **kwargs):
        if not session.get("user_email"):
            flash("נא להתחבר תחילה.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    wrapper.__name__ = view.__name__
    return wrapper

def verified_required(view):
    def wrapper(*args, **kwargs):
        if not session.get("verified"):
            return redirect(url_for("verify"))
        return view(*args, **kwargs)
    wrapper.__name__ = view.__name__
    return wrapper

# ============== דפים ציבוריים ==============
@app.route("/")
def index():
    # דף בית שיווקי עם הכפתורים לשאלון/מיפוי וכו' (כמו במסכים ששלחת)
    return render_template("matching.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("הפנייה נשלחה בהצלחה! נחזור אליך בהקדם.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")

# ============== הרשמה/כניסה/אימות ==============
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        confirm = (request.form.get("password_confirm") or "").strip()

        if not email.endswith("@zefat.ac.il"):
            flash("הרשמה מותרת רק עם כתובת zefat.ac.il@", "error")
            return redirect(url_for("register"))
        if len(password) < 6:
            flash("סיסמה חייבת להיות באורך 6 תווים לפחות.", "error")
            return redirect(url_for("register"))
        if password != confirm:
            flash("אימות סיסמה אינו תואם.", "error")
            return redirect(url_for("register"))

        # דמו: אין DB. “נרשום” לסשן כדי לאפשר כניסה מידית.
        session.clear()
        session["user_email"] = email
        session["verified"] = False
        flash("נרשמת בהצלחה. היכנסי לאימות מרצה.", "success")
        return redirect(url_for("verify"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        confirm = (request.form.get("password_confirm") or "").strip()

        if not email or not password or not confirm:
            flash("נא למלא את כל השדות.", "error")
            return redirect(url_for("login"))
        if not email.endswith("@zefat.ac.il"):
            flash("כניסה מותרת רק עם מייל מוסדי zefat.ac.il@", "error")
            return redirect(url_for("login"))
        if password != confirm:
            flash("אימות סיסמה אינו תואם.", "error")
            return redirect(url_for("login"))

        session.clear()
        session["user_email"] = email
        session["verified"] = False
        flash("ניסיון התחברות נקלט. המשיכי לאימות מרצים.", "success")
        return redirect(url_for("verify"))
    return render_template("login.html")

@app.route("/verify", methods=["GET", "POST"])
@login_required
def verify():
    if request.method == "POST":
        secret = (request.form.get("lecturer_secret") or "").strip()
        expected = os.getenv("LECTURER_SECRET", "lecturer_secret")
        if secret == expected:
            session["verified"] = True
            flash("אומתת בהצלחה.", "success")
            return redirect(url_for("lecturers"))
        else:
            flash("קוד אימות שגוי.", "error")
            return redirect(url_for("verify"))
    return render_template("verify.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("התנתקת מהמערכת.", "success")
    return redirect(url_for("index"))

# ============== אזור מרצים מוגן ==============
@app.route("/lecturers")
@login_required
@verified_required
def lecturers():
    return render_template("lecturers.html")

@app.route("/analytics", methods=["GET", "POST"])
@login_required
@verified_required
def analytics():
    if request.method == "POST":
        f = request.files.get("results_file")
        if not f or f.filename == "":
            return render_template("analytics.html", error="לא נבחר קובץ.")
        try:
            if f.filename.lower().endswith(".csv"):
                df = pd.read_csv(f)
            else:
                df = pd.read_excel(f)

            # שמות עמודות גמישים (עברית/אנגלית)
            col_site = next((c for c in df.columns if c in ["שם מקום ההתמחות","מקום התמחות","Site","Placement Site"]), None)
            col_field = next((c for c in df.columns if c in ["תחום ההתמחות במוסד","תחום","Field"]), None)
            col_score = next((c for c in df.columns if c in ["אחוז התאמה","Score","Match %","אחוז התאמה (%)"]), None)

            if not col_site:
                return render_template("analytics.html", error="לא נמצאה עמודת 'שם מקום ההתמחות' (או Site).")
            if not col_field:
                col_field = col_site  # אם אין תחום – נפיל לפי מקום
            # טבלאות
            by_site = df.groupby(col_site).size().reset_index(name="מספר סטודנטים").sort_values("מספר סטודנטים", ascending=False)
            by_field = df.groupby(col_field).size().reset_index(name="מספר סטודנטים").sort_values("מספר סטודנטים", ascending=False)

            score_avg = []
            if col_score:
                score_avg = (
                    df.groupby(col_site)[col_score].mean()
                    .reset_index(name="ממוצע התאמה")
                    .sort_values("ממוצע התאמה", ascending=False)
                )

            tables = {
                "cols": {"site": col_site, "field": col_field},
                "by_site": by_site.to_dict(orient="records"),
                "by_field": by_field.to_dict(orient="records"),
                "score_avg": score_avg.to_dict(orient="records") if len(score_avg) else []
            }

            charts = {
                "site_labels": by_site[col_site].tolist(),
                "site_values": by_site["מספר סטודנטים"].tolist(),
                "field_labels": by_field[col_field].tolist(),
                "field_values": by_field["מספר סטודנטים"].tolist(),
                "avg_labels": score_avg[col_site].tolist() if len(score_avg) else [],
                "avg_values": score_avg["ממוצע התאמה"].tolist() if len(score_avg) else []
            }

            return render_template("analytics.html", tables=tables, charts=charts)

        except Exception as e:
            return render_template("analytics.html", error=f"שגיאה בקריאת הקובץ: {e}")

    return render_template("analytics.html")

# ============== קיצורים ללינקים חיצוניים (אופציונלי) ==============
@app.route("/students-form")
def students_form():
    return redirect("https://www.studentssurvey.org")

@app.route("/mentors-form")
def mentors_form():
    return redirect("https://www.studentsplacement.org")

@app.route("/placement-system")
def placement_system():
    return redirect("https://www.studentsplacement.org")

if __name__ == "__main__":
    app.run(debug=True)
