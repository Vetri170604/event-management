from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from flask_sqlalchemy import SQLAlchemy
import smtplib
from email.message import EmailMessage
import os
from flask_dance.contrib.google import make_google_blueprint, google

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key")

# SQLite DB setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------- GOOGLE OAUTH CONFIG ----------------
app.config["OAUTHLIB_INSECURE_TRANSPORT"] = True  # Only for development (not for production)
google_bp = make_google_blueprint(
    client_id="YOUR_GOOGLE_CLIENT_ID",
    client_secret="YOUR_GOOGLE_CLIENT_SECRET",
    scope=["profile", "email"],
    redirect_to="google_login"
)
app.register_blueprint(google_bp, url_prefix="/login")

# ---------------- EMAIL SETUP ----------------
OFFICIAL_EMAIL = "vetrikumar6380268095@gmail.com"
OFFICIAL_PASSWORD = "gbbzzxlspddzqyya"

# ---------------- MODELS ----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=True)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)

# ---------------- EMAIL FUNCTION ----------------
def send_email(subject, content, recipient):
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = OFFICIAL_EMAIL
        msg['To'] = recipient
        msg.set_content(content)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(OFFICIAL_EMAIL, OFFICIAL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print("Email sending failed:", e)

# ---------------- ROUTES ----------------
@app.route('/')
def dashboard():
    events = Event.query.all()
    return render_template('dashboard.html', events=events)

@app.route('/home')
def home():
    events = Event.query.all()
    return render_template("home.html", events=events)

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/start-create-event')
def start_create_event():
    if 'user_id' not in session:
        session['next'] = 'create_event'
        return redirect(url_for('register'))
    return redirect(url_for('create_event'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("⚠️ Email already registered. Please login.")
            return redirect(url_for('login'))

        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        send_email("Registration Successful", "You have successfully registered!", email)
        send_email("New User Registered", f"{email} just registered!", OFFICIAL_EMAIL)

        flash("✅ Registered successfully. Please login now.")
        return redirect(url_for('login'))

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session['user_id'] = user.id
            session['user_email'] = user.email
            flash("✅ Logged in successfully!")
            return redirect(url_for('create_event'))
        else:
            flash("❌ Invalid login. Please try again.")
    return render_template("login.html")

@app.route('/login/google')
def google_login():
    if not google.authorized:
        # This will show the Google login page
        return redirect(google.authorization_url())

    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info from Google.")
        return redirect(url_for("register"))

    email = resp.json()["email"]
    user = User.query.filter_by(email=email).first()

    if not user:
        new_user = User(email=email, password=None)
        db.session.add(new_user)
        db.session.commit()
        send_email("Registered with Google", f"You successfully registered with Google: {email}", email)

    session['user_email'] = email
    session['user_id'] = User.query.filter_by(email=email).first().id

    flash("✅ Logged in with Google!")
    return redirect(url_for('create_event'))

@app.route('/create-event', methods=['GET', 'POST'])
def create_event():
    if 'user_id' not in session:
        session['next'] = 'create_event'
        return redirect(url_for('register'))

    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        location = request.form['location']
        description = request.form['description']

        new_event = Event(name=name, date=date, location=location, description=description)
        db.session.add(new_event)
        db.session.commit()

        user_email = session.get('user_email')
        send_email("Event Created", f"Your event '{name}' has been created.", user_email)
        send_email("New Event Added", f"User {user_email} created event '{name}'", OFFICIAL_EMAIL)

        flash(f"🎉 You registered the event: {name}")
        return redirect(url_for('home'))

    return render_template("create_event.html")

@app.route('/cancel-event/<int:event_id>', methods=['POST'])
def cancel_event(event_id):
    if 'user_id' not in session:
        abort(403)

    event = Event.query.get_or_404(event_id)
    user_email = session.get('user_email')

    db.session.delete(event)
    db.session.commit()

    send_email("Event Cancelled", f"Your event '{event.name}' was cancelled.", user_email)
    send_email("Event Deleted", f"{user_email} cancelled the event '{event.name}'", OFFICIAL_EMAIL)

    flash(f"❌ Event '{event.name}' cancelled successfully.")
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.clear()
    flash("👋 Logged out successfully.")
    return redirect(url_for('dashboard'))

# ---------------- INIT APP ----------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
