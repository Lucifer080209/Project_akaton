import os
from kivy.storage.jsonstore import JsonStore


class Config:
    """ניהול הגדרות מאובטח"""

    def __init__(self):
        self.store = JsonStore('user_settings.json')
        self.secure_store = JsonStore('secure_config.json')
        self._init_defaults()

    def _init_defaults(self):
        """יצירת הגדרות ברירת מחדל אם הן לא קיימות"""
        if not self.secure_store.exists('api_data'):
            self.secure_store.put('api_data', api_key='AIzaSyA0Jmp6_Slmima01zKVKtCyonmEKrDxFTU')

        if not self.secure_store.exists('smtp_data'):
            self.secure_store.put('smtp_data',
                                  email='omerniztzanim@gmail.com',
                                  password='doyn unkl izyv wvuz'
                                  )

    def get_api_key(self):
        """קבלת מפתח ה-API"""
        if self.secure_store.exists('api_data'):
            return self.secure_store.get('api_data').get('api_key', 'AIzaSyA0Jmp6_Slmima01zKVKtCyonmEKrDxFTU')
        return 'AIzaSyA0Jmp6_Slmima01zKVKtCyonmEKrDxFTU'

    def save_api_key(self, key):
        """שמירת מפתח API חדש"""
        self.secure_store.put('api_data', key=key)

    def get_smtp_config(self):
        """קבלת הגדרות ה-SMTP"""
        if self.secure_store.exists('smtp_data'):
            return self.secure_store.get('smtp_data')
        return {'email': 'omerniztzanim@gmail.com', 'password': 'doyn unkl izyv wvuz'}

    def save_smtp_config(self, email, password):
        """שמירת הגדרות ה-SMTP"""
        self.secure_store.put('smtp_data', email=email, password=password)

    def get_parent_email(self):
        """קבלת מייל ההורה"""
        if self.store.exists('user'):
            return self.store.get('user').get('email')
        return None

    def save_parent_email(self, email):
        """שמירת מייל ההורה"""
        self.store.put('user', email=email)

    def is_first_run(self):
        """בדיקה אם זו הפעלה ראשונה"""
        return not self.store.exists('consent')

    def mark_consent_given(self):
        """סימון שהמשתמש אישר את תנאי השימוש"""
        import time
        self.store.put('consent', given=True, timestamp=time.time())