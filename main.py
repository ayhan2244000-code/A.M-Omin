import asyncio
import os
import json
import random
import glob
import logging
from datetime import datetime
from threading import Thread
from flask import Flask
from pyrogram import Client, filters, enums
from pyrogram.errors import (SessionPasswordNeeded, PhoneCodeInvalid, 
                             PhoneCodeExpired, FloodWait, PeerIdInvalid)
from pyrogram.types import (InlineKeyboardMarkup, InlineKeyboardButton, 
                            InlineQueryResultArticle, InputTextMessageContent)

# ====================================================================
# ⚙️ CONFIGURATION
# ====================================================================
BOT_TOKEN = "8528881515:AAHiexL1Yw6ekaIOQo04HosVeXJZ0stPIBg"
# ====================================================================

# تنظیمات لاگینگ برای دیدن ارورها
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🌐 WEB SERVER (FLASK) FOR RENDER KEEP-ALIVE
app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "A.M Self Bot is Running Successfully! 🚀"

def run_web():
    # دریافت پورت از رندر یا استفاده از پورت پیش‌فرض
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host='0.0.0.0', port=port)

# 📂 DATABASE & FILE SETTINGS
DB_FILE = "am_settings.json"
SESSION_DIR = "sessions"

if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

def default_config():
    return {
        "self": True, "monshi": False, "smart_monshi": False,
        "monshi_text": "سلام. من در حال حاضر آنلاین نیستم. لطفا پیام بگذارید.",
        "poker": False, "bold": False, "underline": False, "code": False,
        "typing": False, "markread": False, "anti_delete": True,
        "sign": False, "sign_text": "A.M Self",
        "enemies": [], "friends": [], 
        "fosh_list": ["اسکل", "ببند", "سطح!", "نوب", "چاقال"],
        "love_list": ["عشقم", "جانم", "نفسم", "عزیزم"],
        "realm_id": None, "save_pv": False,
        "auto_name": False, "name_format": "A.M | Time",
        "auto_bio": False, "bio_format": "Active Self | Time"
    }

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

user_db = load_db()

def save_db():
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(user_db, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Save DB Error: {e}")

# 📘 HELP TEXT
HELP_TEXT = """
💎 **راهنمای جامع A.M Self** 💎
━━━━━━━━━━━━━━━━━━━━
⚡️ **مدیریت اصلی:**
`.self on/off` ➣ روشن/خاموش ربات
`.ping` ➣ تست سرعت
`.reload` ➣ ریلود

🤖 **منشی (Monshi):**
`.monshi on/off` ➣ روشن/خاموش منشی
`.setmonshi [متن]` ➣ تنظیم متن

🎭 **اکشن‌ها:**
`.poker on/off` ➣ پوکر مود (😐)
`.bold on/off` ➣ بولد نویس
`.typing on/off` ➣ تایپینگ دائم
`.markread on/off` ➣ سین زن خودکار

🛡 **امنیت:**
`.antidel on/off` ➣ آنتی‌دلیت
`.setrealm` ➣ تنظیم چت به عنوان مخزن
`.savepv on/off` ➣ بک‌آپ پی‌وی‌ها

👥 **افراد:**
`.bad` (ریپلای) ➣ افزودن دشمن
`.good` (ریپلای) ➣ افزودن دوست
`.del [تعداد]` ➣ پاکسازی پیام

👤 **پروفایل:**
`.name on/off` ➣ اسم زمان‌دار
`.bio on/off` ➣ بیو زمان‌دار

💡 کلمه **"پنل"** را ارسال کنید.
"""

# GLOBAL VARIABLES
login_state = {}
active_clients = {}

# MANAGER CLIENT
manager = Client("ManagerBot", bot_token=BOT_TOKEN, api_id=6, api_hash="eb06d4abfb49dc3eeb1aeb98ae0f581e")

# ====================================================================
# 🤖 MANAGER BOT LOGIC
# ====================================================================

@manager.on_message(filters.private & filters.command("start"))
async def start_handler(c, m):
    uid = str(m.from_user.id)
    if uid in active_clients:
        await m.reply("✅ **سلف‌بات شما فعال است!**\nدر هر چتی بنویسید `.ping` تا تست کنید.")
    else:
        login_state[uid] = {"step": "API_ID"}
        await m.reply(
            "👋 **به سلف‌بات امن A.M خوش آمدید!**\n\n"
            "لطفاً **API ID** خود را (عدد) بفرستید:\n"
            "(از my.telegram.org بگیرید)"
        )

@manager.on_message(filters.private & filters.text)
async def login_process(c, m):
    uid = str(m.from_user.id)
    text = m.text
    
    if uid not in login_state:
        # اگر کاربر پنل را با متن درخواست کرد
        if text == "پنل" and uid in user_db:
             pass # اینلاین هندل می‌کند
        return

    step = login_state[uid].get("step")
    data = login_state[uid]

    try:
        if step == "API_ID":
            if not text.isdigit(): return await m.reply("❌ API ID باید عدد باشد.")
            data["api_id"] = int(text)
            data["step"] = "API_HASH"
            await m.reply("✅ حالا **API HASH** را بفرستید:")

        elif step == "API_HASH":
            data["api_hash"] = text
            data["step"] = "PHONE"
            await m.reply("✅ حالا **شماره موبایل** را با کد کشور بفرستید:\nمثال: `+989123456789`")

        elif step == "PHONE":
            data["phone"] = text.replace(" ", "")
            msg = await m.reply("⏳ در حال اتصال به تلگرام...")
            
            session_path = os.path.join(SESSION_DIR, uid)
            new_app = Client(session_path, api_id=data["api_id"], api_hash=data["api_hash"])
            await new_app.connect()
            
            sent = await new_app.send_code(data["phone"])
            data["client"] = new_app
            data["phone_hash"] = sent.phone_code_hash
            data["step"] = "CODE"
            await msg.edit("✅ **کد تایید ارسال شد!**\nلطفاً کد ۵ رقمی را بفرستید (مثال: `12345`):")

        elif step == "CODE":
            code = text.replace(" ", "")
            client = data["client"]
            try:
                await client.sign_in(data["phone"], data["phone_hash"], code)
                await m.reply("🎉 **ورود موفقیت آمیز بود!**\nسلف‌بات روشن شد.")
                await setup_user_bot(client, uid)
                del login_state[uid]
            except SessionPasswordNeeded:
                data["step"] = "PASSWORD"
                await m.reply("🔐 اکانت **تایید دو مرحله‌ای** دارد. رمز را بفرستید:")
            except Exception as e:
                await m.reply(f"❌ خطا: {e}")

        elif step == "PASSWORD":
            client = data["client"]
            try:
                await client.check_password(text)
                await m.reply("🎉 **ورود موفق!**\nسلف‌بات روشن شد.")
                await setup_user_bot(client, uid)
                del login_state[uid]
            except Exception as e:
                await m.reply(f"❌ رمز اشتباه است: {e}")

    except Exception as e:
        await m.reply(f"❌ خطای سیستمی: {e}\nلطفا /start را بزنید.")
        if "client" in data:
            try: await data["client"].disconnect()
            except: pass
        del login_state[uid]

@manager.on_inline_query()
async def inline_panel(c, q):
    uid = str(q.from_user.id)
    if uid not in user_db:
        return await q.answer([InlineQueryResultArticle("لاگین نیستید", InputTextMessageContent("/start"))], cache_time=1)

    ud = user_db[uid]
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"سلف: {'✅' if ud['self'] else '❌'}", callback_data="tg_self"),
         InlineKeyboardButton(f"منشی: {'✅' if ud['monshi'] else '❌'}", callback_data="tg_monshi")],
        [InlineKeyboardButton(f"پوکر: {'✅' if ud['poker'] else '❌'}", callback_data="tg_poker"),
         InlineKeyboardButton(f"تایپینگ: {'✅' if ud['typing'] else '❌'}", callback_data="tg_typing")],
        [InlineKeyboardButton(f"بولد: {'✅' if ud['bold'] else '❌'}", callback_data="tg_bold"),
         InlineKeyboardButton("📘 راهنما", callback_data="help")]
    ])
    await q.answer([InlineQueryResultArticle("پنل مدیریت", InputTextMessageContent("⚡️ **پنل تنظیمات A.M Self**"), reply_markup=kb)], cache_time=1)

@manager.on_callback_query()
async def cb_handler(c, cb):
    uid = str(cb.from_user.id)
    if uid not in user_db: return await cb.answer("لطفا لاگین کنید!", show_alert=True)
    
    if cb.data == "help":
        await cb.answer("راهنما", show_alert=True)
        return await cb.edit_message_text(HELP_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))
    elif cb.data == "back":
        return await cb.edit_message_text("⚡️ **پنل تنظیمات:**", reply_markup=cb.message.reply_markup)

    key = cb.data.replace("tg_", "")
    if key in user_db[uid]:
        user_db[uid][key] = not user_db[uid][key]
        save_db()
        status = "روشن" if user_db[uid][key] else "خاموش"
        await cb.answer(f"{key}: {status}")
        await cb.edit_message_text(f"✅ تنظیمات ذخیره شد.\nوضعیت {key}: {status}\n(برای آپدیت دکمه‌ها دوباره پنل را باز کنید)")

# ====================================================================
# 🚀 USER CLIENT LOGIC (SELF BOT)
# ====================================================================

async def setup_user_bot(client: Client, uid: str):
    if uid not in user_db:
        user_db[uid] = default_config()
        save_db()
    
    active_clients[uid] = client

    @client.on_message(filters.me & filters.text)
    async def self_handler(c, m):
        ud = user_db[uid]
        txt = m.text
        
        # باز کردن پنل
        if txt == "پنل" or txt == "panel":
            await m.delete()
            try:
                bot = await manager.get_me()
                r = await c.get_inline_bot_results(bot.username)
                await c.send_inline_bot_result(m.chat.id, r.query_id, r.results[0].id)
            except: pass
            return

        # دستورات (.)
        if txt.startswith("."):
            try:
                parts = txt.split()
                cmd = parts[0].lower()
                args = txt.split(None, 1)[1] if len(parts) > 1 else ""
                reply = m.reply_to_message

                if cmd == ".ping":
                    s = datetime.now()
                    await m.edit("🚀")
                    e = datetime.now()
                    await m.edit(f"💎 **A.M Pong!** `{(e-s).microseconds/1000}ms`")
                elif cmd == ".self":
                    ud["self"] = (args == "on")
                    save_db()
                    await m.edit(f"Self: {ud['self']}")
                elif cmd == ".monshi":
                    ud["monshi"] = (args == "on")
                    save_db()
                    await m.edit(f"Monshi: {ud['monshi']}")
                elif cmd == ".setmonshi":
                    ud["monshi_text"] = args
                    save_db()
                    await m.edit("✅")
                elif cmd == ".poker":
                    ud["poker"] = (args == "on")
                    save_db()
                    await m.edit(f"Poker: {ud['poker']}")
                elif cmd == ".bold":
                    ud["bold"] = (args == "on")
                    save_db()
                    await m.edit(f"Bold: {ud['bold']}")
                elif cmd == ".bad" and reply:
                    tid = reply.from_user.id
                    if tid not in ud["enemies"]: ud["enemies"].append(tid)
                    save_db()
                    await m.edit("👺 Added to Enemies.")
                elif cmd == ".good" and reply:
                    tid = reply.from_user.id
                    if tid not in ud["friends"]: ud["friends"].append(tid)
                    save_db()
                    await m.edit("❤️ Added to Friends.")
                elif cmd == ".del":
                    await m.delete()
                    limit = int(args) if args.isdigit() else 10
                    async for msg in c.get_chat_history(m.chat.id, limit=limit):
                        if msg.from_user.id == c.me.id:
                            try: await msg.delete()
                            except: pass
                elif cmd == ".setrealm":
                    ud["realm_id"] = m.chat.id
                    save_db()
                    await m.edit(f"🛡 Realm ID: {m.chat.id}")
                elif cmd == ".savepv":
                    ud["save_pv"] = (args == "on")
                    save_db()
                    await m.edit(f"Save PV: {ud['save_pv']}")
                elif cmd == ".name":
                    ud["auto_name"] = (args == "on")
                    save_db()
                    await m.edit(f"Auto Name: {ud['auto_name']}")
                elif cmd == ".bio":
                    ud["auto_bio"] = (args == "on")
                    save_db()
                    await m.edit(f"Auto Bio: {ud['auto_bio']}")
            except Exception as e:
                print(f"CMD Error: {e}")
            return

        # افکت‌ها
        new_txt = txt
        if ud["poker"]: new_txt += " 😐"
        if ud["bold"]: new_txt = f"**{new_txt}**"
        if ud["code"]: new_txt = f"`{new_txt}`"
        if ud["underline"]: new_txt = f"<u>{new_txt}</u>"
        if ud["sign"]: new_txt += f"\n\n{ud['sign_text']}"
        
        if new_txt != txt:
            try: await m.edit(new_txt)
            except: pass

    @client.on_message(~filters.me & (filters.private | filters.group))
    async def others_handler(c, m):
        ud = user_db[uid]
        if not ud["self"]: return
        
        sender = m.from_user.id if m.from_user else 0
        
        # Enemy
        if sender in ud["enemies"]:
            try: await m.reply(random.choice(ud["fosh_list"]))
            except: pass
        
        # Friend
        elif sender in ud["friends"]:
            if random.random() > 0.8:
                try: await m.reply(random.choice(ud["love_list"]))
                except: pass

        # MarkRead
        if ud["markread"]:
            try: await m.read()
            except: pass

        # Realm / Save PV
        if ud["save_pv"] and m.chat.type == enums.ChatType.PRIVATE and ud["realm_id"]:
            try: await m.forward(ud["realm_id"])
            except: pass

        # Monshi
        if ud["monshi"] and m.chat.type == enums.ChatType.PRIVATE:
            if not getattr(m, "service", False):
                await m.reply(ud["monshi_text"])

    # تسک‌های پس‌زمینه (Name/Bio/Typing)
    async def bg_tasks():
        while True:
            ud = user_db[uid]
            if ud["self"]:
                now = datetime.now().strftime("%H:%M")
                try:
                    if ud["auto_name"]:
                        await c.update_profile(first_name=ud["name_format"].replace("Time", now))
                    if ud["auto_bio"]:
                        await c.update_profile(bio=ud["bio_format"].replace("Time", now))
                except: pass
            await asyncio.sleep(60)

    asyncio.create_task(bg_tasks())
    print(f"✅ User Client {uid} is Ready.")

# ====================================================================
# 🔥 MAIN EXECUTION
# ====================================================================
async def main():
    # 1. Start Web Server for Render
    Thread(target=run_web).start()
    
    # 2. Start Manager
    print("--- Starting Manager ---")
    await manager.start()
    
    # 3. Reload Previous Sessions
    print("--- Reloading Sessions ---")
    session_files = glob.glob(f"{SESSION_DIR}/*.session")
    for s_file in session_files:
        uid = os.path.basename(s_file).replace(".session", "")
        try:
            uc = Client(f"{SESSION_DIR}/{uid}")
            await uc.start()
            await setup_user_bot(uc, uid)
            print(f"🔄 Reloaded: {uid}")
        except Exception as e:
            print(f"❌ Failed to reload {uid}: {e}")
            
    print("✅ System Online!")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
