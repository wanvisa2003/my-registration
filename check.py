import os
from flask import Flask, request, render_template, redirect, url_for, flash
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'

REGISTRATION_FILE = "registrations.csv"  # Pre-Register
SELECTED_FILE = "selected.csv"  # Register

# Function to initialize CSV files
def initialize_csv(file_path, headers):
    if not os.path.exists(file_path):
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)

# Ensure CSV files exist before reading
initialize_csv(REGISTRATION_FILE, ["first_name", "last_name", "company_name", "position", "email", "country_code", "phone", "image_path", "timestamp", "type", "status"])
initialize_csv(SELECTED_FILE, ["first_name", "last_name", "company_name", "position", "email", "country_code", "phone", "code", "timestamp", "type"])

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/confirm", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # รับค่าจากฟอร์ม
        data = request.form
        first_name = data['first_name']
        last_name = data['last_name']
        company_name = data['company_name']
        position = data['position']
        email = data['email']
        country_code = data['country_code']
        phone = data['phone']
        code = data['code']
        timestamp = datetime.now().isoformat()

        # Capitalize first letter and make other letters lowercase
        first_name = data['first_name'].strip()
        last_name = data['last_name'].strip()

        first_name = first_name[0].upper() + first_name[1:].lower() if first_name else ""
        last_name = last_name[0].upper() + last_name[1:].lower() if last_name else ""


       
        with open(SELECTED_FILE, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["email"] == email:
                    flash("This email has already been registered. Please contact Rungaradee at 0613288930.", "danger")
                    return redirect(url_for("register"))
                if row["code"] == code:
                    flash("This code has already been used. Please contact Rungaradee at 0613288930.", "danger")
                    return redirect(url_for("register"))

       
        with open(SELECTED_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([first_name, last_name, company_name, position, email, 
                             country_code, phone, code, timestamp, "register"])

      
        subject = "Registration Successful"
        body = (f"Dear {first_name} {last_name},\n\n"
                f"You have successfully registered with the code: {code}. "
                f"Please present this email at the event entrance.\n\n"
                f"Thank you!")
        try:
            send_email(email, subject, body)
            flash("Registration successful! A confirmation email has been sent to your email address.", "success")
        except Exception as e:
            flash(f"Registration successful, but failed to send email: {str(e)}", "warning")

        return redirect(url_for("success"))

    return render_template("confirm.html")


@app.route("/admin", methods=["GET"])
def admin():
    registrations = {}

    try:
        # โหลดข้อมูลจาก registrations.csv (Pre-Register)
        if os.path.exists(REGISTRATION_FILE):
            with open(REGISTRATION_FILE, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    email = row["email"]
                    row["status"] = row.get("status", "pending")  # ค่าเริ่มต้น pending
                    row["action"] = "Enter Code"  # Default Action
                    registrations[email] = row  # เก็บข้อมูลโดยใช้ email เป็น key

        # โหลดข้อมูลจาก selected.csv (Register)
        if os.path.exists(SELECTED_FILE):
            with open(SELECTED_FILE, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    email = row["email"]
                    if email in registrations:
                        # อัปเดตข้อมูลหากมีอยู่แล้วใน registrations
                        registrations[email]["type"] = "register"
                        registrations[email]["code"] = row["code"]
                        registrations[email]["status"] = "registered"
                        registrations[email]["action"] = f"Submitted (Code: {row['code']})"
                    else:
                        # ถ้ายังไม่มีใน registrations ให้เพิ่มเข้าไป
                        row["type"] = "register"
                        row["status"] = "registered"
                        row["action"] = f"Submitted (Code: {row['code']})"
                        registrations[email] = row

        for email, user_data in registrations.items():
            if user_data["type"] == "register":
                user_data["action"] = f"Submitted (Code: {user_data['code']})"

        # เรียงข้อมูลตาม timestamp
        registrations = sorted(registrations.values(), key=lambda x: x.get("timestamp", ""), reverse=True)

    except Exception as e:
        flash(f"Error loading data: {str(e)}", "danger")
        print("DEBUG: Error ->", str(e))

    return render_template("admin.html", registrations=registrations)

@app.route("/success")
def success():
    return render_template("success.html")

def send_email(to_email, subject, body):
    # Replace these values with actual credentials
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_username = "email"
    smtp_password = "token"  # Replace with your App Password
    from_email = "email"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(from_email, to_email, msg.as_string())

if __name__ == "__main__":
    app.run(debug=True)
