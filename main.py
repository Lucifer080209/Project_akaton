import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from datetime import datetime
import os
import json
from config import Config


# --- הגדרות צבעים (מבוסס על הקוד המקורי שלך) ---
def hex_color(rgb_tuple):
    """המרה מצבעי Kivy (0-1) לצבעי Hex"""
    r, g, b = rgb_tuple[:3]
    return f'#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}'


BG_DEEP = hex_color((0.059, 0.067, 0.090, 1))  # #0f1117
BG_CARD = hex_color((0.086, 0.106, 0.153, 1))  # #161b27
BG_INPUT = hex_color((0.059, 0.067, 0.090, 1))  # #0f1117
BG_STATUS = hex_color((0.051, 0.122, 0.208, 1))  # #0d1f35
BORDER = hex_color((0.165, 0.176, 0.227, 1))  # #2a2d3a
BLUE = hex_color((0.290, 0.620, 1.000, 1))  # #4a9eff
GREEN = hex_color((0.290, 0.929, 0.502, 1))  # #4ade80
RED = hex_color((0.973, 0.431, 0.431, 1))  # #f87171
YELLOW = hex_color((0.984, 0.749, 0.145, 1))  # #fbbf24
TEXT_PRI = hex_color((0.910, 0.918, 0.941, 1))  # #e8eaf0
TEXT_SEC = hex_color((0.612, 0.635, 0.627, 1))  # #9ca3af
TEXT_MUTED = hex_color((0.420, 0.447, 0.502, 1))  # #6b7280


class CyberGuardApp:
    def __init__(self):
        self.results_file = 'detection_results.json'
        self._ensure_results_file()

        self.root = tk.Tk()
        self.root.title("CyberGuard - Smart Child Protection")
        self.root.geometry("900x700")
        self.root.configure(bg=BG_DEEP)

        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.config = Config()
        self.last_msg_time = ""
        self.running = True

        self._build_ui()

        # הפעלת לופ עדכון התצוגה
        self._update_display()

    def _ensure_results_file(self):
        """יוצר קובץ נתונים התחלתי אם לא קיים"""
        if not os.path.exists(self.results_file):
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump({"stats": {"safe": 0, "alerts": 0, "emails_sent": 0}, "latest": {}}, f)

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────
        header_frame = tk.Frame(self.root, bg=BG_CARD, height=70)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        header_frame.pack_propagate(False)

        logo_frame = tk.Frame(header_frame, bg=BLUE, width=42, height=42)
        logo_frame.place(x=20, y=14)

        tk.Label(header_frame, text="CyberGuard", font=("Arial", 18, "bold"), fg=TEXT_PRI, bg=BG_CARD).place(x=75, y=12)
        tk.Label(header_frame, text="Smart Child Protection | Monitoring Active", font=("Arial", 11), fg=TEXT_MUTED,
                 bg=BG_CARD).place(x=75, y=38)

        # ── Status Bar ──────────────────────────────────────────
        status_frame = tk.Frame(self.root, bg=BG_STATUS, height=36)
        status_frame.pack(fill=tk.X, padx=0, pady=0)
        status_frame.pack_propagate(False)

        self.status_label = tk.Label(status_frame, text="● SYSTEM LIVE", font=("Arial", 10, "bold"), fg=GREEN,
                                     bg=BG_STATUS)
        self.status_label.pack(side=tk.LEFT, padx=20, pady=8)

        self.time_label = tk.Label(status_frame, text="", font=("Arial", 10), fg=TEXT_SEC, bg=BG_STATUS)
        self.time_label.pack(side=tk.RIGHT, padx=20, pady=8)

        # ── Main Content ────────────────────────────────────────
        content_frame = tk.Frame(self.root, bg=BG_DEEP)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)

        # ── Statistics ──────────────────────────────────────────
        stats_frame = tk.Frame(content_frame, bg=BG_CARD, bd=1, highlightbackground=BORDER, highlightthickness=1)
        stats_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        tk.Label(stats_frame, text="📊 Live Statistics", font=("Arial", 14, "bold"), fg=TEXT_PRI, bg=BG_CARD).pack(
            anchor=tk.W, padx=15, pady=(12, 8))

        stats_grid = tk.Frame(stats_frame, bg=BG_CARD)
        stats_grid.pack(fill=tk.X, padx=15, pady=(0, 12))
        for i in range(4): stats_grid.columnconfigure(i, weight=1)

        self.stat_widgets = {}
        s_data = [("safe", "✓ Safe Messages", GREEN, 0),
                  ("alerts", "⚠ Alerts Triggered", YELLOW, 0),
                  ("emails", "📧 Emails Sent", BLUE, 0),
                  ("accuracy", "🎯 Accuracy", GREEN, "-")]

        for idx, (key, label, color, default) in enumerate(s_data):
            f = tk.Frame(stats_grid, bg=BG_CARD)
            f.grid(row=0, column=idx)
            val = tk.Label(f, text=str(default), font=("Arial", 24, "bold"), fg=color, bg=BG_CARD)
            val.pack()
            tk.Label(f, text=label, font=("Arial", 9), fg=TEXT_MUTED, bg=BG_CARD).pack()
            self.stat_widgets[key] = val

        # ── Recent Alerts ──────────────────────────────────────
        alerts_frame = tk.Frame(content_frame, bg=BG_CARD, bd=1, highlightbackground=BORDER, highlightthickness=1)
        alerts_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 15))

        tk.Label(alerts_frame, text="🔔 Recent Alerts", font=("Arial", 14, "bold"), fg=TEXT_PRI, bg=BG_CARD).pack(
            anchor=tk.W, padx=15, pady=(12, 8))
        self.alerts_text = scrolledtext.ScrolledText(alerts_frame, font=("Arial", 10), fg=TEXT_PRI, bg=BG_INPUT,
                                                     relief=tk.FLAT, height=12)
        self.alerts_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 12))
        self.alerts_text.tag_config("high_risk", foreground=RED)

        # ── Settings ──────────────────────────────────────────────
        settings_frame = tk.Frame(content_frame, bg=BG_CARD, bd=1, highlightbackground=BORDER, highlightthickness=1)
        settings_frame.grid(row=1, column=1, sticky="nsew", pady=(0, 15))

        tk.Label(settings_frame, text="⚙ Settings", font=("Arial", 14, "bold"), fg=TEXT_PRI, bg=BG_CARD).pack(
            anchor=tk.W, padx=15, pady=(12, 8))
        tk.Label(settings_frame, text="Parent Email Address:", font=("Arial", 11), fg=TEXT_SEC, bg=BG_CARD).pack(
            anchor=tk.W, padx=15, pady=(10, 5))

        self.email_entry = tk.Entry(settings_frame, font=("Arial", 11), fg=TEXT_PRI, bg=BG_INPUT, insertbackground=BLUE,
                                    relief=tk.FLAT)
        self.email_entry.insert(0, self.config.get_parent_email() or "")
        self.email_entry.pack(fill=tk.X, padx=15, pady=(0, 10), ipady=8)

        tk.Button(settings_frame, text="SAVE SETTINGS", font=("Arial", 11, "bold"), fg=TEXT_PRI, bg=BLUE,
                  relief=tk.FLAT, command=self._save_email, cursor="hand2").pack(fill=tk.X, padx=15, pady=(0, 10))

        self.save_feedback = tk.Label(settings_frame, text="", font=("Arial", 10), fg=GREEN, bg=BG_CARD)
        self.save_feedback.pack(anchor=tk.W, padx=15)

        # ── Log Console ─────────────────────────────────────────
        console_frame = tk.Frame(content_frame, bg=BG_CARD, bd=1, highlightbackground=BORDER, highlightthickness=1)
        console_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")

        tk.Label(console_frame, text="📝 System Log", font=("Arial", 14, "bold"), fg=TEXT_PRI, bg=BG_CARD).pack(
            anchor=tk.W, padx=15, pady=(12, 8))
        self.console_text = scrolledtext.ScrolledText(console_frame, font=("Courier", 9), fg=TEXT_SEC, bg=BG_INPUT,
                                                      relief=tk.FLAT, height=8)
        self.console_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 12))

        content_frame.rowconfigure(1, weight=1)
        content_frame.rowconfigure(2, weight=1)
        self._log("🚀 CyberGuard UI started. Connection to service active.")

    def _save_email(self):
        email = self.email_entry.get().strip()
        if '@' in email:
            self.config.save_parent_email(email)
            self.save_feedback.config(text="✓ Email saved", fg=GREEN)
            self._log(f"✓ Email updated: {email}")
            self.root.after(2000, lambda: self.save_feedback.config(text=""))
        else:
            self.save_feedback.config(text="✗ Invalid email", fg=RED)

    def _log(self, message):
        self.console_text.config(state=tk.NORMAL)
        self.console_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.console_text.see(tk.END)
        self.console_text.config(state=tk.DISABLED)

    def _update_display(self):
        """פונקציה שרצה כל שנייה ומעדכנת את המסך מהקובץ JSON"""
        self.time_label.config(text=datetime.now().strftime("%H:%M:%S"))

        try:
            if os.path.exists(self.results_file):
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # עדכון סטטיסטיקה
                if 'stats' in data:
                    s = data['stats'].get('safe', 0)
                    a = data['stats'].get('alerts', 0)
                    e = data['stats'].get('emails_sent', 0)

                    self.stat_widgets['safe'].config(text=str(s))
                    self.stat_widgets['alerts'].config(text=str(a))
                    self.stat_widgets['emails'].config(text=str(e))

                    total = s + a
                    if total > 0:
                        acc = f"{int((s / total) * 100)}%"
                    else:
                        acc = "-"
                    self.stat_widgets['accuracy'].config(text=acc)

                # עדכון הודעה אחרונה ביומן ההתראות
                if 'latest' in data and data['latest']:
                    lt = data['latest']
                    current_ts = lt.get('timestamp')

                    if current_ts != self.last_msg_time:
                        self.last_msg_time = current_ts
                        msg_text = lt.get('text', '')
                        risk = lt.get('risk_level', 0)

                        self._log(f"📨 New Processed Message: {msg_text[:30]}...")

                        if risk >= 60:
                            self.alerts_text.config(state=tk.NORMAL)
                            self.alerts_text.insert(tk.END,
                                                    f"[{datetime.now().strftime('%H:%M')}] 🚨 ALERT ({risk}%): {msg_text}\n",
                                                    "high_risk")
                            self.alerts_text.see(tk.END)
                            self.alerts_text.config(state=tk.DISABLED)
        except Exception as e:
            pass

        # קריאה חוזרת לפונקציה בעוד 1000 מילישניות (שנייה אחת)
        self.root.after(1000, self._update_display)

    def run(self):
        self.root.mainloop()

    def _on_closing(self):
        self.root.destroy()


if __name__ == '__main__':
    app = CyberGuardApp()
    app.run()
