# app.py
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.config['SECRET_KEY'] = "change-this-key"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # כאן בעתיד אפשר לחבר למייל / DB
        flash("הפנייה נשלחה בהצלחה! נחזור אליך בהקדם.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # דמו בלבד – בלי לוגיקת התחברות אמיתית.
        email = request.form.get("email")
        password = request.form.get("password")
        if email and password:
            flash("ניסיון התחברות נקלט (דמו).", "success")
        else:
            flash("נא למלא את כל השדות.", "error")
        return redirect(url_for("login"))
    return render_template("login.html")


# נתיבי דמו לכפתורים בדף הבית
@app.route("/students-form")
def students_form():
    return "<h2>כאן יהיה שאלון סטודנטים (דף דמו זמני)</h2>"

@app.route("/mentors-form")
def mentors_form():
    return "<h2>כאן יהיה מיפוי מדריכים (דף דמו זמני)</h2>"

if __name__ == "__main__":
    app.run(debug=True)
