from flask import jsonify, render_template_string, request, session

from app import app, require_login
from chatbot import Chatbot


CHAT_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * { box-sizing: border-box; }
        body { margin: 0; font-family: Arial, sans-serif; background: #f5f1ed; color: #252525; }
        .chat-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 30px; }
        .chat-container { width: 100%; max-width: 900px; height: 750px; background: white; border-radius: 24px; box-shadow: 0 15px 50px rgba(0,0,0,.08); display: flex; flex-direction: column; overflow: hidden; }
        .chat-header { padding: 24px 30px; background: #252525; color: white; }
        .chat-header h1 { margin: 0 0 7px; font-size: 25px; }
        .chat-header p { margin: 0; opacity: .75; }
        .messages { flex: 1; overflow-y: auto; padding: 25px; background: #faf8f6; }
        .message { max-width: 75%; padding: 14px 17px; margin-bottom: 14px; border-radius: 17px; white-space: pre-wrap; line-height: 1.55; }
        .user-message { margin-right: auto; background: #252525; color: white; border-bottom-right-radius: 5px; }
        .ai-message { margin-left: auto; background: #eee8e3; border-bottom-left-radius: 5px; }
        .chat-input-area { display: flex; gap: 12px; padding: 18px; border-top: 1px solid #eee; background: white; }
        #messageInput { flex: 1; border: 1px solid #ddd; border-radius: 14px; padding: 15px; font-size: 16px; outline: none; }
        #sendButton { border: none; border-radius: 14px; padding: 0 25px; background: #252525; color: white; cursor: pointer; font-size: 16px; }
        #sendButton:disabled { opacity: .5; cursor: not-allowed; }
        .typing { opacity: .55; font-style: italic; }
    </style>
</head>
<body>
<div class="chat-page">
    <div class="chat-container">
        <div class="chat-header">
            <h1>🤖 {{ title }}</h1>
            <p>שאל אותי בשפה טבעית ואני אמצא את המידע הרלוונטי במערכת.</p>
        </div>
        <div id="messages" class="messages">
            <div class="message ai-message">שלום 👋 איך אפשר לעזור לך?</div>
        </div>
        <div class="chat-input-area">
            <input id="messageInput" type="text" placeholder="כתוב את השאלה שלך..." autocomplete="off">
            <button id="sendButton" onclick="sendMessage()">שלח</button>
        </div>
    </div>
</div>
<script>
const input = document.getElementById("messageInput");
const button = document.getElementById("sendButton");
const messages = document.getElementById("messages");

input.addEventListener("keydown", function(event) {
    if (event.key === "Enter") sendMessage();
});

function addMessage(text, type) {
    const div = document.createElement("div");
    div.className = "message " + (type === "user" ? "user-message" : "ai-message");
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

async function sendMessage() {
    const text = input.value.trim();
    if (!text || button.disabled) return;

    addMessage(text, "user");
    input.value = "";
    button.disabled = true;

    const typing = document.createElement("div");
    typing.className = "message ai-message typing";
    typing.textContent = "חושב...";
    typing.id = "typingMessage";
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });

        const data = await response.json();
        const typingElement = document.getElementById("typingMessage");
        if (typingElement) typingElement.remove();
        addMessage(data.response || "אירעה שגיאה.", "ai");
    } catch (error) {
        const typingElement = document.getElementById("typingMessage");
        if (typingElement) typingElement.remove();
        addMessage("אירעה שגיאה בתקשורת עם השרת.", "ai");
    }

    button.disabled = false;
    input.focus();
}
</script>
</body>
</html>
"""


@app.route("/chat")
def ai_chat():
    check = require_login()
    if check:
        return check

    role = session.get("role")

    titles = {
        "super_admin": "AI מנהל מערכת",
        "owner": "AI עוזר העסק",
        "customer": "AI העוזר האישי שלי",
    }

    title = titles.get(role)
    if not title:
        return "גישה נדחתה", 403

    return render_template_string(CHAT_TEMPLATE, title=title)


@app.route("/api/chat", methods=["POST"])
def ai_chat_api():
    check = require_login()
    if check:
        return jsonify({"response": "אין הרשאה להשתמש בעוזר AI."}), 403

    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"response": "לא קיבלתי הודעה."}), 400

    chatbot = Chatbot(
        role=session.get("role"),
        business_id=session.get("business_id"),
        customer_id=session.get("customer_id"),
    )

    try:
        response = chatbot.handle_message(message)
    except Exception as exc:
        print(f"AI request failed: {type(exc).__name__}: {exc}")
        return jsonify({
            "response": "לא הצלחתי לקבל תשובה מהעוזר כרגע. נסה שוב בעוד כמה שניות."
        }), 503

    # The frontend expects a text response. Keep the API contract stable
    # even if an internal function accidentally returns a dict/list.
    if not isinstance(response, str):
        response = str(response)

    return jsonify({"response": response})
