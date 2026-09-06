# Auto-generated modular route module for Book Smart AI.
from app import *

# Auto-generated modular route module for Book Smart AI.
from app import *


def _customer_appointment_dt(appointment_date, appointment_time):
    for fmt in ("%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(f"{appointment_date} {appointment_time}", fmt)
        except (TypeError, ValueError):
            pass
    return None


def _customer_status_label(appointment):
    if appointment["status"] == "cancelled":
        return "בוטל"
    appointment_dt = _customer_appointment_dt(appointment["appointment_date"], appointment["appointment_time"])
    if appointment_dt and appointment_dt > datetime.now():
        return "טרם הושלם"
    return "הושלם"


def _customer_can_cancel(appointment):
    if appointment["status"] == "cancelled":
        return False
    appointment_dt = _customer_appointment_dt(appointment["appointment_date"], appointment["appointment_time"])
    return bool(appointment_dt and appointment_dt > datetime.now())


@app.route("/customer/appointments/<int:appointment_id>/cancel", methods=["POST"])
def customer_cancel_appointment(appointment_id):
    check = require_customer()
    if check:
        return check

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT appointment_date, appointment_time, status
        FROM appointments
        WHERE appointment_id = ? AND customer_id = ?
    """, (appointment_id, session["customer_id"]))
    appointment = cursor.fetchone()

    if not appointment:
        conn.close()
        return "התור לא נמצא.", 404

    appointment_dt = _customer_appointment_dt(appointment["appointment_date"], appointment["appointment_time"])
    if appointment["status"] == "cancelled":
        conn.close()
        return "התור כבר בוטל.", 409
    if not appointment_dt or appointment_dt <= datetime.now():
        conn.close()
        return "לא ניתן לבטל תור שכבר עבר.", 409

    cursor.execute("""
        UPDATE appointments
        SET status = 'cancelled', cancelled_by = 'customer'
        WHERE appointment_id = ? AND customer_id = ?
    """, (appointment_id, session["customer_id"]))
    conn.commit()
    conn.close()
    return redirect(url_for("customer_dashboard"))


@app.route("/customer/dashboard")
def customer_dashboard():
    check = require_customer()
    if check:
        return check

    customer_id = session.get("customer_id")
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
    customer = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM appointments WHERE customer_id = ?", (customer_id,))
    appointment_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM invoices WHERE customer_id = ?", (customer_id,))
    invoice_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT a.*, b.business_name, b.phone AS business_phone, b.email AS business_email
        FROM appointments a
        LEFT JOIN businesses b ON b.business_id = a.business_id
        WHERE a.customer_id = ?
        ORDER BY a.appointment_date, a.appointment_time
    """, (customer_id,))
    appointments = cursor.fetchall()
    conn.close()

    name = customer["full_name"] if customer else "לקוח"
    business_name = get_business_name(session.get("business_id"))

    future = [a for a in appointments if a["status"] != "cancelled" and _customer_appointment_dt(a["appointment_date"], a["appointment_time"]) and _customer_appointment_dt(a["appointment_date"], a["appointment_time"]) > datetime.now()]
    cancelled = [a for a in appointments if a["status"] == "cancelled"]
    past = [a for a in appointments if a["status"] != "cancelled" and a not in future]

    future.sort(key=lambda a: _customer_appointment_dt(a["appointment_date"], a["appointment_time"]) or datetime.max)
    past.sort(key=lambda a: _customer_appointment_dt(a["appointment_date"], a["appointment_time"]) or datetime.min, reverse=True)

    rows = ""
    for appointment in future[:8] + cancelled[:8] + past[:8]:
        action = ""
        if _customer_can_cancel(appointment):
            action = f"""
                <form method="POST" action="/customer/appointments/{appointment["appointment_id"]}/cancel" style="display:inline;">
                    <button type="submit" class="small-button danger-button" onclick="return confirm('האם אתה בטוח שברצונך לבטל את התור?');">✕ ביטול תור</button>
                </form>
            """
        rows += f"""
            <tr>
                <td>{appointment["appointment_date"]}</td>
                <td>{appointment["appointment_time"]}</td>
                <td>{appointment["service_type"]}</td>
                <td>{_customer_status_label(appointment)}</td>
                <td>{action}</td>
            </tr>
        """

    if not rows:
        rows = '<tr><td colspan="5" class="empty">אין לך תורים.</td></tr>'

    cancelled_notice = ""
    if cancelled:
        c = cancelled[0]
        contact = []
        if c["business_phone"]:
            contact.append(f"טלפון: {c['business_phone']}")
        if c["business_email"]:
            contact.append(f"אימייל: {c['business_email']}")
        contact_text = " · ".join(contact)
        cancelled_notice = f"""
            <div class="warning" style="margin-bottom:18px;">
                <strong>יש לך תור שבוטל.</strong><br>
                התור בוטל על ידי בעל העסק או על ידך. יש ליצור קשר עם בעל העסק לקבלת פרטים נוספים.
                {f"<br>{contact_text}" if contact_text else ""}
            </div>
        """

    return render_template_string(
        STYLE + f"""
        <div class="dashboard">
            {sidebar_html()}
            <div class="content">
                <div class="topbar">
                    <div>
                        <h1>שלום {name}</h1>
                        <div class="user-info">{business_name}</div>
                    </div>
                </div>

                <div class="cards">
                    <div class="stat-card"><div class="stat-title">התורים שלי</div><div class="stat-number">{appointment_count}</div></div>
                    <div class="stat-card"><div class="stat-title">החשבוניות שלי</div><div class="stat-number">{invoice_count}</div></div>
                </div>

                <div class="card">
                    <h2>קביעת תור</h2>
                    <p class="muted">בחר שירות, תאריך ושעה פנויה.</p>
                    <a href="/book"><button>לקביעת תור</button></a>
                </div>

                {cancelled_notice}

                <div class="table-card">
                    <h2>התורים שלי</h2>
                    <table>
                        <thead><tr><th>תאריך</th><th>שעה</th><th>שירות</th><th>סטטוס</th><th>פעולות</th></tr></thead>
                        <tbody>{rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
        """
    )

