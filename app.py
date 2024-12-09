from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import logging
import os
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # For flash messages

# Configure logging
logging.basicConfig(filename='app.log', level=logging.ERROR)

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static/uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# SMTP2Go API Parameters
SMTP2GO_API_URL = "https://api.smtp2go.com/v3/email/send"
SMTP2GO_API_KEY = "api-43E83469CC704967918416A4701A050C"  # Replace with your SMTP2Go API key
SENDER_EMAIL = 'jorge.prado@royalexpressinc.com'
DEFAULT_DEPARTMENT_EMAIL = 'hr_TEST_@royalexpressinc.com'  # Default HR email

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to send email
def send_email(recipient_email, visitor_name, company_name, purpose, department):
    try:
        # Prepare email data
        email_data = {
            "api_key": SMTP2GO_API_KEY,
            "to": [recipient_email],
            "sender": SENDER_EMAIL,
            "subject": f"Visitor Notification - {visitor_name}",
            "text_body": (
                f"Visitor Name: {visitor_name}\n"
                f"Company Name: {company_name}\n"
                f"Purpose: {purpose}\n"
                f"Department: {department}\n"
            ),
            "html_body": (
                f"<p><strong>Visitor Name:</strong> {visitor_name}</p>"
                f"<p><strong>Company Name:</strong> {company_name}</p>"
                f"<p><strong>Purpose:</strong> {purpose}</p>"
                f"<p><strong>Department:</strong> {department}</p>"
            ),
        }

        if not visitor_name or not purpose or not company_name:
            flash("All fields are required.", "danger")
            return redirect(url_for("index"))

        # Send email via SMTP2Go API
        response = requests.post(SMTP2GO_API_URL, json=email_data)

        # Handle API response
        if response.status_code == 200:
            return True
        else:
            print(f"Failed to send email: {response.status_code}, {response.text}")
            return False
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# Routes
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Get form data
        visitor_name = request.form.get("visitor_name")
        company_name = request.form.get("company_name")
        purpose = request.form.get("purpose")
        department_choice = request.form.get("department")

        # Handle photo upload securely
        photo = request.files.get("photo")
        if photo and allowed_file(photo.filename):
            try:
                # Sanitize the filename
                filename = secure_filename(photo.filename)
                photo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                logging.info(f"Attempting to save photo to: {photo_path}")
                photo.save(photo_path)
                logging.info(f"Photo saved to {photo_path}")
            except Exception as e:
                logging.error(f"Error saving photo: {e}")
                flash("Failed to save the photo. Please try again.", "danger")
                return redirect(url_for("index"))
        elif photo:
            flash("Invalid file type. Please upload a PNG, JPG, JPEG, or GIF file.", "danger")
            return redirect(url_for("index"))

        # Map department to email
        department_emails = {
            "1": "hr_TEST_@royalexpressinc.com",
            "2": "revigor5@gmail.com",
            "3": "maritza.canales@royalexpressinc.com",
        }
        department_names = {
            "1": "HR",
            "2": "IT",
            "3": "Sales",
            "4": "Other",
        }
        department_email = department_emails.get(department_choice, DEFAULT_DEPARTMENT_EMAIL)
        department_name = department_names.get(department_choice, "HR")

        # Send email
        email_sent = send_email(department_email, visitor_name, company_name, purpose, department_name)

        if email_sent:
            return redirect(url_for("success"))
        else:
            return redirect(url_for("error"))

    return render_template("index.html")

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/error")
def error():
    return render_template("error.html")
