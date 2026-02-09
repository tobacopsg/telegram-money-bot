import os
import sqlite3
import logging
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ===== CONFIG =====
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO)

# ===== DATABASE =====
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    created TEXT
)
""")
db.commit()

# ===== UTILS =====
def today():
    return date.today().isoformat()

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Số dư", callback_data="balance")],
        [InlineKeyboardButton("💳 Nạp tiền", callback_data="deposit")],
        [InlineKeyboardButton("🏧 Rút tiền", callback_data="withdraw")],
        [InlineKeyboardButton("📅 Điểm danh", callback_data="checkin")],
        [InlineKeyboardButton("👥 Mời bạn", callback_data="invite")],
        [InlineKeyboardButton("📌 Nhiệm vụ", callback_data="task")],
        [InlineKeyboardButton("🏆 Đua top", callback_data="top")],
        [InlineKeyboardButton("🎯 Sự kiện", callback_data="event")],
        [InlineKeyboardButton("🎁 Giftcode", callback_data="gift")],
        [InlineKeyboardButton("🧑‍💼 Đăng ký đại lý", callback_data="agent")],
        [InlineKeyboardButton("💬 CSKH", callback_data="support")]
    ])

# ===== HANDLERS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    cur.execute("SELECT id FROM users WHERE id=?", (user.id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users(id, balance, created) VALUES(?,?,?)",
            (user.id, 0, today())
        )
        db.commit()

    await update.message.reply_text(
        "🤖 CHÀO MỪNG BẠN ĐẾN BOT KIẾM TIỀN\n\n"
        "Chọn chức năng bên dưới:",
        reply_markup=main_menu()
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    if query.data == "balance":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cur.fetchone()[0]
        await query.edit_message_text(
            f"💰 SỐ DƯ HIỆN TẠI\n\n{bal:,} VND",
            reply_markup=main_menu()
        )

    else:
        await query.edit_message_text(
            "⚙️ Chức năng này sẽ được cập nhật tiếp...",
            reply_markup=main_menu()
        )

# ===== RUN =====
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("BOT RUNNING...")
    app.run_polling()

