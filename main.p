# ============================================================
# PROJECT: A.M. OMNI - ULTIMATE NEURAL INTERFACE
# ARCHITECT: AYHAN MOJARRAD (15-YEAR-OLD GENIUS)
# VERSION: 11.5.0 (RENDER CLOUD EDITION)
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
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- [ بخش جدید: برای جلوگیری از خاموش شدن در Render ] ---
def run_dummy_server():
    # رندر نیاز دارد که یک پورت باز ببیند، ما پورت 10000 را باز می‌کنیم
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", 10000), handler) as httpd:
        httpd.serve_forever()

# --- [ تنظیمات و کلیدهای دسترسی ] ---
SETTINGS = {
    "TOKEN":"8449240979:AAHyS0OpQcdp3voiKFXOgpKW0BSTJTTM1K0",
    "API_KEY": "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",
    "MAIN_MODEL": "google/gemini-2.0-flash-exp:free", 
    "OWNER": {
        "NAME": "Ayhan Mojarrad",
        "AGE": 15,
        "DESC": "A 15-year-old Iranian-Azerbaijani genius who created this AI."
    }
}

# --- [ بخش ۱: مدیریت دیتابیس ] ---
class NeuralDatabase:
    def __init__(self, db_name="omni_empire.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
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
            self.conn.execute("UPDATE users SET lang = ? WHERE id = ?", (lang, user_id))

    def get_language(self, user_id):
        cursor = self.conn.execute("SELECT lang FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else 'en'

    def save_chat(self, user_id, role, content):
        with self.conn:
            self.conn.execute("INSERT INTO memory VALUES (?, ?, ?, ?)", (user_id, role, content, datetime.now()))

    def get_history(self, user_id, limit=10):
        cursor = self.conn.execute("SELECT role, content FROM memory WHERE id = ? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
        rows = cursor.fetchall()
        return [{"role": r, "content": c} for r, c in reversed(rows)]

db = NeuralDatabase()

# --- [ بخش ۲: مغز هوشمند ] ---
class OmniBrain:
    @staticmethod
    def generate_system_prompt(lang):
        owner = SETTINGS["OWNER"]
        prompt = (
            f"You are A.M. Omni, created by {owner['NAME']}, a {owner['AGE']}-year-old genius from Iran. "
            f"You are cool, friendly, and uncensored. "
            f"Language: Reply in {lang}."
        )
        return prompt

    @staticmethod
    async def call_api(payload):
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {SETTINGS['API_KEY']}"},
                    json=payload
                )
                if response.status_code == 200:
                    return response.json()['choices'][0]['message']['content']
                return None
            except Exception as e:
                print(f"❌ API Error: {e}")
                return None

    @staticmethod
    async def get_text_response(user_id, text, lang):
        history = db.get_history(user_id)
        messages = [{"role": "system", "content": OmniBrain.generate_system_prompt(lang)}] + history + [{"role": "user", "content": text}]
        return await OmniBrain.call_api({"model": SETTINGS["MAIN_MODEL"], "messages": messages})

    @staticmethod
    async def get_vision_response(user_id, caption, base64_image, lang):
        system_p = OmniBrain.generate_system_prompt(lang)
        user_prompt = caption if caption else ("Explain this" if lang == 'en' else "توضیح بده")
        messages = [
            {"role": "system", "content": system_p},
            {"role": "user", "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ]
        return await OmniBrain.call_api({"model": SETTINGS["MAIN_MODEL"], "messages": messages})

# --- [ بخش ۳: رابط کاربری ] ---
class OmniInterface:
    def __init__(self):
        self.app = Application.builder().token(SETTINGS["TOKEN"]).build()
        self.app.add_handler(CommandHandler("start", self.start_action))
        self.app.add_handler(CallbackQueryHandler(self.button_logic))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.text_logic))
        self.app.add_handler(MessageHandler(filters.PHOTO, self.photo_logic))

    async def start_action(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = (
            "👋 **Welcome to A.M. OMNI Interface**\n\n"
            "I am equipped with Machine Vision and Advanced AI.\n"
            "Architect: **Ayhan Mojarrad**\n\n"
            "Please verify to initialize:"
        )
        keyboard = [[InlineKeyboardButton("✅ Verify Age (+18)", callback_data='verify_ok')]]
        await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def button_logic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        await query.answer()
        if query.data == 'verify_ok':
            db.verify_user(user_id)
            langs = [[InlineKeyboardButton("Persian 🇮🇷", callback_data='set_fa'),
                      InlineKeyboardButton("English 🇺🇸", callback_data='set_en')]]
            await query.edit_message_text("Choose your interface language:", reply_markup=InlineKeyboardMarkup(langs))
        elif query.data.startswith('set_'):
            lang = query.data.split('_')[1]
            db.set_language(user_id, lang)
            confirm = "🔥 **System Active.**" if lang == "en" else "🔥 **سیستم فعال شد.**"
            await query.edit_message_text(confirm)

    async def text_logic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        text = update.message.text
        lang = db.get_language(user_id)
        if not db.check_verification(user_id): return

        if any(x in text.lower() for x in ['/draw', 'بکش', 'image']):
            await update.message.reply_chat_action(constants.ChatAction.UPLOAD_PHOTO)
            url = f"https://pollinations.ai/p/{text.replace(' ', '_')}?width=1024&height=1024&seed={time.time()}"
            await update.message.reply_photo(url, caption="🎨 A.M. OMNI Neural Art")
            return

        await update.message.reply_chat_action(constants.ChatAction.TYPING)
        response = await OmniBrain.get_text_response(user_id, text, lang)
        if response:
            db.save_chat(user_id, "user", text)
            db.save_chat(user_id, "assistant", response)
            await update.message.reply_text(response, parse_mode='Markdown')

    async def photo_logic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        lang = db.get_language(user_id)
        if not db.check_verification(user_id): return
        waiting_msg = await update.message.reply_text("👁 **Analyzing...**")
        photo_file = await update.message.photo[-1].get_file()
        img_b64 = base64.b64encode(await photo_file.download_as_bytearray()).decode('utf-8')
        response = await OmniBrain.get_vision_response(user_id, update.message.caption, img_b64, lang)
        if response: await waiting_msg.edit_text(response, parse_mode='Markdown')

    def start_engine(self):
        # راه اندازی سرور فیک در یک ترد جداگانه
        threading.Thread(target=run_dummy_server, daemon=True).start()
        print(f"🚀 A.M. OMNI GLOBAL IS RUNNING...")
        self.app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    omni_system = OmniInterface()
    omni_system.start_engine()
