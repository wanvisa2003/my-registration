import os
from flask import Flask, request, render_template, redirect, url_for, flash, send_from_directory
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import csv
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

REGISTRATION_FILE = "registrations.csv"
SELECTED_FILE = "selected.csv"

# Function to initialize CSV files
def initialize_csv(file_path, headers):
    if not os.path.exists(file_path):
        with open(file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)

# Ensure CSV files exist before reading
initialize_csv(REGISTRATION_FILE, ["first_name", "last_name", "company_name", "position", "email", "country_code", "phone", "image_path", "timestamp", "type", "status", "code"])
initialize_csv(SELECTED_FILE, ["first_name", "last_name", "company_name", "position", "email", "country_code", "phone", "code", "timestamp", "type"])



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = request.form
        email = data['email']
        image = request.files.get('image')

        # Check for duplicate email in REGISTRATION_FILE
        with open(REGISTRATION_FILE, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            if any(row['email'] == email for row in reader):
                flash("This email has already been registered.", "danger")
                return redirect(url_for("register"))

        # Validate image upload
        if not image or not allowed_file(image.filename):
            flash("Invalid image file. Please upload a valid image (PNG, JPG, JPEG, GIF).", "danger")
            return redirect(url_for("register"))

        # Save the image
        timestamp = datetime.now().isoformat()
        sanitized_filename = re.sub(r'[\\/:*?"<>|]', '_', f"{timestamp}_{image.filename}")
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], sanitized_filename).replace("\\", "/")

        image.save(image_path)

        # Save registration data
        with open(REGISTRATION_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                data['first_name'], data['last_name'], data['company_name'],
                data['position'], email, data['country_code'], data['phone'],
                image_path, timestamp, "pre-register", "pending", ""  # Default: pending, No code
            ])

        flash("Registration successful!", "success")
        return redirect(url_for("success"))

    return render_template("register.html")


@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        email = request.form.get("email")
        code = request.form.get("code")

        selected_user = None
        updated_rows = []

        # อ่านไฟล์และอัปเดตสถานะ
        with open(REGISTRATION_FILE, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["email"] == email:
                    row["status"] = "selected"  # เปลี่ยนสถานะเป็น selected
                    row["code"] = code  # บันทึกโค้ดที่ส่งให้
                    selected_user = row
                updated_rows.append(row)

        if not selected_user:
            flash(f"User with email {email} not found.", "danger")
            return redirect(url_for("admin"))

        # เขียนข้อมูลกลับไปที่ไฟล์เดิม
        with open(REGISTRATION_FILE, mode='w', newline='', encoding='utf-8') as file:
            fieldnames = ["first_name", "last_name", "company_name", "position", "email", 
                          "country_code", "phone", "image_path", "timestamp", "type", "status", "code"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_rows)

        # ส่งอีเมลไปยังผู้ถูกคัดเลือก
        subject = "Event Confirmation Code"
        body = (
            f"Dear {selected_user['first_name']} {selected_user['last_name']},\n\n"
            f"Congratulations! You have been selected in the Pre-Register system.\n"
            f"Please use this code to confirm your registration: {code}\n\n"
            f"Thank you."
        )

        try:
            send_email(email, subject, body)
            flash(f"Code sent successfully to {email}!", "success")
        except Exception as e:
            flash(f"Failed to send code: {str(e)}", "danger")

        return redirect(url_for("admin"))

    # โหลดข้อมูลจาก REGISTRATION_FILE
    registrations = []
    with open(REGISTRATION_FILE, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        registrations = list(reader)

    # Load selected emails
    sent_emails = {}  # ใช้ dict แทน set
    with open(SELECTED_FILE, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            sent_emails[row["email"]] = row["code"]  # เก็บอีเมลและโค้ด

    print(f"Sent Emails: {sent_emails}")
    return render_template("admin.html", registrations=registrations, sent_emails=sent_emails)


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

    try:
        # Connect to SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(from_email, to_email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


if __name__ == "__main__":
    app.run(debug=True)
