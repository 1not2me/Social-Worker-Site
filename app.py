# app.py
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, flash
@app.before_request
def maintenance_mode():
    if os.getenv("MAINTENANCE_MODE", "0") == "1":
        html = """
        <html lang="he" dir="rtl">
        <head>
          <meta charset="utf-8">
          <title>האתר סגור</title>
          <style>
            body{
              font-family:system-ui,-apple-system,Segoe UI,Heebo,Arial;
              background:#f8fafc;
              direction:rtl;
              text-align:center;
              margin:0;
              padding-top:120px;
              color:#111827;
            }
            .box{
              display:inline-block;
              padding:32px 40px;
              border-radius:18px;
              background:#ffffff;
              box-shadow:0 10px 30px rgba(15,23,42,.08);
              border:1px solid #e5e7eb;
            }
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
