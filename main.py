import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = "8209807211:AAEuUJmNHk4TzDAdLSxYMKZ7WljYSxe3U5g"
ADMIN_ID = 6050668835

logging.basicConfig(level=logging.INFO)

users = {}
waiting_deposit = {}
waiting_withdraw = {}

# ===== TIỆN ÍCH =====
def get_user(uid):
    if uid not in users:
        users[uid] = {
            "balance": 0,
            "ref": None,
            "ref_count": 0,
            "checkin": 0
        }
    return users[uid]

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    get_user(uid)

    kb = [
        [InlineKeyboardButton("💳 Nạp tiền", callback_data="deposit"), InlineKeyboardButton("💸 Rút tiền", callback_data="withdraw")],
        [InlineKeyboardButton("🎁 Gift Code", callback_data="gift"), InlineKeyboardButton("🔥 Sự kiện", callback_data="event")],
        [InlineKeyboardButton("🏆 Đua Top", callback_data="top"), InlineKeyboardButton("☎ CSKH", callback_data="support")]
    ]

    await update.message.reply_text("🎛 VIP PANEL", reply_markup=InlineKeyboardMarkup(kb))

# ===== CALLBACK =====
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "deposit":
        waiting_deposit[uid] = True
        await q.message.reply_text("💳 Nhập số tiền cần nạp (VD: 50 = 50.000đ)\nQuy ước: 1 = 1000đ")

    elif q.data == "withdraw":
        waiting_withdraw[uid] = True
        await q.message.reply_text("💸 Nhập số tiền cần rút (tối thiểu 100 = 100.000đ)")

    elif q.data == "gift":
        await q.message.reply_text("🎁 Nhập gift code:")

    elif q.data == "event":
        await q.message.reply_text("🔥 Hiện không có sự kiện")

    elif q.data == "top":
        await q.message.reply_text("🏆 Bảng đua top đang cập nhật")

    elif q.data == "support":
        await q.message.reply_text("☎ Gửi nội dung, admin sẽ phản hồi")

# ===== TEXT =====
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    user = get_user(uid)

    # NẠP
    if uid in waiting_deposit:
        del waiting_deposit[uid]
        try:
            amount = int(text)
            vnd = amount * 1000
            bonus = int(vnd * 0.03)
            total = vnd + bonus

            user["balance"] += total

            await update.message.reply_text(
                f"✅ Ghi nhận nạp {vnd:,}đ\nThưởng +3%: {bonus:,}đ\nSố dư: {user['balance']:,}đ"
            )
        except:
            await update.message.reply_text("❌ Sai định dạng")
        return

    # RÚT
    if uid in waiting_withdraw:
        del waiting_withdraw[uid]
        try:
            amount = int(text)
            if amount < 100:
                await update.message.reply_text("❌ Rút tối thiểu 100 = 100.000đ")
                return

            vnd = amount * 1000
            if user["balance"] < vnd:
                await update.message.reply_text("❌ Không đủ số dư")
                return

            user["balance"] -= vnd
            await update.message.reply_text(f"✅ Đã gửi yêu cầu rút {vnd:,}đ")
        except:
            await update.message.reply_text("❌ Sai định dạng")
        return

    # CSKH
    await context.bot.send_message(ADMIN_ID, f"📩 CSKH từ {uid}: {text}")
    await update.message.reply_text("📨 Đã gửi admin")

# ===== MAIN =====
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
