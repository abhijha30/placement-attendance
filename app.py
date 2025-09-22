from flask import Flask, render_template, request, redirect, send_file, session, url_for
import pandas as pd
import io
import os
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "super-secret-key"
ADMIN_PASSWORD = "itsplacement"

# ---------------- Supabase Setup ----------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- Student Panel ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        roll = request.form.get("roll")
        date = request.form.get("date")
        company = request.form.get("company")

        # 🔒 Prevent duplicate entry
        existing = supabase.table("attendance").select("*").eq("roll", roll).eq("date", date).eq("company", company).execute()
        if existing.data:
            return render_template("submitted.html", message="⚠ You have already submitted attendance for this company today.")

        data = {
            "name": request.form.get("name"),
            "roll": roll,
            "course": request.form.get("course"),
            "section": request.form.get("section"),
            "date": date,
            "company": company,
            "status": request.form.get("status"),
            "on_spot": request.form.get("on_spot")  # ✅ NEW field
        }
        supabase.table("attendance").insert(data).execute()
        return render_template("submitted.html", message="✅ Attendance submitted successfully!")
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

    selected_date = request.args.get("filter_date")
    selected_company = request.args.get("filter_company")
    selected_course = request.args.get("filter_course")

    query = supabase.table("attendance").select("*")

    if selected_date:
        query = query.eq("date", selected_date)
    if selected_company:
        query = query.ilike("company", f"%{selected_company}%")
    if selected_course:
        query = query.eq("course", selected_course)

    response = query.execute()
    records = response.data

    return render_template("records.html", records=records, 
                           selected_date=selected_date, 
                           selected_company=selected_company,
                           selected_course=selected_course)

# ---------------- Download as Excel ----------------
@app.route("/download")
def download():
    if not session.get("admin"):
        return redirect(url_for("admin"))

    filter_date = request.args.get("filter_date", "").strip()
    filter_company = request.args.get("filter_company", "").strip()
    filter_course = request.args.get("filter_course", "").strip()

    query = supabase.table("attendance").select("*")

    if filter_date:
        query = query.eq("date", filter_date)
    if filter_company:
        query = query.ilike("company", f"%{filter_company}%")
    if filter_course:
        query = query.eq("course", filter_course)

    response = query.execute()
    records = response.data if response.data else []

    if not records:
        return "⚠ No records found!"

    df = pd.DataFrame(records)

    # File name logic
    file_name = "attendance.xlsx"
    if filter_course:
        file_name = f"{filter_course}_attendance.xlsx"
    if filter_company:
        file_name = f"{filter_company}_attendance.xlsx"
    if filter_date:
        file_name = f"{filter_date}_attendance.xlsx"

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Attendance")
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=file_name,
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
