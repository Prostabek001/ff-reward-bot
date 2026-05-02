import logging
import json
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ===================== SOZLAMALAR =====================
TOKEN = "8599701889:AAGZ-cM7R06pG6PP3EViO91elsPHcB_Y6Hk"
ADMIN_ID = None  # Quyida /start da avtomatik o'rnatiladi
DATA_FILE = "users.json"

# Narxlar (ballarda)
PRICES = {
    "almaz_100": {"bal": 100, "narx": "100 💎 Almaz"},
    "almaz_200": {"bal": 190, "narx": "200 💎 Almaz"},
    "almaz_500": {"bal": 450, "narx": "500 💎 Almaz"},
    "sensi_normal": {"bal": 50, "narx": "🎮 Normal Sensi"},
    "sensi_pro": {"bal": 80, "narx": "🎯 Pro Sensi"},
}

# Vazifalar
TASKS = {
    "task_sub": {"bal": 30, "text": "📢 Kanalga obuna bo'l", "done_text": "Obuna bo'ldim ✅"},
    "task_share": {"bal": 20, "text": "🔗 Botni 3 do'stingga ulash", "done_text": "Ulashdim ✅"},
    "task_daily": {"bal": 15, "text": "📅 Kunlik bonus (har 24 soatda)", "done_text": "Olish ✅"},
    "task_ff_id": {"bal": 25, "text": "🎮 Free Fire ID ni kiritish", "done_text": "ID kiriting ✅"},
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== MA'LUMOTLAR =====================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_user(user_id, username=""):
    data = load_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "username": username,
            "bal": 0,
            "done_tasks": [],
            "ff_id": "",
            "buyurtmalar": [],
            "last_daily": "",
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        save_data(data)
    return data[uid]

def update_user(user_id, user_data):
    data = load_data()
    data[str(user_id)] = user_data
    save_data(data)

# ===================== ADMINNI ANIQLASH =====================
async def set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN_ID
    data = load_data()
    if not data:
        ADMIN_ID = update.effective_user.id
        logger.info(f"Admin o'rnatildi: {ADMIN_ID}")

# ===================== /start =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_admin(update, context)
    user = update.effective_user
    u = get_user(user.id, user.username or user.first_name)

    text = f"""
🔥 *FREE FIRE REWARD BOT* 🔥
━━━━━━━━━━━━━━━━━━━━
Salom, *{user.first_name}*! 👋

💰 Sizning balingiz: *{u['bal']} bal*
🆔 FF ID: *{u['ff_id'] if u['ff_id'] else 'Kiritilmagan'}*

📌 *Qanday ishlaydi?*
1️⃣ Vazifalarni bajaring → bal to'plang
2️⃣ Bal bilan almaz yoki sensi sotib oling
3️⃣ Screenshot yuboring → Admin tasdiqlaydi
4️⃣ Almazingiz tushadi! 💎

👇 Menyu:
"""
    keyboard = [
        [InlineKeyboardButton("📋 Vazifalar", callback_data="vazifalar"),
         InlineKeyboardButton("🏪 Do'kon", callback_data="dokon")],
        [InlineKeyboardButton("💰 Balim", callback_data="balim"),
         InlineKeyboardButton("📱 Sensi", callback_data="sensi_info")],
        [InlineKeyboardButton("📦 Buyurtmalarim", callback_data="buyurtmalar"),
         InlineKeyboardButton("ℹ️ Yordam", callback_data="yordam")],
    ]
    await update.message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ===================== MENYU =====================
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    u = get_user(user.id)
    data_cb = query.data

    # === VAZIFALAR ===
    if data_cb == "vazifalar":
        keyboard = []
        text = "📋 *VAZIFALAR*\n━━━━━━━━━━━━━━━━\nVazifa bajaring — bal to'plang!\n\n"
        for key, task in TASKS.items():
            done = key in u["done_tasks"]
            status = "✅" if done and key != "task_daily" else ""
            text += f"{'~~' if done and key != 'task_daily' else ''}+{task['bal']} bal — {task['text']}{status}{'~~' if done and key != 'task_daily' else ''}\n"
            if not (done and key != "task_daily"):
                keyboard.append([InlineKeyboardButton(
                    f"+{task['bal']} bal | {task['done_text']}",
                    callback_data=f"task_{key}"
                )])
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="bosh")])
        await query.edit_message_text(text, parse_mode="Markdown",
                                       reply_markup=InlineKeyboardMarkup(keyboard))

    # === DO'KON ===
    elif data_cb == "dokon":
        text = f"🏪 *DO'KON*\n━━━━━━━━━━━━━━━━\n💰 Sizning balingiz: *{u['bal']} bal*\n\n💎 *Almazlar:*\n"
        for key, item in PRICES.items():
            if "almaz" in key:
                status = "✅" if u["bal"] >= item["bal"] else "❌"
                text += f"{status} {item['narx']} — {item['bal']} bal\n"
        text += "\n🎮 *Sensi:*\n"
        for key, item in PRICES.items():
            if "sensi" in key:
                status = "✅" if u["bal"] >= item["bal"] else "❌"
                text += f"{status} {item['narx']} — {item['bal']} bal\n"

        keyboard = []
        for key, item in PRICES.items():
            if u["bal"] >= item["bal"]:
                keyboard.append([InlineKeyboardButton(
                    f"Sotib olish: {item['narx']} ({item['bal']} bal)",
                    callback_data=f"buy_{key}"
                )])
        keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="bosh")])
        await query.edit_message_text(text, parse_mode="Markdown",
                                       reply_markup=InlineKeyboardMarkup(keyboard))

    # === BAL ===
    elif data_cb == "balim":
        text = f"""
💰 *MENING BALLARIM*
━━━━━━━━━━━━━━━━
👤 Ism: *{user.first_name}*
💰 Bal: *{u['bal']} bal*
🆔 FF ID: *{u['ff_id'] if u['ff_id'] else 'Kiritilmagan'}*
📅 Qo'shilgan: *{u['joined']}*
✅ Bajarlgan vazifalar: *{len(u['done_tasks'])}*

💎 100 bal = 100 almaz
🎮 50 bal = Normal sensi
🎯 80 bal = Pro sensi
"""
        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="bosh")]]
        await query.edit_message_text(text, parse_mode="Markdown",
                                       reply_markup=InlineKeyboardMarkup(keyboard))

    # === SENSI INFO ===
    elif data_cb == "sensi_info":
        text = """
📱 *FREE FIRE SENSI SOZLAMALARI*
━━━━━━━━━━━━━━━━

🎯 *Pro Sensi (80 bal)*
• Umumiy: 90-100
• Muhr boshqaruvi: 95-100
• 4x Durbun: 65-75
• AWM durbuni: 55-65
• Avto nishon: Yoqilgan
• Yon harakat: 80-90

🎮 *Normal Sensi (50 bal)*
• Umumiy: 70-80
• Muhr boshqaruvi: 75-85
• 4x Durbun: 50-60
• AWM durbuni: 40-50
• Avto nishon: Yoqilgan
• Yon harakat: 60-70

📌 *Eslatma:* Har bir telefon uchun biroz farq qilishi mumkin!
"""
        keyboard = [
            [InlineKeyboardButton("🛒 Sensi sotib olish", callback_data="dokon")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data="bosh")]
        ]
        await query.edit_message_text(text, parse_mode="Markdown",
                                       reply_markup=InlineKeyboardMarkup(keyboard))

    # === BUYURTMALAR ===
    elif data_cb == "buyurtmalar":
        if not u["buyurtmalar"]:
            text = "📦 *Buyurtmalaringiz yo'q*\n\nDo'kondan nimarsa sotib oling!"
        else:
            text = "📦 *BUYURTMALARIM*\n━━━━━━━━━━━━━━━━\n"
            for b in u["buyurtmalar"][-5:]:
                text += f"• {b['narx']} — {b['status']} — {b['vaqt']}\n"
        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="bosh")]]
        await query.edit_message_text(text, parse_mode="Markdown",
                                       reply_markup=InlineKeyboardMarkup(keyboard))

    # === YORDAM ===
    elif data_cb == "yordam":
        text = """
ℹ️ *YORDAM*
━━━━━━━━━━━━━━━━

📌 *Qanday ishlaydi?*
1. Vazifalarni bajaring
2. Bal to'plang
3. Do'kondan sotib oling
4. Admin tasdiqlaydi
5. Free Fire ga tushadi!

💎 *Narxlar:*
• 100 almaz = 100 bal
• 200 almaz = 190 bal
• 500 almaz = 450 bal
• Normal sensi = 50 bal
• Pro sensi = 80 bal

❓ *Muammo bo'lsa:*
Admin bilan bog'laning
"""
        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="bosh")]]
        await query.edit_message_text(text, parse_mode="Markdown",
                                       reply_markup=InlineKeyboardMarkup(keyboard))

    # === BOSH SAHIFA ===
    elif data_cb == "bosh":
        u = get_user(user.id)
        text = f"""
🔥 *FREE FIRE REWARD BOT* 🔥
━━━━━━━━━━━━━━━━━━━━
Salom, *{user.first_name}*! 👋

💰 Sizning balingiz: *{u['bal']} bal*
🆔 FF ID: *{u['ff_id'] if u['ff_id'] else 'Kiritilmagan'}*
"""
        keyboard = [
            [InlineKeyboardButton("📋 Vazifalar", callback_data="vazifalar"),
             InlineKeyboardButton("🏪 Do'kon", callback_data="dokon")],
            [InlineKeyboardButton("💰 Balim", callback_data="balim"),
             InlineKeyboardButton("📱 Sensi", callback_data="sensi_info")],
            [InlineKeyboardButton("📦 Buyurtmalarim", callback_data="buyurtmalar"),
             InlineKeyboardButton("ℹ️ Yordam", callback_data="yordam")],
        ]
        await query.edit_message_text(text, parse_mode="Markdown",
                                       reply_markup=InlineKeyboardMarkup(keyboard))

    # === VAZIFA BAJARISH ===
    elif data_cb.startswith("task_task_"):
        task_key = data_cb.replace("task_", "", 1)
        u = get_user(user.id)

        if task_key == "task_ff_id":
            context.user_data["waiting_ff_id"] = True
            await query.edit_message_text(
                "🎮 *Free Fire ID ingizni yozing:*\n\nMasalan: `123456789`",
                parse_mode="Markdown"
            )
            return

        if task_key == "task_daily":
            today = datetime.now().strftime("%Y-%m-%d")
            if u["last_daily"] == today:
                await query.answer("⏰ Kunlik bonus allaqachon olindi!", show_alert=True)
                return
            u["last_daily"] = today
            u["bal"] += TASKS[task_key]["bal"]
            update_user(user.id, u)
            await query.answer(f"✅ +{TASKS[task_key]['bal']} bal olindi!", show_alert=True)
            return

        if task_key in u["done_tasks"]:
            await query.answer("✅ Bu vazifa allaqachon bajarilgan!", show_alert=True)
            return

        u["done_tasks"].append(task_key)
        u["bal"] += TASKS[task_key]["bal"]
        update_user(user.id, u)
        await query.answer(f"✅ +{TASKS[task_key]['bal']} bal olindi!", show_alert=True)
        await menu_vazifalar(query, user.id)

    # === SOTIB OLISH ===
    elif data_cb.startswith("buy_"):
        item_key = data_cb.replace("buy_", "")
        u = get_user(user.id)
        item = PRICES.get(item_key)

        if not item:
            await query.answer("❌ Mahsulot topilmadi!", show_alert=True)
            return

        if not u["ff_id"]:
            await query.answer("❌ Avval FF ID ni kiriting!", show_alert=True)
            return

        if u["bal"] < item["bal"]:
            await query.answer(f"❌ Yetarli bal yo'q! Kerak: {item['bal']} bal", show_alert=True)
            return

        u["bal"] -= item["bal"]
        buyurtma = {
            "narx": item["narx"],
            "bal": item["bal"],
            "status": "⏳ Kutilmoqda",
            "vaqt": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ff_id": u["ff_id"]
        }
        u["buyurtmalar"].append(buyurtma)
        update_user(user.id, u)

        # Adminga xabar
        global ADMIN_ID
        if ADMIN_ID:
            admin_text = f"""
🛒 *YANGI BUYURTMA!*
━━━━━━━━━━━━━━━━
👤 Foydalanuvchi: @{user.username or user.first_name}
🆔 FF ID: `{u['ff_id']}`
🛍 Mahsulot: {item['narx']}
💰 Bal: {item['bal']}
📅 Vaqt: {buyurtma['vaqt']}
━━━━━━━━━━━━━━━━
✅ Tasdiqlash uchun almaz yuboring!
"""
            try:
                await context.bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
            except:
                pass

        text = f"""
✅ *BUYURTMA QABUL QILINDI!*
━━━━━━━━━━━━━━━━
🛍 Mahsulot: *{item['narx']}*
🆔 FF ID: `{u['ff_id']}`
💰 Qolgan bal: *{u['bal']} bal*
⏳ Status: *Kutilmoqda*

📌 Admin tez orada tasdiqlaydi!
"""
        keyboard = [[InlineKeyboardButton("🔙 Bosh sahifa", callback_data="bosh")]]
        await query.edit_message_text(text, parse_mode="Markdown",
                                       reply_markup=InlineKeyboardMarkup(keyboard))

async def menu_vazifalar(query, user_id):
    u = get_user(user_id)
    text = "📋 *VAZIFALAR*\n━━━━━━━━━━━━━━━━\n\n"
    keyboard = []
    for key, task in TASKS.items():
        done = key in u["done_tasks"]
        if not (done and key != "task_daily"):
            keyboard.append([InlineKeyboardButton(
                f"+{task['bal']} bal | {task['done_text']}",
                callback_data=f"task_{key}"
            )])
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="bosh")])
    await query.edit_message_text(text, parse_mode="Markdown",
                                   reply_markup=InlineKeyboardMarkup(keyboard))

# ===================== MATN XABARLAR =====================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = get_user(user.id)

    if context.user_data.get("waiting_ff_id"):
        ff_id = update.message.text.strip()
        if ff_id.isdigit() and len(ff_id) >= 6:
            u["ff_id"] = ff_id
            if "task_ff_id" not in u["done_tasks"]:
                u["done_tasks"].append("task_ff_id")
                u["bal"] += TASKS["task_ff_id"]["bal"]
            update_user(user.id, u)
            context.user_data["waiting_ff_id"] = False
            await update.message.reply_text(
                f"✅ FF ID saqlandi: `{ff_id}`\n+{TASKS['task_ff_id']['bal']} bal olindi! 🎉",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Noto'g'ri ID! Faqat raqam kiriting.")
        return

    await update.message.reply_text(
        "👇 /start ni bosing yoki menyudan foydalaning!",
    )

# ===================== ADMIN KOMANDALAR =====================
async def admin_bal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN_ID
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz!")
        return
    try:
        args = context.args
        target_id = args[0]
        amount = int(args[1])
        data = load_data()
        if target_id in data:
            data[target_id]["bal"] += amount
            save_data(data)
            await update.message.reply_text(f"✅ {target_id} ga {amount} bal qo'shildi!")
            await context.bot.send_message(int(target_id),
                f"🎉 Admindan *+{amount} bal* olindiz!", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Foydalanuvchi topilmadi!")
    except:
        await update.message.reply_text("❗ Format: /addbal [user_id] [miqdor]")

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN_ID
    if update.effective_user.id != ADMIN_ID:
        return
    data = load_data()
    text = f"👥 *Foydalanuvchilar: {len(data)} ta*\n━━━━━━━━━━━━\n"
    for uid, u in list(data.items())[-10:]:
        text += f"• {u.get('username','?')} | {u['bal']} bal | FF: {u.get('ff_id','—')}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ===================== MAIN =====================
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addbal", admin_bal))
    app.add_handler(CommandHandler("users", admin_users))
    app.add_handler(CallbackQueryHandler(menu))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("🤖 Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
