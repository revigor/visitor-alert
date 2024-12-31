from flask import Flask, render_template, request, redirect, url_for, flash
import qrcode
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # For flash messages

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///warehouse.db"  # Database file
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Configure logging. Might not be needed anymore.
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static/uploads")
QR_FOLDER = os.path.join(os.path.dirname(__file__), "static/qrcodes")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

# Configure upload folders
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static/uploads")
QR_FOLDER = os.path.join(os.path.dirname(__file__), "static/qrcodes")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- DATABASE MODELS ---
class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    photo_path = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    truck_license = db.Column(db.String(50), nullable=False)
    card_id = db.Column(db.String(50), unique=True, nullable=False)
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)
    check_out_time = db.Column(db.DateTime, nullable=True)

# --- ROUTES ---
# Add routes for visitors, drivers, and logs as described earlier.

# Visitor Check-In Route (Existing)
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        visitor_name = request.form.get("visitor_name")
        company_name = request.form.get("company_name")
        purpose = request.form.get("purpose")
        department_choice = request.form.get("department")
        photo = request.files.get("photo")

        photo_path = None
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            photo.save(photo_path)

        department_names = {"1": "HR", "2": "IT", "3": "Sales", "4": "Other"}
        department_name = department_names.get(department_choice, "HR")

        visitor = Visitor(
            name=visitor_name,
            company_name=company_name,
            purpose=purpose,
            department=department_name,
            photo_path=photo_path,
        )
        db.session.add(visitor)
        db.session.commit()

        flash(f"Visitor {visitor_name} checked in successfully!", "success")
        return redirect(url_for("index"))
    return render_template("index.html")

# Driver Management Route
@app.route("/drivers", methods=["GET", "POST"])
def drivers():
    if request.method == "POST":
        driver_name = request.form.get("driver_name")
        company_name = request.form.get("company_name")
        truck_license = request.form.get("truck_license")
        card_id = request.form.get("card_id")

        driver = Driver(
            name=driver_name,
            company_name=company_name,
            truck_license=truck_license,
            card_id=card_id,
        )
        db.session.add(driver)
        db.session.commit()

        flash(f"Driver {driver_name} checked in successfully!", "success")
        return redirect(url_for("drivers"))

    active_drivers = Driver.query.filter(Driver.check_out_time.is_(None)).all()
    return render_template("drivers.html", drivers=active_drivers)

# Driver Check-Out Route
@app.route("/checkout/<card_id>", methods=["POST"])
def checkout(card_id):
    driver = Driver.query.filter_by(card_id=card_id).first()
    if driver:
        driver.check_out_time = datetime.utcnow()
        db.session.commit()
        flash(f"Driver with Card ID {card_id} checked out successfully!", "success")
    else:
        flash("Invalid Card ID. No driver found.", "danger")
    return redirect(url_for("drivers"))

# Logs Route
@app.route("/logs")
def logs():
    visitors = Visitor.query.all()
    drivers = Driver.query.all()
    return render_template("logs.html", visitors=visitors, drivers=drivers)

# --- MAIN ---
if __name__ == "__main__":
    app.run(debug=True)