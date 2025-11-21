import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import razorpay
import urllib.parse
import requests
import hmac
import hashlib
import base64
import math
import time

# -------------------- FLASK APP -------------------- #
app = Flask(__name__)
app.secret_key = "your_secret_key"

# -------------------- RAZORPAY -------------------- #
RAZORPAY_KEY_ID = "rzp_test_RKFRNhf7xcHQgR"
RAZORPAY_KEY_SECRET = "hRgiFkFXxAFA2fACRGnmwo1F"
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# -------------------- DATABASE PATHS -------------------- #
DB_PATH = "new_user.db"
SALON_DB_PATH = "gloora.db"    # use single DB for salons + slots to avoid cross-DB FK issues
SLOT_DB_PATH = SALON_DB_PATH

# -------------------- GEOAPIFY -------------------- #
GEOAPIFY_KEY = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

# -------------------- UPLOAD FOLDER (inside static so templates can use url_for('static', filename=...)) -------------------- #
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}

# -------------------- DATABASE CONNECTION -------------------- #
def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # enable foreign keys in sqlite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# -------------------- DATABASE INITIALIZATION -------------------- #
def init_user_db():
    if not os.path.exists(DB_PATH):
        with get_db_connection(DB_PATH) as conn:
            conn.execute(
                """
                CREATE TABLE users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                );
                """
            )
            conn.commit()

def init_salon_and_slot_db():
    with get_db_connection(SALON_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='salons'")
        if not cur.fetchone():
            cur.execute(
                """
                CREATE TABLE salons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    lat REAL,
                    lng REAL,
                    contact TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ON',
                    owner_username TEXT DEFAULT '',
                    services TEXT,
                    price REAL,
                    pass_key TEXT NOT NULL,
                    rating_total INTEGER DEFAULT 0,
                    rating_count INTEGER DEFAULT 0,
                    image_path TEXT DEFAULT NULL
                );
                """
            )
        else:
            cur.execute("PRAGMA table_info(salons)")
            cols = [c[1] for c in cur.fetchall()]
            if "rating_total" not in cols:
                cur.execute("ALTER TABLE salons ADD COLUMN rating_total INTEGER DEFAULT 0")
            if "rating_count" not in cols:
                cur.execute("ALTER TABLE salons ADD COLUMN rating_count INTEGER DEFAULT 0")
            if "image_path" not in cols:
                cur.execute("ALTER TABLE salons ADD COLUMN image_path TEXT DEFAULT NULL")
            if "owner_username" not in cols:
                cur.execute("ALTER TABLE salons ADD COLUMN owner_username TEXT DEFAULT ''")

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='slots'")
        if not cur.fetchone():
            cur.execute(
                """
                CREATE TABLE slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    salon_id INTEGER NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    FOREIGN KEY (salon_id) REFERENCES salons(id) ON DELETE CASCADE
                );
                """
            )
        conn.commit()

# init DBs
init_user_db()
init_salon_and_slot_db()

# -------------------- HELPERS -------------------- #
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def save_image(file_storage):
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        return None
    filename = secure_filename(file_storage.filename)
    # unique filename
    filename = f"{int(time.time())}_{filename}"
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file_storage.save(filepath)
    # store path relative to static folder so templates using url_for('static', filename=...) work
    return f"uploads/{filename}"

def haversine(lat1, lon1, lat2, lon2):
    # distance in kilometers
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# -------------------- STATIC PAGES -------------------- #
@app.route("/")
def home():
    return render_template("gender.html", username=session.get("username"))

@app.route("/gender")
def gender():
    return render_template("gender.html", username=session.get("username"))

@app.route("/about")
def about():
    return render_template("about.html", username=session.get("username"))

@app.route("/services_categories")
def services_categories():
    return render_template("services_categories.html", username=session.get("username"))

@app.route("/contact_us")
def contact_us():
    # always render contact page even after logout
    return render_template("contact_us.html", username=session.get("username"))

@app.route("/help")
def help_page():
    username = session.get("username")
    if not username:
        message = " Login Required"
        description = "Please sign in to access personalized help, order support, and chat assistance."
        return render_template("help.html", login_required=True, message=message, description=description, username=None)
    return render_template("help.html", username=username, login_required=False)

@app.route("/term")
def term():
    return render_template("term.html", username=session.get("username"))

@app.route("/cancellation")
def cancellation():
    return render_template("cancellation.html", username=session.get("username"))

@app.route("/privacy")
def privacy():
    return render_template("privacy.html", username=session.get("username"))

# -------------------- AUTH -------------------- #
@app.route("/login_page")
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login_help():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        with get_db_connection(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? AND email=?", (username, email))
            user = cursor.fetchone()
            if user and check_password_hash(user["password"], password):
                session["username"] = username
                session["email"] = email
                flash(f"Welcome back, {username}!", "success")
                return redirect(url_for("help_page"))
            else:
                flash("Invalid credentials!", "error")
                return redirect(url_for("help_page"))
    return render_template("help_login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("gender"))

def handle_auth(action, gender_page):
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    if not username or not email or not password:
        flash("All fields are mandatory!", "error")
        return redirect(url_for(gender_page))
    if not email.lower().endswith("@gmail.com"):
        flash("Please enter a valid Gmail address.", "error")
        return redirect(url_for(gender_page))
    if action == "login" and email.lower() == "admin@gmail.com" and password == "admin123":
        session["admin"] = True
        flash("Welcome, Admin!", "success")
        return redirect(url_for("database_views"))
    with get_db_connection(DB_PATH) as conn:
        cursor = conn.cursor()
        if action == "register":
            hashed_pw = generate_password_hash(password)
            try:
                cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                               (username, email, hashed_pw))
                conn.commit()
                flash("Registration successful! Please login.", "success")
            except sqlite3.IntegrityError:
                flash("Username or Email already exists!", "error")
        elif action == "login":
            cursor.execute("SELECT * FROM users WHERE username=? AND email=?", (username, email))
            user = cursor.fetchone()
            if user and check_password_hash(user["password"], password):
                session["username"] = username
                session["email"] = email
                flash(f"Welcome back, {username}!", "success")
            else:
                flash("Invalid credentials!", "error")
    return redirect(url_for(gender_page))

@app.route("/male", methods=["GET", "POST"])
def male():
    show_login = request.args.get("login") == "1"
    if request.method == "POST":
        return handle_auth(request.form.get("action"), "male")
    return render_template("male_page.html", show_login=show_login, username=session.get("username"))

@app.route("/female", methods=["GET", "POST"])
def female():
    show_login = request.args.get("login") == "1"
    if request.method == "POST":
        return handle_auth(request.form.get("action"), "female")
    return render_template("female_page.html", show_login=show_login, username=session.get("username"))

# -------------------- ROUTE TO SERVE UPLOADS (optional) -------------------- #
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    # serves files from static/uploads if needed
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# -------------------- REGISTER SALON -------------------- #
@app.route("/register_salon", methods=["GET", "POST"])
def register_salon():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        contact = request.form.get("contact", "").strip()
        pass_key = request.form.get("pass_key", "").strip()
        image_file = request.files.get("image")

        if not all([name, city, state, contact, pass_key]):
            flash("All fields including Pass Key are mandatory!", "error")
            return render_template("register_salon.html", username=session.get("username"))

        hashed_pass_key = generate_password_hash(pass_key)
        full_address = f"{address}, {city}, {state}, India" if address else f"{city}, {state}, India"

        lat = None
        lng = None
        try:
            encoded_address = urllib.parse.quote(full_address)
            resp = requests.get(
                f"https://api.geoapify.com/v1/geocode/search?text={encoded_address}&apiKey={GEOAPIFY_KEY}",
                timeout=10
            )
            data = resp.json()
            if data.get("features"):
                lat = data["features"][0]["properties"]["lat"]
                lng = data["features"][0]["properties"]["lon"]
        except Exception:
            flash("Geoapify error. Saving salon without coordinates.", "warning")

        image_path = save_image(image_file)

        with get_db_connection(SALON_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM salons WHERE LOWER(name)=? AND LOWER(address)=?",
                           (name.lower(), full_address.lower()))
            if cursor.fetchone():
                flash("Salon already exists!", "error")
                return render_template("register_salon.html", username=session.get("username"))

            cursor.execute(
                """
                INSERT INTO salons (name, address, lat, lng, contact, status, owner_username, pass_key, image_path)
                VALUES (?, ?, ?, ?, ?, 'ON', ?, ?, ?)
                """,
                (name, full_address, lat, lng, contact, session.get("username") or "", hashed_pass_key, image_path),
            )
            conn.commit()
            salon_id = cursor.lastrowid

        flash("Salon registered successfully with Pass Key!", "success")
        return redirect(url_for("book_slot_for_salon", salon_id=salon_id))

    return render_template("register_salon.html", username=session.get("username"))

# -------------------- SHOW SALONS (search fallback + optional lat/lng sorting) -------------------- #
@app.route("/salons", methods=["GET"])
def show_salons():
    search_query = request.args.get("search", "").strip().lower()
    user_lat = request.args.get("lat", type=float)
    user_lng = request.args.get("lng", type=float)

    with get_db_connection(SALON_DB_PATH) as conn:
        if search_query:
            salons = conn.execute(
                "SELECT * FROM salons WHERE LOWER(name) LIKE ? OR LOWER(address) LIKE ?",
                (f"%{search_query}%", f"%{search_query}%"),
            ).fetchall()
            if not salons:
                salons = conn.execute("SELECT * FROM salons").fetchall()
                flash("No matches found — showing all salons.", "info")
        else:
            salons = conn.execute("SELECT * FROM salons").fetchall()

    salons_list = []
    for s in salons:
        d = dict(s)
        # compute avg rating
        if s["rating_count"] and s["rating_count"] > 0:
            d["avg_rating"] = round(s["rating_total"] / s["rating_count"], 1)
        else:
            d["avg_rating"] = None
        # image url for templates that use url_for('static', filename=...)
        d["image_path"] = s["image_path"]  # this is relative to static/ (e.g., 'uploads/123.jpg') or None
        # compute distance if user provided
        if user_lat is not None and user_lng is not None and s["lat"] is not None and s["lng"] is not None:
            try:
                d["distance_km"] = round(haversine(user_lat, user_lng, s["lat"], s["lng"]), 2)
            except Exception:
                d["distance_km"] = None
        else:
            d["distance_km"] = None
        salons_list.append(d)

    if user_lat is not None and user_lng is not None:
        salons_list.sort(key=lambda x: (x["distance_km"] is None, x["distance_km"]))

    return render_template(
        "show_salon.html",
        salons=salons_list,
        search_query=search_query,
        username=session.get("username"),
    )

# -------------------- RECOMMEND (accepts lat & lon and shows nearest first) -------------------- #
@app.route("/recommend", methods=["GET"])
def recommend():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    category = request.args.get("category", default=None, type=str)

    if lat is None or lon is None:
        flash("Location not provided.", "error")
        return redirect(url_for("show_salons"))

    # reuse show logic but force sorting by distance and optional category filter
    with get_db_connection(SALON_DB_PATH) as conn:
        if category:
            salons = conn.execute(
                "SELECT * FROM salons WHERE LOWER(services) LIKE ? OR LOWER(name) LIKE ?",
                (f"%{category.lower()}%", f"%{category.lower()}%"),
            ).fetchall()
            if not salons:
                salons = conn.execute("SELECT * FROM salons").fetchall()
        else:
            salons = conn.execute("SELECT * FROM salons").fetchall()

    salons_list = []
    for s in salons:
        d = dict(s)
        d["image_path"] = s["image_path"]
        try:
            d["distance_km"] = round(haversine(lat, lon, s["lat"], s["lng"]), 2) if s["lat"] and s["lng"] else None
        except Exception:
            d["distance_km"] = None
        salons_list.append(d)

    salons_list.sort(key=lambda x: (x["distance_km"] is None, x["distance_km"]))

    return render_template(
        "show_salon.html",
        salons=salons_list,
        search_query="",
        username=session.get("username"),
    )

# -------------------- TOGGLE SALON STATUS -------------------- #
@app.route("/toggle_salon/<int:salon_id>", methods=["POST"])
def toggle_salon(salon_id):
    username = session.get("username")
    entered_pass_key = request.form.get("pass_key", "").strip()

    if not username:
        flash("Please login first!", "error")
        return redirect(url_for("show_salons"))

    with get_db_connection(SALON_DB_PATH) as conn:
        cur = conn.cursor()
        salon = cur.execute("SELECT * FROM salons WHERE id=?", (salon_id,)).fetchone()
        if not salon:
            flash("Salon not found!", "error")
            return redirect(url_for("show_salons"))
        if salon["owner_username"] != username:
            flash("You do not have permission to change this salon’s status!", "error")
            return redirect(url_for("show_salons"))
        if not check_password_hash(salon["pass_key"], entered_pass_key):
            flash("Incorrect Pass Key!", "error")
            return redirect(url_for("show_salons"))
        new_status = "OFF" if salon["status"] == "ON" else "ON"
        cur.execute("UPDATE salons SET status=? WHERE id=?", (new_status, salon_id))
        conn.commit()

    flash(f"Salon status changed to {new_status}!", "success")
    return redirect(url_for("show_salons"))

# -------------------- RATE SALON -------------------- #
@app.route("/rate/<int:salon_id>", methods=["POST"])
def rate_salon(salon_id):
    rating = int(request.form.get("rating", 0))
    if rating < 1 or rating > 5:
        flash("Invalid rating value!", "error")
        return redirect(url_for("show_salons"))
    with get_db_connection(SALON_DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT rating_total, rating_count FROM salons WHERE id=?", (salon_id,))
        salon = cur.fetchone()
        if not salon:
            flash("Salon not found!", "error")
            return redirect(url_for("show_salons"))
        new_total = salon["rating_total"] + rating
        new_count = salon["rating_count"] + 1
        cur.execute("UPDATE salons SET rating_total=?, rating_count=? WHERE id=?", (new_total, new_count, salon_id))
        conn.commit()
    flash("Thank you for rating!", "success")
    return redirect(url_for("show_salons"))

# -------------------- BOOK SLOT -------------------- #
@app.route("/book-slot/<int:salon_id>", methods=["GET", "POST"])
def book_slot_for_salon(salon_id):
    username = session.get("username")
    if not username:
        flash("Please login first!", "error")
        return redirect(url_for("gender"))
    with get_db_connection(SALON_DB_PATH) as conn:
        salon = conn.execute("SELECT * FROM salons WHERE id=?", (salon_id,)).fetchone()
    if not salon or salon["status"] == "OFF":
        flash("This salon is currently not accepting bookings.", "error")
        return redirect(url_for("show_salons"))

    with get_db_connection(SLOT_DB_PATH) as conn:
        booked_slots = conn.execute(
            "SELECT start_time, COUNT(*) as count FROM slots WHERE salon_id=? GROUP BY start_time", (salon_id,)
        ).fetchall()
    booked_counts = {}
    for slot in booked_slots:
        try:
            dt = datetime.strptime(slot["start_time"], "%Y-%m-%d %H:%M:%S")
            hour = dt.hour
            booked_counts[hour] = slot["count"]
        except Exception:
            continue

    slot_periods = {
        "Morning": list(range(7, 12)),
        "Afternoon": list(range(12, 17)),
        "Evening": list(range(17, 21)),
        "Night": list(range(21, 24)),
    }

    if request.method == "POST":
        selected_date = request.form.get("date")
        if not selected_date:
            flash("Please select a booking date & time!", "error")
            return redirect(url_for("book_slot_for_salon", salon_id=salon_id))
        try:
            selected_dt = datetime.fromisoformat(selected_date)
        except ValueError:
            flash("Invalid date format!", "error")
            return redirect(url_for("book_slot_for_salon", salon_id=salon_id))
        selected_hour = selected_dt.hour
        if booked_counts.get(selected_hour, 0) >= 2:
            flash(f"Slot {selected_hour}:00 - {selected_hour+1}:00 is full.", "error")
            return redirect(url_for("book_slot_for_salon", salon_id=salon_id))
        start_time = selected_dt
        end_time = selected_dt + timedelta(hours=1)
        pending_slots = [
            {
                "salon_id": salon_id,
                "username": username,
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        ]
        session["pending_slots"] = pending_slots
        return redirect(url_for("payment"))

    return render_template(
        "book_slot.html", username=username, salon=salon, booked_counts=booked_counts, slot_periods=slot_periods
    )

# -------------------- PAYMENT -------------------- #
@app.route("/payment")
def payment():
    username = session.get("username")
    pending_slots = session.get("pending_slots", [])
    if not username or not pending_slots:
        flash("No slot selected!", "error")
        return redirect(url_for("show_salons"))
    amount = 10000
    razorpay_order = razorpay_client.order.create({"amount": amount, "currency": "INR", "payment_capture": "1"})
    return render_template("payment.html", username=username, slots=pending_slots, razorpay_order=razorpay_order, razorpay_key=RAZORPAY_KEY_ID)

@app.route("/payment-success", methods=["POST"])
def payment_success():
    payment_id = request.form.get("razorpay_payment_id")
    order_id = request.form.get("razorpay_order_id")
    signature = request.form.get("razorpay_signature")
    generated_signature = base64.b64encode(
        hmac.new(bytes(RAZORPAY_KEY_SECRET, "utf-8"), bytes(order_id + "|" + payment_id, "utf-8"), hashlib.sha256).digest()
    ).decode()
    if generated_signature != signature:
        flash("Payment verification failed!", "error")
        return redirect(url_for("payment"))
    username = session.get("username")
    pending_slots = session.get("pending_slots")
    if not username or not pending_slots:
        flash("Invalid payment flow!", "error")
        return redirect(url_for("show_salons"))
    with get_db_connection(SLOT_DB_PATH) as conn:
        cursor = conn.cursor()
        for slot in pending_slots:
            cursor.execute("INSERT INTO slots (username, salon_id, start_time, end_time) VALUES (?, ?, ?, ?)",
                           (username, slot["salon_id"], slot["start_time"], slot["end_time"]))
        conn.commit()
    session.pop("pending_slots", None)
    flash("Payment successful! Slots booked.", "success")
    return redirect(url_for("show_salons"))

# -------------------- ADMIN DATABASE VIEW -------------------- #
@app.route("/database_views")
def database_views():
    if not session.get("admin"):
        flash("Admin access only!", "error")
        return redirect(url_for("gender"))
    with get_db_connection(DB_PATH) as conn:
        users = conn.execute("SELECT * FROM users").fetchall()
    with get_db_connection(SALON_DB_PATH) as conn:
        salons = conn.execute("SELECT * FROM salons").fetchall()
    with get_db_connection(SLOT_DB_PATH) as conn:
        slots = conn.execute("SELECT * FROM slots").fetchall()
    return render_template("database_views.html", users=users, salons=salons, slots=slots, username=session.get("username"))

# -------------------- RUN APP -------------------- #
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
