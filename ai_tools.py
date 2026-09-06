import sqlite3

from database import DATABASE_NAME


def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def rows_to_dict(rows):
    return [dict(row) for row in rows]


def normalize_phone(phone):
    if phone is None:
        return ""
    return "".join(ch for ch in str(phone) if ch.isdigit())


def search_customers_by_name(name, business_id=None):
    if not name:
        return []

    conn = get_connection()
    try:
        if business_id is None:
            rows = conn.execute(
                """
                SELECT customer_id, full_name, phone, email, address, business_id
                FROM customers
                WHERE full_name LIKE ? COLLATE NOCASE
                ORDER BY full_name
                """,
                (f"%{name}%",),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT customer_id, full_name, phone, email, address, business_id
                FROM customers
                WHERE business_id = ?
                  AND full_name LIKE ? COLLATE NOCASE
                ORDER BY full_name
                """,
                (business_id, f"%{name}%"),
            ).fetchall()
        return rows_to_dict(rows)
    finally:
        conn.close()


def verify_customer_phone(customer_id, entered_phone):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT phone FROM customers WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()
        if not row:
            return False
        return normalize_phone(row["phone"]) == normalize_phone(entered_phone)
    finally:
        conn.close()


def get_customer_info(customer_id, business_id=None):
    conn = get_connection()
    try:
        if business_id is None:
            row = conn.execute(
                """
                SELECT customer_id, full_name, phone, email, address, business_id, created_at
                FROM customers
                WHERE customer_id = ?
                """,
                (customer_id,),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT customer_id, full_name, phone, email, address, business_id, created_at
                FROM customers
                WHERE customer_id = ? AND business_id = ?
                """,
                (customer_id, business_id),
            ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_customer_appointments(customer_id, business_id=None, appointment_date=None):
    conn = get_connection()
    try:
        query = """
            SELECT
                a.appointment_id,
                a.business_id,
                a.customer_id,
                a.service_id,
                a.service_type,
                a.appointment_date,
                a.appointment_time,
                a.status,
                a.notes,
                s.service_name,
                b.business_name
            FROM appointments a
            LEFT JOIN services s ON s.service_id = a.service_id
            LEFT JOIN businesses b ON b.business_id = a.business_id
            WHERE a.customer_id = ?
        """
        params = [customer_id]

        if business_id is not None:
            query += " AND a.business_id = ?"
            params.append(business_id)

        if appointment_date:
            query += " AND a.appointment_date = ?"
            params.append(appointment_date)

        query += " ORDER BY a.appointment_date, a.appointment_time"
        rows = conn.execute(query, params).fetchall()
        return rows_to_dict(rows)
    finally:
        conn.close()


def get_business_appointments(business_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                a.appointment_id,
                a.customer_id,
                c.full_name AS customer_name,
                a.service_id,
                COALESCE(s.service_name, a.service_type) AS service_name,
                a.appointment_date,
                a.appointment_time,
                a.status,
                a.notes
            FROM appointments a
            LEFT JOIN customers c ON c.customer_id = a.customer_id
            LEFT JOIN services s ON s.service_id = a.service_id
            WHERE a.business_id = ?
            ORDER BY a.appointment_date, a.appointment_time
            """,
            (business_id,),
        ).fetchall()
        return rows_to_dict(rows)
    finally:
        conn.close()


def get_business_customers(business_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT customer_id, full_name, phone, email, address, created_at
            FROM customers
            WHERE business_id = ?
            ORDER BY full_name
            """,
            (business_id,),
        ).fetchall()
        return rows_to_dict(rows)
    finally:
        conn.close()


def get_customer_invoices(customer_id, business_id=None):
    conn = get_connection()
    try:
        query = """
            SELECT
                i.invoice_id,
                i.customer_id,
                i.service_id,
                i.service_type,
                i.amount,
                i.invoice_date,
                i.status,
                i.notes,
                s.service_name,
                b.business_name
            FROM invoices i
            LEFT JOIN services s ON s.service_id = i.service_id
            LEFT JOIN businesses b ON b.business_id = i.business_id
            WHERE i.customer_id = ?
        """
        params = [customer_id]

        if business_id is not None:
            query += " AND i.business_id = ?"
            params.append(business_id)

        query += " ORDER BY i.invoice_date DESC, i.invoice_id DESC"
        rows = conn.execute(query, params).fetchall()
        return rows_to_dict(rows)
    finally:
        conn.close()


def get_business_invoices(business_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                i.invoice_id,
                i.customer_id,
                c.full_name AS customer_name,
                i.service_id,
                COALESCE(s.service_name, i.service_type) AS service_name,
                i.amount,
                i.invoice_date,
                i.status,
                i.notes
            FROM invoices i
            LEFT JOIN customers c ON c.customer_id = i.customer_id
            LEFT JOIN services s ON s.service_id = i.service_id
            WHERE i.business_id = ?
            ORDER BY i.invoice_date DESC, i.invoice_id DESC
            """,
            (business_id,),
        ).fetchall()
        return rows_to_dict(rows)
    finally:
        conn.close()


def get_business_services(business_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT service_id, service_name, description, price,
                   duration_minutes, is_active, created_at
            FROM services
            WHERE business_id = ?
            ORDER BY service_name
            """,
            (business_id,),
        ).fetchall()
        return rows_to_dict(rows)
    finally:
        conn.close()


def get_business_leads(business_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT lead_id, full_name, phone, email, source,
                   status, notes, created_at
            FROM leads
            WHERE business_id = ?
            ORDER BY created_at DESC, lead_id DESC
            """,
            (business_id,),
        ).fetchall()
        return rows_to_dict(rows)
    finally:
        conn.close()


def get_business_info(business_id):
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT business_id, business_name, business_type, phone,
                   email, address, description, logo_url, is_active,
                   created_at
            FROM businesses
            WHERE business_id = ?
            """,
            (business_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_business_availability(business_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT availability_id, availability_date, is_available,
                   start_time, end_time, note
            FROM availability
            WHERE business_id = ?
            ORDER BY availability_date, start_time
            """,
            (business_id,),
        ).fetchall()
        return rows_to_dict(rows)
    finally:
        conn.close()


def get_all_businesses():
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT business_id, business_name, business_type, phone,
                   email, address, is_active, created_at
            FROM businesses
            ORDER BY business_name
            """
        ).fetchall()
        return rows_to_dict(rows)
    finally:
        conn.close()


def get_all_users():
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                u.user_id,
                u.email,
                u.role,
                u.business_id,
                b.business_name,
                u.customer_id,
                u.full_name,
                u.phone,
                u.is_active,
                u.created_at
            FROM users u
            LEFT JOIN businesses b ON b.business_id = u.business_id
            ORDER BY u.user_id
            """
        ).fetchall()
        return rows_to_dict(rows)
    finally:
        conn.close()


def get_all_leads():
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                l.lead_id,
                l.business_id,
                b.business_name,
                l.full_name,
                l.phone,
                l.email,
                l.source,
                l.status,
                l.notes,
                l.created_at
            FROM leads l
            LEFT JOIN businesses b ON b.business_id = l.business_id
            ORDER BY l.created_at DESC, l.lead_id DESC
            """
        ).fetchall()
        return rows_to_dict(rows)
    finally:
        conn.close()


def get_system_summary():
    conn = get_connection()
    try:
        tables = [
            "businesses",
            "users",
            "customers",
            "appointments",
            "invoices",
            "leads",
            "services",
        ]
        result = {}
        for table in tables:
            result[table] = conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
        return result
    finally:
        conn.close()


def get_all_customers():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT c.customer_id, c.full_name, c.phone, c.email, c.address,
                   c.business_id, b.business_name
            FROM customers c
            LEFT JOIN businesses b ON b.business_id = c.business_id
            ORDER BY c.full_name
        """).fetchall()
        return rows_to_dict(rows)
    finally:
        conn.close()


def get_all_appointments():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT a.appointment_id, a.customer_id, c.full_name AS customer_name,
                   a.business_id, b.business_name, a.service_id,
                   COALESCE(s.service_name, a.service_type) AS service_name,
                   a.appointment_date, a.appointment_time, a.status, a.notes
            FROM appointments a
            LEFT JOIN customers c ON c.customer_id = a.customer_id
            LEFT JOIN businesses b ON b.business_id = a.business_id
            LEFT JOIN services s ON s.service_id = a.service_id
            ORDER BY a.appointment_date, a.appointment_time
        """).fetchall()
        return rows_to_dict(rows)
    finally:
        conn.close()


def get_all_invoices():
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT i.invoice_id, i.customer_id, c.full_name AS customer_name,
                   i.business_id, b.business_name, i.service_id,
                   COALESCE(s.service_name, i.service_type) AS service_name,
                   i.amount, i.invoice_date, i.status, i.notes
            FROM invoices i
            LEFT JOIN customers c ON c.customer_id = i.customer_id
            LEFT JOIN businesses b ON b.business_id = i.business_id
            LEFT JOIN services s ON s.service_id = i.service_id
            ORDER BY i.invoice_date DESC, i.invoice_id DESC
        """).fetchall()
        return rows_to_dict(rows)
    finally:
        conn.close()

def _query_rows(query, params=()):
    conn = get_connection()
    try:
        return rows_to_dict(conn.execute(query, params).fetchall())
    finally:
        conn.close()


def get_scoped_context(role, business_id=None, customer_id=None):
    """Return all non-secret data available to the authenticated AI path."""
    context = {}

    if role == "owner":
        if business_id is None:
            return context

        context["business"] = get_business_info(business_id)
        context["customers"] = get_business_customers(business_id)
        context["appointments"] = get_business_appointments(business_id)
        context["invoices"] = get_business_invoices(business_id)
        context["services"] = get_business_services(business_id)
        context["leads"] = get_business_leads(business_id)
        context["availability"] = get_business_availability(business_id)
        context["business_hours"] = _query_rows(
            """
            SELECT business_hour_id, day_of_week, is_open, open_time, close_time
            FROM business_hours
            WHERE business_id = ?
            ORDER BY day_of_week
            """,
            (business_id,),
        )
        context["availability_breaks"] = _query_rows(
            """
            SELECT break_id, availability_id, break_date, start_time, end_time, note, created_at
            FROM availability_breaks
            WHERE business_id = ?
            ORDER BY break_date, start_time
            """,
            (business_id,),
        )
        context["contact_requests"] = _query_rows(
            """
            SELECT contact_request_id, full_name, business_name, phone, email,
                   subject, message, status, created_at
            FROM contact_requests
            WHERE business_id = ?
            ORDER BY created_at DESC, contact_request_id DESC
            """,
            (business_id,),
        )
        context["business_invoice_connections"] = _query_rows(
            """
            SELECT connection_id, provider, account_reference, status, connected_at, created_at
            FROM business_invoice_connections
            WHERE business_id = ?
            """,
            (business_id,),
        )
        context["appointment_invoice_links"] = _query_rows(
            """
            SELECT link_id, appointment_id, status, provider_invoice_id, invoice_url, created_at
            FROM appointment_invoice_links
            WHERE business_id = ?
            ORDER BY link_id
            """,
            (business_id,),
        )
        return context

    if role == "customer":
        if customer_id is None:
            return context

        context["customer"] = get_customer_info(customer_id, business_id)
        context["appointments"] = get_customer_appointments(customer_id, business_id)
        context["invoices"] = get_customer_invoices(customer_id, business_id)

        # The customer may see relevant information about the business they
        # belong to, but never other customers, owners, or system-wide data.
        if business_id is not None:
            context["business"] = get_business_info(business_id)
            context["services"] = get_business_services(business_id)
            context["business_hours"] = _query_rows(
                """
                SELECT business_hour_id, day_of_week, is_open, open_time, close_time
                FROM business_hours
                WHERE business_id = ?
                ORDER BY day_of_week
                """,
                (business_id,),
            )
            context["availability"] = get_business_availability(business_id)
        return context

    if role == "super_admin":
        context["businesses"] = get_all_businesses()
        context["users"] = get_all_users()
        context["customers"] = get_all_customers()
        context["appointments"] = get_all_appointments()
        context["invoices"] = get_all_invoices()
        context["services"] = _query_rows(
            """
            SELECT service_id, business_id, service_name, description, price,
                   duration_minutes, is_active, created_at
            FROM services
            ORDER BY business_id, service_name
            """
        )
        context["leads"] = get_all_leads()
        context["availability"] = _query_rows(
            """
            SELECT availability_id, business_id, availability_date, is_available,
                   start_time, end_time, note
            FROM availability
            ORDER BY business_id, availability_date, start_time
            """
        )
        context["business_hours"] = _query_rows(
            """
            SELECT business_hour_id, business_id, day_of_week, is_open, open_time, close_time
            FROM business_hours
            ORDER BY business_id, day_of_week
            """
        )
        context["availability_breaks"] = _query_rows(
            """
            SELECT break_id, business_id, availability_id, break_date, start_time, end_time, note, created_at
            FROM availability_breaks
            ORDER BY business_id, break_date, start_time
            """
        )
        context["contact_requests"] = _query_rows(
            """
            SELECT contact_request_id, business_id, full_name, business_name, phone,
                   email, subject, message, status, created_at
            FROM contact_requests
            ORDER BY created_at DESC, contact_request_id DESC
            """
        )
        context["business_invoice_connections"] = _query_rows(
            """
            SELECT connection_id, business_id, provider, account_reference, status,
                   connected_at, created_at
            FROM business_invoice_connections
            ORDER BY business_id
            """
        )
        context["appointment_invoice_links"] = _query_rows(
            """
            SELECT link_id, appointment_id, business_id, status, provider_invoice_id,
                   invoice_url, created_at
            FROM appointment_invoice_links
            ORDER BY business_id, link_id
            """
        )
        context["business_invites"] = _query_rows(
            """
            SELECT invite_id, business_id, expires_at, used_at, created_at
            FROM business_invites
            ORDER BY business_id, invite_id DESC
            """
        )
        context["pending_owner_registrations"] = _query_rows(
            """
            SELECT pending_id, email, full_name, phone, business_id, expires_at, created_at
            FROM pending_owner_registrations
            ORDER BY created_at DESC, pending_id DESC
            """
        )
        context["business_invoice_connections"] = _query_rows(
            """
            SELECT connection_id, business_id, provider, account_reference, status,
                   connected_at, created_at
            FROM business_invoice_connections
            ORDER BY business_id
            """
        )
        context["summary"] = get_system_summary()
        context["schema_meta"] = _query_rows("SELECT key, value FROM schema_meta ORDER BY key")
        return context

    return context

