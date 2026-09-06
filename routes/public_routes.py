# Auto-generated modular route module for Book Smart AI.
from app import *


def _user_phone_exists(phone):
    normalized = normalize_phone(phone)
    if not normalized:
        return False
    conn = connect_db()
    try:
        rows = conn.execute("SELECT phone FROM users WHERE phone IS NOT NULL AND phone != ''").fetchall()
        return any(normalize_phone(row["phone"]) == normalized for row in rows)
    finally:
        conn.close()

@app.route("/")
def home():

    # The root URL is always the public entry screen.
    # It must never automatically open an existing business/dashboard.
    return render_template_string(
        STYLE + """

        <div class="landing">

            <div class="landing-nav">

                <div class="logo">
                    BOOK SMART AI
                </div>

                <a
                    href="/login"
                    style="text-decoration:none;"
                >
                    התחברות
                </a>

            </div>

            <div class="hero">

                <div class="hero-inner">

                    <h1>
                        ניהול העסק שלך
                        <br>
                        <span>ברמה אחרת.</span>
                    </h1>

                    <p>
                        מערכת חכמה לניהול עסקים,
                        לקוחות, שירותים, תורים,
                        זמינות וחשבוניות —
                        הכול במקום אחד.
                    </p>

                    <div class="hero-buttons">

                        <a href="/register">
                            <button>
                                פתיחת עסק
                            </button>
                        </a>

                        <a href="/login">
                            <button class="secondary-button">
                                כניסה למערכת
                            </button>
                        </a>

                        <a href="/contact">
                            <button class="secondary-button">
                                צור קשר
                            </button>
                        </a>

                    </div>

                </div>

            </div>

        </div>

        """
    )

@app.route("/contact", methods=["GET", "POST"])
def contact():

    error = ""

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        phone = normalize_phone(request.form.get("phone", ""))
        email = request.form.get("email", "").strip()

        # The public contact form intentionally accepts only these fields.
        if not full_name:
            error = "יש להזין שם מלא."
        elif not phone:
            error = "יש להזין מספר טלפון."
        elif email and "@" not in email:
            error = "כתובת האימייל אינה תקינה."
        else:
            conn = connect_db()
            try:
                # A landing-page contact is a lead immediately.  There is no
                # intermediate contact-request workflow in the admin panel.
                conn.execute("""
                    INSERT INTO leads
                        (business_id, full_name, phone, email, source, status, notes)
                    VALUES (NULL, ?, ?, ?, 'landing_page', 'new', NULL)
                """, (full_name, phone, email))
                conn.commit()
            finally:
                conn.close()

            return render_template_string(
                STYLE + """
                <div class="auth-page">
                    <div class="auth-card">
                        <h1>תודה!</h1>
                        <div class="success">
                            הפרטים התקבלו בהצלחה. ניצור איתך קשר בהקדם.
                        </div>
                        <a href="/">
                            <button class="auth-button">חזרה לאתר</button>
                        </a>
                    </div>
                </div>
                """
            )

    return render_template_string(
        STYLE + f"""
        <div class="auth-page">
            <div class="auth-card">
                <h1>צור קשר</h1>
                <div class="auth-subtitle">
                    רוצה להצטרף למערכת? יש לך שאלה? אנחנו כאן.
                </div>

                {(f'<div class="error">{safe(error)}</div>' if error else "")}

                <form method="POST">
                    <label>שם מלא *</label>
                    <input type="text" name="full_name" required autocomplete="name">

                    <label>מספר טלפון *</label>
                    <input type="tel" name="phone" required autocomplete="tel">

                    <label>אימייל <span class="muted">(רשות)</span></label>
                    <input type="email" name="email" autocomplete="email">

                    <button class="auth-button" type="submit">
                        שליחת פרטים
                    </button>
                </form>

                <div class="auth-link">
                    <a href="/">חזרה לאתר</a>
                </div>
            </div>
        </div>
        """
    )

@app.route("/register", methods=["GET", "POST"])
def register():

    error = ""
    step = "details"
    pending_token = ""

    if request.method == "POST":

        role = request.form.get("role", "customer")

        # -------------------------------------------------
        # OWNER - STEP 2: verify the one-time admin code
        # -------------------------------------------------
        if role == "owner" and request.form.get("pending_token"):

            pending_token = request.form.get("pending_token", "").strip()
            invite_code = request.form.get("invite_code", "").strip().upper()
            token_hash = hashlib.sha256(pending_token.encode("utf-8")).hexdigest()

            conn = connect_db()
            pending = conn.execute("""
                SELECT *
                FROM pending_owner_registrations
                WHERE token_hash = ?
                  AND datetime(expires_at) > datetime('now')
                LIMIT 1
            """, (token_hash,)).fetchone()

            if not pending:
                conn.close()
                error = "שלב האימות פג תוקף. יש להתחיל את ההרשמה מחדש."
                step = "details"
            else:
                business = get_business_by_invite_code(invite_code)

                if not business or business["business_id"] != pending["business_id"]:
                    conn.close()
                    error = "קוד ההרשאה שגוי, כבר נוצל או שפג תוקפו."
                    step = "code"
                else:
                    if _user_phone_exists(pending["phone"]):
                        conn.close()
                        error = "מספר הטלפון כבר משויך למשתמש קיים."
                        step = "code"
                    else:
                        cur = conn.cursor()
                        cur.execute("""
                        UPDATE business_invites
                        SET used_at = CURRENT_TIMESTAMP
                        WHERE invite_id = ?
                          AND used_at IS NULL
                          AND datetime(expires_at) > datetime('now')
                    """, (business["invite_id"],))

                    if cur.rowcount != 1:
                        conn.rollback()
                        conn.close()
                        error = "קוד ההרשאה כבר נוצל או שפג תוקפו."
                        step = "code"
                    else:
                        try:
                            cur.execute("""
                                INSERT INTO users
                                (email, password_hash, role, business_id, full_name, phone)
                                VALUES (?, ?, 'owner', ?, ?, ?)
                            """, (
                                pending["email"],
                                pending["password_hash"],
                                pending["business_id"],
                                pending["full_name"],
                                pending["phone"]
                            ))
                            cur.execute(
                                "DELETE FROM pending_owner_registrations WHERE pending_id = ?",
                                (pending["pending_id"],)
                            )
                            conn.commit()
                            conn.close()
                            flash_message("החשבון נוצר בהצלחה. אפשר להתחבר.", "success")
                            return redirect(url_for("login"))
                        except Exception:
                            conn.rollback()
                            conn.close()
                            error = "לא ניתן ליצור את החשבון. ייתכן שהאימייל כבר קיים."
                            step = "code"

        # -------------------------------------------------
        # OWNER - STEP 1: verify phone against admin-created business
        # -------------------------------------------------
        elif role == "owner":

            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            full_name = request.form.get("full_name", "").strip()
            phone = normalize_phone(request.form.get("phone", ""))

            if not email or not password:
                error = "יש למלא אימייל וסיסמה."
            elif get_user_by_email(email):
                error = "כבר קיים חשבון עם האימייל הזה."
            elif not full_name:
                error = "נא להזין שם מלא."
            elif not phone:
                error = "נא להזין מספר טלפון."
            elif _user_phone_exists(phone):
                error = "מספר הטלפון כבר משויך למשתמש קיים."
            else:
                business = get_business_by_owner_phone(phone)

                if not business:
                    error = "מספר הטלפון לא נמצא במערכת או שאינו משויך לעסק מאושר. יש לפנות למנהל המערכת."
                else:
                    token = secrets.token_urlsafe(32)
                    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
                    expires = (datetime.utcnow() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")

                    conn = connect_db()
                    conn.execute("""
                        DELETE FROM pending_owner_registrations
                        WHERE datetime(expires_at) <= datetime('now')
                           OR email = ?
                    """, (email,))
                    conn.execute("""
                        INSERT INTO pending_owner_registrations
                        (token_hash, email, password_hash, full_name, phone, business_id, expires_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        token_hash,
                        email,
                        generate_password_hash(password),
                        full_name,
                        phone,
                        business["business_id"],
                        expires
                    ))
                    conn.commit()
                    conn.close()

                    pending_token = token
                    step = "code"

        # -------------------------------------------------
        # CUSTOMER - existing phone authorization flow
        # -------------------------------------------------
        elif role == "customer":

            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            full_name = request.form.get("full_name", "").strip()
            phone = normalize_phone(request.form.get("phone", ""))
            address = request.form.get("address", "").strip()

            if not email or not password:
                error = "יש למלא אימייל וסיסמה."
            elif get_user_by_email(email):
                error = "כבר קיים חשבון עם האימייל הזה."
            elif not full_name:
                error = "נא להזין שם מלא."
            elif not phone:
                error = "נא להזין מספר טלפון."
            elif _user_phone_exists(phone):
                error = "מספר הטלפון כבר משויך למשתמש קיים."
            else:
                conn = connect_db()
                customer_rows = conn.execute("""
                    SELECT *
                    FROM customers
                    WHERE phone IS NOT NULL
                """).fetchall()
                conn.close()

                customer = None
                for candidate in customer_rows:
                    if normalize_phone(candidate["phone"]) == phone:
                        customer = candidate
                        break

                if not customer:
                    error = "מספר הטלפון לא נמצא במערכת. יש לפנות לבית העסק."
                else:
                    try:
                        conn = connect_db()
                        conn.execute("""
                            UPDATE customers
                            SET email = ?, address = ?
                            WHERE customer_id = ? AND business_id = ?
                        """, (
                            email,
                            address or None,
                            customer["customer_id"],
                            customer["business_id"]
                        ))

                        conn.execute("""
                            INSERT INTO users
                            (email, password_hash, role, business_id, customer_id, full_name, phone)
                            VALUES (?, ?, 'customer', ?, ?, ?, ?)
                        """, (
                            email,
                            generate_password_hash(password),
                            customer["business_id"],
                            customer["customer_id"],
                            full_name,
                            phone
                        ))
                        conn.commit()
                        conn.close()
                        flash_message("החשבון נוצר בהצלחה.", "success")
                        return redirect(url_for("login"))
                    except Exception:
                        error = "לא ניתן ליצור את החשבון."

        else:
            error = "סוג החשבון אינו תקין."

    # The second screen is intentionally shown only after the phone matched an
    # active business created by the Super Admin.
    if step == "code":
        form_html = f"""
        <div class="card" style="margin-top:15px;">
            <h2>🔐 אימות בעל העסק</h2>
            <p>מספר הטלפון אומת ונמצא משויך לעסק במערכת.</p>
            <p>כעת הזן את קוד ההרשאה שקיבלת ממנהל המערכת.</p>
            {(f'<div class="error">{error}</div>' if error else '')}
            <form method="POST">
                <input type="hidden" name="role" value="owner">
                <input type="hidden" name="pending_token" value="{pending_token}">
                <label>קוד הרשאה</label>
                <input type="text" name="invite_code" placeholder="BS-ABCDE-12345" autocomplete="off" required>
                <button class="auth-button" type="submit">אימות קוד ויצירת חשבון</button>
            </form>
        </div>
        """
    else:
        error_html = f'<div class="error">{error}</div>' if error else ''
        form_html = f"""
        {error_html}
        <form method="POST">
            <label>סוג חשבון</label>
            <select name="role" id="role" onchange="changeRole()">
                <option value="owner">בעל עסק</option>
                <option value="customer">לקוח</option>
            </select>

            <label>אימייל</label>
            <input type="email" name="email" required>

            <label>סיסמה</label>
            <input type="password" name="password" required>

            <div id="ownerIntro">
                <div class="muted" style="margin:12px 0;">
                    העסק כבר הוגדר על ידי מנהל המערכת. לאחר לחיצה על "יצירת חשבון"
                    נבדוק את מספר הטלפון ורק אם הוא תואם לעסק ייפתח שלב קוד ההרשאה.
                </div>
            </div>

            <label>שם מלא</label>
            <input type="text" name="full_name" required>

            <label>טלפון</label>
            <input type="text" name="phone" placeholder="0501234567" required>

            <div id="customerAddress">
                <label>כתובת</label>
                <input type="text" name="address" placeholder="כתובת מגורים">
            </div>

            <button class="auth-button" type="submit">יצירת חשבון</button>
        </form>
        """

    return render_template_string(
        STYLE + f"""
        <div class="auth-page">
            <div class="auth-card">
                <h1>יצירת חשבון</h1>
                <div class="auth-subtitle">הצטרפות למערכת</div>
                {form_html}
                <div class="auth-link">
                    כבר יש לך חשבון?
                    <a href="/login">התחברות</a>
                </div>
            </div>
        </div>

        <script>
        function changeRole() {{
            const role = document.getElementById("role").value;
            const ownerIntro = document.getElementById("ownerIntro");
            const customerAddress = document.getElementById("customerAddress");
            if (ownerIntro) {{
                ownerIntro.style.display = role === "owner" ? "block" : "none";
            }}
            if (customerAddress) {{
                customerAddress.style.display = role === "customer" ? "block" : "none";
            }}
        }}
        changeRole();
        </script>
        """
    )

@app.route("/login", methods=["GET", "POST"])
def login():

    error = ""

    message, message_type = consume_flash()

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = get_user_by_email(email)

        if not user:

            error = "האימייל או הסיסמה שגויים."

        elif not user["is_active"]:

            error = "המשתמש אינו פעיל."

        elif not check_password_hash(
            user["password_hash"],
            password
        ):

            error = "האימייל או הסיסמה שגויים."

        else:

            session.clear()

            session["user_id"] = user["user_id"]
            session["email"] = user["email"]
            session["role"] = user["role"]
            session["business_id"] = user["business_id"]
            session["customer_id"] = user["customer_id"]

            return redirect(
                url_for("dashboard")
            )

    return render_template_string(
        STYLE + f"""

        <div class="auth-page">

            <div class="auth-card">

                <div class="auth-brand">BOOK SMART AI</div>

                <h1>
                    ברוך הבא
                </h1>

                <div class="auth-subtitle">
                    מערכת AI חכמה לניהול תורים
                </div>

                <p class="auth-tagline">
                    פחות התעסקות. יותר לקוחות. ניהול תורים חכם שעובד בשביל העסק שלך.
                </p>

                {(
                    f'<div class="success">{message}</div>'
                    if message and message_type == "success"
                    else ""
                )}

                {(
                    f'<div class="error">{error}</div>'
                    if error else ""
                )}

                <form method="POST">

                    <label>
                        אימייל
                    </label>

                    <input
                        type="email"
                        name="email"
                        required
                    >

                    <label>
                        סיסמה
                    </label>

                    <input
                        type="password"
                        name="password"
                        required
                    >

                    <button
                        class="auth-button"
                        type="submit"
                    >
                        התחברות
                    </button>

                </form>

                <div class="auth-link">

                    אין לך חשבון?

                    <a href="/register">
                        פתיחת חשבון
                    </a>

                </div>

                <div class="auth-link">

                    <a href="/contact">
                        צור קשר
                    </a>

                </div>

            </div>

        </div>

        """
    )

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )

