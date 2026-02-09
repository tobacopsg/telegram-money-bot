import os
import sqlite3
from datetime import datetime, date

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# ================= DATABASE =================

conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    invite_by INTEGER,
    last_checkin TEXT
)
""")

conn.commit()

# ================= HELPERS =================

def get_user(uid: int):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (uid,))
        conn.commit()
        return get_user(uid)
    return user

def add_balance(uid, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))
    conn.commit()

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    get_user(uid)

    keyboard = [
        [InlineKeyboardButton("💰 Nạp tiền", callback_data="deposit"),
         InlineKeyboardButton("🏧 Rút tiền", callback_data="withdraw")],
        [InlineKeyboardButton("📅 Điểm danh", callback_data="checkin"),
         InlineKeyboardButton("👥 Mời bạn", callback_data="invite")],
        [InlineKeyboardButton("🎯 Nhiệm vụ", callback_data="tasks"),
         InlineKeyboardButton("🏆 Đua top", callback_data="top")],
        [InlineKeyboardButton("💳 Số dư", callback_data="balance"),
         InlineKeyboardButton("🎁 Giftcode", callback_data="gift")],
        [InlineKeyboardButton("📞 CSKH", callback_data="support"),
         InlineKeyboardButton("💼 Đăng ký đại lý", callback_data="agent")]
    ]

    await update.message.reply_text(
        "🤖 BOT TELE MONEY\n\nChọn chức năng bên dưới:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= CALLBACK =================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    user = get_user(uid)
    balance = user[1]

    if query.data == "deposit":
        await query.message.reply_text("💰 NẠP TIỀN\n\nAdmin sẽ xử lý thủ công.")

    elif query.data == "withdraw":
        await query.message.reply_text("🏧 RÚT TIỀN\n\nGửi yêu cầu rút cho admin.")

    elif query.data == "checkin":
        today = str(date.today())
        if user[3] == today:
            await query.message.reply_text("❌ Hôm nay bạn đã điểm danh rồi!")
        else:
            cursor.execute("UPDATE users SET last_checkin=? WHERE user_id=?", (today, uid))
            conn.commit()
            add_balance(uid, 1000)
            await query.message.reply_text("✅ Điểm danh thành công +1000 VNĐ")

    elif query.data == "invite":
        link = f"https://t.me/{context.bot.username}?start={uid}"
        await query.message.reply_text(
            f"👥 MỜI BẠN\n\nLink giới thiệu của bạn:\n{link}\n\nMỗi người: +5,000 VNĐ"
        )

    elif query.data == "tasks":
        await query.message.reply_text("🎯 NHIỆM VỤ\n\n• Điểm danh: +1000\n• Mời bạn: +5000")

    elif query.data == "top":
        cursor.execute("SELECT user_id, balance FROM users ORDER BY balance DESC LIMIT 10")
        rows = cursor.fetchall()
        text = "🏆 ĐUA TOP\n\n"
        for i, r in enumerate(rows, 1):
            text += f"{i}. {r[0]} — {r[1]} VNĐ\n"
        await query.message.reply_text(text)

    elif query.data == "balance":
        await query.message.reply_text(f"💳 SỐ DƯ HIỆN TẠI: {balance} VNĐ")

    elif query.data == "gift":
        await query.message.reply_text("🎁 Nhập giftcode bằng lệnh:\n/gift CODE")

    elif query.data == "support":
        await query.message.reply_text("📞 CSKH\n\nLiên hệ admin để được hỗ trợ.")

    elif query.data == "agent":
        await query.message.reply_text("💼 ĐĂNG KÝ ĐẠI LÝ\n\nLiên hệ admin để xét duyệt.")

# ================= ADMIN =================

async def admin_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        uid = int(context.args[0])
        amount = int(context.args[1])
        add_balance(uid, amount)
        await update.message.reply_text(f"✅ Đã cộng {amount} cho {uid}")
    except:
        await update.message.reply_text("Sai cú pháp: /add user_id số_tiền")

# ================= MAIN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", admin_add))
app.add_handler(CallbackQueryHandler(callback_handler))

print("BOT STARTED")
app.run_polling()

