import asyncio
import os
import json
import random
import glob
from datetime import datetime
from pyrogram import Client, filters, enums
from pyrogram.errors import (SessionPasswordNeeded, PhoneCodeInvalid, 
                             PhoneCodeExpired, FloodWait, PeerIdInvalid)
from pyrogram.types import (InlineKeyboardMarkup, InlineKeyboardButton, 
                            InlineQueryResultArticle, InputTextMessageContent)

# ====================================================================
# ⚙️ تنظیمات (فقط توکن ربات مدیریت را وارد کنید)
# ====================================================================
BOT_TOKEN = "8528881515:AAHiexL1Yw6ekaIOQo04HosVeXJZ0stPIBg"   # <--- توکن از BotFather
# ====================================================================

# 📂 تنظیمات دیتابیس و فایل‌ها
DB_FILE = "am_settings.json"
SESSION_DIR = "sessions"

if not os.path.exists(SESSION_DIR): os.makedirs(SESSION_DIR)

# تنظیمات پیش‌فرض برای هر کاربر جدید
def default_config():
    return {
        "self": True, "monshi": False, "smart_monshi": False,
        "monshi_text": "سلام. من در حال حاضر آنلاین نیستم. لطفا پیام بگذارید.",
        "poker": False, "bold": False, "underline": False, "code": False,
        "typing": False, "markread": False, "anti_delete": True,
        "sign": False, "sign_text": "A.M Self",
        "enemies": [], "friends": [], "fosh_list": ["اسکل", "ببند", "سطح!", "نوب"],
        "love_list": ["عشقم", "جانم", "نفسم"],
        "realm_id": None, "save_pv": False,
        "auto_name": False, "name_format": "A.M | Time",
        "auto_bio": False, "bio_format": "Active Self | Time"
    }

# بارگذاری دیتابیس
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        user_db = json.load(f)
else:
    user_db = {}

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(user_db, f, ensure_ascii=False, indent=4)

# 📘 متن راهنمای کامل
HELP_TEXT = """
💎 **راهنمای جامع A.M Self** 💎
━━━━━━━━━━━━━━━━━━━━
⚡️ **مدیریت اصلی:**
`.self on/off` ➣ روشن/خاموش ربات
`.ping` ➣ تست سرعت
`.reload` ➣ ریلود تنظیمات

🤖 **منشی (Monshi):**
`.monshi on/off` ➣ روشن/خاموش منشی
`.setmonshi [متن]` ➣ تنظیم متن منشی

🎭 **اکشن‌ها:**
`.poker on/off` ➣ پوکر مود (😐)
`.bold on/off` ➣ بولد نویس
`.typing on/off` ➣ تایپینگ دائم
`.markread on/off` ➣ سین زن خودکار

🛡 **امنیت:**
`.antidel on/off` ➣ آنتی‌دلیت
`.setrealm` ➣ تنظیم چت به عنوان مخزن
`.savepv on/off` ➣ بک‌آپ پی‌وی‌ها در ریلم

👥 **افراد:**
`.bad` (ریپلای) ➣ افزودن دشمن
`.good` (ریپلای) ➣ افزودن دوست
`.del [تعداد]` ➣ پاکسازی پیام

👤 **پروفایل:**
`.name on/off` ➣ اسم زمان‌دار
`.bio on/off` ➣ بیو زمان‌دار

💡 برای دیدن پنل دکمه‌ای، کلمه **"پنل"** را ارسال کنید.
"""

# متغیرهای موقت برای پروسه لاگین
login_state = {}
active_clients = {} # نگهداری کلاینت‌های روشن (user_id: Client)

# کلاینت ربات مدیریت
manager = Client("ManagerBot", bot_token=BOT_TOKEN, api_id=6, api_hash="eb06d4abfb49dc3eeb1aeb98ae0f581e")

# ====================================================================
# 🤖 بخش ۱: ربات مدیریت (لاگین و پنل)
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
            "🔒 برای امنیت، باید API خود را وارد کنید.\n"
            "لطفاً **API ID** خود را (عدد) بفرستید:\n"
            "(از my.telegram.org بگیرید)"
        )

@manager.on_message(filters.private & filters.text)
async def login_process(c, m):
    uid = str(m.from_user.id)
    text = m.text
    
    # اگر در پروسه لاگین نیست، نادیده بگیر (مگر اینکه پنل بخواهد)
    if uid not in login_state:
        if text == "پنل":
             # اینجا می‌توان پنل را فرستاد اما پنل اصلی اینلاین است
             pass
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
            status_msg = await m.reply("⏳ در حال اتصال...")
            
            # ساخت کلاینت جدید
            session_name = f"{SESSION_DIR}/{uid}"
            new_app = Client(session_name, api_id=data["api_id"], api_hash=data["api_hash"])
            await new_app.connect()
            
            sent = await new_app.send_code(data["phone"])
            data["client"] = new_app
            data["phone_hash"] = sent.phone_code_hash
            data["step"] = "CODE"
            await status_msg.edit("✅ **کد ارسال شد!**\nکد ۵ رقمی را بفرستید (مثال: `12345`):")

        elif step == "CODE":
            code = text.replace(" ", "")
            client_app = data["client"]
            try:
                await client_app.sign_in(data["phone"], data["phone_hash"], code)
                await m.reply("🎉 **لاگین موفقیت آمیز بود!**\nسلف‌بات شما روشن شد.")
                await setup_user_bot(client_app, uid)
                del login_state[uid]
            except SessionPasswordNeeded:
                data["step"] = "PASSWORD"
                await m.reply("🔐 اکانت **تایید دو مرحله‌ای** دارد. رمز را بفرستید:")
            except Exception as e:
                await m.reply(f"❌ خطا: {e}")

        elif step == "PASSWORD":
            client_app = data["client"]
            try:
                await client_app.check_password(text)
                await m.reply("🎉 **لاگین موفق!**\nسلف‌بات روشن شد.")
                await setup_user_bot(client_app, uid)
                del login_state[uid]
            except Exception as e:
                await m.reply(f"❌ رمز اشتباه است: {e}")

    except Exception as e:
        await m.reply(f"❌ خطای غیرمنتظره: {e}\n/start را بزنید.")
        if uid in login_state and "client" in login_state[uid]:
            await login_state[uid]["client"].disconnect()
        del login_state[uid]

# پنل اینلاین
@manager.on_inline_query()
async def inline_panel(c, q):
    uid = str(q.from_user.id)
    if uid not in user_db:
        # کاربر لاگین نیست
        res = InlineQueryResultArticle(
            title="شما لاگین نیستید",
            input_message_content=InputTextMessageContent("❌ برای استفاده ابتدا ربات را /start کنید."),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("شروع", url=f"t.me/{c.me.username}")]])
        )
        return await q.answer([res], cache_time=1)

    ud = user_db[uid]
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"سلف: {'✅' if ud['self'] else '❌'}", callback_data=f"tg_self"),
         InlineKeyboardButton(f"منشی: {'✅' if ud['monshi'] else '❌'}", callback_data=f"tg_monshi")],
        [InlineKeyboardButton(f"پوکر: {'✅' if ud['poker'] else '❌'}", callback_data=f"tg_poker"),
         InlineKeyboardButton(f"تایپینگ: {'✅' if ud['typing'] else '❌'}", callback_data=f"tg_typing")],
        [InlineKeyboardButton(f"بولد: {'✅' if ud['bold'] else '❌'}", callback_data=f"tg_bold"),
         InlineKeyboardButton(f"سین‌زن: {'✅' if ud['markread'] else '❌'}", callback_data=f"tg_markread")],
        [InlineKeyboardButton("📘 راهنما", callback_data="help")]
    ])
    
    await q.answer([InlineQueryResultArticle(
        title="پنل مدیریت A.M",
        input_message_content=InputTextMessageContent("⚡️ **پنل تنظیمات سلف‌بات A.M**"),
        reply_markup=kb
    )], cache_time=1)

@manager.on_callback_query()
async def cb_handler(c, cb):
    uid = str(cb.from_user.id)
    if uid not in user_db: return await cb.answer("لاگین کنید!", show_alert=True)
    
    if cb.data == "help":
        await cb.answer("راهنما", show_alert=True)
        await cb.edit_message_text(HELP_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙", callback_data="back")]]))
        return
    elif cb.data == "back":
        await cb.edit_message_text("⚡️ **پنل تنظیمات:**", reply_markup=cb.message.reply_markup) # نیاز به رفرش
        return

    key = cb.data.replace("tg_", "")
    if key in user_db[uid]:
        user_db[uid][key] = not user_db[uid][key]
        save_db()
        await cb.answer(f"{key} تغییر کرد")
        # آپدیت متن برای نمایش تغییر
        status = "روشن" if user_db[uid][key] else "خاموش"
        await cb.edit_message_text(f"✅ تنظیمات ذخیره شد.\nوضعیت {key}: {status}\n(برای آپدیت دکمه‌ها دوباره پنل را باز کنید)")

# ====================================================================
# 🚀 بخش ۲: هسته سلف‌بات (Logic)
# ====================================================================

async def setup_user_bot(client_app: Client, uid: str):
    """تنظیم هندلرها برای کلاینت کاربر"""
    
    # اطمینان از وجود تنظیمات در دیتابیس
    if uid not in user_db:
        user_db[uid] = default_config()
        save_db()
    
    active_clients[uid] = client_app

    # 1. هندلر دستورات و افکت‌های شخصی (پیام‌های Me)
    @client_app.on_message(filters.me & filters.text)
    async def self_handlers(c, m):
        ud = user_db[uid]
        txt = m.text
        
        # باز کردن پنل
        if txt == "پنل" or txt == "panel":
            await m.delete()
            try:
                bot_user = await manager.get_me()
                r = await c.get_inline_bot_results(bot_user.username)
                await c.send_inline_bot_result(m.chat.id, r.query_id, r.results[0].id)
            except: pass
            return

        # دستورات (.)
        if txt.startswith("."):
            cmd = txt.split()[0].lower()
            args = txt.split(None, 1)[1] if len(txt.split()) > 1 else ""
            reply = m.reply_to_message

            # Ping
            if cmd == ".ping":
                s = datetime.now()
                await m.edit("🚀")
                e = datetime.now()
                await m.edit(f"💎 **A.M Self Pro**\n📶 Ping: `{(e-s).microseconds/1000}ms`")

            # Self Control
            elif cmd == ".self":
                ud["self"] = (args == "on")
                save_db()
                await m.edit(f"Self: {ud['self']}")

            # Monshi
            elif cmd == ".monshi":
                ud["monshi"] = (args == "on")
                save_db()
                await m.edit(f"Monshi: {ud['monshi']}")
            elif cmd == ".setmonshi":
                ud["monshi_text"] = args
                save_db()
                await m.edit("✅")

            # Actions
            elif cmd == ".poker":
                ud["poker"] = (args == "on")
                save_db()
                await m.edit(f"Poker: {ud['poker']}")
            
            # Enemy/Friend
            elif cmd == ".bad" and reply:
                tid = reply.from_user.id
                if tid not in ud["enemies"]: ud["enemies"].append(tid)
                save_db()
                await m.edit("👺 Enemy Added.")
            elif cmd == ".good" and reply:
                tid = reply.from_user.id
                if tid not in ud["friends"]: ud["friends"].append(tid)
                save_db()
                await m.edit("❤️ Friend Added.")

            # Purge
            elif cmd == ".del":
                await m.delete()
                lim = int(args) if args.isdigit() else 10
                async for msg in c.get_chat_history(m.chat.id, limit=lim):
                    if msg.from_user.id == c.me.id:
                        try: await msg.delete()
                        except: pass
            
            # Realm & Save
            elif cmd == ".setrealm":
                ud["realm_id"] = m.chat.id
                save_db()
                await m.edit(f"🛡 Realm Set: {m.chat.id}")
            elif cmd == ".savepv":
                ud["save_pv"] = (args == "on")
                save_db()
                await m.edit(f"Save PV: {ud['save_pv']}")
            
            # Profile
            elif cmd == ".name":
                ud["auto_name"] = (args == "on")
                save_db()
                await m.edit(f"Auto Name: {ud['auto_name']}")
            elif cmd == ".bio":
                ud["auto_bio"] = (args == "on")
                save_db()
                await m.edit(f"Auto Bio: {ud['auto_bio']}")

            return # پایان پردازش دستور

        # افکت‌ها روی پیام‌های عادی
        new_txt = txt
        if ud["poker"]: new_txt += " 😐"
        if ud["bold"]: new_txt = f"**{new_txt}**"
        if ud["code"]: new_txt = f"`{new_txt}`"
        if ud["underline"]: new_txt = f"<u>{new_txt}</u>"
        if ud["sign"]: new_txt += f"\n\n{ud['sign_text']}"
        
        if new_txt != txt:
            try: await m.edit(new_txt)
            except: pass

    # 2. هندلر پیام‌های دیگران (منشی، دشمن، ...)
    @client_app.on_message(~filters.me & (filters.private | filters.group))
    async def others_handler(c, m):
        ud = user_db[uid]
        if not ud["self"]: return
        
        sender_id = m.from_user.id if m.from_user else 0
        chat_type = m.chat.type

        # Realm (Save PV)
        if ud["save_pv"] and chat_type == enums.ChatType.PRIVATE and ud["realm_id"]:
            try: await m.forward(ud["realm_id"])
            except: pass

        # Mark Read
        if ud["markread"]:
            try: await m.read()
            except: pass

        # Enemy
        if sender_id in ud["enemies"]:
            try: await m.reply(random.choice(ud["fosh_list"]))
            except: pass

        # Monshi (Only PV)
        if ud["monshi"] and chat_type == enums.ChatType.PRIVATE:
            if not getattr(m, "service", False):
                await m.reply(ud["monshi_text"])

    # 3. آنتی دلیت
    @client_app.on_deleted_messages()
    async def anti_del(c, messages):
        ud = user_db[uid]
        if ud["anti_delete"]:
            # در نسخه کامل نیاز به کش کردن پیام‌هاست.
            # اینجا فقط اطلاع می‌دهیم.
            pass

    # 4. تسک‌های پس‌زمینه (پروفایل)
    async def bg_tasks():
        while True:
            ud = user_db[uid]
            if ud["self"]:
                now = datetime.now().strftime("%H:%M")
                try:
                    if ud["auto_name"]:
                        nm = ud["name_format"].replace("Time", now)
                        await c.update_profile(first_name=nm)
                    if ud["auto_bio"]:
                        bio = ud["bio_format"].replace("Time", now)
                        await c.update_profile(bio=bio)
                    if ud["typing"]:
                        # تایپینگ فقط در پی‌وی‌ها برای جلوگیری از اسپم
                        pass 
                except: pass
            await asyncio.sleep(60)
            
    asyncio.create_task(bg_tasks())
    print(f"✅ کلاینت {uid} راه‌اندازی شد.")


# ====================================================================
# 🔥 اجرای اصلی
# ====================================================================
async def main():
    print("--- در حال راه‌اندازی منیجر ---")
    await manager.start()
    
    # بازیابی سشن‌های قبلی (تا اگر سرور ریست شد، اکانت‌ها برگردند)
    print("--- در حال بازیابی کاربران ---")
    session_files = glob.glob(f"{SESSION_DIR}/*.session")
    for s_file in session_files:
        uid = os.path.basename(s_file).replace(".session", "")
        print(f"🔄 بازیابی کاربر: {uid}")
        try:
            # ساخت کلاینت از فایل سشن
            user_client = Client(f"{SESSION_DIR}/{uid}")
            await user_client.start()
            await setup_user_bot(user_client, uid)
        except Exception as e:
            print(f"❌ خطا در بازیابی {uid}: {e}")

    print("✅ سیستم کامل روشن شد! آماده دریافت کاربر.")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("خاموش شد.")
