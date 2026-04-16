import warnings
import json
from google import genai
from google.genai import types

warnings.filterwarnings("ignore")


class GeminiAnalyzer:
    """ניתוח הודעות עם Gemini AI + Fallback מקומי"""

    def __init__(self, api_key):
        try:
            self.client = genai.Client(api_key=api_key)
            self.model_id = "gemini-2.0-flash-exp"
            print("✓ Gemini AI initialized")
        except Exception as e:
            print(f"⚠️ Gemini AI failed to initialize: {e}")
            self.client = None

        self.conversation_cache = {}

        # רשימות מילים למצב חירום
        self.high_risk_words = [
            "לוזר", "מפגר", "תמות", "זונה", "זין", "מטומטם",
            "בוא נפגש", "שלח תמונה", "תמונה שלך", "כמה את שוקלת",
            "תראי לי", "בואי נדבר", "אל תספרי לאף אחד"
        ]

        self.medium_risk_words = [
            "אפס", "חרם", "תחנק", "מסכן", "פתטי", "דפוק",
            "מוזר", "נחשל", "טמבל"
        ]

    def analyze_with_context(self, current_msg, sender_id):
        """
        ניתוח הודעה עם הקשר שיחה

        Args:
            current_msg: תוכן ההודעה
            sender_id: מזהה השולח (לשמירת היסטוריה)

        Returns:
            dict: {
                "risk_level": 0-100,
                "category": "safe/suspicious/bullying/grooming",
                "reason": "הסבר בעברית",
                "keywords": ["מילה1", "מילה2"]
            }
        """

        # עדכון היסטוריית שיחה
        if sender_id not in self.conversation_cache:
            self.conversation_cache[sender_id] = []

        self.conversation_cache[sender_id].append(current_msg)
        recent_history = self.conversation_cache[sender_id][-5:]  # 5 הודעות אחרונות

        # ניסיון ניתוח עם AI
        if self.client:
            try:
                return self._analyze_with_ai(current_msg, recent_history)
            except Exception as e:
                print(f"⚠️ AI analysis failed: {e}, using fallback")

        # Fallback - בדיקה מקומית
        return self._emergency_check(current_msg)

    def _analyze_with_ai(self, current_msg, history):
        """ניתוח עם Gemini AI"""

        prompt = f"""נתח את ההודעה הבאה בעברית לזיהוי סכנות לילדים.
החזר JSON בלבד בפורמט הבא (ללא markdown, ללא טקסט נוסף):
{{
  "risk_level": <מספר בין 0 ל-100>,
  "category": "<safe או suspicious או bullying או grooming>",
  "reason": "<הסבר קצר בעברית למה זה מסוכן או בטוח>",
  "keywords": ["מילת מפתח1", "מילת מפתח2"]
}}

קטגוריות:
- safe: הודעה רגילה וחפה מפשע
- suspicious: משהו חשוד שדורש תשומת לב
- bullying: חרם, השפלה, איומים, קללות
- grooming: ניסיון פדופילי, בקשה למפגש או תמונות אינטימיות

היסטוריית שיחה אחרונה: {history}
הודעה נוכחית לניתוח: "{current_msg}"

דוגמאות:
- "מה קורה?" → safe, 0%
- "לוזר אף אחד לא אוהב אותך" → bullying, 95%
- "בוא נפגש בסוד" → grooming, 100%
"""

        response = self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json",
                safety_settings=[
                    types.SafetySetting(
                        category="HARM_CATEGORY_HARASSMENT",
                        threshold="BLOCK_NONE"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_HATE_SPEECH",
                        threshold="BLOCK_NONE"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        threshold="BLOCK_NONE"
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_DANGEROUS_CONTENT",
                        threshold="BLOCK_NONE"
                    )
                ]
            )
        )

        result = json.loads(response.text)

        # וידוא שהתשובה תקינה
        if 'risk_level' not in result:
            result['risk_level'] = 0
        if 'category' not in result:
            result['category'] = 'safe'
        if 'reason' not in result:
            result['reason'] = ''
        if 'keywords' not in result:
            result['keywords'] = []

        return result

    def _emergency_check(self, text):
        """בדיקת חירום ללא AI - רשימת מילים"""

        text_lower = text.lower()
        found_keywords = []

        # בדיקת מילים בסיכון גבוה
        for word in self.high_risk_words:
            if word in text_lower:
                found_keywords.append(word)
                return {
                    "risk_level": 100,
                    "category": "bullying",
                    "reason": f"זוהתה מילה מסוכנת: '{word}'",
                    "keywords": found_keywords
                }

        # בדיקת מילים בסיכון בינוני
        for word in self.medium_risk_words:
            if word in text_lower:
                found_keywords.append(word)
                return {
                    "risk_level": 65,
                    "category": "suspicious",
                    "reason": f"זוהתה מילה חשודה: '{word}'",
                    "keywords": found_keywords
                }

        # הודעה בטוחה
        return {
            "risk_level": 0,
            "category": "safe",
            "reason": "לא זוהו מילים מסוכנות",
            "keywords": []
        }