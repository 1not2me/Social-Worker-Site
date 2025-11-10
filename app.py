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
        flash("הפנייה נשלחה בהצלחה! נחזור אליך בהקדם.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        # בדיקת דמו בסיסית: מייל של המכללה + סיסמה לא ריקה
        if email.endswith("@zefat.ac.il") and password:
            # הפניה למערכת המרצים האמיתית
            return redirect("https://students-placement-lecturer.onrender.com")
        else:
            flash("התחברות נכשלה. יש להזין מייל מכללת צפת וסיסמה.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)
