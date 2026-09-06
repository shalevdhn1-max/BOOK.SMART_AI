from flask import (
    Flask,
    request,
    redirect,
    url_for,
    session,
    render_template_string
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database import connect_db, create_tables

from datetime import datetime, timedelta, date
import calendar
import secrets
import hashlib
import string


# =========================================================
# APP
# =========================================================

app = Flask(__name__)

app.secret_key = "appointment-manager-secret-key"


# =========================================================
# CONSTANTS
# =========================================================

SUPER_ADMIN_EMAIL = "shalevdhn1@gmail.com"
SUPER_ADMIN_PASSWORD = "admin085"

DAY_NAMES = [
    "ראשון",
    "שני",
    "שלישי",
    "רביעי",
    "חמישי",
    "שישי",
    "שבת"
]

STATUS_NAMES = {
    "pending": "ממתין",
    "confirmed": "מאושר",
    "completed": "הושלם",
    "cancelled": "בוטל"
}


# =========================================================
# DATABASE HELPERS
# =========================================================

def get_user_by_email(email):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE email = ?
    """, (email,))

    user = cursor.fetchone()

    conn.close()

    return user


def get_business(business_id):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM businesses
        WHERE business_id = ?
    """, (business_id,))

    business = cursor.fetchone()

    conn.close()

    return business


def get_all_businesses():

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM businesses
        ORDER BY business_name
    """)

    businesses = cursor.fetchall()

    conn.close()

    return businesses


def get_business_name(business_id):

    business = get_business(business_id)

    if not business:
        return "העסק"

    return business["business_name"]



# =========================================================
# BUSINESS INVITATION / AUTHORIZATION HELPERS
# =========================================================

def normalize_phone(phone):
    return "".join(ch for ch in (phone or "") if ch.isdigit())


def hash_invite_code(code):
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def generate_business_invite_code():
    alphabet = string.ascii_uppercase + string.digits
    while True:
        raw = "".join(secrets.choice(alphabet) for _ in range(10))
        code = f"BS-{raw[:5]}-{raw[5:]}"
        conn = connect_db()
        exists = conn.execute(
            "SELECT 1 FROM business_invites WHERE code_hash = ?",
            (hash_invite_code(code),)
        ).fetchone()
        conn.close()
        if not exists:
            return code


def get_business_by_owner_phone(phone):
    normalized = normalize_phone(phone)
    if not normalized:
        return None

    conn = connect_db()
    rows = conn.execute("""
        SELECT *
        FROM businesses
        WHERE is_active = 1
        ORDER BY business_id
    """).fetchall()
    conn.close()

    for row in rows:
        raw = normalize_phone(row["phone"])
        if raw == normalized:
            return row
        if raw.startswith("972") and "0" + raw[3:] == normalized:
            return row
        if normalized.startswith("972") and "0" + normalized[3:] == raw:
            return row
    return None


def get_business_by_invite_code(code):
    if not code:
        return None
    conn = connect_db()
    row = conn.execute("""
        SELECT b.*, bi.invite_id, bi.expires_at, bi.used_at
        FROM business_invites bi
        JOIN businesses b ON b.business_id = bi.business_id
        WHERE bi.code_hash = ?
          AND bi.used_at IS NULL
          AND datetime(bi.expires_at) > datetime('now')
          AND b.is_active = 1
        ORDER BY bi.invite_id DESC
        LIMIT 1
    """, (hash_invite_code(code.strip().upper()),)).fetchone()
    conn.close()
    return row

# =========================================================
# INITIAL SETUP
# =========================================================

def ensure_super_admin():

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id
        FROM users
        WHERE email = ?
    """, (SUPER_ADMIN_EMAIL,))

    existing = cursor.fetchone()

    if not existing:

        cursor.execute("""
            INSERT INTO users
            (
                email,
                password_hash,
                role,
                full_name,
                is_active
            )
            VALUES (?, ?, ?, ?, 1)
        """, (
            SUPER_ADMIN_EMAIL,
            generate_password_hash(SUPER_ADMIN_PASSWORD),
            "super_admin",
            "מנהל מערכת"
        ))

        conn.commit()

    else:

        cursor.execute("""
            UPDATE users
            SET role = 'super_admin',
                is_active = 1
            WHERE email = ?
        """, (SUPER_ADMIN_EMAIL,))

        conn.commit()

    conn.close()


# =========================================================
# AUTHENTICATION
# =========================================================

def is_logged_in():

    return "user_id" in session


def require_login():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    user_id = session.get("user_id")
    conn = connect_db()
    user = conn.execute(
        "SELECT is_active FROM users WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()

    if not user or not user["is_active"]:
        session.clear()
        return redirect(url_for("login"))

    return None


def require_owner():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    if session.get("role") != "owner":

        return "הגישה נדחתה", 403

    return None


def require_customer():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    if session.get("role") != "customer":

        return "הגישה נדחתה", 403

    return None


def require_super_admin():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    if session.get("role") != "super_admin":

        return "הגישה נדחתה", 403

    return None


# =========================================================
# HTML HELPERS
# =========================================================

def flash_message(message, message_type="success"):

    session["flash_message"] = message
    session["flash_type"] = message_type


def consume_flash():

    message = session.pop("flash_message", None)
    message_type = session.pop(
        "flash_type",
        "success"
    )

    return message, message_type


def safe(value):

    if value is None:
        return "-"

    return str(value)


# =========================================================
# STYLE
# =========================================================

STYLE = """

<style>

* {
    box-sizing: border-box;
}

:root {
    --black: #090909;
    --black2: #121212;
    --black3: #1c1c1c;
    --gold: #c9a227;
    --gold-light: #e6c45a;
    --white: #ffffff;
    --gray: #b8b8b8;
    --gray2: #777777;
    --border: rgba(201,162,39,0.22);
    --card: #151515;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    font-family:
        Arial,
        Helvetica,
        sans-serif;

    background:
        radial-gradient(
            circle at top right,
            rgba(201,162,39,0.08),
            transparent 30%
        ),
        #090909;

    color: #f5f5f5;

    direction: rtl;
    text-align: right;
}

a {
    color: inherit;
}

button,
input,
select,
textarea {
    font-family: inherit;
}

button {
    cursor: pointer;
}

input,
select,
textarea {
    width: 100%;
    padding: 13px 14px;

    background: #101010;
    color: white;

    border: 1px solid #333;
    border-radius: 10px;

    font-size: 15px;
}

textarea {
    min-height: 120px;
    resize: vertical;
}

input:focus,
select:focus,
textarea:focus {
    outline: none;
    border-color: var(--gold);
    box-shadow:
        0 0 0 2px rgba(201,162,39,0.10);
}

button {
    border: 0;
    border-radius: 10px;

    padding: 12px 20px;

    background:
        linear-gradient(
            135deg,
            #d8b33f,
            #a98213
        );

    color: #080808;

    font-size: 15px;
    font-weight: bold;

    transition: 0.2s;
}

button:hover {
    transform: translateY(-1px);

    box-shadow:
        0 8px 25px rgba(201,162,39,0.18);
}

.secondary-button {
    background: #242424;
    color: white;
    border: 1px solid #444;
}

.danger-button {
    background: #5b1515;
    color: white;
}

.small-button {
    padding: 8px 13px;
    font-size: 13px;
}

.gold {
    color: var(--gold-light);
}

.muted {
    color: var(--gray2);
}

.error {
    background: rgba(150,30,30,0.20);
    border: 1px solid rgba(220,60,60,0.35);

    color: #ffb0b0;

    padding: 13px;
    border-radius: 10px;

    margin-bottom: 18px;
}

.success {
    background: rgba(50,140,70,0.18);
    border: 1px solid rgba(80,190,100,0.30);

    color: #b9f3c2;

    padding: 13px;
    border-radius: 10px;

    margin-bottom: 18px;
}

.warning {
    background: rgba(180,130,30,0.15);
    border: 1px solid rgba(201,162,39,0.30);

    color: #f4db86;

    padding: 13px;
    border-radius: 10px;

    margin-bottom: 18px;
}


/* ======================================================
   LANDING
   ====================================================== */

.landing {
    min-height: 100vh;

    background:
        linear-gradient(
            rgba(0,0,0,0.82),
            rgba(0,0,0,0.95)
        );
}

.landing-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;

    padding: 25px 7%;

    border-bottom:
        1px solid rgba(201,162,39,0.16);
}

.logo {
    font-size: 25px;
    font-weight: bold;

    color: var(--gold-light);
}

.hero {
    min-height: 75vh;

    display: flex;
    align-items: center;
    justify-content: center;

    text-align: center;

    padding: 60px 25px;
}

.hero-inner {
    max-width: 850px;
}

.hero h1 {
    font-size: 62px;
    margin: 0 0 20px;

    line-height: 1.1;
}

.hero h1 span {
    color: var(--gold-light);
}

.hero p {
    font-size: 20px;
    color: #c5c5c5;

    line-height: 1.8;
}

.hero-buttons {
    display: flex;
    gap: 14px;

    justify-content: center;

    margin-top: 35px;

    flex-wrap: wrap;
}

.hero-buttons a {
    text-decoration: none;
}


/* ======================================================
   AUTH
   ====================================================== */

.auth-page {
    min-height: 100vh;

    display: flex;
    align-items: center;
    justify-content: center;

    padding: 25px;
}

.auth-card {
    width: 100%;
    max-width: 500px;

    background:
        linear-gradient(
            145deg,
            #181818,
            #0d0d0d
        );

    border:
        1px solid var(--border);

    padding: 38px;

    border-radius: 18px;

    box-shadow:
        0 25px 80px rgba(0,0,0,0.55);
}

.auth-card h1 {
    text-align: center;
    margin-top: 0;
}

.auth-subtitle {
    text-align: center;
    color: var(--gray);

    margin-bottom: 28px;
}

label {
    display: block;

    margin-top: 16px;
    margin-bottom: 7px;

    font-weight: bold;
}

.auth-button {
    width: 100%;
    margin-top: 25px;
}

.auth-brand {
    color: var(--gold-light);
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 2px;
    text-align: center;
    margin-bottom: 14px;
}

.auth-tagline {
    color: var(--gray);
    line-height: 1.7;
    text-align: center;
    margin: 10px 0 24px;
    font-size: 14px;
}

.auth-link {
    text-align: center;
    margin-top: 22px;
}

.auth-link a {
    color: var(--gold-light);
    text-decoration: none;
    font-weight: bold;
}


/* ======================================================
   DASHBOARD
   ====================================================== */

.dashboard {
    display: flex;
    min-height: 100vh;
}

.sidebar {
    width: 260px;
    min-height: 100vh;

    background:
        linear-gradient(
            180deg,
            #101010,
            #080808
        );

    border-left:
        1px solid rgba(201,162,39,0.15);

    padding: 25px 17px;

    flex-shrink: 0;
}

.sidebar h2 {
    color: var(--gold-light);

    margin:
        0 10px 8px;
}

.sidebar-business {
    color: #777;
    font-size: 13px;

    margin:
        0 10px 28px;
}

.sidebar-section {
    color: #777;

    font-size: 11px;

    margin:
        22px 10px 8px;

    text-transform: uppercase;
}

.sidebar a {
    display: block;

    color: #ddd;

    text-decoration: none;

    padding: 12px;

    margin-bottom: 4px;

    border-radius: 9px;

    transition: 0.2s;
}

.sidebar a:hover {
    background:
        rgba(201,162,39,0.10);

    color: var(--gold-light);
}

.sidebar .logout {
    margin-top: 25px;

    border-top:
        1px solid #292929;

    padding-top: 20px;
}

.content {
    flex: 1;

    padding: 35px;

    overflow-x: auto;
}

.topbar {
    display: flex;

    justify-content: space-between;

    align-items: center;

    margin-bottom: 28px;
}

.topbar h1 {
    margin: 0;

    font-size: 32px;
}

.user-info {
    color: #777;

    margin-top: 6px;
}


/* ======================================================
   CARDS
   ====================================================== */

.cards {
    display: grid;

    grid-template-columns:
        repeat(
            4,
            minmax(160px, 1fr)
        );

    gap: 18px;
}

.stat-card {
    background:
        linear-gradient(
            145deg,
            #181818,
            #101010
        );

    border:
        1px solid rgba(201,162,39,0.13);

    padding: 23px;

    border-radius: 15px;
}

.stat-title {
    color: #888;
    font-size: 14px;
}

.stat-number {
    color: var(--gold-light);

    font-size: 34px;
    font-weight: bold;

    margin-top: 9px;
}

.card {
    background:
        linear-gradient(
            145deg,
            #171717,
            #101010
        );

    border:
        1px solid rgba(201,162,39,0.13);

    padding: 25px;

    border-radius: 15px;

    margin-top: 22px;
}

.card h2 {
    margin-top: 0;
}


/* ======================================================
   TABLES
   ====================================================== */

.table-card {
    background:
        linear-gradient(
            145deg,
            #171717,
            #101010
        );

    border:
        1px solid rgba(201,162,39,0.13);

    padding: 24px;

    border-radius: 15px;

    overflow-x: auto;

    margin-top: 22px;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th {
    color: var(--gold-light);

    text-align: right;

    padding: 13px;

    border-bottom:
        1px solid #343434;
}

td {
    padding: 13px;

    border-bottom:
        1px solid #242424;
}

.empty {
    text-align: center;

    color: #777;

    padding: 30px;
}


/* ======================================================
   FORMS
   ====================================================== */

.form-grid {
    display: grid;

    grid-template-columns:
        repeat(
            2,
            minmax(200px, 1fr)
        );

    gap: 15px;
}

.form-full {
    grid-column: 1 / -1;
}

.form-actions {
    margin-top: 22px;

    display: flex;
    gap: 10px;

    flex-wrap: wrap;
}


/* ======================================================
   CALENDAR
   ====================================================== */

.calendar-header {
    display: flex;

    justify-content: space-between;

    align-items: center;

    gap: 15px;

    margin-bottom: 20px;
}

.calendar-header h2 {
    margin: 0;
}

.calendar-navigation {
    display: flex;

    gap: 8px;
}

.calendar-grid {
    display: grid;

    grid-template-columns:
        repeat(7, 1fr);

    gap: 8px;
}

.calendar-weekday {
    text-align: center;

    color: var(--gold-light);

    padding: 8px;

    font-size: 13px;

    font-weight: bold;
}

.calendar-day {
    min-height: 105px;

    background: #111;

    border:
        1px solid #2b2b2b;

    border-radius: 10px;

    padding: 10px;

    text-decoration: none;

    display: block;

    transition: 0.2s;
}

.calendar-day:hover {
    border-color: var(--gold);

    transform: translateY(-2px);
}

.calendar-day.empty-day {
    opacity: 0.2;
}

.calendar-day-number {
    font-size: 16px;

    font-weight: bold;
}

.calendar-day-status {
    margin-top: 12px;

    font-size: 12px;
}

.available {
    border-color:
        rgba(60,180,90,0.35);

    background:
        rgba(40,120,60,0.10);
}

.unavailable {
    border-color:
        rgba(200,50,50,0.30);

    background:
        rgba(120,30,30,0.10);
}

.today {
    box-shadow:
        inset 0 0 0 1px var(--gold);
}


/* ======================================================
   AVAILABILITY
   ====================================================== */

.availability-options {
    display: grid;

    grid-template-columns:
        repeat(
            2,
            minmax(200px, 1fr)
        );

    gap: 15px;
}

.option-card {
    padding: 20px;

    background: #111;

    border:
        1px solid #292929;

    border-radius: 12px;
}

.option-card:hover {
    border-color: var(--gold);
}


/* ======================================================
   TIME SLOTS
   ====================================================== */

.time-slots {
    display: grid;

    grid-template-columns:
        repeat(
            auto-fill,
            minmax(110px, 1fr)
        );

    gap: 10px;

    margin-top: 20px;
}

.time-slot {
    text-decoration: none;

    text-align: center;

    padding: 13px;

    border-radius: 10px;

    background: #151515;

    border:
        1px solid #333;
}

.time-slot:hover {
    border-color: var(--gold);

    color: var(--gold-light);
}

.time-slot.disabled {
    opacity: 0.3;

    pointer-events: none;
}


/* ======================================================
   PUBLIC BUSINESS PAGE
   ====================================================== */

.business-page {
    min-height: 100vh;

    background:
        radial-gradient(
            circle at top,
            rgba(201,162,39,0.09),
            transparent 40%
        );
}

.business-header {
    padding: 70px 25px 40px;

    text-align: center;

    border-bottom:
        1px solid rgba(201,162,39,0.13);
}

.business-header h1 {
    font-size: 45px;

    color: var(--gold-light);
}

.business-header p {
    color: #aaa;

    max-width: 700px;

    margin: auto;

    line-height: 1.8;
}

.business-body {
    max-width: 1100px;

    margin: auto;

    padding: 35px 20px;
}


/* ======================================================
   RESPONSIVE
   ====================================================== */

@media (max-width: 950px) {

    .cards {
        grid-template-columns:
            repeat(
                2,
                minmax(150px, 1fr)
            );
    }

    .sidebar {
        width: 220px;
    }

}

@media (max-width: 700px) {

    .dashboard {
        display: block;
    }

    .sidebar {
        width: 100%;
        min-height: auto;
    }

    .content {
        padding: 20px;
    }

    .cards {
        grid-template-columns: 1fr;
    }

    .form-grid {
        grid-template-columns: 1fr;
    }

    .calendar-grid {
        gap: 4px;
    }

    .calendar-day {
        min-height: 80px;

        padding: 6px;
    }

    .hero h1 {
        font-size: 42px;
    }

}

</style>
"""


# =========================================================
# SIDEBAR
# =========================================================

def sidebar_html():

    role = session.get("role")

    business_id = session.get("business_id")

    business_name = ""

    if business_id:

        business_name = get_business_name(
            business_id
        )

    if role == "super_admin":

        return f"""

        <div class="sidebar">

            <h2>מערכת ניהול</h2>

            <div class="sidebar-business">
                Super Admin
            </div>

            <div class="sidebar-section">
                מערכת
            </div>

            <a href="/admin">
                👑 מרכז ניהול
            </a>

            <a href="/admin/businesses">
                🏢 עסקים
            </a>

            <a href="/admin/users">
                👥 משתמשים
            </a>

            <a href="/admin/leads">
                🎯 לידים
            </a>

            <div class="sidebar-section">
                כלים
            </div>

            <a href="/chat">
                🤖 עוזר AI
            </a>

            <a href="/">
                🌐 אתר
            </a>

            <a class="logout" href="/logout">
                🚪 התנתקות
            </a>

        </div>

        """

    if role == "owner":

        return f"""

        <div class="sidebar">

            <h2>מערכת ניהול</h2>

            <div class="sidebar-business">
                {business_name}
            </div>

            <div class="sidebar-section">
                ניהול
            </div>

            <a href="/dashboard">
                🏠 לוח בקרה
            </a>

            <a href="/business/settings">
                🏢 העסק שלי
            </a>

            <a href="/services">
                ✂️ שירותים ומחירים
            </a>

            <a href="/business/hours">
                🕐 שעות פעילות
            </a>

            <a href="/calendar">
                📅 יומן וזמינות
            </a>

            <a href="/appointments">
                📆 תורים
            </a>

            <a href="/customers">
                👥 לקוחות
            </a>

            <a href="/invoices">
                🧾 חשבוניות
            </a>

            <a href="/invoices/settings">
                🔗 חיבור חשבוניות
            </a>

            <a href="/leads">
                🎯 לידים
            </a>

            <div class="sidebar-section">
                כלים
            </div>

            <a href="/chat">
                🤖 עוזר AI
            </a>

            <a class="logout" href="/logout">
                🚪 התנתקות
            </a>

        </div>

        """

    return """

    <div class="sidebar">

        <h2>מערכת ניהול</h2>

        <div class="sidebar-business">
            לקוח
        </div>

        <div class="sidebar-section">
            האזור שלי
        </div>

        <a href="/dashboard">
            🏠 לוח בקרה
        </a>

        <a href="/book">
            📅 קביעת תור
        </a>

        <a href="/appointments">
            📆 התורים שלי
        </a>

        <a href="/invoices">
            🧾 החשבוניות שלי
        </a>

        <div class="sidebar-section">
            כלים
        </div>

        <a href="/chat">
            🤖 עוזר AI
        </a>

        <a class="logout" href="/logout">
            🚪 התנתקות
        </a>

    </div>

    """

# =========================================================
# INVOICE INFRASTRUCTURE
# =========================================================

def invoices_connected(business_id):
    conn=connect_db()
    row=conn.execute("SELECT status FROM business_invoice_connections WHERE business_id=? LIMIT 1",(business_id,)).fetchone()
    conn.close()
    return bool(row and row["status"] == "connected")

@app.after_request
def _security_headers(response):
    if session.get("user_id"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# =========================================================
# ROUTES
# =========================================================

# When app.py is executed directly, Python names this module __main__.
# The route modules import `app`, so make sure they receive this exact
# running module instead of creating a second Flask app instance.
import sys
sys.modules.setdefault("app", sys.modules[__name__])

from routes import public_routes
from routes import owner_routes
from routes import customer_routes
from routes import booking_routes
from routes import admin_routes
from routes import ai_routes


if __name__ == "__main__":

    create_tables()
    ensure_super_admin()

    print()
    print("=" * 55)
    print("Book Smart AI - מערכת ניהול תורים")
    print("=" * 55)
    print()
    print("כתובת:")
    print("http://127.0.0.1:5001")
    print()
    print("Super Admin:")
    print(SUPER_ADMIN_EMAIL)
    print(SUPER_ADMIN_PASSWORD)
    print()
    print("=" * 55)

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )
