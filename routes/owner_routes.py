# Auto-generated modular route module for Book Smart AI.
from app import *

@app.route("/dashboard")
def dashboard():

    login_check = require_login()

    if login_check:
        return login_check

    role = session["role"]

    if role == "super_admin":

        return redirect(
            url_for("admin_dashboard")
        )

    if role == "owner":

        return owner_dashboard()

    return redirect(url_for("customer_dashboard"))

def owner_dashboard():

    business_id = session["business_id"]

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM customers
        WHERE business_id = ?
    """, (business_id,))

    customer_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM appointments
        WHERE business_id = ?
    """, (business_id,))

    appointment_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM invoices
        WHERE business_id = ?
    """, (business_id,))

    invoice_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM leads
        WHERE business_id = ?
    """, (business_id,))

    lead_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT
            a.appointment_date,
            a.appointment_time,
            c.full_name,
            a.service_type,
            a.status

        FROM appointments a

        JOIN customers c
            ON a.customer_id = c.customer_id

        WHERE a.business_id = ?

        ORDER BY
            a.appointment_date,
            a.appointment_time

        LIMIT 8
    """, (business_id,))

    appointments = cursor.fetchall()

    business = get_business(
        business_id
    )

    conn.close()

    rows = ""

    for appointment in appointments:

        rows += f"""

        <tr>

            <td>
                {appointment["appointment_date"]}
            </td>

            <td>
                {appointment["appointment_time"]}
            </td>

            <td>
                {appointment["full_name"]}
            </td>

            <td>
                {appointment["service_type"]}
            </td>

            <td>
                {STATUS_NAMES.get(
                    appointment["status"],
                    appointment["status"]
                )}
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
                אין תורים להצגה.
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

                        <h1>
                            {business["business_name"] if business else "העסק שלי"}
                        </h1>

                        <div class="user-info">
                            לוח הבקרה של העסק
                        </div>

                    </div>

                </div>

                <div class="cards">

                    <div class="stat-card">

                        <div class="stat-title">
                            לקוחות
                        </div>

                        <div class="stat-number">
                            {customer_count}
                        </div>

                    </div>

                    <div class="stat-card">

                        <div class="stat-title">
                            תורים
                        </div>

                        <div class="stat-number">
                            {appointment_count}
                        </div>

                    </div>

                    <div class="stat-card">

                        <div class="stat-title">
                            חשבוניות
                        </div>

                        <div class="stat-number">
                            {invoice_count}
                        </div>

                    </div>

                    <div class="stat-card">

                        <div class="stat-title">
                            לידים
                        </div>

                        <div class="stat-number">
                            {lead_count}
                        </div>

                    </div>

                </div>

                <div class="table-card">

                    <h2>
                        כל התורים
                    </h2>

                    <table>

                        <thead>

                            <tr>

                                <th>תאריך</th>
                                <th>שעה</th>
                                <th>לקוח</th>
                                <th>שירות</th>
                                <th>סטטוס</th>

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

@app.route("/business/settings", methods=["GET", "POST"])
def business_settings():

    check = require_owner()

    if check:
        return check

    business_id = session["business_id"]

    if request.method == "POST":

        business_name = request.form.get(
            "business_name",
            ""
        ).strip()

        business_type = request.form.get(
            "business_type",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE businesses

            SET
                business_name = ?,
                business_type = ?,
                phone = ?,
                email = ?,
                address = ?,
                description = ?

            WHERE business_id = ?
        """, (
            business_name,
            business_type,
            phone,
            email,
            address,
            description,
            business_id
        ))

        conn.commit()
        conn.close()

        flash_message(
            "פרטי העסק עודכנו.",
            "success"
        )

        return redirect(
            url_for("business_settings")
        )

    business = get_business(
        business_id
    )

    return render_template_string(
        STYLE + f"""

        <div class="dashboard">

            {sidebar_html()}

            <div class="content">

                <div class="topbar">

                    <div>

                        <h1>
                            העסק שלי
                        </h1>

                        <div class="user-info">
                            פרטי העסק
                        </div>

                    </div>

                </div>

                <div class="card">

                    <form method="POST">

                        <div class="form-grid">

                            <div>

                                <label>
                                    שם העסק
                                </label>

                                <input
                                    name="business_name"
                                    value="{safe(business["business_name"] if business else "העסק שלי")}"
                                    required
                                >

                            </div>

                            <div>

                                <label>
                                    סוג העסק
                                </label>

                                <input
                                    name="business_type"
                                    value="{safe(business["business_type"])}"
                                >

                            </div>

                            <div>

                                <label>
                                    טלפון
                                </label>

                                <input
                                    name="phone"
                                    value="{safe(business["phone"])}"
                                >

                            </div>

                            <div>

                                <label>
                                    אימייל
                                </label>

                                <input
                                    name="email"
                                    type="email"
                                    value="{safe(business["email"])}"
                                >

                            </div>

                            <div class="form-full">

                                <label>
                                    כתובת
                                </label>

                                <input
                                    name="address"
                                    value="{safe(business["address"])}"
                                >

                            </div>

                            <div class="form-full">

                                <label>
                                    תיאור העסק
                                </label>

                                <textarea
                                    name="description"
                                >{safe(business["description"])}</textarea>

                            </div>

                        </div>

                        <div class="form-actions">

                            <button type="submit">
                                שמירת שינויים
                            </button>

                        </div>

                    </form>

                </div>

            </div>

        </div>

        """
    )

@app.route("/services", methods=["GET", "POST"])
def services():

    check = require_owner()

    if check:
        return check

    business_id = session["business_id"]

    if request.method == "POST":

        action = request.form.get(
            "action"
        )

        if action == "create":

            service_name = request.form.get(
                "service_name",
                ""
            ).strip()

            description = request.form.get(
                "description",
                ""
            ).strip()

            price = request.form.get(
                "price",
                "0"
            )

            duration = request.form.get(
                "duration_minutes",
                "30"
            )

            if service_name:

                try:

                    price = float(price)
                    duration = int(duration)

                    conn = connect_db()
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT INTO services
                        (
                            business_id,
                            service_name,
                            description,
                            price,
                            duration_minutes
                        )
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        business_id,
                        service_name,
                        description,
                        price,
                        duration
                    ))

                    conn.commit()
                    conn.close()

                    flash_message(
                        "השירות נוסף בהצלחה.",
                        "success"
                    )

                except Exception:

                    flash_message(
                        "לא ניתן להוסיף את השירות.",
                        "error"
                    )

        elif action == "delete":

            service_id = request.form.get(
                "service_id"
            )

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE services
                SET is_active = 0

                WHERE service_id = ?
                AND business_id = ?
            """, (
                service_id,
                business_id
            ))

            conn.commit()
            conn.close()

            flash_message(
                "השירות הושבת.",
                "success"
            )

        return redirect(
            url_for("services")
        )

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM services

        WHERE business_id = ?

        ORDER BY service_name
    """, (business_id,))

    services_list = cursor.fetchall()

    conn.close()

    rows = ""

    for service in services_list:

        rows += f"""

        <tr>

            <td>
                {service["service_name"]}
            </td>

            <td>
                {service["price"]:.2f} ₪
            </td>

            <td>
                {service["duration_minutes"]} דקות
            </td>

            <td>
                {
                    "פעיל"
                    if service["is_active"]
                    else "מושבת"
                }
            </td>

            <td>

                {
                    f'''
                    <form
                        method="POST"
                        style="display:inline;"
                    >

                        <input
                            type="hidden"
                            name="action"
                            value="delete"
                        >

                        <input
                            type="hidden"
                            name="service_id"
                            value="{service["service_id"]}"
                        >

                        <button
                            class="small-button danger-button"
                            type="submit"
                        >
                            השבתה
                        </button>

                    </form>
                    '''
                    if service["is_active"]
                    else ""
                }

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

                        <h1>
                            שירותים ומחירים
                        </h1>

                        <div class="user-info">
                            הגדרת השירותים שהלקוחות יוכלו להזמין
                        </div>

                    </div>

                </div>

                <div class="card">

                    <h2>
                        הוספת שירות
                    </h2>

                    <form method="POST">

                        <input
                            type="hidden"
                            name="action"
                            value="create"
                        >

                        <div class="form-grid">

                            <div>

                                <label>
                                    שם השירות
                                </label>

                                <input
                                    name="service_name"
                                    placeholder="תספורת"
                                    required
                                >

                            </div>

                            <div>

                                <label>
                                    מחיר
                                </label>

                                <input
                                    name="price"
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    placeholder="70"
                                    required
                                >

                            </div>

                            <div>

                                <label>
                                    משך השירות בדקות
                                </label>

                                <input
                                    name="duration_minutes"
                                    type="number"
                                    min="5"
                                    step="5"
                                    value="30"
                                    required
                                >

                            </div>

                            <div>

                                <label>
                                    תיאור
                                </label>

                                <input
                                    name="description"
                                >

                            </div>

                        </div>

                        <div class="form-actions">

                            <button type="submit">
                                הוספת שירות
                            </button>

                        </div>

                    </form>

                </div>

                <div class="table-card">

                    <h2>
                        השירותים שלך
                    </h2>

                    <table>

                        <thead>

                            <tr>

                                <th>שירות</th>
                                <th>מחיר</th>
                                <th>משך</th>
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

@app.route("/business/hours", methods=["GET", "POST"])
def business_hours():

    check = require_owner()

    if check:
        return check

    business_id = session["business_id"]

    if request.method == "POST":

        conn = connect_db()
        cursor = conn.cursor()

        for day in range(7):

            is_open = (
                1
                if request.form.get(
                    f"is_open_{day}"
                )
                else 0
            )

            open_time = request.form.get(
                f"open_time_{day}"
            )

            close_time = request.form.get(
                f"close_time_{day}"
            )

            cursor.execute("""
                INSERT INTO business_hours
                (
                    business_id,
                    day_of_week,
                    is_open,
                    open_time,
                    close_time
                )
                VALUES (?, ?, ?, ?, ?)

                ON CONFLICT (
                    business_id,
                    day_of_week
                )

                DO UPDATE SET

                    is_open =
                        excluded.is_open,

                    open_time =
                        excluded.open_time,

                    close_time =
                        excluded.close_time
            """, (
                business_id,
                day,
                is_open,
                open_time,
                close_time
            ))

        conn.commit()
        conn.close()

        flash_message(
            "שעות הפעילות נשמרו.",
            "success"
        )

        return redirect(
            url_for("business_hours")
        )

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM business_hours

        WHERE business_id = ?

        ORDER BY day_of_week
    """, (business_id,))

    hours = cursor.fetchall()

    conn.close()

    hours_by_day = {
        h["day_of_week"]: h
        for h in hours
    }

    rows = ""

    for day in range(7):

        current = hours_by_day.get(
            day
        )

        is_open = (
            current["is_open"]
            if current
            else 0
        )

        open_time = (
            current["open_time"]
            if current and current["open_time"]
            else "09:00"
        )

        close_time = (
            current["close_time"]
            if current and current["close_time"]
            else "18:00"
        )

        rows += f"""

        <div class="option-card">

            <h3>
                {DAY_NAMES[day]}
            </h3>

            <label>

                <input
                    type="checkbox"
                    name="is_open_{day}"
                    {"checked" if is_open else ""}
                    style="width:auto;"
                    onchange="
                        document.getElementById(
                            'times_{day}'
                        ).style.opacity =
                        this.checked ? '1' : '0.4';
                    "
                >

                פתוח

            </label>

            <label>
                שעת פתיחה
            </label>

            <input
                type="time"
                name="open_time_{day}"
                value="{open_time}"
            >

            <label>
                שעת סגירה
            </label>

            <input
                type="time"
                name="close_time_{day}"
                value="{close_time}"
            >

        </div>

        """

    return render_template_string(
        STYLE + f"""

        <div class="dashboard">

            {sidebar_html()}

            <div class="content">

                <div class="topbar">

                    <div>

                        <h1>
                            שעות פעילות
                        </h1>

                        <div class="user-info">
                            הגדר את השעות הקבועות של העסק
                        </div>

                    </div>

                </div>

                <form method="POST">

                    <div class="availability-options">

                        {rows}

                    </div>

                    <div class="form-actions">

                        <button type="submit">
                            שמירת שעות הפעילות
                        </button>

                    </div>

                </form>

            </div>

        </div>

        """
    )

def get_month_year():

    today = date.today()

    try:

        year = int(
            request.args.get(
                "year",
                today.year
            )
        )

        month = int(
            request.args.get(
                "month",
                today.month
            )
        )

    except ValueError:

        year = today.year
        month = today.month

    if month < 1:

        month = 12
        year -= 1

    if month > 12:

        month = 1
        year += 1

    return year, month

def get_date_availability(
    business_id,
    selected_date
):

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM availability

        WHERE business_id = ?
        AND availability_date = ?
    """, (
        business_id,
        selected_date
    ))

    override = cursor.fetchone()

    if override:

        conn.close()

        return override

    selected = datetime.strptime(
        selected_date,
        "%Y-%m-%d"
    ).date()

    day_of_week = (selected.weekday() + 1) % 7  # Sunday=0, Monday=1, ..., Saturday=6

    cursor.execute("""
        SELECT *
        FROM business_hours

        WHERE business_id = ?
        AND day_of_week = ?
    """, (
        business_id,
        day_of_week
    ))

    hours = cursor.fetchone()

    conn.close()

    if not hours:

        return None

    return {
        "is_available":
            hours["is_open"],

        "start_time":
            hours["open_time"],

        "end_time":
            hours["close_time"]
    }

@app.route("/calendar")
def calendar_view():

    check = require_owner()

    if check:
        return check

    business_id = session["business_id"]

    year, month = get_month_year()

    month_name = (
        f"{calendar.month_name[month]}"
    )

    first_weekday, days_in_month = (
        calendar.monthrange(
            year,
            month
        )
    )

    # Python Monday=0.
    # We need Sunday=0 for Hebrew calendar.
    start_offset = (
        first_weekday + 1
    ) % 7

    cells = ""

    for _ in range(start_offset):

        cells += """
        <div class="calendar-day empty-day">
        </div>
        """

    today = date.today()

    for day in range(
        1,
        days_in_month + 1
    ):

        selected = date(
            year,
            month,
            day
        )

        selected_string = (
            selected.isoformat()
        )

        availability = get_date_availability(
            business_id,
            selected_string
        )

        if availability is None:

            is_available = False
            status_text = "לא מוגדר"

        else:

            is_available = bool(
                availability["is_available"]
            )

            status_text = (
                "זמין"
                if is_available
                else "לא זמין"
            )

        classes = (
            "available"
            if is_available
            else "unavailable"
        )

        if selected == today:

            classes += " today"

        cells += f"""

        <a
            class="calendar-day {classes}"
            href="/calendar/day/{selected_string}"
        >

            <div class="calendar-day-number">
                {day}
            </div>

            <div class="calendar-day-status">
                {status_text}
            </div>

        </a>

        """

    previous_month = month - 1
    previous_year = year

    if previous_month < 1:

        previous_month = 12
        previous_year -= 1

    next_month = month + 1
    next_year = year

    if next_month > 12:

        next_month = 1
        next_year += 1

    return render_template_string(
        STYLE + f"""

        <div class="dashboard">

            {sidebar_html()}

            <div class="content">

                <div class="topbar">

                    <div>

                        <h1>
                            יומן וזמינות
                        </h1>

                        <div class="user-info">
                            בחר שנה, חודש ויום כדי להגדיר זמינות
                        </div>

                    </div>

                </div>

                <div class="table-card">

                    <div class="calendar-header">

                        <a href="/calendar?year={previous_year}&month={previous_month}">
                            <button
                                class="secondary-button"
                                type="button"
                            >
                                חודש קודם
                            </button>
                        </a>

                        <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;justify-content:center;">

                            <select
                                onchange="window.location='/calendar?year=' + this.value + '&month={month}'"
                                style="width:auto;min-width:120px;"
                            >
                                {''.join(
                                    f'<option value="{y}" {"selected" if y == year else ""}>{y}</option>'
                                    for y in range(max(date.today().year - 2, 2020), date.today().year + 6)
                                )}
                            </select>

                            <select
                                onchange="window.location='/calendar?year={year}&month=' + this.value"
                                style="width:auto;min-width:150px;"
                            >
                                {''.join(
                                    f'<option value="{m}" {"selected" if m == month else ""}>{calendar.month_name[m]}</option>'
                                    for m in range(1, 13)
                                )}
                            </select>

                        </div>

                        <a href="/calendar?year={next_year}&month={next_month}">
                            <button
                                class="secondary-button"
                                type="button"
                            >
                                חודש הבא
                            </button>
                        </a>

                    </div>

                    <div class="calendar-grid">

                        <div class="calendar-weekday">
                            א'
                        </div>

                        <div class="calendar-weekday">
                            ב'
                        </div>

                        <div class="calendar-weekday">
                            ג'
                        </div>

                        <div class="calendar-weekday">
                            ד'
                        </div>

                        <div class="calendar-weekday">
                            ה'
                        </div>

                        <div class="calendar-weekday">
                            ו'
                        </div>

                        <div class="calendar-weekday">
                            ש'
                        </div>

                        {cells}

                    </div>

                </div>

            </div>

        </div>

        """
    )

@app.route("/calendar/day/<selected_date>", methods=["GET", "POST"])
def calendar_day(selected_date):
    check = require_owner()
    if check:
        return check

    business_id = session["business_id"]
    try:
        selected = datetime.strptime(selected_date, "%Y-%m-%d").date()
    except ValueError:
        return "תאריך לא תקין", 400

    conn = connect_db()
    cursor = conn.cursor()

    if request.method == "POST":
        action = request.form.get("action", "save_availability")

        if action == "add_break":
            start_time = request.form.get("break_start_time", "").strip()
            end_time = request.form.get("break_end_time", "").strip()
            note = request.form.get("break_note", "").strip()

            if not start_time or not end_time or start_time >= end_time:
                conn.close()
                flash_message("יש לבחור שעת התחלה וסיום תקינות להפסקה.", "error")
                return redirect(url_for("calendar_day", selected_date=selected_date))

            # Break must sit inside the day's effective availability window.
            availability = get_date_availability(business_id, selected_date)
            if not availability or not availability["is_available"]:
                conn.close()
                flash_message("לא ניתן להוסיף הפסקה ליום שאינו זמין.", "error")
                return redirect(url_for("calendar_day", selected_date=selected_date))

            day_start = availability["start_time"] or ""
            day_end = availability["end_time"] or ""
            if not day_start or not day_end or start_time < day_start or end_time > day_end:
                conn.close()
                flash_message("ההפסקה חייבת להיות בתוך שעות הפעילות של היום.", "error")
                return redirect(url_for("calendar_day", selected_date=selected_date))

            overlap = cursor.execute("""
                SELECT 1 FROM availability_breaks
                WHERE business_id = ? AND break_date = ?
                  AND NOT (end_time <= ? OR start_time >= ?)
                LIMIT 1
            """, (business_id, selected_date, start_time, end_time)).fetchone()
            if overlap:
                conn.close()
                flash_message("ההפסקה חופפת להפסקה קיימת.", "error")
                return redirect(url_for("calendar_day", selected_date=selected_date))

            availability_id = availability["availability_id"] if "availability_id" in availability.keys() else None
            cursor.execute("""
                INSERT INTO availability_breaks
                    (business_id, availability_id, break_date, start_time, end_time, note)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (business_id, availability_id, selected_date, start_time, end_time, note))
            conn.commit()
            conn.close()
            flash_message("ההפסקה נוספה בהצלחה.", "success")
            return redirect(url_for("calendar_day", selected_date=selected_date))

        if action == "delete_break":
            break_id = request.form.get("break_id")
            cursor.execute("DELETE FROM availability_breaks WHERE break_id = ? AND business_id = ?", (break_id, business_id))
            conn.commit()
            conn.close()
            flash_message("ההפסקה נמחקה.", "success")
            return redirect(url_for("calendar_day", selected_date=selected_date))

        is_available = 1 if request.form.get("is_available") == "1" else 0
        start_time = request.form.get("start_time", "").strip() or None
        end_time = request.form.get("end_time", "").strip() or None
        note = request.form.get("note", "").strip()

        if is_available and (not start_time or not end_time or start_time >= end_time):
            conn.close()
            flash_message("יש לבחור שעות פעילות תקינות ליום זמין.", "error")
            return redirect(url_for("calendar_day", selected_date=selected_date))

        cursor.execute("""
            INSERT INTO availability
                (business_id, availability_date, is_available, start_time, end_time, note)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (business_id, availability_date)
            DO UPDATE SET
                is_available = excluded.is_available,
                start_time = excluded.start_time,
                end_time = excluded.end_time,
                note = excluded.note
        """, (business_id, selected_date, is_available, start_time, end_time, note))

        # If the day was closed, its breaks can no longer be valid.
        if not is_available:
            cursor.execute("DELETE FROM availability_breaks WHERE business_id = ? AND break_date = ?", (business_id, selected_date))

        conn.commit()
        conn.close()
        flash_message("הזמינות לתאריך נשמרה.", "success")
        return redirect(url_for("calendar_day", selected_date=selected_date))

    availability = get_date_availability(business_id, selected_date)
    if availability:
        is_available = bool(availability["is_available"])
        start_time = availability["start_time"] or ""
        end_time = availability["end_time"] or ""
        note = availability["note"] if "note" in availability.keys() else ""
        availability_id = availability["availability_id"] if "availability_id" in availability.keys() else None
    else:
        is_available = False
        start_time = ""
        end_time = ""
        note = ""
        availability_id = None

    breaks = cursor.execute("""
        SELECT break_id, start_time, end_time, note
        FROM availability_breaks
        WHERE business_id = ? AND break_date = ?
        ORDER BY start_time
    """, (business_id, selected_date)).fetchall()
    conn.close()

    break_rows = ""
    for br in breaks:
        br_note = safe(br["note"] or "")
        break_rows += f"""
        <div class="table-row" style="display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 0;border-bottom:1px solid #333;">
            <div><strong>{br['start_time']} – {br['end_time']}</strong><span class="muted"> {br_note}</span></div>
            <form method="POST" style="margin:0;">
                <input type="hidden" name="action" value="delete_break">
                <input type="hidden" name="break_id" value="{br['break_id']}">
                <button type="submit" class="secondary-button">🗑️ מחיקה</button>
            </form>
        </div>
        """
    if not break_rows:
        break_rows = '<div class="muted" style="padding:10px 0;">אין הפסקות מוגדרות ליום הזה.</div>'

    return render_template_string(STYLE + f"""
        <div class="dashboard">
            {sidebar_html()}
            <div class="content">
                <div class="topbar">
                    <div>
                        <h1>ניהול זמינות ליום {selected.strftime('%d/%m/%Y')}</h1>
                        <div class="user-info">הגדרת שעות, זמינות והפסקות לתאריך ספציפי</div>
                    </div>
                </div>

                <div class="card">
                    <form method="POST">
                        <input type="hidden" name="action" value="save_availability">
                        <label>סטטוס</label>
                        <select name="is_available">
                            <option value="1" {'selected' if is_available else ''}>🟢 זמין</option>
                            <option value="0" {'selected' if not is_available else ''}>🔴 לא זמין</option>
                        </select>
                        <div class="form-grid">
                            <div><label>התחלה</label><input type="time" name="start_time" value="{start_time}"></div>
                            <div><label>סיום</label><input type="time" name="end_time" value="{end_time}"></div>
                            <div class="form-full"><label>הערה</label><textarea name="note">{safe(note)}</textarea></div>
                        </div>
                        <div class="form-actions">
                            <button type="submit">שמירת זמינות</button>
                            <a href="/calendar"><button type="button" class="secondary-button">חזרה ליומן</button></a>
                        </div>
                    </form>
                </div>

                <div class="card" style="margin-top:20px;">
                    <h2>⏸️ הפסקות במהלך היום</h2>
                    <p class="muted">הפסקות אלה יחסמו אוטומטית את השעות המתאימות ללקוחות.</p>
                    {break_rows}
                    <form method="POST" style="margin-top:18px;">
                        <input type="hidden" name="action" value="add_break">
                        <div class="form-grid">
                            <div><label>תחילת הפסקה</label><input type="time" name="break_start_time" required></div>
                            <div><label>סיום הפסקה</label><input type="time" name="break_end_time" required></div>
                            <div class="form-full"><label>הערה (אופציונלי)</label><input type="text" name="break_note" placeholder="למשל: הפסקת צהריים"></div>
                        </div>
                        <button type="submit">＋ הוסף הפסקה</button>
                    </form>
                </div>
            </div>
        </div>
    """)


# =========================================================
# APPOINTMENT HISTORY / CANCELLATION
# =========================================================

def _appointment_dt(appointment_date, appointment_time):
    try:
        return datetime.strptime(
            f"{appointment_date} {appointment_time}",
            "%Y-%m-%d %H:%M"
        )
    except (TypeError, ValueError):
        # Support the common DD/MM/YYYY display/input format as a fallback.
        try:
            return datetime.strptime(
                f"{appointment_date} {appointment_time}",
                "%d/%m/%Y %H:%M"
            )
        except (TypeError, ValueError):
            return None


def _appointment_is_future(appointment):
    appointment_dt = _appointment_dt(
        appointment["appointment_date"],
        appointment["appointment_time"]
    )
    return bool(appointment_dt and appointment_dt > datetime.now())


def _appointment_status_label(appointment):
    if appointment["status"] == "cancelled":
        return "בוטל"
    if _appointment_is_future(appointment):
        return "טרם הושלם"
    return "הושלם"


def _cancel_appointment(appointment_id, business_id=None, customer_id=None):
    conn = connect_db()
    cursor = conn.cursor()

    if business_id is not None:
        cursor.execute("""
            SELECT appointment_date, appointment_time, status
            FROM appointments
            WHERE appointment_id = ?
              AND business_id = ?
        """, (appointment_id, business_id))
    else:
        cursor.execute("""
            SELECT appointment_date, appointment_time, status
            FROM appointments
            WHERE appointment_id = ?
              AND customer_id = ?
        """, (appointment_id, customer_id))

    appointment = cursor.fetchone()

    if not appointment:
        conn.close()
        return False, "התור לא נמצא."

    appointment_dt = _appointment_dt(
        appointment["appointment_date"],
        appointment["appointment_time"]
    )

    if appointment["status"] == "cancelled":
        conn.close()
        return False, "התור כבר בוטל."

    if not appointment_dt or appointment_dt <= datetime.now():
        conn.close()
        return False, "לא ניתן לבטל תור שכבר עבר."

    if business_id is not None:
        cursor.execute("""
            UPDATE appointments
            SET status = 'cancelled', cancelled_by = 'owner'
            WHERE appointment_id = ?
              AND business_id = ?
        """, (appointment_id, business_id))
    else:
        cursor.execute("""
            UPDATE appointments
            SET status = 'cancelled', cancelled_by = 'customer'
            WHERE appointment_id = ?
              AND customer_id = ?
        """, (appointment_id, customer_id))

    changed = cursor.rowcount
    conn.commit()
    conn.close()

    return bool(changed), "התור בוטל בהצלחה." if changed else "לא ניתן לבטל את התור."


@app.route("/appointments/<int:appointment_id>/cancel", methods=["POST"])
def cancel_appointment():
    check = require_login()
    if check:
        return check

    appointment_id = request.view_args["appointment_id"]
    role = session.get("role")

    if role == "owner":
        changed, message = _cancel_appointment(
            appointment_id,
            business_id=session["business_id"]
        )
    elif role == "customer":
        changed, message = _cancel_appointment(
            appointment_id,
            customer_id=session["customer_id"]
        )
    else:
        return "הגישה נדחתה", 403

    if not changed:
        return message, 409

    return redirect(url_for("appointments"))


def _appointment_action_button(appointment, role):
    if appointment["status"] == "cancelled" or not _appointment_is_future(appointment):
        return ""

    label = "ביטול תור"
    return f"""
        <form method="POST" action="/appointments/{appointment["appointment_id"]}/cancel" style="display:inline;">
            <button
                type="submit"
                class="small-button danger-button"
                onclick="return confirm('האם אתה בטוח שברצונך לבטל את התור?');"
            >
                ✕ {label}
            </button>
        </form>
    """


def _appointment_rows(appointments_list, role):
    rows = ""
    for appointment in appointments_list:
        action = _appointment_action_button(appointment, role)
        rows += f"""
        <tr>
            <td>{appointment["appointment_date"]}</td>
            <td>{appointment["appointment_time"]}</td>
            {f'<td>{appointment["full_name"]}</td>' if role == "owner" else ''}
            <td>{appointment["service_type"]}</td>
            <td>{_appointment_status_label(appointment)}</td>
            <td>
                <button type="button" class="invoice-action-disabled" disabled>
                    🧾 {'הפק חשבונית' if role == 'owner' else 'חשבונית'}
                </button>
            </td>
            <td>{action}</td>
        </tr>
        """
    return rows


def _group_appointment_sections(appointments_list, role, past=False):
    """Build month/day grouped HTML while preserving the appointment table columns."""
    if not appointments_list:
        colspan = 7 if role == "owner" else 6
        return f'<tr><td colspan="{colspan}" class="empty">אין תורים להצגה.</td></tr>'

    groups = {}
    for appointment in appointments_list:
        date_key = appointment["appointment_date"]
        groups.setdefault(date_key, []).append(appointment)

    month_names = {
        1: "ינואר", 2: "פברואר", 3: "מרץ", 4: "אפריל",
        5: "מאי", 6: "יוני", 7: "יולי", 8: "אוגוסט",
        9: "ספטמבר", 10: "אוקטובר", 11: "נובמבר", 12: "דצמבר"
    }

    html = ""
    current_month = None
    for date_key in sorted(groups.keys(), reverse=past):
        parsed = None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                parsed = datetime.strptime(date_key, fmt)
                break
            except ValueError:
                pass

        month_key = (parsed.year, parsed.month) if parsed else (date_key[:7], "")
        if month_key != current_month:
            current_month = month_key
            if parsed:
                month_title = f"{month_names[parsed.month]} {parsed.year}"
            else:
                month_title = str(date_key)[:7]
            colspan = 7 if role == "owner" else 6
            html += f'<tr class="month-divider"><td colspan="{colspan}"><strong>{month_title}</strong></td></tr>'

        html += f'<tr class="day-divider"><td colspan="{colspan}"><strong>📅 {date_key}</strong></td></tr>'
        day_appointments = sorted(
            groups[date_key],
            key=lambda a: a["appointment_time"],
            reverse=past
        )
        html += _appointment_rows(day_appointments, role)

    return html


@app.route("/appointments")
def appointments():

    check = require_login()
    if check:
        return check

    role = session["role"]
    conn = connect_db()
    cursor = conn.cursor()

    if role == "owner":
        business_id = session["business_id"]
        cursor.execute("""
            SELECT a.*, c.full_name
            FROM appointments a
            JOIN customers c ON a.customer_id = c.customer_id
            WHERE a.business_id = ?
            ORDER BY a.appointment_date, a.appointment_time
        """, (business_id,))
        appointments_list = cursor.fetchall()
        customer_cancelled_count = sum(1 for a in appointments_list if a["status"] == "cancelled" and a["cancelled_by"] == "customer")
        title = "תורים"
    elif role == "customer":
        customer_id = session["customer_id"]
        cursor.execute("""
            SELECT a.*, b.business_name, b.phone AS business_phone, b.email AS business_email
            FROM appointments a
            LEFT JOIN businesses b ON b.business_id = a.business_id
            WHERE a.customer_id = ?
            ORDER BY a.appointment_date, a.appointment_time
        """, (customer_id,))
        appointments_list = cursor.fetchall()
        title = "התורים שלי"
    else:
        conn.close()
        return "הגישה נדחתה", 403

    conn.close()

    future = [a for a in appointments_list if a["status"] != "cancelled" and _appointment_is_future(a)]
    cancelled_future = [a for a in appointments_list if a["status"] == "cancelled" and _appointment_is_future(a)]
    past = [a for a in appointments_list if a["status"] != "cancelled" and not _appointment_is_future(a)]
    cancelled_past = [a for a in appointments_list if a["status"] == "cancelled" and not _appointment_is_future(a)]

    future += cancelled_future
    past += cancelled_past

    future.sort(key=lambda a: (_appointment_dt(a["appointment_date"], a["appointment_time"]) or datetime.max))
    past.sort(key=lambda a: (_appointment_dt(a["appointment_date"], a["appointment_time"]) or datetime.min), reverse=True)

    if role == "owner":
        headers = """
            <th>תאריך</th><th>שעה</th><th>לקוח</th><th>שירות</th>
            <th>סטטוס</th><th>חשבונית</th><th>פעולות</th>
        """
    else:
        headers = """
            <th>תאריך</th><th>שעה</th><th>שירות</th>
            <th>סטטוס</th><th>חשבונית</th><th>פעולות</th>
        """

    business_contact = ""
    if role == "customer":
        contact_rows = [a for a in appointments_list if a["status"] == "cancelled"]
        if contact_rows:
            business = contact_rows[0]
            contact_bits = []
            if business["business_phone"]:
                contact_bits.append(f'טלפון: {business["business_phone"]}')
            if business["business_email"]:
                contact_bits.append(f'אימייל: {business["business_email"]}')
            contact_text = " · ".join(contact_bits) or "פרטי הקשר של העסק זמינים אצל העסק."
            business_contact = f"""
                <div class="warning" style="margin-bottom:18px;">
                    <strong>יש ליצור קשר עם בעל העסק.</strong><br>
                    {contact_text}
                </div>
            """

    return render_template_string(
        STYLE + f"""
        <div class="dashboard">
            {sidebar_html()}
            <div class="content">
                <div class="topbar"><h1>{title}</h1></div>
                {f'<div class="warning" style="margin-bottom:18px;"><strong>🔔 התראה:</strong> {customer_cancelled_count} תורים בוטלו על ידי לקוחות.</div>' if role == "owner" and customer_cancelled_count else ''}
                {business_contact}

                <div class="table-card">
                    <h2>📅 תורים עתידיים</h2>
                    <p class="muted">תורים שטרם הגיע מועד ביצועם. סטטוס: <strong>טרם הושלם</strong>.</p>
                    <table>
                        <thead><tr>{headers}</tr></thead>
                        <tbody>{_group_appointment_sections(future, role, past=False)}</tbody>
                    </table>
                </div>

                <div class="table-card" style="margin-top:22px;">
                    <h2>🕘 תורים שעברו</h2>
                    <p class="muted">היסטוריית התורים נשמרת ומסודרת לפי חודש, יום ושעה. סטטוס: <strong>הושלם</strong>.</p>
                    <table>
                        <thead><tr>{headers}</tr></thead>
                        <tbody>{_group_appointment_sections(past, role, past=True)}</tbody>
                    </table>
                </div>
            </div>
        </div>
        """
    )

@app.route("/owner/customers/add", methods=["GET", "POST"])
def add_customer():

    check = require_owner()

    if check:
        return check

    business_id = session["business_id"]
    error = ""
    success = ""

    full_name = ""
    phone = ""
    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        phone = normalize_phone(request.form.get("phone", ""))
        if not full_name:
            error = "נא להזין שם מלא."

        elif not phone:
            error = "נא להזין מספר טלפון."

        else:
            conn = connect_db()
            cursor = conn.cursor()

            existing = cursor.execute("""
                SELECT customer_id
                FROM customers
                WHERE business_id = ?
                AND phone = ?
            """, (
                business_id,
                phone
            )).fetchone()

            if existing:
                error = "לקוח עם מספר הטלפון הזה כבר קיים בעסק."

            else:
                try:
                    cursor.execute("""
                        INSERT INTO customers
                        (
                            full_name,
                            phone,
                            business_id
                        )
                        VALUES (?, ?, ?)
                    """, (
                        full_name,
                        phone,
                        business_id
                    ))

                    conn.commit()
                    success = (
                        "הלקוח נוסף בהצלחה. "
                        "כעת הוא מורשה ליצור משתמש עם מספר הטלפון הזה."
                    )

                    full_name = ""
                    phone = ""
                except Exception as e:
                    conn.rollback()
                    error = "לא ניתן להוסיף את הלקוח: " + str(e)

            conn.close()

    return render_template_string(
        STYLE + f"""

        <div class="dashboard">

            {sidebar_html()}

            <div class="content">

                <div class="topbar">

                    <div>

                        <h1>
                            הוספת לקוח
                        </h1>

                        <div class="user-info">
                            הוספת לקוח והרשאתו ליצור משתמש במערכת
                        </div>

                    </div>

                </div>

                {f'<div class="success">{success}</div>' if success else ""}
                {f'<div class="error">{error}</div>' if error else ""}

                <div class="card">

                    <h2>
                        פרטי הלקוח
                    </h2>

                    <p class="muted">
                        לאחר ההוספה, הלקוח יוכל ליצור חשבון באמצעות
                        מספר הטלפון שאישרת.
                    </p>

                    <form method="POST">

                        <label>
                            שם מלא *
                        </label>

                        <input
                            type="text"
                            name="full_name"
                            value="{safe(full_name)}"
                            required
                        >

                        <label>
                            מספר טלפון *
                        </label>

                        <input
                            type="tel"
                            name="phone"
                            value="{safe(phone)}"
                            placeholder="0501234567"
                            required
                        >

                        <button
                            type="submit"
                            style="margin-top:22px;"
                        >
                            + הוסף לקוח
                        </button>

                        <a
                            href="/owner/customers"
                            style="margin-right:10px;"
                        >
                            <button
                                type="button"
                                class="secondary-button"
                            >
                                ביטול
                            </button>
                        </a>

                    </form>

                </div>

            </div>

        </div>

        """
    )


@app.route("/customers/<int:customer_id>/delete", methods=["POST"])
def delete_customer(customer_id):
    check = require_owner()
    if check:
        return check

    business_id = session["business_id"]
    conn = connect_db()
    try:
        customer = conn.execute(
            "SELECT customer_id FROM customers WHERE customer_id = ? AND business_id = ?",
            (customer_id, business_id),
        ).fetchone()
        if not customer:
            return "לקוח לא נמצא", 404

        conn.execute("DELETE FROM users WHERE customer_id = ?", (customer_id,))
        conn.execute("DELETE FROM customers WHERE customer_id = ? AND business_id = ?", (customer_id, business_id))
        conn.commit()
    finally:
        conn.close()

    flash_message("הלקוח והמידע המשויך אליו נמחקו.", "success")
    return redirect(url_for("customers"))


@app.route("/customers")
def customers():

    check = require_owner()

    if check:
        return check

    business_id = session["business_id"]

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            customer_id,
            full_name,
            phone,
            email,
            address

        FROM customers

        WHERE business_id = ?

        ORDER BY full_name
    """, (business_id,))

    customers_list = cursor.fetchall()

    conn.close()

    rows = ""

    for customer in customers_list:

        rows += f"""

        <tr>

            <td>
                {customer["full_name"]}
            </td>

            <td>
                {customer["phone"]}
            </td>

            <td>
                {safe(customer["email"])}
            </td>

            <td>
                {safe(customer["address"])}
            </td>

            <td>

                <a
                    href="/customer/{customer["customer_id"]}"
                >

                    <button
                        class="small-button"
                        type="button"
                    >
                        צפייה
                    </button>

                </a>

                <form method="POST" action="/customers/{customer["customer_id"]}/delete" style="display:inline; margin-right:8px;">
                    <button type="submit" class="small-button danger-button" onclick="return confirm('מחיקת הלקוח תמחק גם את התורים והחשבוניות שלו. להמשיך?');">🗑️ מחיקה</button>
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
                לא נמצאו לקוחות.
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

                        <h1>
                            לקוחות
                        </h1>

                        <div class="user-info">
                            ניהול הלקוחות שלך
                        </div>

                    </div>

                    <a href="/owner/customers/add">
                        <button>
                            + הוסף לקוח
                        </button>
                    </a>

                </div>

                <div class="table-card">

                    <table>

                        <thead>

                            <tr>

                                <th>שם</th>
                                <th>טלפון</th>
                                <th>אימייל</th>
                                <th>כתובת</th>
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

@app.route("/customer/<int:customer_id>")
def customer_details(customer_id):

    check = require_owner()

    if check:
        return check

    business_id = session["business_id"]

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM customers

        WHERE customer_id = ?
        AND business_id = ?
    """, (
        customer_id,
        business_id
    ))

    customer = cursor.fetchone()

    if not customer:

        conn.close()

        return "לקוח לא נמצא", 404

    cursor.execute("""
        SELECT *
        FROM appointments

        WHERE customer_id = ?
        AND business_id = ?

        ORDER BY
            appointment_date,
            appointment_time
    """, (
        customer_id,
        business_id
    ))

    appointments_list = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM invoices

        WHERE customer_id = ?
        AND business_id = ?

        ORDER BY invoice_date DESC
    """, (
        customer_id,
        business_id
    ))

    invoices_list = cursor.fetchall()

    conn.close()

    appointment_rows = ""

    for appointment in appointments_list:

        appointment_rows += f"""

        <tr>

            <td>
                {appointment["appointment_date"]}
            </td>

            <td>
                {appointment["appointment_time"]}
            </td>

            <td>
                {appointment["service_type"]}
            </td>

            <td>
                {STATUS_NAMES.get(
                    appointment["status"],
                    appointment["status"]
                )}
            </td>

        </tr>

        """

    invoice_rows = ""

    for invoice in invoices_list:

        invoice_rows += f"""

        <tr>

            <td>
                {invoice["invoice_id"]}
            </td>

            <td>
                {invoice["service_type"]}
            </td>

            <td>
                {invoice["amount"]} ₪
            </td>

            <td>
                {invoice["invoice_date"]}
            </td>

            <td>
                {invoice["status"]}
            </td>

        </tr>

        """

    if not appointment_rows:

        appointment_rows = """

        <tr>

            <td
                colspan="4"
                class="empty"
            >
                אין תורים.
            </td>

        </tr>

        """

    if not invoice_rows:

        invoice_rows = """

        <tr>

            <td
                colspan="5"
                class="empty"
            >
                אין חשבוניות.
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

                        <h1>
                            {customer["full_name"]}
                        </h1>

                        <div class="user-info">
                            פרטי לקוח
                        </div>

                    </div>

                </div>

                <div class="card">

                    <h2>
                        פרטי לקוח
                    </h2>

                    <p>
                        <strong>
                            טלפון:
                        </strong>

                        {customer["phone"]}
                    </p>

                    <p>
                        <strong>
                            אימייל:
                        </strong>

                        {safe(customer["email"])}
                    </p>

                    <p>
                        <strong>
                            כתובת:
                        </strong>

                        {safe(customer["address"])}
                    </p>

                </div>

                <div class="table-card">

                    <h2>
                        היסטוריית תורים
                    </h2>

                    <table>

                        <thead>

                            <tr>

                                <th>תאריך</th>
                                <th>שעה</th>
                                <th>שירות</th>
                                <th>סטטוס</th>

                            </tr>

                        </thead>

                        <tbody>

                            {appointment_rows}

                        </tbody>

                    </table>

                </div>

                <div class="table-card">

                    <h2>
                        חשבוניות
                    </h2>

                    <table>

                        <thead>

                            <tr>

                                <th>מזהה</th>
                                <th>שירות</th>
                                <th>סכום</th>
                                <th>תאריך</th>
                                <th>סטטוס</th>

                            </tr>

                        </thead>

                        <tbody>

                            {invoice_rows}

                        </tbody>

                    </table>

                </div>

            </div>

        </div>

        """
    )

@app.route("/invoices/settings", methods=["GET", "POST"])
def invoice_settings():

    check = require_owner()
    if check:
        return check

    business_id = session["business_id"]
    message = ""
    error = ""

    if request.method == "POST":
        provider = request.form.get("provider", "generic").strip() or "generic"
        account_reference = request.form.get("account_reference", "").strip()
        action = request.form.get("action", "save")

        if provider not in {"generic"}:
            error = "ספק החשבוניות שנבחר אינו זמין עדיין."
        else:
            conn = connect_db()
            try:
                if action == "disconnect":
                    conn.execute("""
                        UPDATE business_invoice_connections
                        SET status = 'not_connected', connected_at = NULL
                        WHERE business_id = ?
                    """, (business_id,))
                    conn.commit()
                    message = "חיבור החשבוניות נותק."
                elif not account_reference:
                    error = "יש להזין מזהה חשבון/חיבור לספק."
                else:
                    conn.execute("""
                        INSERT INTO business_invoice_connections
                            (business_id, provider, account_reference, status, connected_at)
                        VALUES (?, ?, ?, 'connected', CURRENT_TIMESTAMP)
                        ON CONFLICT(business_id) DO UPDATE SET
                            provider = excluded.provider,
                            account_reference = excluded.account_reference,
                            status = 'connected',
                            connected_at = CURRENT_TIMESTAMP
                    """, (business_id, provider, account_reference))
                    conn.commit()
                    message = "תשתית חיבור החשבוניות נשמרה בהצלחה."
            finally:
                conn.close()

    conn = connect_db()
    try:
        connection = conn.execute("""
            SELECT provider, account_reference, status, connected_at
            FROM business_invoice_connections
            WHERE business_id = ?
            LIMIT 1
        """, (business_id,)).fetchone()
    finally:
        conn.close()

    provider_value = connection["provider"] if connection else "generic"
    account_value = connection["account_reference"] if connection else ""
    status_label = "מחובר" if connection and connection["status"] == "connected" else "לא מחובר"

    return render_template_string(
        STYLE + f"""
        <div class="dashboard">
            {sidebar_html()}
            <div class="content">
                <div class="topbar">
                    <div>
                        <h1>חיבור חשבוניות</h1>
                        <div class="user-info">תשתית לחיבור עתידי לספק חשבוניות אמיתי</div>
                    </div>
                </div>

                {f'<div class="success">{safe(message)}</div>' if message else ''}
                {f'<div class="error">{safe(error)}</div>' if error else ''}

                <div class="card">
                    <h2>סטטוס החיבור: {status_label}</h2>
                    <p class="muted">
                        בשלב זה נשמרת תצורת החיבור בלבד. הפקת חשבוניות בפועל תבוצע
                        לאחר חיבור Adapter/API של ספק חשבוניות מאומת, בלי לשנות את המערכת העסקית.
                    </p>

                    <form method="POST">
                        <input type="hidden" name="action" value="save">

                        <label>ספק</label>
                        <select name="provider">
                            <option value="generic" {"selected" if provider_value == "generic" else ""}>ספק חשבוניות חיצוני</option>
                        </select>

                        <label>מזהה חשבון / מזהה חיבור</label>
                        <input type="text" name="account_reference" value="{safe(account_value)}" placeholder="לדוגמה: מזהה החשבון אצל הספק">

                        <button class="auth-button" type="submit">שמירת חיבור</button>
                    </form>

                    <form method="POST" style="margin-top:12px;">
                        <input type="hidden" name="action" value="disconnect">
                        <button class="secondary-button" type="submit">ניתוק חיבור</button>
                    </form>
                </div>

                <div class="card">
                    <h2>מוכן לשלב הבא</h2>
                    <p>
                        המערכת כבר מחזיקה שכבת Adapter אחידה ונתוני קישור לפי עסק.
                        בעתיד ניתן לחבר ספק אמיתי, לבדוק חיבור, להפיק חשבונית ולשמור
                        את מזהה החשבונית וקישור המסמך בלי לשנות את ממשק בעל העסק.
                    </p>
                </div>
            </div>
        </div>
        """
    )

@app.route("/invoices")
def invoices():

    check = require_login()

    if check:
        return check

    role = session["role"]

    conn = connect_db()
    cursor = conn.cursor()

    if role == "owner":

        business_id = session["business_id"]

        cursor.execute("""
            SELECT
                i.*,
                c.full_name

            FROM invoices i

            JOIN customers c
                ON i.customer_id = c.customer_id

            WHERE i.business_id = ?

            ORDER BY i.invoice_date DESC
        """, (business_id,))

        invoice_list = cursor.fetchall()

        title = "חשבוניות"

        rows = ""

        for invoice in invoice_list:

            rows += f"""

            <tr>

                <td>
                    {invoice["invoice_id"]}
                </td>

                <td>
                    {invoice["full_name"]}
                </td>

                <td>
                    {invoice["service_type"]}
                </td>

                <td>
                    {invoice["amount"]} ₪
                </td>

                <td>
                    {invoice["invoice_date"]}
                </td>

                <td>
                    {invoice["status"]}
                </td>

            </tr>

            """

        headers = """
            <th>מזהה</th>
            <th>לקוח</th>
            <th>שירות</th>
            <th>סכום</th>
            <th>תאריך</th>
            <th>סטטוס</th>
            <th>חשבונית</th>
        """

        colspan = 6

    else:

        customer_id = session["customer_id"]

        cursor.execute("""
            SELECT *
            FROM invoices

            WHERE customer_id = ?

            ORDER BY invoice_date DESC
        """, (customer_id,))

        invoice_list = cursor.fetchall()

        title = "החשבוניות שלי"

        rows = ""

        for invoice in invoice_list:

            rows += f"""

            <tr>

                <td>
                    {invoice["service_type"]}
                </td>

                <td>
                    {invoice["amount"]} ₪
                </td>

                <td>
                    {invoice["invoice_date"]}
                </td>

                <td>
                    {invoice["status"]}
                </td>

            </tr>

            """

        headers = """
            <th>שירות</th>
            <th>סכום</th>
            <th>תאריך</th>
            <th>סטטוס</th>
            <th>חשבונית</th>
        """

        colspan = 4

    conn.close()

    if not rows:

        rows = f"""

        <tr>

            <td
                colspan="{colspan}"
                class="empty"
            >
                אין חשבוניות.
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
                        {title}
                    </h1>

                </div>

                <div class="table-card">

                    <table>

                        <thead>

                            <tr>

                                {headers}

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


@app.route("/leads", methods=["GET", "POST"])
def leads():
    check=require_owner()
    if check: return check
    business_id=session["business_id"]; conn=connect_db(); cur=conn.cursor(); message=""; error=""
    if request.method=="POST":
        action=request.form.get("action"); lead_id=request.form.get("lead_id")
        if action=="add":
            name=request.form.get("full_name","").strip(); phone=normalize_phone(request.form.get("phone","")); email=request.form.get("email","").strip(); source=request.form.get("source","manual").strip() or "manual"
            if not name: error="נא להזין שם מלא."
            else: cur.execute("INSERT INTO leads(business_id,full_name,phone,email,source,status) VALUES(?,?,?,?,?,\'new\')",(business_id,name,phone,email,source)); conn.commit(); message="הליד נוסף בהצלחה."
        elif action=="delete" and lead_id:
            cur.execute("DELETE FROM leads WHERE lead_id=? AND business_id=?",(lead_id,business_id)); conn.commit(); message="הליד נמחק."
        elif action=="status" and lead_id:
            status=request.form.get("status")
            if status in {"new","contacted","in_progress","appointment","customer","not_interested"}: cur.execute("UPDATE leads SET status=? WHERE lead_id=? AND business_id=?",(status,lead_id,business_id)); conn.commit(); message="סטטוס הליד עודכן."
        elif action=="convert" and lead_id:
            lead=cur.execute("SELECT * FROM leads WHERE lead_id=? AND business_id=?",(lead_id,business_id)).fetchone()
            if not lead: error="הליד לא נמצא."
            elif lead["phone"] and cur.execute("SELECT customer_id FROM customers WHERE business_id=? AND phone=?",(business_id,lead["phone"])).fetchone(): error="לקוח עם מספר הטלפון הזה כבר קיים בעסק."
            else: cur.execute("INSERT INTO customers(full_name,phone,email,business_id) VALUES(?,?,?,?)",(lead["full_name"],lead["phone"],lead["email"],business_id)); cur.execute("UPDATE leads SET status=\'customer\' WHERE lead_id=? AND business_id=?",(lead_id,business_id)); conn.commit(); message="הליד הפך ללקוח בהצלחה."
    leads_list=cur.execute("SELECT * FROM leads WHERE business_id=? ORDER BY created_at DESC",(business_id,)).fetchall(); conn.close()
    labels={"new":"🆕 חדש","contacted":"📞 נוצר קשר","in_progress":"🔄 בטיפול","appointment":"📅 נקבע תור","customer":"👤 הפך ללקוח","not_interested":"❌ לא מעוניין"}
    rows=""
    for l in leads_list:
        opts="".join(f'<option value="{k}" {"selected" if k==l["status"] else ""}>{v}</option>' for k,v in labels.items())
        rows+=f'<tr><td>{safe(l["full_name"])}</td><td>{safe(l["phone"])}</td><td>{safe(l["email"])}</td><td><form method="POST"><input type="hidden" name="action" value="status"><input type="hidden" name="lead_id" value="{l["lead_id"]}"><select name="status" onchange="this.form.submit()">{opts}</select></form></td><td>{safe(l["source"])}</td><td><form method="POST"><input type="hidden" name="action" value="convert"><input type="hidden" name="lead_id" value="{l["lead_id"]}"><button>👤 הפוך ללקוח</button></form><form method="POST"><input type="hidden" name="action" value="delete"><input type="hidden" name="lead_id" value="{l["lead_id"]}"><button>🗑️ מחק ליד</button></form></td></tr>'
    return render_template_string(STYLE+f"""<div class=\"dashboard\">{sidebar_html()}<div class=\"content\"><div class=\"topbar\"><h1>לידים</h1></div>{f'<div class=\"success\">{message}</div>' if message else ''}{f'<div class=\"error\">{error}</div>' if error else ''}<div class=\"card\"><h2>+ הוסף ליד</h2><form method=\"POST\"><input type=\"hidden\" name=\"action\" value=\"add\"><label>שם מלא *</label><input name=\"full_name\" required><label>טלפון</label><input name=\"phone\"><label>אימייל</label><input name=\"email\" type=\"email\"><label>מקור</label><input name=\"source\" value=\"manual\"><button>הוסף ליד</button></form></div><div class=\"table-card\"><table><thead><tr><th>שם</th><th>טלפון</th><th>אימייל</th><th>סטטוס</th><th>מקור</th><th>פעולות</th></tr></thead><tbody>{rows or '<tr><td colspan=\"6\">לא נמצאו לידים.</td></tr>'}</tbody></table></div></div></div>""")
