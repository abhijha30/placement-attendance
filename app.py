from flask import Flask, render_template, request, redirect, send_file, session, url_for
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "super-secret-key"
FILE_NAME = "placement_attendance.xlsx"
ADMIN_PASSWORD = "itsplacement"  # change this

# Create Excel if missing
if not os.path.exists(FILE_NAME):
    pd.DataFrame(columns=["Name", "Roll No", "Course", "Section", "Date", "Company", "Status"]).to_excel(FILE_NAME, index=False)

# ---------------- Student Panel ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        df = pd.read_excel(FILE_NAME)
        new_data = {
            "Name": request.form.get("name"),
            "Roll No": request.form.get("roll"),
            "Course": request.form.get("course"),
            "Section": request.form.get("section"),
            "Date": request.form.get("date"),
            "Company": request.form.get("company"),
            "Status": request.form.get("status")
        }
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        df.to_excel(FILE_NAME, index=False)
        return render_template("submitted.html")
    return render_template("form.html")

# ---------------- Admin Login ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("records"))
        else:
            return render_template("admin.html", error="❌ Wrong password!")
    return render_template("admin.html", error=None)

# ---------------- Admin Panel ----------------
@app.route("/records")
def records():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    df = pd.read_excel(FILE_NAME)
    records = df.to_dict(orient="records")
    return render_template("records.html", records=records)

@app.route("/download")
def download():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    return send_file(FILE_NAME, as_attachment=True)

# ---------------- Logout ----------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))

# ✅ Vercel expects this
def handler(event, context):
    return app(event, context)

if __name__ == "__main__":
    app.run(debug=True)
