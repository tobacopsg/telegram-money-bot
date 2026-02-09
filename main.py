import asyncio
import logging
import aiosqlite
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8209807211:AAEuUJmNHk4TzDAdLSxYMKZ7WljYSxe3U5g"

DB_NAME = "database.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ---------- DATABASE ----------

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            invited_by INTEGER,
            streak INTEGER DEFAULT 0,
            last_checkin TEXT
        )
        """)
        await db.commit()

# ---------- HANDLERS ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(user_id) VALUES(?)",
            (user_id,)
        )
        await db.commit()

    keyboard = [
        [InlineKeyboardButton("💰 Nạp tiền", callback_data="deposit"),
         InlineKeyboardButton("💸 Rút tiền", callback_data="withdraw")],
        [InlineKeyboardButton("🎁 Điểm danh", callback_data="checkin"),
         InlineKeyboardButton("👥 Mời bạn", callback_data="invite")],
        [InlineKeyboardButton("🏆 Đua top", callback_data="top"),
         InlineKeyboardButton("🎫 Giftcode", callback_data="gift")]
    ]

    await update.message.reply_text(
        "🔥 OKVIP BOT KHUYẾN MÃI 🔥\n\n"
        "Chọn chức năng bên dưới:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------- CALLBACK ----------

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "deposit":
        await query.edit_message_text("💰 Gửi ảnh bill + nội dung chuyển khoản cho admin.")
    elif query.data == "withdraw":
        await query.edit_message_text("💸 Nhập số tiền muốn rút, admin sẽ duyệt.")
    elif query.data == "checkin":
        await query.edit_message_text("🎁 Điểm danh thành công +5000 VNĐ.")
    elif query.data == "invite":
        await query.edit_message_text("👥 Mời bạn bè để nhận thưởng.")
    elif query.data == "top":
        await query.edit_message_text("🏆 Bảng xếp hạng đang cập nhật.")
    elif query.data == "gift":
        await query.edit_message_text("🎫 Nhập giftcode để nhận quà.")

# ---------- MAIN ----------

async def main():
    await init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
