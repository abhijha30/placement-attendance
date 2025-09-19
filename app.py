from flask import Flask, render_template, request, redirect, send_file, session, url_for
import pandas as pd
import io
import os
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "super-secret-key"
ADMIN_PASSWORD = "itsplacement"  # change this

# ---------------- Supabase Setup ----------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- Student Panel ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = {
            "name": request.form.get("name"),
            "roll": request.form.get("roll"),
            "course": request.form.get("course"),
            "section": request.form.get("section"),
            "date": request.form.get("date"),
            "company": request.form.get("company"),
            "status": request.form.get("status"),
        }
        supabase.table("attendance").insert(data).execute()
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
    response = supabase.table("attendance").select("*").execute()
    records = response.data or []   # ✅ safe fallback
    return render_template("records.html", records=records)

# ---------------- Download as Excel ----------------
@app.route("/download")
def download():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    response = supabase.table("attendance").select("*").execute()
    records = response.data or []   # ✅ safe fallback

    if not records:
        return "⚠ No records found in database."

    df = pd.DataFrame(records)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Attendance")
    output.seek(0)   # ✅ reset pointer

    return send_file(
        output,
        as_attachment=True,
        download_name="attendance.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ---------------- Download Company-specific Excel ----------------
@app.route("/download_company", methods=["POST"])
def download_company():
    if not session.get("admin"):
        return redirect(url_for("admin"))

    company = request.form.get("company")
    if not company:
        return "❌ Please enter a company name."

    response = supabase.table("attendance").select("*").eq("company", company).execute()
    records = response.data or []   # ✅ safe fallback

    if not records:
        return f"⚠ No records found for {company}"

    df = pd.DataFrame(records)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=f"{company}_Attendance")
    output.seek(0)   # ✅ reset pointer

    return send_file(
        output,
        as_attachment=True,
        download_name=f"{company}_attendance.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ---------------- Logout ----------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))

# ✅ Vercel entry
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
