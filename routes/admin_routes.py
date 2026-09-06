# Auto-generated modular route module for Book Smart AI.
from app import *

@app.route("/admin")
def admin_dashboard():

    check = require_super_admin()
    if check:
        return check

    conn = connect_db()
    try:
        business_count = conn.execute("SELECT COUNT(*) FROM businesses").fetchone()[0]
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        lead_count = conn.execute("SELECT COUNT(*) FROM leads WHERE business_id IS NULL").fetchone()[0]
    finally:
        conn.close()

    return render_template_string(
        STYLE + f"""
        <div class="dashboard">
            {sidebar_html()}
            <div class="content">
                <div class="topbar">
                    <div>
                        <h1>מרכז ניהול</h1>
                        <div class="user-info">ניהול עסקים, משתמשים ולידים</div>
                    </div>
                </div>

                <div class="cards">
                    <div class="stat-card">
                        <div class="stat-title">עסקים</div>
                        <div class="stat-number">{business_count}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title">משתמשים</div>
                        <div class="stat-number">{user_count}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title">לידים</div>
                        <div class="stat-number">{lead_count}</div>
                    </div>
                </div>

                <div class="card">
                    <h2>ניהול המערכת</h2>
                    <p>בחר מהתפריט: עסקים, משתמשים או לידים.</p>
                    <div class="form-actions">
                        <a href="/admin/businesses"><button>🏢 עסקים</button></a>
                        <a href="/admin/users"><button>👥 משתמשים</button></a>
                        <a href="/admin/leads"><button>🎯 לידים</button></a>
                    </div>
                </div>
            </div>
        </div>
        """
    )

@app.route("/admin/business/create", methods=["GET", "POST"])
def admin_create_business():
    check = require_super_admin()
    if check:
        return check

    error = ""
    generated_code = None

    if request.method == "POST":
        business_name = request.form.get("business_name", "").strip()
        business_type = request.form.get("business_type", "").strip()
        owner_name = request.form.get("owner_name", "").strip()
        owner_phone = request.form.get("owner_phone", "").strip()

        if not business_name or not owner_name or not owner_phone:
            error = "יש למלא שם עסק, שם בעל העסק ומספר טלפון."
        else:
            conn = connect_db()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO businesses
                    (business_name, business_type, phone, approval_status, is_active)
                    VALUES (?, ?, ?, 'approved', 1)
                """, (business_name, business_type, normalize_phone(owner_phone)))
                business_id = cursor.lastrowid

                default_hours = [
                    (0, 1, "09:00", "18:00"),
                    (1, 1, "09:00", "18:00"),
                    (2, 1, "09:00", "18:00"),
                    (3, 1, "09:00", "18:00"),
                    (4, 1, "09:00", "18:00"),
                    (5, 1, "09:00", "13:00"),
                    (6, 0, None, None),
                ]
                cursor.executemany("""
                    INSERT INTO business_hours
                    (business_id, day_of_week, is_open, open_time, close_time)
                    VALUES (?, ?, ?, ?, ?)
                """, [(business_id, *row) for row in default_hours])

                code = generate_business_invite_code()
                expires = (datetime.utcnow() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    INSERT INTO business_invites
                    (business_id, code_hash, expires_at)
                    VALUES (?, ?, ?)
                """, (business_id, hash_invite_code(code), expires))

                conn.commit()
                generated_code = code
            except Exception as e:
                conn.rollback()
                error = "לא ניתן ליצור את העסק: " + str(e)
            finally:
                conn.close()

    if generated_code:
        content = f"""
        <div class="card">
            <h2>העסק נוצר בהצלחה ✅</h2>
            <p>זהו קוד ההרשאה של בעל העסק:</p>
            <div style="font-size:30px;font-weight:bold;letter-spacing:3px;color:var(--gold-light);padding:20px 0;">
                {generated_code}
            </div>
            <div class="warning">
                הקוד חד־פעמי ותוקפו 24 שעות מרגע יצירת העסק.
                לאחר השימוש בו לא ניתן להשתמש בו שוב.
            </div>
            <a href="/admin/businesses"><button>חזרה לרשימת העסקים</button></a>
        </div>
        """
    else:
        content = f"""
        <div class="card">
            <h2>הוסף עסק</h2>
            <p>יצירת עסק מאושר והפקת קוד הרשאה חד־פעמי.</p>
            {f'<div class="error">{error}</div>' if error else ""}
            <form method="POST">
                <label>שם העסק</label>
                <input name="business_name" required>

                <label>סוג העסק</label>
                <input name="business_type">

                <label>שם בעל העסק</label>
                <input name="owner_name" required>

                <label>מספר טלפון של בעל העסק</label>
                <input name="owner_phone" required>

                <button type="submit" style="margin-top:22px;">
                    צור עסק והפק קוד הרשאה
                </button>
            </form>
        </div>
        """

    return render_template_string(
        STYLE + f"""
        <div class="dashboard">
            {sidebar_html()}
            <div class="content">
                <div class="topbar">
                    <div>
                        <h1>הוספת עסק</h1>
                        <div class="user-info">Super Admin — הרשאת עסק</div>
                    </div>
                </div>
                {content}
            </div>
        </div>
        """
    )


@app.route("/admin/business/<int:business_id>/delete", methods=["POST"])
def admin_delete_business(business_id):
    check = require_super_admin()
    if check:
        return check

    conn = connect_db()
    try:
        if not conn.execute("SELECT 1 FROM businesses WHERE business_id = ?", (business_id,)).fetchone():
            return "עסק לא נמצא", 404
        conn.execute("DELETE FROM businesses WHERE business_id = ?", (business_id,))
        conn.commit()
    finally:
        conn.close()

    flash_message("העסק וכל הנתונים והמשתמשים השייכים אליו נמחקו.", "success")
    return redirect(url_for("admin_businesses"))


@app.route("/admin/businesses")
def admin_businesses():

    check = require_super_admin()

    if check:
        return check

    businesses = get_all_businesses()

    rows = ""

    for business in businesses:

        rows += f"""

        <tr>

            <td>
                {business["business_id"]}
            </td>

            <td>
                {business["business_name"]}
            </td>

            <td>
                {safe(business["business_type"])}
            </td>

            <td>
                {safe(business["phone"])}
            </td>

            <td>

                <a
                    href="/admin/business/{business["business_id"]}"
                >

                    <button class="small-button">
                        כניסה לנתונים
                    </button>

                </a>

                <form method="POST" action="/admin/business/{business["business_id"]}/delete" style="display:inline; margin-right:8px;">
                    <button type="submit" class="small-button danger-button" onclick="return confirm('מחיקת העסק תמחק את כל הנתונים והמשתמשים השייכים אליו. להמשיך?');">🗑️ מחיקה</button>
                </form>

            </td>

        </tr>

        """

    if not rows:

        rows = """

        <tr>

            <td
                colspan="5"
                class="empty"
            >
                אין עסקים.
            </td>

        </tr>

        """

    return render_template_string(
        STYLE + f"""

        <div class="dashboard">

            {sidebar_html()}

            <div class="content">

                <div class="topbar">

                    <div>
                        <h1>כל העסקים</h1>
                        <div class="user-info">ניהול ואישור העסקים במערכת</div>
                    </div>
                    <a href="/admin/business/create">
                        <button>+ הוסף עסק</button>
                    </a>

                </div>

                <div class="table-card">

                    <table>

                        <thead>

                            <tr>

                                <th>מזהה</th>
                                <th>שם העסק</th>
                                <th>סוג</th>
                                <th>טלפון</th>
                                <th>פעולות</th>

                            </tr>

                        </thead>

                        <tbody>

                            {rows}

                        </tbody>

                    </table>

                </div>

            </div>

        </div>

        """
    )

@app.route("/admin/business/<int:business_id>")
def admin_business_details(business_id):

    check = require_super_admin()
    if check:
        return check

    business = get_business(business_id)
    if not business:
        return "עסק לא נמצא", 404

    conn = connect_db()
    try:
        users_list = conn.execute("""
            SELECT email, full_name, role, is_active
            FROM users
            WHERE business_id = ?
            ORDER BY user_id
        """, (business_id,)).fetchall()

        leads_list = conn.execute("""
            SELECT full_name, phone, email, source, status, created_at
            FROM leads
            WHERE business_id = ?
            ORDER BY created_at DESC
            LIMIT 100
        """, (business_id,)).fetchall()
    finally:
        conn.close()

    def table_rows(items, colspan):
        if not items:
            return f'<tr><td colspan="{colspan}" class="empty">אין נתונים.</td></tr>'
        return "".join(
            "<tr>" + "".join(f"<td>{safe(value)}</td>" for value in row) + "</tr>"
            for row in items
        )

    user_rows = table_rows(
        [(u["email"], u["full_name"], u["role"], "פעיל" if u["is_active"] else "לא פעיל") for u in users_list],
        4,
    )
    lead_rows = table_rows(
        [(l["full_name"], l["phone"], l["email"], l["source"], l["status"], l["created_at"]) for l in leads_list],
        6,
    )

    return render_template_string(
        STYLE + f"""
        <div class="dashboard">
            {sidebar_html()}
            <div class="content">
                <div class="topbar">
                    <div>
                        <h1>{safe(business["business_name"])}</h1>
                        <div class="user-info">פרטי העסק וניהול משתמשים ולידים</div>
                    </div>
                </div>

                <div class="card">
                    <h2>פרטי העסק</h2>
                    <p><strong>סוג:</strong> {safe(business["business_type"])}</p>
                    <p><strong>טלפון:</strong> {safe(business["phone"])}</p>
                    <p><strong>אימייל:</strong> {safe(business["email"])}</p>
                    <p><strong>כתובת:</strong> {safe(business["address"])}</p>
                    <p><strong>תיאור:</strong> {safe(business["description"])}</p>
                </div>

                <div class="table-card">
                    <h2>משתמשי העסק</h2>
                    <table>
                        <thead><tr><th>אימייל</th><th>שם</th><th>תפקיד</th><th>סטטוס</th></tr></thead>
                        <tbody>{user_rows}</tbody>
                    </table>
                </div>

                <div class="table-card">
                    <h2>לידים של העסק</h2>
                    <table>
                        <thead><tr><th>שם</th><th>טלפון</th><th>אימייל</th><th>מקור</th><th>סטטוס</th><th>נוצר</th></tr></thead>
                        <tbody>{lead_rows}</tbody>
                    </table>
                </div>

                <div class="form-actions">
                    <a href="/admin/businesses"><button class="secondary-button">חזרה לעסקים</button></a>
                </div>
            </div>
        </div>
        """
    )

@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
def admin_delete_user(user_id):
    check = require_super_admin()
    if check:
        return check

    conn = connect_db()
    try:
        user = conn.execute("SELECT role FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user:
            return "משתמש לא נמצא", 404
        if user["role"] == "super_admin":
            return "לא ניתן למחוק את מנהל המערכת הראשי.", 403
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()

    flash_message("המשתמש נמחק.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/users")
def admin_users():

    check = require_super_admin()

    if check:
        return check

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            u.*,
            b.business_name

        FROM users u

        LEFT JOIN businesses b
            ON u.business_id = b.business_id

        ORDER BY u.user_id DESC
    """)

    users = cursor.fetchall()

    conn.close()

    rows = ""

    for user in users:

        rows += f"""

        <tr>

            <td>
                {user["user_id"]}
            </td>

            <td>
                {user["email"]}
            </td>

            <td>
                {user["role"]}
            </td>

            <td>
                {safe(user["business_name"])}
            </td>

            <td>
                {
                    "פעיל"
                    if user["is_active"]
                    else "לא פעיל"
                }
            </td>

            <td>
                {f"""
                <form method="POST" action="/admin/user/{user["user_id"]}/delete" style="display:inline;">
                    <button type="submit" class="small-button danger-button" onclick="return confirm('למחוק את המשתמש?');">🗑️ מחיקה</button>
                </form>
                """ if user["role"] != "super_admin" else "—"}
            </td>

        </tr>

        """

    return render_template_string(
        STYLE + f"""

        <div class="dashboard">

            {sidebar_html()}

            <div class="content">

                <div class="topbar">

                    <h1>
                        משתמשים
                    </h1>

                </div>

                <div class="table-card">

                    <table>

                        <thead>

                            <tr>

                                <th>ID</th>
                                <th>אימייל</th>
                                <th>תפקיד</th>
                                <th>עסק</th>
                                <th>סטטוס</th>
                                <th>פעולות</th>

                            </tr>

                        </thead>

                        <tbody>

                            {rows}

                        </tbody>

                    </table>

                </div>

            </div>

        </div>

        """
    )

@app.route("/admin/leads", methods=["GET", "POST"])
def admin_leads():
    check=require_super_admin()
    if check: return check
    conn=connect_db(); cur=conn.cursor(); message=""; error=""
    if request.method=="POST":
        action=request.form.get("action"); lead_id=request.form.get("lead_id")
        if action=="add":
            name=request.form.get("full_name","").strip(); phone=normalize_phone(request.form.get("phone","")); email=request.form.get("email","").strip(); source=request.form.get("source","manual").strip() or "manual"
            if not name: error="נא להזין שם מלא."
            else: cur.execute("INSERT INTO leads(business_id,full_name,phone,email,source,status) VALUES(NULL,?,?,?,?,\'new\')",(name,phone,email,source)); conn.commit(); message="הליד נוסף בהצלחה."
        elif action=="delete" and lead_id: cur.execute("DELETE FROM leads WHERE lead_id=? AND business_id IS NULL",(lead_id,)); conn.commit(); message="הליד נמחק."
        elif action=="status" and lead_id:
            status=request.form.get("status")
            if status in {"new","contacted","in_progress","appointment","customer","not_interested"}: cur.execute("UPDATE leads SET status=? WHERE lead_id=? AND business_id IS NULL",(status,lead_id)); conn.commit(); message="סטטוס הליד עודכן."
    leads_list=cur.execute("SELECT * FROM leads WHERE business_id IS NULL ORDER BY created_at DESC").fetchall(); conn.close()
    labels={"new":"🆕 חדש","contacted":"📞 נוצר קשר","in_progress":"🔄 בטיפול","appointment":"📅 נקבע תור","customer":"👤 הפך ללקוח","not_interested":"❌ לא מעוניין"}; rows=""
    for l in leads_list:
        opts="".join(f'<option value="{k}" {"selected" if k==l["status"] else ""}>{v}</option>' for k,v in labels.items())
        rows+=f'<tr><td>{safe(l["full_name"])}</td><td>{safe(l["phone"])}</td><td>{safe(l["email"])}</td><td>{safe(l["source"])}</td><td><form method="POST"><input type="hidden" name="action" value="status"><input type="hidden" name="lead_id" value="{l["lead_id"]}"><select name="status" onchange="this.form.submit()">{opts}</select></form></td><td><form method="POST"><input type="hidden" name="action" value="delete"><input type="hidden" name="lead_id" value="{l["lead_id"]}"><button>🗑️ מחק ליד</button></form></td></tr>'
    return render_template_string(STYLE+f"""<div class=\"dashboard\">{sidebar_html()}<div class=\"content\"><div class=\"topbar\"><h1>לידים</h1></div>{f'<div class=\"success\">{message}</div>' if message else ''}{f'<div class=\"error\">{error}</div>' if error else ''}<div class=\"card\"><h2>+ הוסף ליד</h2><form method=\"POST\"><input type=\"hidden\" name=\"action\" value=\"add\"><label>שם מלא *</label><input name=\"full_name\" required><label>טלפון</label><input name=\"phone\"><label>אימייל</label><input name=\"email\" type=\"email\"><label>מקור</label><input name=\"source\" value=\"manual\"><button>הוסף ליד</button></form></div><div class=\"table-card\"><table><thead><tr><th>שם</th><th>טלפון</th><th>אימייל</th><th>מקור</th><th>סטטוס</th><th>פעולות</th></tr></thead><tbody>{rows or '<tr><td colspan=\"6\">לא נמצאו לידים.</td></tr>'}</tbody></table></div></div></div>""")
