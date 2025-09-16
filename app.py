from flask import Flask, render_template, request, redirect, send_file
import pandas as pd
import os

app = Flask(__name__)
FILE_NAME = "placement_attendance.xlsx"

# Ensure Excel file exists
if not os.path.exists(FILE_NAME):
    pd.DataFrame(columns=["Name", "Roll No", "Date", "Company", "Status"]).to_excel(FILE_NAME, index=False)

@app.route('/', methods=["GET", "POST"])
def index():
    df = pd.read_excel(FILE_NAME)

    filter_company = request.form.get("filter_company")
    filter_date = request.form.get("filter_date")

    if filter_company and filter_company.strip():
        df = df[df["Company"].str.contains(filter_company.strip(), case=False, na=False)]
    if filter_date and filter_date.strip():
        df = df[df["Date"].astype(str) == filter_date]

    records = df.to_dict(orient="records")
    return render_template("index.html", records=records)

@app.route('/submit', methods=["POST"])
def submit():
    df = pd.read_excel(FILE_NAME)
    new_data = {
        "Name": request.form.get("name"),
        "Roll No": request.form.get("roll"),
        "Date": request.form.get("date"),
        "Company": request.form.get("company"),
        "Status": request.form.get("status")
    }
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_excel(FILE_NAME, index=False)
    return redirect('/')

@app.route('/download')
def download():
    return send_file(FILE_NAME, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
