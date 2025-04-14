from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
import smtplib
from email.message import EmailMessage
import os

# ====================
# App Configuration
# ====================
app = Flask(__name__)
app.secret_key = "your_secret_key"

# SQLite DB Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Email Configuration
OFFICIAL_EMAIL = "vetrikumar6380268095@gmail.com"       # Replace with your Gmail
OFFICIAL_PASSWORD = "gbbzzxlspddzqyya"                # Use Gmail App Password

# ====================
# Database Models
# ====================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

# ====================
# Email Helpers
# ====================
def send_registration_email(user_email):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(OFFICIAL_EMAIL, OFFICIAL_PASSWORD)
        subject = "Event Registration Successful"
        body = "✅ You have successfully registered for the Event Management System."
        email_message = f"Subject: {subject}\n\n{body}"
        server.sendmail(OFFICIAL_EMAIL, user_email, email_message)
        server.quit()
    except Exception as e:
        print("Email to user failed:", e)

def send_registration_notice_to_admin(user_email):
    try:
        msg = EmailMessage()
        msg['Subject'] = 'New Event Registration'
        msg['From'] = OFFICIAL_EMAIL
        msg['To'] = OFFICIAL_EMAIL
        msg.set_content(f"User with email {user_email} has registered.")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(OFFICIAL_EMAIL, OFFICIAL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print("Admin notification failed:", e)

def send_event_creation_email(event_name):
    try:
        msg = EmailMessage()
        msg['Subject'] = 'New Event Created'
        msg['From'] = OFFICIAL_EMAIL
        msg['To'] = OFFICIAL_EMAIL
        msg.set_content(f"A new event '{event_name}' has been created.")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(OFFICIAL_EMAIL, OFFICIAL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print("Failed to send creation email:", e)

def send_event_cancellation_email(event_name):
    try:
        msg = EmailMessage()
        msg['Subject'] = 'Event Cancelled'
        msg['From'] = OFFICIAL_EMAIL
        msg['To'] = OFFICIAL_EMAIL
        msg.set_content(f"The event '{event_name}' has been cancelled.")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(OFFICIAL_EMAIL, OFFICIAL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print("Failed to send cancellation email:", e)

# ====================
# Routes
# ====================

# Dashboard (First Page After Login)
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

# Home shows Upcoming Events
@app.route('/home')
def home():
    events = Event.query.all()
    return render_template("home.html", events=events)

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash("⚠️ Email already registered.")
            return redirect(url_for('register'))

        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        send_registration_email(email)
        send_registration_notice_to_admin(email)
        message = f"✅ Registered successfully! Confirmation sent to {email}"
        return render_template("register.html", message=message)
    return render_template("register.html", message=message)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            flash("✅ Login successful!")
            return redirect(url_for('dashboard'))
        flash("❌ Invalid email or password.")
    return render_template("login.html")

@app.route('/events')
def events_list():
    events = Event.query.all()
    return render_template('events.html', events=events)

@app.route('/create-event', methods=['GET', 'POST'])
def create_event():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        location = request.form['location']
        description = request.form['description']
        event = Event(name=name, date=date, location=location, description=description)
        db.session.add(event)
        db.session.commit()
        send_event_creation_email(name)
        flash(f"🎉 Event '{name}' created successfully!")
        return redirect(url_for('home'))
    return render_template("create_event.html")

@app.route('/cancel-event/<int:event_id>', methods=['POST'])
def cancel_event(event_id):
    if 'user_id' not in session:
        abort(403)
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    send_event_cancellation_email(event.name)
    flash(f"❌ Event '{event.name}' cancelled successfully.")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash("👋 You have been logged out.")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)