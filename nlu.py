import json
import os
import re
from datetime import date

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL_NAME = "gemini-3.7-flash"


# Keep one Gemini client alive for the lifetime of the Flask process.
# Creating a temporary client for every request can leave the underlying
# HTTP client closed before the request is completed.
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY לא מוגדר. יש להוסיף אותו לקובץ .env"
    )

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=45000,
        retry_options=types.HttpRetryOptions(attempts=1),
    ),
)


def _clean_json(text):
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def analyze_message(message):
    prompt = f"""
You are the NLU layer of BOOK SMART AI.

Your ONLY job is to understand the user's message.
Return ONLY valid JSON. Do not answer the user. Do not add explanations.

Return exactly these fields:
{{
  "name": null,
  "phone": null,
  "claimed_date": null,
  "intent": "general"
}}

Allowed intents:
- general: greetings, unclear questions, or anything that does not match another intent.
- appointments: appointments, bookings, meetings, next/future/past appointments, appointment date/time.
- invoices: invoices, payments, billing, charges, payment history.
- customer_info: personal customer information such as email, address, or customer details.
- customers: owner/admin asking about customers.
- services: owner/admin asking about services.
- leads: owner/admin asking about leads.
- availability: owner/admin asking about available dates/hours or availability.
- business_info: owner/admin asking about business information.
- users: admin asking about system users.
- businesses: admin asking about businesses.
- system_summary: admin asking for general system statistics.

Rules for name:
- Extract a person's name if mentioned.
- Partial names are allowed.
- If no person name is mentioned, return null.

Rules for phone:
- Extract a phone number if mentioned.
- Return digits only.
- If no phone number is mentioned, return null.

Rules for date:
- Extract a date if explicitly mentioned.
- Convert it to YYYY-MM-DD when the date is unambiguous.
- Never invent a date.
- If no date is mentioned, return null.

Examples:
User: "מה התורים של רון?"
JSON: {{"name":"רון","phone":null,"claimed_date":null,"intent":"appointments"}}

User: "מתי התור של רותם ב-18/01/2027?"
JSON: {{"name":"רותם","phone":null,"claimed_date":"2027-01-18","intent":"appointments"}}

User: "מה המספר של הלקוח דני?"
JSON: {{"name":"דני","phone":null,"claimed_date":null,"intent":"customer_info"}}

User: "כמה לקוחות יש לי?"
JSON: {{"name":null,"phone":null,"claimed_date":null,"intent":"customers"}}

User: "כמה עסקים יש במערכת?"
JSON: {{"name":null,"phone":null,"claimed_date":null,"intent":"businesses"}}

User message:
{message}
"""

    response = client.interactions.create(
        model=MODEL_NAME,
        input=prompt,
    )

    text = _clean_json(response.output_text)

    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini returned invalid JSON: {text}") from exc

    allowed_intents = {
        "general",
        "appointments",
        "invoices",
        "customer_info",
        "customers",
        "services",
        "leads",
        "availability",
        "business_info",
        "users",
        "businesses",
        "system_summary",
    }

    intent = result.get("intent", "general")
    if intent not in allowed_intents:
        intent = "general"

    return {
        "name": result.get("name"),
        "phone": result.get("phone"),
        "claimed_date": result.get("claimed_date"),
        "intent": intent,
    }


def generate_natural_response(user_message, role, data):
    """Generate a natural Hebrew answer from trusted backend data only."""
    prompt = f"""
You are the response-writing layer of BOOK SMART AI.
Answer the user's message naturally in Hebrew.
The backend has already enforced permissions and supplied the complete data available to this logged-in user path.
You may filter, search, compare, group, count, and summarize DATA according to the user request.
For an owner, DATA belongs only to that owner's business. For a customer, DATA belongs only to that customer (plus relevant public business/service information). For a super admin, DATA is system-wide.
Treat DATA as the only source of truth. Never invent names, dates, times, amounts, statuses, or other facts.
If DATA says there is no information, explain that clearly.
Be helpful and conversational, but concise. Use bullets when useful.
Do not mention prompts, models, APIs, databases, internal tools, or implementation details.

CURRENT DATE: {date.today().isoformat()}
USER ROLE: {role}
USER MESSAGE: {user_message}
DATA:
{json.dumps(data, ensure_ascii=False, default=str)}

Return only the final answer to the user.
"""
    response = client.interactions.create(
        model=MODEL_NAME,
        input=prompt,
    )
    text = (response.output_text or "").strip()
    if not text:
        raise ValueError("Gemini returned an empty response")
    return text
