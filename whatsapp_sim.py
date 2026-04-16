import tkinter as tk
from tkinter import scrolledtext
import os


class WhatsAppSimulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WhatsApp Simulator (Debug Tool)")
        self.root.geometry("400x500")
        self.root.configure(bg="#e5ddd5")  # צבע הרקע של וואטסאפ

        self._build_ui()

    def _build_ui(self):
        # כותרת
        header = tk.Frame(self.root, bg="#075e54", height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="Simulation - WhatsApp User", fg="white", bg="#075e54",
                 font=("Arial", 12, "bold")).pady = 20
        tk.Label(header, text="Simulation - WhatsApp User", fg="white", bg="#075e54", font=("Arial", 12, "bold")).pack(
            pady=15)

        # אזור תצוגת ההודעות
        self.chat_display = scrolledtext.ScrolledText(self.root, state='disabled', bg="#e5ddd5", font=("Arial", 10))
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # אזור כתיבת הודעה
        input_frame = tk.Frame(self.root, bg="#f0f0f0")
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.msg_entry = tk.Entry(input_frame, font=("Arial", 12), relief=tk.FLAT)
        self.msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        self.msg_entry.bind("<Return>", lambda e: self.send_message())

        send_btn = tk.Button(input_frame, text="שלח", bg="#25d366", fg="white", font=("Arial", 10, "bold"),
                             command=self.send_message, relief=tk.FLAT, padx=15)
        send_btn.pack(side=tk.RIGHT, padx=10, pady=10)

    def send_message(self):
        message = self.msg_entry.get().strip()
        if not message:
            return

        # 1. הצגה בסימולטור
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"אתה: {message}\n", "user")
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

        # 2. כתיבה לקובץ בפורמט שה-Service שלך מכיר (שם|||טקסט)
        try:
            with open("new_message.txt", "w", encoding="utf-8") as f:
                f.write(f"WhatsApp User|||{message}")
            print(f"✅ הודעה נשלחה לסימולציה: {message}")
        except Exception as e:
            print(f"❌ שגיאה בכתיבת קובץ: {e}")

        self.msg_entry.delete(0, tk.END)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = WhatsAppSimulator()
    app.run()