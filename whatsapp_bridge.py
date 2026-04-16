from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from Analyzer import GeminiAnalyzer
from Notifier import AlertSystem
from config import Config
import time


def start_whatsapp_scanner(ui_callback):
    """
    מריץ את סורק הוואטסאפ ושולח נתונים ל-GUI דרך ה-callback
    """
    cfg = Config()
    analyzer = GeminiAnalyzer(cfg.get_api_key())
    notifier = AlertSystem(cfg.get_smtp_config())

    # הגדרות Chrome אופטימליות
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # הפעלת הדפדפן
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        driver.get("https://web.whatsapp.com")
    except WebDriverException as e:
        print(f"\n❌ שגיאה בהפעלת Chrome: {e}")
        print("אנא ודא שדפדפן Chrome מותקן במחשב")
        return

    print("\n🚀 CyberGuard Web Bridge מופעל...")
    print("נא לסרוק את קוד ה-QR בדפדפן שנפתח.")
    print("ממתין לחיבור...\n")

    # המתנה לטעינת WhatsApp Web
    time.sleep(5)

    last_message = ""
    error_count = 0
    max_errors = 10

    while True:
        try:
            # איפוס מונה שגיאות אם הכל עובד
            error_count = 0

            # שליפת המייל המעודכן מההגדרות בכל סבב
            parent_email = cfg.get_parent_email() or "omerniztzanim@gmail.com"

            # חיפוש הודעות נכנסות (טקסט בלבד)
            # נסיון מספר selectors שונים למקרה ש-WhatsApp שינה את המבנה
            selectors = [
                "div.message-in span.selectable-text",
                "span.selectable-text.copyable-text",
                "div[data-pre-plain-text] span.selectable-text"
            ]

            messages = []
            for selector in selectors:
                try:
                    messages = driver.find_elements(By.CSS_SELECTOR, selector)
                    if messages:
                        break
                except NoSuchElementException:
                    continue

            if messages:
                latest_msg_element = messages[-1]
                current_text = latest_msg_element.text.strip()

                # בדיקה שהטקסט לא ריק ושונה מההודעה הקודמת
                if current_text and current_text != last_message:
                    last_message = current_text

                    print(f"\n📨 הודעה חדשה זוהתה: {current_text[:50]}...")

                    # ניתוח AI
                    result = analyzer.analyze_with_context(current_text, "WhatsApp User")

                    # הצגת תוצאות
                    print(f"   רמת סיכון: {result['risk_level']}%")
                    print(f"   קטגוריה: {result['category']}")
                    print(f"   נימוק: {result['reason']}")

                    # עדכון ה-GUI דרך הפונקציה שקיבלנו מה-main
                    if ui_callback:
                        try:
                            ui_callback(current_text, result['risk_level'], result['category'])
                        except Exception as e:
                            print(f"⚠️ שגיאה ב-callback: {e}")

                    # שליחת מייל במקרה של סיכון גבוה
                    if result['risk_level'] >= 60:
                        try:
                            sent = notifier.send_alert("WhatsApp User", current_text, result, parent_email)
                            if sent:
                                print(f"   ✅ התראה נשלחה למייל: {parent_email}")
                        except Exception as e:
                            print(f"⚠️ שגיאה בשליחת מייל: {e}")

        except NoSuchElementException:
            # אם לא מצאנו אלמנטים, זה נורמלי - WhatsApp עדיין לא טעון או שאין הודעות
            pass

        except WebDriverException as e:
            error_count += 1
            print(f"⚠️ שגיאת דפדפן ({error_count}/{max_errors}): {e}")

            if error_count >= max_errors:
                print("❌ יותר מדי שגיאות - מפסיק סריקה")
                break

            # המתנה ארוכה יותר לפני ניסיון חוזר
            time.sleep(5)
            continue

        except Exception as e:
            error_count += 1
            print(f"⚠️ שגיאה כללית ({error_count}/{max_errors}): {e}")

            if error_count >= max_errors:
                print("❌ יותר מדי שגיאות - מפסיק סריקה")
                break

            time.sleep(5)
            continue

        # המתנה קצרה לפני הבדיקה הבאה
        time.sleep(2)

    # סגירה נקייה
    try:
        driver.quit()
        print("\n🛑 CyberGuard Web Bridge הופסק")
    except:
        pass