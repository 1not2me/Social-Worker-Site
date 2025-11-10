# app.py
# -*- coding: utf-8 -*-

import os
from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

# יצירת האפליקציה
app = Flask(__name__)

# מפתח להצפנת session
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET", "devkey")

# סיסמה סודית למרצים - מגיעה מרנדר (Environment Variable)
LECTURER_SECRET = os.environ.get("LECTURER_SECRET")

if not LECTURER_SECRET:
    # אם שכחנו להגדיר ברנדר - נעצור כדי שלא ירוץ לא מאובטח
    raise RuntimeError("LECTURER_SECRET is not set in environment")


# ---------- דף ראשי רגיל (תשאירי פה את הדף שלך) ----------
@app.route("/")
def index():
    # הדף הציבורי שלך (כמו בתמונה היפה)
    return render_template("index.html")


# ---------- פונקציה לבדוק אם מרצה מחובר ----------
def lecturer_login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get("is_lecturer"):
            return view_func(*args, **kwargs)
        # אם לא מחובר -> מעבירים לדף התחברות
        return redirect(url_for("lecturer_login"))
    return wrapper


# ---------- התחברות מרצים ----------
@app.route("/login", methods=["GET", "POST"])
def lecturer_login():
    error = None

    if request.method == "POST":
        password = request.form.get("password", "")

        if password == LECTURER_SECRET:
            # סימון ב-session שהמשתמש מרצה
            session["is_lecturer"] = True
            return redirect(url_for("lecturers_area"))
        else:
            error = "סיסמה שגויה. אנא בדקו עם רואן."

    return render_template("login.html", error=error)


# ---------- יציאה ----------
@app.route("/logout")
def logout():
    session.clear()
    flash("התנתקת בהצלחה.", "info")
    return redirect(url_for("index"))


# ---------- אזור מרצים מוגן ----------
@app.route("/lecturers")
@lecturer_login_required
def lecturers_area():
    # כאן תכניסי את מה שמיועד רק למרצים:
    # טבלאות, קישורים לשאלונים, קבצים, וכו'
    return render_template("lecturers.html")


# ---------- להרצה מקומית ----------
if __name__ == "__main__":
    # להרצה מקומית; ברנדר מריץ לפי ה-Start Command
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
