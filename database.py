import sqlite3
from datetime import datetime

DATABASE_NAME = "appointments.db"


def connect_db():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return any(row["name"] == column_name for row in cursor.fetchall())


def add_column_if_missing(cursor, table_name, column_name, definition):
    if not column_exists(cursor, table_name, column_name):
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
        )


def table_exists(cursor, table_name):
    cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def _create_tables(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS businesses (
            business_id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            business_type TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            description TEXT,
            logo_url TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            address TEXT,
            business_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses(business_id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('super_admin', 'owner', 'customer')),
            business_id INTEGER,
            customer_id INTEGER,
            full_name TEXT,
            phone TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses(business_id)
                ON DELETE CASCADE,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            service_id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            service_name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL DEFAULT 0,
            duration_minutes INTEGER NOT NULL DEFAULT 30,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses(business_id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS business_hours (
            business_hour_id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            day_of_week INTEGER NOT NULL,
            is_open INTEGER NOT NULL DEFAULT 1,
            open_time TEXT,
            close_time TEXT,
            FOREIGN KEY (business_id) REFERENCES businesses(business_id)
                ON DELETE CASCADE,
            UNIQUE(business_id, day_of_week)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS availability (
            availability_id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            availability_date TEXT NOT NULL,
            is_available INTEGER NOT NULL DEFAULT 1,
            start_time TEXT,
            end_time TEXT,
            note TEXT,
            FOREIGN KEY (business_id) REFERENCES businesses(business_id)
                ON DELETE CASCADE,
            UNIQUE(business_id, availability_date)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER,
            customer_id INTEGER NOT NULL,
            service_id INTEGER,
            service_type TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses(business_id)
                ON DELETE CASCADE,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                ON DELETE CASCADE,
            FOREIGN KEY (service_id) REFERENCES services(service_id)
                ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER,
            customer_id INTEGER NOT NULL,
            service_id INTEGER,
            service_type TEXT NOT NULL,
            amount REAL NOT NULL,
            invoice_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'unpaid',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses(business_id)
                ON DELETE CASCADE,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                ON DELETE CASCADE,
            FOREIGN KEY (service_id) REFERENCES services(service_id)
                ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            lead_id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            source TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses(business_id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contact_requests (
            contact_request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER,
            full_name TEXT NOT NULL,
            business_name TEXT,
            phone TEXT,
            email TEXT,
            subject TEXT,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses(business_id)
                ON DELETE SET NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS availability_breaks (
            break_id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            availability_id INTEGER,
            break_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses(business_id) ON DELETE CASCADE,
            FOREIGN KEY (availability_id) REFERENCES availability(availability_id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_availability_breaks_business_date
        ON availability_breaks(business_id, break_date)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS business_invites (
            invite_id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            code_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            used_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses(business_id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_business_invites_business
        ON business_invites(business_id)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_owner_registrations (
            pending_id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_hash TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            business_id INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (business_id) REFERENCES businesses(business_id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_pending_owner_token
        ON pending_owner_registrations(token_hash)
    """)

    cursor.execute("""CREATE TABLE IF NOT EXISTS business_invoice_connections (
        connection_id INTEGER PRIMARY KEY AUTOINCREMENT, business_id INTEGER NOT NULL UNIQUE,
        provider TEXT, account_reference TEXT, status TEXT NOT NULL DEFAULT 'not_connected',
        connected_at TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (business_id) REFERENCES businesses(business_id) ON DELETE CASCADE
    )""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS appointment_invoice_links (
        link_id INTEGER PRIMARY KEY AUTOINCREMENT, appointment_id INTEGER NOT NULL UNIQUE,
        business_id INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'not_issued',
        provider_invoice_id TEXT, invoice_url TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE CASCADE,
        FOREIGN KEY (business_id) REFERENCES businesses(business_id) ON DELETE CASCADE
    )""")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)


def _migrate_columns(cursor):
    # Older versions of the project created smaller tables.  Every column
    # below is added only when it is missing, so existing data is preserved.
    migrations = {
        "businesses": [
            ("approval_status", "TEXT NOT NULL DEFAULT 'approved'"),
            ("business_type", "TEXT"), ("phone", "TEXT"), ("email", "TEXT"),
            ("address", "TEXT"), ("description", "TEXT"), ("logo_url", "TEXT"),
            ("is_active", "INTEGER NOT NULL DEFAULT 1"),
            ("created_at", "TEXT"),
        ],
        "customers": [
            ("business_id", "INTEGER"), ("created_at", "TEXT"),
        ],
        "users": [
            ("business_id", "INTEGER"), ("customer_id", "INTEGER"),
            ("full_name", "TEXT"), ("phone", "TEXT"),
            ("is_active", "INTEGER NOT NULL DEFAULT 1"),
            ("created_at", "TEXT"),
        ],
        "services": [
            ("business_id", "INTEGER"), ("service_name", "TEXT"),
            ("description", "TEXT"), ("price", "REAL DEFAULT 0"),
            ("duration_minutes", "INTEGER DEFAULT 30"),
            ("is_active", "INTEGER NOT NULL DEFAULT 1"),
            ("created_at", "TEXT"),
        ],
        "business_hours": [
            ("business_id", "INTEGER"), ("day_of_week", "INTEGER"),
            ("is_open", "INTEGER NOT NULL DEFAULT 1"),
            ("open_time", "TEXT"), ("close_time", "TEXT"),
        ],
        "availability": [
            ("business_id", "INTEGER"), ("availability_date", "TEXT"),
            ("is_available", "INTEGER NOT NULL DEFAULT 1"),
            ("start_time", "TEXT"), ("end_time", "TEXT"), ("note", "TEXT"),
        ],
        "appointments": [
            ("business_id", "INTEGER"), ("service_id", "INTEGER"),
            ("notes", "TEXT"), ("created_at", "TEXT"),
            ("cancelled_by", "TEXT"),
        ],
        "invoices": [
            ("business_id", "INTEGER"), ("service_id", "INTEGER"),
            ("notes", "TEXT"), ("created_at", "TEXT"),
        ],
        "leads": [
            ("business_id", "INTEGER"), ("email", "TEXT"),
            ("notes", "TEXT"), ("created_at", "TEXT"),
        ],
        "contact_requests": [
            ("business_id", "INTEGER"), ("business_name", "TEXT"),
            ("phone", "TEXT"), ("email", "TEXT"), ("subject", "TEXT"),
            ("status", "TEXT DEFAULT 'new'"),
            ("created_at", "TEXT"),
        ],
    }

    for table_name, columns in migrations.items():
        if not table_exists(cursor, table_name):
            continue
        for column_name, definition in columns:
            add_column_if_missing(cursor, table_name, column_name, definition)


def _normalize_legacy_dates(cursor):
    # The original console version stored dates as DD/MM/YYYY.  The web
    # application uses ISO YYYY-MM-DD because it sorts correctly and works
    # naturally with HTML date inputs.
    for table_name, column_name in (
        ("appointments", "appointment_date"),
        ("invoices", "invoice_date"),
    ):
        if not table_exists(cursor, table_name) or not column_exists(cursor, table_name, column_name):
            continue
        cursor.execute(f"SELECT rowid AS __rowid, {column_name} FROM {table_name}")
        rows = cursor.fetchall()
        for row in rows:
            value = row[column_name]
            if not value or not isinstance(value, str):
                continue
            try:
                converted = datetime.strptime(value, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                continue
            cursor.execute(
                f"UPDATE {table_name} SET {column_name} = ? WHERE rowid = ?",
                (converted, row["__rowid"]),
            )


def _ensure_default_business(cursor):
    cursor.execute("SELECT business_id FROM businesses ORDER BY business_id LIMIT 1")
    row = cursor.fetchone()
    if row:
        return row["business_id"]

    cursor.execute("""
        INSERT INTO businesses (business_name, business_type, description)
        VALUES (?, ?, ?)
    """, ("העסק שלי", "עסק", "העסק הקיים במערכת"))
    return cursor.lastrowid


def _attach_legacy_rows(cursor, business_id):
    for table_name in ("customers", "appointments", "invoices"):
        if table_exists(cursor, table_name) and column_exists(cursor, table_name, "business_id"):
            cursor.execute(
                f"UPDATE {table_name} SET business_id = ? WHERE business_id IS NULL",
                (business_id,),
            )


def _ensure_default_hours(cursor, business_id):
    cursor.execute(
        "SELECT COUNT(*) AS count FROM business_hours WHERE business_id = ?",
        (business_id,),
    )
    if cursor.fetchone()["count"]:
        return

    default_hours = [
        (0, 1, "09:00", "18:00"),
        (1, 1, "09:00", "18:00"),
        (2, 1, "09:00", "18:00"),
        (3, 1, "09:00", "18:00"),
        (4, 1, "09:00", "18:00"),
        (5, 1, "13:00", "18:00"),
        (6, 0, None, None),
    ]
    cursor.executemany("""
        INSERT INTO business_hours
            (business_id, day_of_week, is_open, open_time, close_time)
        VALUES (?, ?, ?, ?, ?)
    """, [(business_id, *row) for row in default_hours])


def _create_indexes(cursor):
    indexes = [
        ("idx_customers_business", "customers", "business_id"),
        ("idx_users_business", "users", "business_id"),
        ("idx_users_customer", "users", "customer_id"),
        ("idx_services_business", "services", "business_id"),
        ("idx_hours_business", "business_hours", "business_id"),
        ("idx_availability_business_date", "availability", "business_id, availability_date"),
        ("idx_appointments_business", "appointments", "business_id"),
        ("idx_appointments_customer", "appointments", "customer_id"),
        ("idx_appointments_date", "appointments", "appointment_date, appointment_time"),
        ("idx_invoices_business", "invoices", "business_id"),
        ("idx_invoices_customer", "invoices", "customer_id"),
        ("idx_leads_business", "leads", "business_id"),
        ("idx_contact_status", "contact_requests", "status"),
    ]
    for index_name, table_name, columns in indexes:
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({columns})"
        )

    duplicate_phone = cursor.execute("""
        SELECT 1 FROM users
        WHERE phone IS NOT NULL AND phone != ''
        GROUP BY phone HAVING COUNT(*) > 1 LIMIT 1
    """).fetchone()
    if not duplicate_phone:
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_phone_unique
            ON users(phone)
            WHERE phone IS NOT NULL AND phone != ''
        """)


def create_tables():
    conn = connect_db()
    try:
        cursor = conn.cursor()
        _create_tables(cursor)
        _migrate_columns(cursor)

        # Backfill timestamps for rows that came from the original console version.
        for table_name in ("businesses", "customers", "users", "services", "appointments", "invoices", "leads", "contact_requests"):
            if table_exists(cursor, table_name) and column_exists(cursor, table_name, "created_at"):
                cursor.execute(f"UPDATE {table_name} SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL OR created_at = ''")

        _normalize_legacy_dates(cursor)

        # Do NOT create a default/fake business on startup.
        # Businesses are created explicitly by the Super Admin.
        first_business = cursor.execute(
            "SELECT business_id FROM businesses ORDER BY business_id LIMIT 1"
        ).fetchone()
        if first_business:
            business_id = first_business["business_id"]
            _attach_legacy_rows(cursor, business_id)
            _ensure_default_hours(cursor, business_id)

        _create_indexes(cursor)

        cursor.execute("""
            INSERT INTO schema_meta(key, value)
            VALUES ('schema_version', '3')
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """)

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    create_tables()
    print("Database initialized successfully.")
