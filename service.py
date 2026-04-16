import time
import os
import json
import google.generativeai as genai
from config import Config
from Notifier import AlertSystem

# --- אתחול הגדרות ---
config = Config()

# משיכת מפתח ה-API מהקונפיג
genai.configure(api_key=config.get_api_key())
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# משיכת הגדרות ה-SMTP (מייל וסיסמה) ישירות מהקונפיג שלך
smtp_data = config.get_smtp_config()
notifier = AlertSystem(smtp_data)

RESULTS_FILE = 'detection_results.json'


def ensure_json_exists():
    """מוודא שקובץ התוצאות קיים למניעת קריסה"""
    if not os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"stats": {"safe": 0, "alerts": 0, "emails_sent": 0}, "latest": {}}, f)


def analyze_with_ai(text):
    """מנתח את ההודעה בעזרת Gemini"""
    prompt = (
        f"Analyze this Hebrew message: '{text}'. "
        f"Return ONLY a JSON object with: "
        f"'risk_level' (0-100), 'category' (bullying/spam/safe), "
        f"'reason' (short explanation in English), 'keywords' (list of bad words)."
    )
    try:
        response = ai_model.generate_content(prompt)
        # ניקוי פורמט Markdown אם קיים
        result_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(result_text)
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return {"risk_level": 50, "category": "unknown", "reason": "Error in analysis", "keywords": []}


def process_messages():
    print("🚀 CyberGuard Service is LIVE...")
    ensure_json_exists()

    while True:
        # בדיקה אם יש הודעה חדשה שממתינה לעיבוד
        if os.path.exists('new_message.txt'):
            try:
                # 1. קריאת ההודעה
                with open('new_message.txt', 'r', encoding='utf-8') as f:
                    content = f.read()

                # מחיקת הקובץ מיד כדי לא לעבד שוב
                os.remove('new_message.txt')

                if "|||" in content:
                    sender, text = content.split("|||", 1)
                    print(f"🔍 Analyzing message from {sender}...")

                    # 2. ניתוח AI
                    analysis = analyze_with_ai(text)
                    risk = analysis.get('risk_level', 0)

                    # 3. קריאת הסטטיסטיקה הקיימת
                    with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # 4. שליחת מייל דרך ה-Notifier (רק אם הוגדר מייל הורה ב-UI)
                    parent_email = config.get_parent_email()
                    email_sent = False
                    if parent_email:
                        # ה-send_alert כבר מכיל בדיקה של risk_level >= 60 בפנים
                        email_sent = notifier.send_alert(sender, text, analysis, parent_email)

                    # 5. עדכון הסטטיסטיקה עבור ה-Main UI
                    if risk >= 60:
                        data['stats']['alerts'] += 1
                        if email_sent:
                            data['stats']['emails_sent'] += 1
                    else:
                        data['stats']['safe'] += 1

                    # 6. עדכון "הודעה אחרונה" כדי שה-UI יקפוץ ויציג אותה
                    data['latest'] = {
                        "text": text,
                        "risk_level": risk,
                        "timestamp": str(time.time())
                    }

                    # שמירה לקובץ ה-JSON
                    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

                    print(f"✅ Processed: {text[:20]}... | Risk: {risk}% | Email: {email_sent}")

            except Exception as e:
                print(f"❌ Error in service loop: {e}")

        time.sleep(1)


if __name__ == "__main__":
    process_messages()