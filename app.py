from flask import Flask, render_template, request, redirect, send_file, session, url_for
import pandas as pd
import io
import os
from supabase import create_client, Client
from postgrest.exceptions import APIError

app = Flask(__name__)
app.secret_key = "super-secret-key"

# ---------------- Admin Password (Vercel or default) ----------------
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "itsplacement")

# ---------------- Supabase Setup (MUST be env variables) ----------------
SUPABASE_URL = os.environ.get("https://dsasywpfgomnrhhpvfdh.supabase.co")
SUPABASE_KEY = os.environ.get("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRzYXN5d3BmZ29tbnJoaHB2ZmRoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgyNzg1NDYsImV4cCI6MjA3Mzg1NDU0Nn0.YUbh42wUoZFON9NizD-vmrKGgea6D1tSMBIFAuFHX8s")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- Student Panel ----------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        roll = request.form.get("roll")
        date = request.form.get("date")
        company = request.form.get("company")
        course = request.form.get("course")

        if not roll or not date or not company or not course:
            return render_template("submitted.html", message="⚠ Missing required fields!")

        try:
            data = {
                "name": request.form.get("name"),
                "roll": roll,
                "course": course,
                "section": request.form.get("section"),
                "date": date,
                "company": company,
                "status": request.form.get("status"),
                "on_spot": request.form.get("on_spot")
            }

            supabase.table("attendance").insert(data).execute()

            return render_template("submitted.html",
                                   message="✅ Attendance submitted successfully!")

        except APIError as e:
            if "duplicate key value violates unique constraint" in str(e):
                return render_template(
                    "submitted.html",
                    message="⚠ Already submitted for this course & company today."
                )
            return render_template("submitted.html", message=f"⚠ Error: {str(e)}")

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

    return render_template(
        "records.html",
        records=records,
        selected_date=selected_date,
        selected_company=selected_company,
        selected_course=selected_course
    )


# ---------------- Download Excel (FINAL FIX) ----------------
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

    try:
        response = query.execute()
        records = response.data

        if not records:
            return "⚠ No records found!"

        df = pd.DataFrame(records)
        df = df.astype(str)  # Prevent Excel-type errors

        # File naming
        file_name = "attendance.xlsx"
        if filter_date:
            file_name = f"{filter_date}_attendance.xlsx"
        elif filter_company:
            file_name = f"{filter_company}_attendance.xlsx"
        elif filter_course:
            file_name = f"{filter_course}_attendance.xlsx"

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

    except Exception as e:
        return f"❌ Excel generation failed: {str(e)}"


# ---------------- Logout ----------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin"))


# ---------------- Vercel Entry ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
