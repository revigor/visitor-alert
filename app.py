from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import base64
import pytz

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # For flash messages

LOCAL_TZ = pytz.timezone("America/Chicago")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///warehouse.db"  # Database file
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Configure upload folders
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static/uploads")
QR_FOLDER = os.path.join(os.path.dirname(__file__), "static/qrcodes")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# SMTP2Go API Parameters
SMTP2GO_API_URL = "https://api.smtp2go.com/v3/email/send"
SMTP2GO_API_KEY = "api-43E83469CC704967918416A4701A050C"  # Replace with your SMTP2Go API key
SENDER_EMAIL = 'jorge.prado@royalexpressinc.com'
DEFAULT_DEPARTMENT_EMAIL = 'hr_TEST_@royalexpressinc.com'  # Default HR email

# Allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# --- DATABASE MODELS ---
class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    personnel = db.Column(db.String(100), nullable=False) 
    photo_path = db.Column(db.String(200), nullable=True)
    badge_number = db.Column(db.Integer, nullable=True)  # Assigned badge number
    check_in_time = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc).astimezone(LOCAL_TZ).replace(microsecond=0))
    check_out_time = db.Column(db.DateTime, nullable=True)  # Set check_out_time as nullable

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    provider_name = db.Column(db.String(100), nullable=False)
    truck_license = db.Column(db.String(50), nullable=False)
    card_id = db.Column(db.String(50), unique=True, nullable=False)
    purpose_of_visit = db.Column(db.String(100), nullable=False)  # New column
    point_of_contact = db.Column(db.String(100), nullable=False)  # New column
    check_in_time = db.Column(db.DateTime, default=lambda: datetime.now().replace(microsecond=0))
    check_out_time = db.Column(db.DateTime, nullable=True)

# --- HELPER FUNCTIONS ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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

        response = requests.post(SMTP2GO_API_URL, json=email_data)

        # Handle API response
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_driver_email(recipient_email, driver_name, provider_name, purpose_of_visit, point_of_contact, check_in_time):
    try:
        # Prepare email data for driver notification
        email_data = {
            "api_key": SMTP2GO_API_KEY,
            "to": [recipient_email],  # Send to security email
            "sender": SENDER_EMAIL,
            "subject": f"Driver Check-In Notification - {driver_name}",
            "text_body": (
                f"Name: {driver_name}\n"
                f"Provider Name: {provider_name}\n"
                f"Purpose of Visit: {purpose_of_visit}\n"
                f"Point of Contact: {point_of_contact}\n"
                f"Check-In Time: {check_in_time}\n"
            ),
            "html_body": (
                f"<p><strong>Driver Name:</strong> {driver_name}</p>"
                f"<p><strong>Provider Name:</strong> {provider_name}</p>"
                f"<p><strong>Purpose of Visit:</strong> {purpose_of_visit}</p>"
                f"<p><strong>Point of Contact:</strong> {point_of_contact}</p>"
                f"<p><strong>Check-In Time:</strong> {check_in_time}</p>"
            ),
        }

        print("Sending check-in email...")  # Debugging
        response = requests.post(SMTP2GO_API_URL, json=email_data)

        # Handle API response
        print(f"Check-in Email Response: {response.status_code}, Response: {response.text}")  # Debugging
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending driver check-in email: {e}")
        return False

def send_driver_checkout_email(recipient_email, driver_name, provider_name, check_out_time, point_of_contact):
    try:
        # Prepare email data for driver check-out notification
        email_data = {
            "api_key": SMTP2GO_API_KEY,
            "to": [recipient_email],  # Send to security email
            "sender": SENDER_EMAIL,
            "subject": f"Driver Check-Out Notification - {driver_name}",
            "text_body": (
                f"Name: {driver_name}\n"
                f"Provider Name: {provider_name}\n"
                f"Point of Contact: {point_of_contact}\n"
                f"Check-Out Time: {check_out_time}\n"
            ),
            "html_body": (
                f"<p><strong>Driver Name:</strong> {driver_name}</p>"
                f"<p><strong>Provider Name:</strong> {provider_name}</p>"
                f"<p><strong>Point of Contact:</strong> {point_of_contact}</p>"
                f"<p><strong>Check-Out Time:</strong> {check_out_time}</p>"
            ),
        }

        print("Sending check-out email...")  # Debugging
        response = requests.post(SMTP2GO_API_URL, json=email_data)

        # Handle API response
        print(f"Check-out Email Response: {response.status_code}, Response: {response.text}")  # Debugging
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending driver check-out email: {e}")
        return False

def get_available_badge():
    assigned_badges = [visitor.badge_number for visitor in Visitor.query.filter(Visitor.badge_number.isnot(None)).all()]
    for badge in range(1, 6):  # Checking badges 1-5
        if badge not in assigned_badges:
            return badge
    return None  # No available badge

# --- ROUTES ---

@app.route("/get_personnel", methods=["GET"])
def get_personnel():
    department = request.args.get("department")
    personnel = {
        "HR": [
            {"name": "Alice Johnson", "email": "hr@royalexpressinc.com"}
        ],
        "IT": [
            {"name": "Ivan Ramirez", "email": "ivan.ramirez@royalexpressinc.com"},
            {"name": "IT-Departament", "email": "wotickets@royalexpressinc.com"},
            {"name": "Carlos Lopez", "email": "revigor5@gmail.com"}
        ],
        "Accounting": [
            {"name": "Lesly Espinoza", "email": "carriersmx@royalexpressinc.com"},
            {"name": "David Mata", "email": "accounting1@royalexpressinc.com"},
            {"name": "Saul Alcorta", "email": "salcorta@royalexpressinc.com"},
            {"name": "Karen Maldonado", "email": "kmaldonado@royalexpressinc.com"}
        ],
        "Settlements": [
            {"name": "Edith Ochoa", "email": "edith@royalexpressinc.com"},
            {"name": "Arleen", "email": "arleen@royalexpressinc.com"}
        ],
        "Fuel": [
            {"name": "Brenda Ceballos", "email": "brendac@royalexpressinc.com"}
        ],
        "Safety": [
            {"name": "Vanesa Uribe", "email": "vanessau@royalexpressinc.com"},
            {"name": "Mauricio", "email": "safety.recruiter@royalexpressinc.com"},
            {"name": "Joyce Zavala", "email": "insurance.handler@royalexpressinc.com"},
            {"name": "Magaly", "email": "safety.clerk@royalexpressinc.com"}
        ],
        "Shop": [
            {"name": "Oscar Garcia", "email": "ogarcia@royalexpressinc.com"},
            {"name": "Mariam Treviño", "email": "mariamt@royalexpressinc.com"}
        ]
    }
    return jsonify(personnel.get(department, []))

# Visitor Check-In Route
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        visitor_name = request.form.get("visitor_name")
        company_name = request.form.get("company_name")
        purpose = request.form.get("purpose")
        department_name = request.form.get("department")  # Directly from the form
        point_of_contact_email = request.form.get("personnel")  # This now contains the selected email
        photo = request.files.get("photo")

        # Handle photo upload
        photo_path = None
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            photo.save(photo_path)

         # 🔥 Assign an available badge
        badge_number = get_available_badge()
        if badge_number is None:
            flash("No visitor badges available. Please wait for one to be returned.", "danger")
            return redirect(url_for("index"))

        # Save visitor to database
        visitor = Visitor(
            name=visitor_name,
            company_name=company_name,
            purpose=purpose,
            department=department_name,
            personnel=point_of_contact_email,  # Save the email of the point of contact
            photo_path=photo_path,
            badge_number=badge_number,  # Store assigned badge
            check_in_time=datetime.now(pytz.utc).astimezone(LOCAL_TZ).replace(microsecond=0),
            check_out_time=None  # ✅ Ensure this is explicitly set to None
        )
        db.session.add(visitor)
        db.session.commit()

        # Send email notification
        email_sent = send_email(
        recipient_email=point_of_contact_email,  # Send the email to the selected contact
        visitor_name=visitor_name,
        company_name=company_name,
        purpose=purpose,
        department=department_name
)
        if email_sent:
            flash(f"Visitor {visitor_name} checked in successfully!", "success")
            flash(f"Assigned Visitor Badge: {badge_number}", "info")  # Show badge assignment
        else:
            flash("Failed to send notification email. Please check the system settings.", "danger")

        return redirect(url_for("index"))
    return render_template("index.html")

# Driver Management Route
@app.route("/drivers", methods=["GET", "POST"])
def drivers():
    if request.method == "POST":
        driver_name = request.form.get("driver_name")
        provider_name = request.form.get("provider_name")
        truck_license = request.form.get("truck_license")
        card_id = request.form.get("card_id")
        purpose_of_visit = request.form.get("purpose_of_visit")  # Get purpose of visit
        point_of_contact = request.form.get("point_of_contact")  # Get point of contact
        photo_data = request.form.get("photo_data")  # Get base64 photo data

        print("Received Data:", {  # Debugging output
            "driver_name": driver_name,
            "provider_name": provider_name,
            "truck_license": truck_license,
            "purpose_of_visit": purpose_of_visit,
            "point_of_contact": point_of_contact,
            "card_id": card_id
        })
        
        # Handle base64 photo data
        photo_path = None
        if photo_data:
            try:
                # Create a unique filename based on the current timestamp
                filename = f"{datetime.now().replace(microsecond=0).strftime('%Y%m%d%H%M')}_driver.jpg"
                photo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

                # Decode the base64 data and save it as an image
                with open(photo_path, "wb") as f:
                    f.write(base64.b64decode(photo_data.split(",")[1]))
            except Exception as e:
                flash("Failed to process the photo. Please try again.", "danger")
                print(f"Error saving photo: {e}")
                return redirect(url_for("drivers"))

        # Check if a driver with the same card_id exists
        existing_driver = Driver.query.filter_by(card_id=card_id).first()

        if existing_driver:
            # If the driver is already checked in
            if existing_driver.check_out_time is None:
                flash(f"Driver with card ID {card_id} is already checked in.", "danger")
                return redirect(url_for("drivers"))

            # If the driver is checked out, reset check_out_time and update details
            existing_driver.name = driver_name
            existing_driver.provider_name = provider_name
            existing_driver.truck_license = truck_license
            existing_driver.purpose_of_visit = purpose_of_visit
            existing_driver.point_of_contact = point_of_contact
            existing_driver.check_in_time = datetime.now().replace(microsecond=0)
            existing_driver.check_out_time = None
            db.session.commit()
            flash(f"Driver {driver_name} has been checked in again.", "success")
        else:
            # If no existing driver with the same card_id, create a new record
            driver = Driver(
                name=driver_name,
                provider_name=provider_name,
                truck_license=truck_license,
                purpose_of_visit=purpose_of_visit,
                point_of_contact=point_of_contact,
                card_id=card_id,
            )
            db.session.add(driver)
            db.session.commit()
            flash(f"Driver {driver_name} checked in successfully!", "success")

        # Automatically send email if the purpose of visit is "Guardia"
        if purpose_of_visit == "Guardia":
            print("Sending check-in email for Guardia...")  # Debugging
            recipient_email = "maritza.canales@royalexpressinc.com"
            email_sent = send_driver_email(
                recipient_email,
                driver_name,
                provider_name,
                purpose_of_visit,
                point_of_contact,
                datetime.now().replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")  # Include formatted check-in time
            )
            if email_sent:
                flash("Notification email sent successfully.", "success")
                print("✅ Email sent successfully!")  # Debugging line
            else:
                flash("Failed to send notification email.", "danger")
                print("❌ Email failed to send!")  # Debugging line

        return redirect(url_for("drivers"))

    # Query active drivers
    active_drivers = Driver.query.filter(Driver.check_out_time.is_(None)).all()
    return render_template("drivers.html", drivers=active_drivers)

# Driver Check-Out Route
@app.route("/checkout/<card_id>", methods=["POST"])
def checkout(card_id):
    driver = Driver.query.filter_by(card_id=card_id).first()
    
    if driver:
        if driver.check_out_time is None:
            driver.check_out_time = datetime.now().replace(microsecond=0)
            db.session.commit()
            flash(f"Driver {driver.name} checked out successfully!", "success")

            # 🚨 Send check-out email if the driver checked in for "Guardia"
            if driver.purpose_of_visit == "Guardia":
                print("Sending check-out email for Guardia...")  # Debugging
                recipient_email = "maritza.canales@royalexpressinc.com"
                email_sent = send_driver_checkout_email(
                    recipient_email,
                    driver.name,
                    driver.provider_name,
                    driver.check_out_time.strftime("%Y-%m-%d %H:%M:%S"),  # Format time for email
                    driver.point_of_contact
                )
                if email_sent:
                    print("✅ Check-out email sent successfully!")  # Debugging line
                else:
                    print("❌ Failed to send check-out email!")  # Debugging line

            return "Driver checked out successfully.", 200
        else:
            return "Driver is already checked out.", 400

    return "Driver not found.", 404

@app.route("/visitor_checkout/<int:visitor_id>", methods=["POST"])
def visitor_checkout(visitor_id):
    visitor = Visitor.query.get(visitor_id)
    
    if visitor:
        if visitor.check_out_time is None:
            visitor.check_out_time = datetime.now(pytz.utc).astimezone(LOCAL_TZ).replace(microsecond=0)  # Set check-out time
            badge_number = visitor.badge_number  # Save the badge number before releasing it
            visitor.badge_number = None  # Release badge number
            db.session.commit()
            flash(f"Visitor {visitor.name} checked out successfully! Badge {badge_number} is now available.", "success")
        else:
            flash(f"Visitor {visitor.name} has already checked out.", "info")
    else:
        flash("Visitor not found.", "danger")

    return redirect(url_for("visitor_logs"))

# Logs Route
@app.route("/logs")
def logs():
    visitors = Visitor.query.all()
    drivers = Driver.query.all()
    return render_template("logs.html", visitors=visitors, drivers=drivers)

@app.route("/visitor_logs")
def visitor_logs():
    visitors = Visitor.query.all()
    return render_template("visitor_logs.html", visitors=visitors)

# --- MAIN ---
if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)