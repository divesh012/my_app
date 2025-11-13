from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
import sqlite3, os, razorpay, hmac, hashlib, requests, urllib.parse
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"

# -------------------- RAZORPAY -------------------- #
RAZORPAY_KEY_ID = "rzp_test_RKFRNhf7xcHQgR"
RAZORPAY_KEY_SECRET = "hRgiFkFXxAFA2fACRGnmwo1F"
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# -------------------- DATABASE PATHS -------------------- #
DB_PATH = 'new_user.db'
SLOT_DB_PATH = 'gloora.db'
SALON_DB_PATH = 'salons.db'

# -------------------- GEOAPIFY -------------------- #
GEOAPIFY_KEY = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

# -------------------- DATABASE INITIALIZATION -------------------- #
def init_user_db():
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            """)

def init_slot_db():
    if not os.path.exists(SLOT_DB_PATH):
        with sqlite3.connect(SLOT_DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    salon_id INTEGER NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    FOREIGN KEY (salon_id) REFERENCES salons(id)
                )
            """)

def init_salon_db():
    if not os.path.exists(SALON_DB_PATH):
        with sqlite3.connect(SALON_DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE salons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    lat REAL,
                    lng REAL,
                    contact TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ON',
                    owner_username TEXT NOT NULL,
                    services TEXT,
                    price REAL,
                    pass_key TEXT NOT NULL
                )
            """)

def get_db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# -------------------- RUN INITIALIZATION -------------------- #
init_user_db()
init_slot_db()
init_salon_db()

# -------------------- STATIC PAGES -------------------- #
@app.route('/')
@app.route('/gender')
def gender():
    return render_template('gender.html', username=session.get('username'))

@app.route('/about')
def about():
    return render_template('about.html', username=session.get('username'))

@app.route('/services_categories')
def services_categories():
    return render_template('services_categories.html', username=session.get('username'))

@app.route('/contact_us')
def contact_us():
    return render_template('contact_us.html', username=session.get('username'))
@app.route('/help')
def help_page():
    username = session.get('username')

    if not username:
        # User not logged in → show message on Help page
        message = " Login Required"
        description = "Please sign in to access personalized help, order support, and chat assistance."
        return render_template("help.html", login_required=True, message=message, description=description)

    # If logged in → show normal Help page
    return render_template("help.html", username=username, login_required=False)

@app.route('/login')
def login():
    return render_template("login.html")



# -------------------- LOGIN & REGISTER HELPER -------------------- #
def handle_auth(action, gender_page):
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not email or not password:
        flash("All fields are mandatory!", "error")
        return redirect(url_for(gender_page))

    if not email.lower().endswith('@gmail.com'):
        flash("Please enter a valid Gmail address.", "error")
        return redirect(url_for(gender_page))

    if action == 'login' and email.lower() == 'admin@gmail.com' and password == 'admin123':
        session['admin'] = True
        flash("Welcome, Admin!", "success")
        return redirect(url_for('database_views'))

    with get_db_connection(DB_PATH) as conn:
        cursor = conn.cursor()

        if action == 'register':
            hashed_pw = generate_password_hash(password)
            try:
                cursor.execute(
                    "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                    (username, email, hashed_pw)
                )
                conn.commit()
                flash("Registration successful! Please login.", "success")
            except sqlite3.IntegrityError:
                flash("Username or Email already exists!", "error")

        elif action == 'login':
            cursor.execute(
                "SELECT * FROM users WHERE username=? AND email=?",
                (username, email)
            )
            user = cursor.fetchone()
            if user and check_password_hash(user['password'], password):
                session['username'] = username
                session['email'] = email
                flash(f"Welcome back, {username}!", "success")
            else:
                flash("Invalid credentials!", "error")

    return redirect(url_for(gender_page))

# -------------------- MALE & FEMALE PAGES -------------------- #
@app.route('/male', methods=['GET', 'POST'])
def male():
    show_login = request.args.get('login') == '1'
    if request.method == 'POST':
        return handle_auth(request.form.get('action'), 'male')
    return render_template('male_page.html', show_login=show_login, username=session.get('username'))

@app.route('/female', methods=['GET', 'POST'])
def female():
    show_login = request.form.get('login') == '1'
    if request.method == 'POST':
        return handle_auth(request.form.get('action'), 'female')
    return render_template('female_page.html', show_login=show_login, username=session.get('username'))

# -------------------- LOGIN / LOGOUT FOR HELP CENTER -------------------- #
@app.route('/login', methods=['GET', 'POST'])
def login_help():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        with get_db_connection(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? AND email=?", (username, email))
            user = cursor.fetchone()
            if user and check_password_hash(user['password'], password):
                session['username'] = username
                session['email'] = email
                flash(f"Welcome back, {username}!", "success")
                return redirect(url_for('help_page'))
            else:
                flash("Invalid credentials!", "error")
                return redirect(url_for('help_page'))

    return render_template('help_login.html')  # Optional dedicated login page

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('pending_slots', None)
    session.pop('admin', None)
    session.pop('email', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('gender'))

# -------------------- SALON & SLOT ROUTES -------------------- #
# Keep all your existing routes like register_salon, show_salons, book_slot_for_salon, payment, admin database views, toggle_salon_status, owner_toggle_salon_status etc. intact
# No changes needed for your current booking/payment/admin logic


# -------------------- SALON REGISTRATION -------------------- #
@app.route("/register_salon", methods=["GET", "POST"])
def register_salon():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        state = request.form.get("state", "").strip()
        contact = request.form.get("contact", "").strip()
        pass_key = request.form.get("pass_key", "").strip()

        # --- Validation ---
        if not name or not city or not state or not contact or not pass_key:
            flash("All fields including Pass Key are mandatory!", "error")
            return render_template("register_salon.html")

        hashed_pass_key = generate_password_hash(pass_key)

        # --- Geoapify Address Handling ---
        
        # --- Geoapify Address Handling ---
        full_address = f"{address}, {city}, {state}, India" if address else f"{city}, {state}, India"
        encoded_address = urllib.parse.quote(full_address)

        lat, lng = None, None
        try:
            response = requests.get(
                f"https://api.geoapify.com/v1/geocode/search?text={encoded_address}&apiKey={GEOAPIFY_KEY}",
                timeout=10
            ).json()
            if response.get("features"):
                lat = response["features"][0]["properties"]["lat"]
                lng = response["features"][0]["properties"]["lon"]
        except Exception:
            flash("Geoapify error. Saving salon without coordinates.", "warning")

        # --- If still no lat/lng, allow saving with NULL ---
        if lat is None or lng is None:
            flash("Could not fetch exact coordinates. Saved without location mapping.", "warning")

        # --- Save to DB ---
        with get_db_connection(SALON_DB_PATH) as conn:
            cursor = conn.cursor()

            # check duplicate salon
            cursor.execute(
                "SELECT * FROM salons WHERE LOWER(name)=? AND LOWER(address)=?",
                (name.lower(), full_address.lower())
            )
            if cursor.fetchone():
                flash("Salon already exists!", "error")
                return render_template("register_salon.html")

            # insert new salon
            cursor.execute(
                """
                INSERT INTO salons 
                (name, address, lat, lng, contact, status, owner_username, pass_key) 
                VALUES (?, ?, ?, ?, ?, 'ON', ?, ?)
                """,
                (name, full_address, lat, lng, contact, session.get("username"), hashed_pass_key)
            )
            conn.commit()
            salon_id = cursor.lastrowid

        flash("Salon registered successfully with Pass Key!", "success")
        return redirect(url_for("book_slot_for_salon", salon_id=salon_id))

    return render_template("register_salon.html")

# -------------------- SHOW SALONS -------------------- #
@app.route('/salons', methods=['GET', 'POST'])
def show_salons():
    search_query = request.args.get('search', '').strip().lower()
    with get_db_connection(SALON_DB_PATH) as conn:
        if search_query:
            salons = conn.execute(
                "SELECT * FROM salons WHERE LOWER(name) LIKE ? OR LOWER(address) LIKE ?",
                (f"%{search_query}%", f"%{search_query}%")
            ).fetchall()
        else:
            salons = conn.execute("SELECT * FROM salons").fetchall()
    return render_template('show_salon.html', salons=salons, search_query=search_query)

# -------------------- OWNER TOGGLE -------------------- #
from werkzeug.security import check_password_hash
@app.route('/owner_toggle_salon_status/<int:salon_id>', methods=['GET', 'POST'])
def owner_toggle_salon_status(salon_id):
    # Fetch salon info from DB
    with get_db_connection(SALON_DB_PATH) as conn:
        salon = conn.execute("SELECT * FROM salons WHERE id=?", (salon_id,)).fetchone()

    if not salon:
        flash("Salon not found!", "error")
        return redirect(url_for('show_salons'))

    if request.method == 'POST':
        entered_key = request.form.get('pass_key', '').strip()
        if not entered_key:
            return render_template('enter_pass_key.html', error="Pass Key required.", salon=salon)

        #  Check Pass Key (hashed)
        if check_password_hash(salon['pass_key'], entered_key):
            # Toggle status
            new_status = 'OFF' if salon['status'] == 'ON' else 'ON'
            with get_db_connection(SALON_DB_PATH) as conn:
                conn.execute("UPDATE salons SET status=? WHERE id=?", (new_status, salon_id))
                conn.commit()
            flash(f"Salon status changed to {new_status}.", "success")
            return redirect(url_for('show_salons'))
        else:
            return render_template('enter_pass_key.html', error="Incorrect Pass Key!", salon=salon)

    # GET request → show Pass Key form
    return render_template('enter_pass_key.html', salon=salon)

# -------------------- ADMIN TOGGLE -------------------- #
@app.route('/toggle_salon_status/<int:salon_id>')
def toggle_salon_status(salon_id):
    if not session.get('admin'):
        flash("Admin access only!", "error")
        return redirect(url_for('gender'))

    with get_db_connection(SALON_DB_PATH) as conn:
        salon = conn.execute("SELECT * FROM salons WHERE id=?", (salon_id,)).fetchone()
        if salon:
            new_status = 'OFF' if salon['status'] == 'ON' else 'ON'
            conn.execute("UPDATE salons SET status=? WHERE id=?", (new_status, salon_id))
            conn.commit()
            flash(f"Salon '{salon['name']}' status changed to {new_status}.", "success")
        else:
            flash("Salon not found!", "error")
    return redirect(url_for('database_views'))

# -------------------- BOOK SLOT -------------------- #
@app.route('/book-slot/<int:salon_id>', methods=['GET', 'POST'])
def book_slot_for_salon(salon_id):
    username = session.get('username')
    if not username:
        flash("Please login first!", "error")
        return redirect(url_for('gender'))

    with get_db_connection(SALON_DB_PATH) as conn:
        salon = conn.execute("SELECT * FROM salons WHERE id=?", (salon_id,)).fetchone()

    if not salon or salon['status'] == 'OFF':
        flash("This salon is currently not accepting bookings.", "error")
        return redirect(url_for('show_salons'))

    with get_db_connection(SLOT_DB_PATH) as conn:
        booked_slots = conn.execute(
            "SELECT start_time, COUNT(*) as count FROM slots WHERE salon_id=? GROUP BY start_time",
            (salon_id,)
        ).fetchall()

    booked_counts = {int(slot['start_time'].split()[1].split(':')[0]): slot['count'] for slot in booked_slots}

    slot_periods = {
        "Morning": list(range(7, 12)),
        "Afternoon": list(range(12, 17)),
        "Evening": list(range(17, 21)),
        "Night": list(range(21, 23)),
    }

    if request.method == "POST":
        selected_slots = request.form.getlist('slot_time')
        if not selected_slots:
            flash("Please select at least one slot!", "error")
            return redirect(url_for("book_slot_for_salon", salon_id=salon_id))

        today = datetime.now().date()
        pending_slots = []
        for slot_hour in selected_slots:
            start_hour = int(slot_hour)
            if booked_counts.get(start_hour, 0) >= 2:
                flash(f"Slot {start_hour}:00 - {start_hour+1}:00 is full.", "error")
                return redirect(url_for("book_slot_for_salon", salon_id=salon_id))

            start_time = datetime.combine(today, datetime.min.time()) + timedelta(hours=start_hour)
            end_time = start_time + timedelta(hours=1)

            pending_slots.append({
                "salon_id": salon_id,
                "username": username,
                "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S")
            })

        session['pending_slots'] = pending_slots
        return redirect(url_for('payment'))

    return render_template(
        "book_slot.html",
        username=username,
        salon=salon,
        booked_counts=booked_counts,
        slot_periods=slot_periods
    )

# -------------------- PAYMENT -------------------- #
@app.route('/payment')
def payment():
    username = session.get('username')
    pending_slots = session.get('pending_slots', [])
    if not username or not pending_slots:
        flash("No slot selected!", "error")
        return redirect(url_for('show_salons'))

    amount = 10000
    razorpay_order = razorpay_client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": "1"
    })

    return render_template('payment.html', username=username, slots=pending_slots,
                           razorpay_order=razorpay_order, razorpay_key=RAZORPAY_KEY_ID)

@app.route('/payment-success', methods=['POST'])
def payment_success():
    payment_id = request.form.get("razorpay_payment_id")
    order_id = request.form.get("razorpay_order_id")
    signature = request.form.get("razorpay_signature")

    generated_signature = hmac.new(
        bytes(RAZORPAY_KEY_SECRET, 'utf-8'),
        bytes(order_id + "|" + payment_id, 'utf-8'),
        hashlib.sha256
    ).hexdigest()

    if generated_signature != signature:
        flash("Payment verification failed!", "error")
        return redirect(url_for('payment'))

    username = session.get("username")
    pending_slots = session.get("pending_slots")
    if not username or not pending_slots:
        flash("Invalid payment flow!", "error")
        return redirect(url_for('show_salons'))

    with get_db_connection(SLOT_DB_PATH) as conn:
        cursor = conn.cursor()
        for slot in pending_slots:
            cursor.execute("INSERT INTO slots (username, salon_id, start_time, end_time) VALUES (?, ?, ?, ?)",
                           (username, slot['salon_id'], slot['start_time'], slot['end_time']))
        conn.commit()

    session.pop("pending_slots", None)
    flash("Payment successful! Slots booked.", "success")
    return redirect(url_for('show_salons'))

# -------------------- ADMIN DATABASE VIEW -------------------- #
@app.route('/database_views')
def database_views():
    if not session.get('admin'):
        flash("Admin access only!", "error")
        return redirect(url_for('gender'))

    with get_db_connection(DB_PATH) as conn:
        users = conn.execute("SELECT * FROM users").fetchall()
    with get_db_connection(SALON_DB_PATH) as conn:
        salons = conn.execute("SELECT * FROM salons").fetchall()
    with get_db_connection(SLOT_DB_PATH) as conn:
        slots = conn.execute("SELECT * FROM slots").fetchall()

    return render_template('database_views.html', users=users, salons=salons, slots=slots)

# -------------------- RUN APP -------------------- #
if __name__ == '__main__':
    app.run(debug=True)
