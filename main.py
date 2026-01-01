# ============================================================
# PROJECT: A.M. OMNI - ULTIMATE NEURAL INTERFACE
# ARCHITECT: AYHAN MOJARRAD (15-YEAR-OLD GENIUS)
# VERSION: 12.0.0 (RENDER OPTIMIZED)
# ============================================================

import logging
import sqlite3
import httpx 
import base64
import json
import time
import threading
import http.server
import socketserver
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- [ بخش حیاتی: سرور برای خوشحال نگه داشتن رندر ] ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"A.M. OMNI IS ALIVE AND RUNNING!")
            
    try:
        with socketserver.TCPServer(("", port), HealthCheckHandler) as httpd:
            print(f"📡 Health check server started on port {port}")
            httpd.serve_forever()
    except Exception as e:
        print(f"⚠️ Server error: {e}")

# --- [ تنظیمات ] ---
SETTINGS = {
    "TOKEN": "8243698179:AAF5dnygT59WJm_XhSDhWijikmbA1Rqjx3I",
    "API_KEY": "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",
    "MAIN_MODEL": "google/gemini-2.0-flash-exp:free", 
    "OWNER": {
        "NAME": "Ayhan Mojarrad",
        "AGE": 15,
        "DESC": "A 15-year-old Iranian-Azerbaijani genius who created this AI."
    }
}

# --- [ مدیریت دیتابیس (بهینه شده برای رندر) ] ---
class NeuralDatabase:
    def __init__(self):
        # استفاده از :memory: برای جلوگیری از ارور نوشتن روی دیسک در رندر
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._build_infrastructure()

    def _build_infrastructure(self):
        with self.conn:
            self.conn.execute('''CREATE TABLE IF NOT EXISTS users 
                                (id INTEGER PRIMARY KEY, verified INTEGER DEFAULT 0, lang TEXT DEFAULT 'en')''')
            self.conn.execute('''CREATE TABLE IF NOT EXISTS memory 
                                (id INTEGER, role TEXT, content TEXT, timestamp DATETIME)''')

    def verify_user(self, user_id):
        with self.conn:
            self.conn.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
            self.conn.execute("UPDATE users SET verified = 1 WHERE id = ?", (user_id,))

    def check_verification(self, user_id):
        cursor = self.conn.execute("SELECT verified FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return row and row[0] == 1

    def set_language(self, user_id, lang):
        with self.conn:
            self.conn.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
            self.conn.execute("UPDATE users SET lang = ? WHERE id = ?", (lang, user_id))

    def get_language(self, user_id):
        cursor = self.conn.execute("SELECT lang FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else 'en'

    def save_chat(self, user_id, role, content):
        with self.conn:
            self.conn.execute("INSERT INTO memory VALUES (?, ?, ?, ?)", (user_id, role, content, datetime.now()))

    def get_history(self, user_id, limit=6):
        cursor = self.conn.execute("SELECT role, content FROM memory WHERE id = ? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
        rows = cursor.fetchall()
        return [{"role": r, "content": c} for r, c in reversed(rows)]

db = NeuralDatabase()

# --- [ مغز هوشمند ] ---
class OmniBrain:
    @staticmethod
    def generate_system_prompt(lang):
        owner = SETTINGS["OWNER"]
        return f"You are A.M. Omni, created by {owner['NAME']}, a {owner['AGE']}-year-old genius. Language: {lang}."

    @staticmethod
    async def call_api(payload):
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                res = await client.post("https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {SETTINGS['API_KEY']}"}, json=payload)
                return res.json()['choices'][0]['message']['content']
            except: return None

# --- [ رابط کاربری ] ---
class OmniInterface:
    def __init__(self):
        self.app = Application.builder().token(SETTINGS["TOKEN"]).build()
        self.app.add_handler(CommandHandler("start", self.start_action))
        self.app.add_handler(CallbackQueryHandler(self.button_logic))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_logic))
        self.app.add_handler(MessageHandler(filters.PHOTO, self.photo_logic))

    async def start_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[InlineKeyboardButton("✅ Verify Age (+18)", callback_data='verify_ok')]]
        await update.message.reply_text("👋 **Welcome to A.M. OMNI**\nArchitect: **Ayhan Mojarrad**", 
                                       reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def button_logic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.data == 'verify_ok':
            langs = [[InlineKeyboardButton("Persian 🇮🇷", callback_data='set_fa'),
                      InlineKeyboardButton("English 🇺🇸", callback_data='set_en')]]
            await query.edit_message_text("Language:", reply_markup=InlineKeyboardMarkup(langs))
        elif query.data.startswith('set_'):
            lang = query.data.split('_')[1]
            db.set_language(query.from_user.id, lang)
            await query.edit_message_text("🔥 System Active.")

    async def text_logic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not db.check_verification(user_id): return
        await update.message.reply_chat_action(constants.ChatAction.TYPING)
        lang = db.get_language(user_id)
        
        # بخش نقاشی
        if any(x in update.message.text.lower() for x in ['/draw', 'بکش', 'image']):
            url = f"https://pollinations.ai/p/{update.message.text.replace(' ', '_')}?width=1024&height=1024&seed={time.time()}"
            await update.message.reply_photo(url, caption="🎨 A.M. OMNI Neural Art")
            return

        response = await OmniBrain.get_text_response(user_id, update.message.text, lang)
        if response:
            db.save_chat(user_id, "user", update.message.text)
            db.save_chat(user_id, "assistant", response)
            await update.message.reply_text(response, parse_mode='Markdown')

    async def photo_logic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # بخش پردازش تصویر (بماند برای هوش مصنوعی)
        await update.message.reply_text("👁 Vision processing is active.")

    def start_engine(self):
        threading.Thread(target=run_dummy_server, daemon=True).start()
        print("🚀 A.M. OMNI IS LIVE!")
        # بسیار مهم برای رندر: drop_pending_updates باعث میشه Conflict حل بشه
        self.app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    OmniInterface().start_engine()
