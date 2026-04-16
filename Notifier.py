import smtplib
from email.message import EmailMessage
import time


class AlertSystem:
    """מערכת שליחת התראות במייל"""

    def __init__(self, smtp_config):
        self.sender_email = smtp_config['email']
        self.sender_password = smtp_config['password']
        self.alert_cooldown = {}  # מניעת שליחת אותה התראה שוב ושוב

    def send_alert(self, sender, text, analysis_result, receiver_email):
        """
        שליחת התראה במייל (רק אם רמת הסיכון גבוהה מספיק)

        Args:
            sender: שם השולח
            text: תוכן ההודעה
            analysis_result: תוצאת הניתוח מה-AI
            receiver_email: מייל ההורה

        Returns:
            bool: האם ההתראה נשלחה בהצלחה
        """

        risk_level = analysis_result.get('risk_level', 0)
        category = analysis_result.get('category', 'unknown')
        reason = analysis_result.get('reason', '')
        keywords = analysis_result.get('keywords', [])

        # שליחה רק אם רמת הסיכון 60% ומעלה
        if risk_level < 60:
            print(f"ℹ️ Risk too low ({risk_level}%), not sending alert")
            return False

        # מניעת שליחת אותה התראה בתוך 5 דקות
        cache_key = f"{sender}:{text[:30]}"
        current_time = time.time()

        if cache_key in self.alert_cooldown:
            time_since_last = current_time - self.alert_cooldown[cache_key]
            if time_since_last < 300:  # 5 דקות
                print(f"⏳ Alert cooldown active ({int(300 - time_since_last)}s remaining)")
                return False

        # בחירת אימוג'י לפי רמת חומרה
        if risk_level >= 90:
            emoji = "🚨"
            severity = "CRITICAL"
        elif risk_level >= 75:
            emoji = "⚠️"
            severity = "HIGH"
        else:
            emoji = "⚡"
            severity = "MODERATE"

        # בניית תוכן המייל
        msg = EmailMessage()

        keywords_str = ", ".join(keywords) if keywords else "None detected"

        msg.set_content(f"""
Hello,

{emoji} CyberGuard Alert: {severity} Risk Detected

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 Sender: {sender}
💬 Message Content: "{text}"

📊 Risk Level: {risk_level}%
🏷️ Category: {category.upper()}
💡 Reason: {reason}
🔑 Keywords: {keywords_str}

⏰ Time: {time.strftime('%d/%m/%Y at %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Recommendation: We suggest discussing this conversation with your child to understand the context.

--
CyberGuard PRO System
Smart Child Protection
        """)

        msg['Subject'] = f"{emoji} CyberGuard - {severity}: {category.upper()}"
        msg['From'] = self.sender_email
        msg['To'] = receiver_email

        # שליחת המייל
        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(self.sender_email, self.sender_password)
                smtp.send_message(msg)

            # עדכון cooldown
            self.alert_cooldown[cache_key] = current_time

            print(f"✓ Alert sent successfully to {receiver_email}")
            print(f"  Sender: {sender}, Risk: {risk_level}%, Category: {category}")
            return True

        except smtplib.SMTPAuthenticationError:
            print("✗ Email authentication failed - check credentials")
            return False
        except smtplib.SMTPException as e:
            print(f"✗ SMTP error: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error sending email: {e}")
            return False