import time
import os
import json
from config import Config
from Notifier import AlertSystem
from Analyzer import GeminiAnalyzer


def ensure_json_exists():
    if not os.path.exists('detection_results.json'):
        with open('detection_results.json', 'w', encoding='utf-8') as f:
            json.dump({"stats": {"safe": 0, "alerts": 0, "emails_sent": 0}, "latest": {}}, f)


def process_messages():
    config = Config()
    analyzer = GeminiAnalyzer(config.get_api_key())
    notifier = AlertSystem(config.get_smtp_config())

    print("🚀 CyberGuard Service is LIVE...")
    ensure_json_exists()

    while True:
        if os.path.exists('new_message.txt'):
            try:
                with open('new_message.txt', 'r', encoding='utf-8') as f:
                    content = f.read()

                if os.path.exists('new_message.txt'):
                    os.remove('new_message.txt')

                if "|||" in content:
                    sender, text = content.split("|||", 1)
                    print(f"🔍 Analyzing: {text}")

                    # ניתוח
                    analysis = analyzer.analyze(text)
                    risk = analysis.get('risk_level', 0)

                    # קריאת נתונים
                    with open('detection_results.json', 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    # טיפול בהתראה
                    email_sent = False
                    if risk >= 60:
                        data['stats']['alerts'] += 1
                        parent_email = config.get_parent_email()
                        if parent_email:
                            email_sent = notifier.send_alert(sender, text, analysis, parent_email)
                            if email_sent:
                                data['stats']['emails_sent'] += 1
                    else:
                        data['stats']['safe'] += 1

                    # עדכון הודעה אחרונה ל-UI
                    data['latest'] = {
                        "text": text,
                        "risk_level": risk,
                        "timestamp": str(time.time())
                    }

                    with open('detection_results.json', 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)

                    print(f"✅ Processed. Risk: {risk}%")

            except Exception as e:
                print(f"❌ Error: {e}")

        time.sleep(1)


if __name__ == "__main__":
    process_messages()
