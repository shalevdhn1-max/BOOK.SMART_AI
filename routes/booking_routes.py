# Auto-generated modular route module for Book Smart AI.
from app import *


def get_date_availability_for_booking(business_id, selected_date):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM availability
        WHERE business_id = ? AND availability_date = ?
    """, (business_id, selected_date))
    override = cursor.fetchone()
    if override:
        conn.close()
        return override
    selected = datetime.strptime(selected_date, "%Y-%m-%d").date()
    day_of_week = (selected.weekday() + 1) % 7
    cursor.execute("""
        SELECT * FROM business_hours
        WHERE business_id = ? AND day_of_week = ?
    """, (business_id, day_of_week))
    hours = cursor.fetchone()
    conn.close()
    if not hours:
        return None
    return {"is_available": hours["is_open"], "start_time": hours["open_time"], "end_time": hours["close_time"]}

@app.route("/book")
def book():

    check = require_customer()

    if check:
        return check

    business_id = session["business_id"]

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM services

        WHERE business_id = ?
        AND is_active = 1

        ORDER BY service_name
    """, (business_id,))

    services_list = cursor.fetchall()

    conn.close()

    business = get_business(
        business_id
    )

    cards = ""

    for service in services_list:

        cards += f"""

        <a
            href="/book/service/{service["service_id"]}"
            style="text-decoration:none;"
        >

            <div class="option-card">

                <h2 class="gold">
                    {service["service_name"]}
                </h2>

                <p>
                    {safe(service["description"])}
                </p>

                <p>
                    <strong>
                        {service["price"]} ₪
                    </strong>
                </p>

                <p class="muted">
                    {service["duration_minutes"]} דקות
                </p>

                <button>
                    בחירת שירות
                </button>

            </div>

        </a>

        """

    if not cards:

        cards = """

        <div class="warning">
            בית העסק עדיין לא הגדיר שירותים.
        </div>

        """

    return render_template_string(
        STYLE + f"""

        <div class="business-page">

            <div class="business-header">

                <h1>
                    {business["business_name"]}
                </h1>

                <p>
                    בחר את השירות הרצוי
                    כדי להמשיך לקביעת התור.
                </p>

            </div>

            <div class="business-body">

                <div class="availability-options">

                    {cards}

                </div>

            </div>

        </div>

        """
    )

@app.route("/book/service/<int:service_id>")
def book_service(service_id):

    check = require_customer()

    if check:
        return check

    business_id = session["business_id"]

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM services

        WHERE service_id = ?
        AND business_id = ?
        AND is_active = 1
    """, (
        service_id,
        business_id
    ))

    service = cursor.fetchone()

    conn.close()

    if not service:

        return "השירות לא נמצא", 404

    today = date.today()

    cells = ""

    for offset in range(60):

        selected = (
            today
            + timedelta(days=offset)
        )

        selected_string = (
            selected.isoformat()
        )

        availability = get_date_availability_for_booking(
            business_id,
            selected_string
        )

        if not availability:
            continue

        if not availability["is_available"]:
            continue

        cells += f"""

        <a
            href="/book/service/{service_id}/date/{selected_string}"
            style="text-decoration:none;"
        >

            <div class="option-card">

                <div class="gold">
                    {selected.strftime("%d/%m/%Y")}
                </div>

                <div class="muted">
                    {DAY_NAMES[
                        (selected.weekday() + 1) % 7
                    ]}
                </div>

                <button
                    style="margin-top:12px;"
                >
                    בחירת תאריך
                </button>

            </div>

        </a>

        """

    if not cells:

        cells = """

        <div class="warning">
            אין תאריכים זמינים ב־60 הימים הקרובים.
        </div>

        """

    return render_template_string(
        STYLE + f"""

        <div class="business-page">

            <div class="business-header">

                <h1>
                    {service["service_name"]}
                </h1>

                <p>
                    {service["price"]} ₪
                    ·
                    {service["duration_minutes"]} דקות
                </p>

            </div>

            <div class="business-body">

                <h2>
                    בחר תאריך
                </h2>

                <div class="availability-options">

                    {cells}

                </div>

            </div>

        </div>

        """
    )

def generate_time_slots(
    start_time,
    end_time,
    duration_minutes
):

    if not start_time or not end_time:

        return []

    try:

        start = datetime.strptime(
            start_time,
            "%H:%M"
        )

        end = datetime.strptime(
            end_time,
            "%H:%M"
        )

    except ValueError:

        return []

    slots = []

    current = start

    while (
        current + timedelta(
            minutes=duration_minutes
        )
        <= end
    ):

        slots.append(
            current.strftime("%H:%M")
        )

        current += timedelta(
            minutes=duration_minutes
        )

    return slots

def slot_is_free(
    business_id,
    selected_date,
    slot_time,
    duration_minutes
):

    try:

        slot_start = datetime.strptime(
            slot_time,
            "%H:%M"
        )

    except ValueError:

        return False

    slot_end = (
        slot_start
        + timedelta(
            minutes=duration_minutes
        )
    )

    conn = connect_db()
    break_rows = conn.execute("""
        SELECT start_time, end_time
        FROM availability_breaks
        WHERE business_id = ? AND break_date = ?
    """, (business_id, selected_date)).fetchall()

    for br in break_rows:
        try:
            break_start = datetime.strptime(br["start_time"], "%H:%M")
            break_end = datetime.strptime(br["end_time"], "%H:%M")
        except ValueError:
            continue
        if slot_start < break_end and slot_end > break_start:
            conn.close()
            return False
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            appointment_time,
            service_id

        FROM appointments

        WHERE business_id = ?
        AND appointment_date = ?

        AND status != 'cancelled'
    """, (
        business_id,
        selected_date
    ))

    existing = cursor.fetchall()

    for appointment in existing:

        try:

            existing_start = datetime.strptime(
                appointment["appointment_time"],
                "%H:%M"
            )

        except ValueError:

            continue

        existing_duration = 30

        if appointment["service_id"]:

            cursor.execute("""
                SELECT duration_minutes
                FROM services
                WHERE service_id = ?
            """, (
                appointment["service_id"],
            ))

            service = cursor.fetchone()

            if service:

                existing_duration = (
                    service["duration_minutes"]
                )

        existing_end = (
            existing_start
            + timedelta(
                minutes=existing_duration
            )
        )

        overlap = (
            slot_start < existing_end
            and slot_end > existing_start
        )

        if overlap:

            conn.close()

            return False

    conn.close()

    return True

@app.route("/book/service/<int:service_id>/date/<selected_date>")
def book_time(
    service_id,
    selected_date
):

    check = require_customer()

    if check:
        return check

    business_id = session["business_id"]

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM services

        WHERE service_id = ?
        AND business_id = ?
        AND is_active = 1
    """, (
        service_id,
        business_id
    ))

    service = cursor.fetchone()

    conn.close()

    if not service:

        return "השירות לא נמצא", 404

    availability = get_date_availability_for_booking(
        business_id,
        selected_date
    )

    if not availability:

        return "התאריך אינו זמין", 400

    if not availability["is_available"]:

        return "התאריך אינו זמין", 400

    slots = generate_time_slots(
        availability["start_time"],
        availability["end_time"],
        service["duration_minutes"]
    )

    available_slots = []

    for slot in slots:

        if slot_is_free(
            business_id,
            selected_date,
            slot,
            service["duration_minutes"]
        ):

            available_slots.append(
                slot
            )

    buttons = ""

    for slot in available_slots:

        buttons += f"""

        <a
            href="/book/confirm/{service_id}/{selected_date}/{slot}"
            class="time-slot"
        >
            {slot}
        </a>

        """

    if not buttons:

        buttons = """

        <div class="warning">
            אין שעות פנויות בתאריך הזה.
        </div>

        """

    return render_template_string(
        STYLE + f"""

        <div class="business-page">

            <div class="business-header">

                <h1>
                    בחירת שעה
                </h1>

                <p>
                    {service["service_name"]}
                    ·
                    {selected_date}
                </p>

            </div>

            <div class="business-body">

                <h2>
                    שעות פנויות
                </h2>

                <div class="time-slots">

                    {buttons}

                </div>

            </div>

        </div>

        """
    )

@app.route("/book/confirm/<int:service_id>/<selected_date>/<slot>", methods=["GET", "POST"])
def book_confirm(
    service_id,
    selected_date,
    slot
):
    selected_time = slot

    check = require_customer()

    if check:
        return check

    business_id = session["business_id"]
    customer_id = session["customer_id"]

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM services

        WHERE service_id = ?
        AND business_id = ?
        AND is_active = 1
    """, (
        service_id,
        business_id
    ))

    service = cursor.fetchone()

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

    conn.close()

    if not service or not customer:

        return "נתוני ההזמנה אינם תקינים", 400

    if not slot_is_free(
        business_id,
        selected_date,
        selected_time,
        service["duration_minutes"]
    ):

        return "השעה כבר נתפסה. חזור ובחר שעה אחרת.", 409

    if request.method == "POST":

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO appointments
            (
                business_id,
                customer_id,
                service_id,
                service_type,
                appointment_date,
                appointment_time,
                status,
                notes,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'confirmed', ?, CURRENT_TIMESTAMP)
        """, (
            business_id,
            customer_id,
            service_id,
            service["service_name"],
            selected_date,
            selected_time,
            notes
        ))

        conn.commit()
        conn.close()

        return render_template_string(
            STYLE + f"""

            <div class="auth-page">

                <div class="auth-card">

                    <h1>
                        התור נקבע בהצלחה
                    </h1>

                    <div class="success">

                        {service["service_name"]}

                        <br>

                        {selected_date}

                        <br>

                        {selected_time}

                    </div>

                    <a href="/dashboard">

                        <button
                            class="auth-button"
                        >
                            חזרה ללוח הבקרה
                        </button>

                    </a>

                </div>

            </div>

            """
        )

    return render_template_string(
        STYLE + f"""

        <div class="auth-page">

            <div class="auth-card">

                <h1>
                    אישור תור
                </h1>

                <div class="card">

                    <p>
                        <strong>
                            שירות:
                        </strong>

                        {service["service_name"]}
                    </p>

                    <p>
                        <strong>
                            תאריך:
                        </strong>

                        {selected_date}
                    </p>

                    <p>
                        <strong>
                            שעה:
                        </strong>

                        {selected_time}
                    </p>

                    <p>
                        <strong>
                            מחיר:
                        </strong>

                        {service["price"]} ₪
                    </p>

                </div>

                <form method="POST">

                    <label>
                        הערה
                    </label>

                    <textarea
                        name="notes"
                    ></textarea>

                    <button
                        class="auth-button"
                        type="submit"
                    >
                        אישור וקביעת התור
                    </button>

                </form>

            </div>

        </div>

        """
    )

