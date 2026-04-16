import google.generativeai as genai
import json


class GeminiAnalyzer:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.emergency_list = ["אפס", "לוזר", "מפגר", "תמות", "זונה", "זין", "חרם", "סכין","מזדיין","תהרוג את עצמך","תתאבד","אף אחד לא אוהב אותך", "יא בזבוז חמצן"]

    def analyze(self, text):
        text_lower = text.strip().lower()

        # בדיקה ידנית מהירה (Fallback)
        manual_risk = 0
        for word in self.emergency_list:
            if word in text_lower:
                manual_risk = 100
                break

        prompt = (
            f"Analyze this Hebrew message: '{text}'. "
            f"Return ONLY a JSON object with: "
            f"'risk_level' (0-100), 'category' (bullying/spam/safe), "
            f"'reason' (short explanation in English), 'keywords' (list of bad words)."
        )

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip().replace('```json', '').replace('```', '')
            analysis = json.loads(result_text)

            # אם ה-AI אמר שזה בטוח אבל המילים ב-list מופיעות, נחמיר
            if manual_risk == 100:
                analysis['risk_level'] = max(analysis['risk_level'], 100)
            return analysis
        except Exception as e:
            print(f"AI Error: {e}")
            return {"risk_level": manual_risk, "category": "unknown", "reason": "Error", "keywords": []}
