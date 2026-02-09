import os, sqlite3, datetime, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

db = sqlite3.connect("data.db", check_same_thread=False)
c = db.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    invited_by INTEGER,
    checkin_date TEXT,
    total_invite INTEGER DEFAULT 0
)
""")
db.commit()

def get_user(uid):
    c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not c.fetchone():
        c.execute("INSERT INTO users(user_id) VALUES(?)", (uid,))
        db.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    get_user(uid)

    kb = [
        [InlineKeyboardButton("💰 Nạp tiền", callback_data="deposit"),
         InlineKeyboardButton("🏧 Rút tiền", callback_data="withdraw")],
        [InlineKeyboardButton("📅 Điểm danh", callback_data="checkin"),
         InlineKeyboardButton("👥 Mời bạn", callback_data="invite")],
        [InlineKeyboardButton("🎯 Nhiệm vụ", callback_data="task"),
         InlineKeyboardButton("🏆 Đua top", callback_data="top")],
        [InlineKeyboardButton("🎁 Giftcode", callback_data="gift"),
         InlineKeyboardButton("📞 CSKH", callback_data="support")],
        [InlineKeyboardButton("💼 Đăng ký đại lý", callback_data="agent")]
    ]

    await update.message.reply_text("🤖 BOT TELE MONEY", reply_markup=InlineKeyboardMarkup(kb))

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    get_user(uid)

    if q.data == "deposit":
        await q.message.reply_text("💰 Gửi bill chuyển khoản cho admin.")

    elif q.data == "withdraw":
        await q.message.reply_text("🏧 Nhập số tiền + thông tin ngân hàng.")

    elif q.data == "checkin":
        today = str(datetime.date.today())
        c.execute("SELECT checkin_date FROM users WHERE user_id=?", (uid,))
        last = c.fetchone()[0]

        if last == today:
            await q.message.reply_text("❌ Hôm nay đã điểm danh.")
        else:
            c.execute("UPDATE users SET balance=balance+10000, checkin_date=? WHERE user_id=?", (today, uid))
            db.commit()
            await q.message.reply_text("✅ Điểm danh +10.000đ")

    elif q.data == "invite":
        link = f"https://t.me/{context.bot.username}?start={uid}"
        await q.message.reply_text(f"👥 Link mời bạn:\n{link}\n+50.000đ / lượt")

    elif q.data == "task":
        await q.message.reply_text("🎯 Nhiệm vụ:\n- Nạp tiền +30%\n- Mời 3 bạn +50k\n- Rút 50k +15k")

    elif q.data == "top":
        c.execute("SELECT user_id,total_invite FROM users ORDER BY total_invite DESC LIMIT 10")
        rows = c.fetchall()
        msg = "🏆 TOP MỜI BẠN\n\n"
        for i, r in enumerate(rows,1):
            msg += f"{i}. {r[0]} — {r[1]} lượt\n"
        await q.message.reply_text(msg)

    elif q.data == "gift":
        await q.message.reply_text("🎁 Nhập giftcode:")

    elif q.data == "support":
        await q.message.reply_text("📞 CSKH: @admin")

    elif q.data == "agent":
        await q.message.reply_text("💼 Điều kiện đại lý: Nạp ≥5 triệu")

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = context.args
    get_user(uid)

    if args:
        ref = int(args[0])
        if ref != uid:
            c.execute("SELECT invited_by FROM users WHERE user_id=?", (uid,))
            if not c.fetchone()[0]:
                c.execute("UPDATE users SET invited_by=? WHERE user_id=?", (ref, uid))
                c.execute("UPDATE users SET balance=balance+50000,total_invite=total_invite+1 WHERE user_id=?", (ref,))
                db.commit()

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("start", referral))
app
