import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ===== MENU =====
def main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 Nạp tiền", callback_data="deposit"),
         InlineKeyboardButton("🏧 Rút tiền", callback_data="withdraw")],

        [InlineKeyboardButton("📅 Điểm danh", callback_data="checkin"),
         InlineKeyboardButton("👥 Mời bạn", callback_data="invite")],

        [InlineKeyboardButton("🎯 Nhiệm vụ", callback_data="task"),
         InlineKeyboardButton("🏆 Đua top", callback_data="top")],

        [InlineKeyboardButton("🎁 Giftcode", callback_data="gift"),
         InlineKeyboardButton("📞 CSKH", callback_data="support")],

        [InlineKeyboardButton("💼 Đăng ký đại lý", callback_data="agent")],
        [InlineKeyboardButton("💳 Số dư", callback_data="balance")]
    ]
    return InlineKeyboardMarkup(keyboard)


# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 BOT TELE MONEY\n\nChọn chức năng bên dưới:",
        reply_markup=main_menu()
    )


# ===== CALLBACK =====
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    text_map = {
        "deposit": "💰 Nạp tiền\n\nGửi bill cho admin xử lý.",
        "withdraw": "🏧 Rút tiền\n\nNhập số tiền muốn rút.",
        "checkin": "📅 Điểm danh thành công!",
        "invite": "👥 Mời bạn\n\nLink giới thiệu:\nhttps://t.me/YOUR_BOT?start=ref",
        "task": "🎯 Nhiệm vụ ngày",
        "top": "🏆 BXH đua top tuần",
        "gift": "🎁 Nhập giftcode",
        "support": "📞 CSKH\n\nLiên hệ admin.",
        "agent": "💼 Đăng ký đại lý",
        "balance": "💳 Số dư: 0 VNĐ"
    }

    await query.edit_message_text(
        text=text_map.get(query.data, "Chức năng đang phát triển"),
        reply_markup=main_menu()
    )


# ===== MAIN =====
def main():
    print("BOT STARTING...")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("BOT STARTED SUCCESSFULLY")
    app.run_polling()


if __name__ == "__main__":
    main()
