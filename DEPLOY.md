# DEPLOY – BOOK SMART AI

## תיאור הפריסה

BOOK SMART AI היא מערכת Web המבוססת על Flask, אשר נפרסה על גבי PythonAnywhere.
קוד המקור מנוהל באמצעות Git ו-GitHub, ומסד הנתונים מבוסס SQLite.

## הרצה מקומית

דרישות:
- Python 3.13 ומעלה
- Git
- Gemini API Key

התקנת תלויות:

pip install -r requirements.txt

יש ליצור קובץ .env בתיקיית הפרויקט ולהוסיף:

GEMINI_API_KEY=YOUR_API_KEY

הרצת המערכת:

python app.py

כתובת מקומית:

http://127.0.0.1:5001

## עדכון המערכת בשרת

לאחר ביצוע שינויים בקוד והעלאתם ל-GitHub:

cd /home/shalevdahan/BOOK.SMART_AI
git pull origin main

לאחר מכן יש להיכנס ללשונית Web ב-PythonAnywhere וללחוץ על Reload.

## כתובת המערכת

https://shalevdahan.pythonanywhere.com

## טכנולוגיות

- Python
- Flask
- SQLite
- Google Gemini
- Git
- GitHub
- PythonAnywhere

## אבטחה

מפתחות API ופרטי התחברות אינם נשמרים בקוד המקור ואינם מועלים ל-GitHub.