from ai_tools import (
    get_scoped_context,
    get_all_businesses,
    get_all_leads,
    get_all_users,
    get_business_appointments,
    get_business_availability,
    get_business_customers,
    get_business_info,
    get_business_invoices,
    get_business_leads,
    get_business_services,
    get_customer_appointments,
    get_customer_info,
    get_customer_invoices,
    get_system_summary,
    search_customers_by_name,
    verify_customer_phone,
)
from nlu import analyze_message, generate_natural_response


class Chatbot:
    MAX_VERIFICATION_ATTEMPTS = 3

    def __init__(self, role, business_id=None, customer_id=None):
        self.role = role
        self.business_id = business_id
        self.customer_id = customer_id
        self.pending_customer_id = None
        self.pending_customer_name = None
        self.verification_attempts = 0
        self.blocked = False

        # Logged-in customers are already authenticated by the application.
        # Owner and Super Admin are also authenticated by the application.
        self.verified = role in {"customer", "owner", "super_admin"}

    def handle_message(self, message):
        if not message:
            return "לא קיבלתי הודעה."

        # The user is already authenticated by Flask. The AI receives the
        # complete data available to this login path and can filter it
        # according to the natural-language request.
        if self.role in {"customer", "owner", "super_admin"}:
            context = get_scoped_context(
                self.role,
                business_id=self.business_id,
                customer_id=self.customer_id,
            )
            if not context:
                return "לא נמצא מידע זמין עבור המשתמש המחובר."
            return self._smart_answer(message, context)

        return "אין הרשאה להשתמש בעוזר AI."

    def _smart_answer(self, user_message, trusted_data):
        try:
            answer = generate_natural_response(user_message, self.role, trusted_data)
            if isinstance(answer, str):
                return answer
            return str(answer)
        except Exception:
            # Never return a dict/list to the frontend, because JavaScript
            # would render it as "[object Object]".
            return "לא הצלחתי לנסח תשובה כרגע. הנתונים נמצאו, אבל שירות התשובות לא החזיר ניסוח תקין. נסה שוב בעוד כמה שניות."

    def _handle_verification(self, data):
        if self.pending_customer_id is not None:
            phone = data.get("phone")
            if not phone:
                return "כדי להמשיך באימות, נא לשלוח את מספר הטלפון של הלקוח."

            if verify_customer_phone(self.pending_customer_id, phone):
                self.customer_id = self.pending_customer_id
                self.verified = True
                self.pending_customer_id = None
                self.pending_customer_name = None
                self.verification_attempts = 0
                return "האימות הצליח ✅ עכשיו אפשר לשאול אותי על הנתונים שלך."

            self.verification_attempts += 1
            if self.verification_attempts >= self.MAX_VERIFICATION_ATTEMPTS:
                self.blocked = True
                return "מספר הטלפון שהוזן אינו תואם. בוצעו 3 ניסיונות אימות שגויים ולכן לא ניתן להמשיך את השיחה."

            remaining = self.MAX_VERIFICATION_ATTEMPTS - self.verification_attempts
            return f"מספר הטלפון שהוזן אינו תואם. נשארו {remaining} ניסיונות."

        name = data.get("name")
        if not name:
            return "כדי לזהות את הלקוח, נא לציין את שמו."

        matches = search_customers_by_name(name)

        if not matches:
            return "לא מצאתי לקוח בשם הזה. אפשר לנסות שם אחר?"

        if len(matches) > 1:
            names = ", ".join(item["full_name"] for item in matches)
            return f"מצאתי כמה לקוחות מתאימים: {names}. נא לציין את השם המלא של הלקוח."

        customer = matches[0]
        self.pending_customer_id = customer["customer_id"]
        self.pending_customer_name = customer["full_name"]
        return "מצאתי את הלקוח. כדי לאמת את הזהות ולחשוף מידע אישי, נא להזין את מספר הטלפון של הלקוח."

    def _handle_authorized_request(self, data, user_message):
        intent = data.get("intent", "general")

        if self.role == "customer":
            return self._customer_request(intent, data, user_message)

        if self.role == "owner":
            return self._owner_request(intent, data, user_message)

        if self.role == "super_admin":
            return self._admin_request(intent, data, user_message)

        return "אין הרשאה להשתמש בעוזר AI."

    def _customer_request(self, intent, data, user_message):
        if self.customer_id is None:
            return "לא ניתן לזהות את הלקוח המחובר."

        if intent == "appointments":
            appointments = get_customer_appointments(
                self.customer_id,
                self.business_id,
                data.get("claimed_date"),
            )
            if not appointments:
                return "לא מצאתי תורים מתאימים."
            return self._smart_answer(user_message, self._format_appointments(appointments, customer_view=True))

        if intent == "invoices":
            invoices = get_customer_invoices(self.customer_id, self.business_id)
            if not invoices:
                return "לא מצאתי חשבוניות."
            return self._smart_answer(user_message, self._format_invoices(invoices, customer_view=True))

        if intent == "customer_info":
            info = get_customer_info(self.customer_id, self.business_id)
            if not info:
                return "לא מצאתי את פרטי הלקוח."
            return self._smart_answer(user_message, self._format_customer(info))

        return "אני יכול לעזור לך עם התורים, החשבוניות או הפרטים האישיים שלך."

    def _owner_request(self, intent, data, user_message):
        if self.business_id is None:
            return "לא ניתן לזהות את העסק של המשתמש המחובר."

        if intent == "customers":
            customers = get_business_customers(self.business_id)
            if not customers:
                return "אין כרגע לקוחות בעסק."
            return self._smart_answer(user_message, self._format_customers(customers))

        if intent == "appointments":
            appointments = get_business_appointments(self.business_id)
            if not appointments:
                return "אין כרגע תורים בעסק."
            return self._smart_answer(user_message, self._format_appointments(appointments))

        if intent == "invoices":
            invoices = get_business_invoices(self.business_id)
            if not invoices:
                return "אין כרגע חשבוניות בעסק."
            return self._smart_answer(user_message, self._format_invoices(invoices))

        if intent == "services":
            services = get_business_services(self.business_id)
            if not services:
                return "אין כרגע שירותים בעסק."
            return self._smart_answer(user_message, self._format_services(services))

        if intent == "leads":
            leads = get_business_leads(self.business_id)
            if not leads:
                return "אין כרגע לידים בעסק."
            return self._smart_answer(user_message, self._format_leads(leads))

        if intent == "availability":
            availability = get_business_availability(self.business_id)
            if not availability:
                return "אין כרגע נתוני זמינות."
            return self._smart_answer(user_message, self._format_availability(availability))

        if intent == "business_info":
            info = get_business_info(self.business_id)
            if not info:
                return "לא מצאתי את פרטי העסק."
            return self._smart_answer(user_message, self._format_business(info))

        return "אני יכול לעזור לך עם לקוחות, תורים, חשבוניות, שירותים, לידים, זמינות ופרטי העסק."

    def _admin_request(self, intent, data, user_message):
        if intent == "businesses":
            businesses = get_all_businesses()
            if not businesses:
                return "אין עסקים במערכת."
            return self._smart_answer(user_message, self._format_businesses(businesses))

        if intent == "users":
            users = get_all_users()
            if not users:
                return "אין משתמשים במערכת."
            return self._smart_answer(user_message, self._format_users(users))

        if intent == "leads":
            leads = get_all_leads()
            if not leads:
                return "אין לידים במערכת."
            return self._smart_answer(user_message, self._format_leads(leads, include_business=True))

        if intent == "system_summary":
            return self._smart_answer(user_message, self._format_summary(get_system_summary()))

        if intent == "customers":
            from ai_tools import get_all_customers
            customers = get_all_customers()
            return self._smart_answer(user_message, self._format_customers(customers) if customers else "אין לקוחות במערכת.")

        if intent == "appointments":
            from ai_tools import get_all_appointments
            appointments = get_all_appointments()
            return self._smart_answer(user_message, self._format_appointments(appointments) if appointments else "אין תורים במערכת.")

        if intent == "invoices":
            from ai_tools import get_all_invoices
            invoices = get_all_invoices()
            return self._smart_answer(user_message, self._format_invoices(invoices) if invoices else "אין חשבוניות במערכת.")

        return "אני יכול לעזור לך עם עסקים, משתמשים, לידים ונתוני מערכת כלליים."

    @staticmethod
    def _format_customer(item):
        return (
            f"שם: {item.get('full_name') or '—'}\n"
            f"טלפון: {item.get('phone') or '—'}\n"
            f"אימייל: {item.get('email') or '—'}\n"
            f"כתובת: {item.get('address') or '—'}"
        )

    @staticmethod
    def _format_customers(items):
        lines = [f"נמצאו {len(items)} לקוחות:"]
        for item in items:
            lines.append(
                f"• {item['full_name']} | טלפון: {item.get('phone') or '—'} | אימייל: {item.get('email') or '—'}"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_appointments(items, customer_view=False):
        lines = [f"נמצאו {len(items)} תורים:"]
        for item in items:
            service = item.get("service_name") or item.get("service_type") or "—"
            status = item.get("status") or "—"
            prefix = "" if customer_view else f"{item.get('customer_name') or 'לקוח'} | "
            lines.append(
                f"• {prefix}{item.get('appointment_date')} בשעה {item.get('appointment_time')} | {service} | סטטוס: {status}"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_invoices(items, customer_view=False):
        lines = [f"נמצאו {len(items)} חשבוניות:"]
        for item in items:
            prefix = "" if customer_view else f"{item.get('customer_name') or 'לקוח'} | "
            lines.append(
                f"• {prefix}חשבונית #{item.get('invoice_id')} | {item.get('invoice_date')} | {item.get('amount')} ₪ | סטטוס: {item.get('status') or '—'}"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_services(items):
        lines = [f"נמצאו {len(items)} שירותים:"]
        for item in items:
            lines.append(
                f"• {item['service_name']} | מחיר: {item.get('price', 0)} ₪ | משך: {item.get('duration_minutes', '—')} דקות"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_leads(items, include_business=False):
        lines = [f"נמצאו {len(items)} לידים:"]
        for item in items:
            business = f" | עסק: {item.get('business_name') or '—'}" if include_business else ""
            lines.append(
                f"• {item.get('full_name') or '—'} | טלפון: {item.get('phone') or '—'} | סטטוס: {item.get('status') or '—'}{business}"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_availability(items):
        lines = [f"נמצאו {len(items)} רשומות זמינות:"]
        for item in items:
            status = "זמין" if item.get("is_available") else "לא זמין"
            lines.append(
                f"• {item.get('availability_date')} | {status} | {item.get('start_time') or '—'}-{item.get('end_time') or '—'}"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_business(item):
        return (
            f"שם העסק: {item.get('business_name') or '—'}\n"
            f"סוג: {item.get('business_type') or '—'}\n"
            f"טלפון: {item.get('phone') or '—'}\n"
            f"אימייל: {item.get('email') or '—'}\n"
            f"כתובת: {item.get('address') or '—'}\n"
            f"תיאור: {item.get('description') or '—'}"
        )

    @staticmethod
    def _format_businesses(items):
        lines = [f"נמצאו {len(items)} עסקים:"]
        for item in items:
            lines.append(
                f"• {item['business_name']} | סוג: {item.get('business_type') or '—'} | פעיל: {'כן' if item.get('is_active') else 'לא'}"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_users(items):
        lines = [f"נמצאו {len(items)} משתמשים:"]
        for item in items:
            lines.append(
                f"• {item.get('full_name') or item.get('email')} | {item.get('role')} | אימייל: {item.get('email')} | פעיל: {'כן' if item.get('is_active') else 'לא'}"
            )
        return "\n".join(lines)

    @staticmethod
    def _format_summary(summary):
        return (
            "סיכום המערכת:\n"
            f"• עסקים: {summary['businesses']}\n"
            f"• משתמשים: {summary['users']}\n"
            f"• לקוחות: {summary['customers']}\n"
            f"• תורים: {summary['appointments']}\n"
            f"• חשבוניות: {summary['invoices']}\n"
            f"• לידים: {summary['leads']}\n"
            f"• שירותים: {summary['services']}"
        )
