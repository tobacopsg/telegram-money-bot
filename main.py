# Python 3.10+ | python-telegram-bot v20+
# 1 = 1000 VND

import sqlite3, time
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = "8209807211:AAEuUJmNHk4TzDAdLSxYMKZ7WljYSxe3U5g"
ADMIN_ID = 6050668835

# ================= DATABASE =================

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    total_deposit INTEGER DEFAULT 0,
    invite_count INTEGER DEFAULT 0,
    referrer INTEGER,
    created_at TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS deposits(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    status TEXT,
    created_at TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS withdrawals(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    bank TEXT,
    status TEXT,
    reason TEXT,
    created_at TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS invites(
    inviter INTEGER,
    invitee INTEGER,
    valid INTEGER DEFAULT 0,
    day TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS rewards(
    user_id INTEGER,
    reward_key TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS giftcodes(
    code TEXT PRIMARY KEY,
    amount INTEGER,
    used INTEGER DEFAULT 0
)""")

conn.commit()

# ================= HELPERS =================

def get_user(uid):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    return cur.fetchone()

def create_user(uid, ref=None):
    cur.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?)",
                (uid, 0, 0, 0, ref, datetime.now().isoformat()))
    conn.commit()

def add_balance(uid, amt):
    cur.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amt, uid))
    conn.commit()

def sub_balance(uid, amt):
    cur.execute("UPDATE users SET balance=balance-? WHERE user_id=?", (amt, uid))
    conn.commit()

def has_reward(uid, key):
    cur.execute("SELECT 1 FROM rewards WHERE user_id=? AND reward_key=?", (uid, key))
    return cur.fetchone()

def add_reward(uid, key):
    cur.execute("INSERT INTO rewards VALUES (?,?)", (uid, key))
    conn.commit()

# ================= MENU =================

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Nạp tiền", callback_data="deposit"),
         InlineKeyboardButton("🏧 Rút tiền", callback_data="withdraw"),
         InlineKeyboardButton("📊 Số dư", callback_data="balance")],
        [InlineKeyboardButton("🎉 Sự kiện", callback_data="events"),
         InlineKeyboardButton("🔥 Khuyến mãi", callback_data="promo"),
         InlineKeyboardButton("📋 Nhiệm vụ", callback_data="tasks")],
        [InlineKeyboardButton("🎁 Giftcode", callback_data="giftcode"),
         InlineKeyboardButton("☎️ CSKH", callback_data="support")]
    ])

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    ref = int(context.args[0]) if context.args else None
    create_user(uid, ref)
    await update.message.reply_text("🤖 BOT HOẠT ĐỘNG", reply_markup=main_menu())

# ================= CALLBACK =================

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data

    if data == "balance":
        u = get_user(uid)
        await q.message.edit_text(
            f"💰 Số dư: {u[1]}\n📥 Tổng nạp: {u[2]}\n👥 Mời: {u[3]}",
            reply_markup=main_menu())

    # ---------- NẠP ----------
    elif data == "deposit":
        kb = [
            [InlineKeyboardButton("50", callback_data="dep_50"),
             InlineKeyboardButton("100", callback_data="dep_100"),
             InlineKeyboardButton("200", callback_data="dep_200")],
            [InlineKeyboardButton("500", callback_data="dep_500"),
             InlineKeyboardButton("1000", callback_data="dep_1000")],
        ]
        await q.message.edit_text("Chọn số tiền:", reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("dep_"):
        amt = int(data.split("_")[1])
        context.user_data["dep"] = amt
        await q.message.edit_text(
            f"Chuyển khoản...\nNội dung: NAP {uid}\nSố tiền: {amt}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Đã hoàn tất", callback_data="dep_done"),
                InlineKeyboardButton("❌ Hủy", callback_data="cancel")
            ]]))

    elif data == "dep_done":
        amt = context.user_data.get("dep")
        cur.execute("INSERT INTO deposits(user_id,amount,status,created_at) VALUES (?,?,?,?)",
                    (uid, amt, "pending", datetime.now().isoformat()))
        conn.commit()
        await q.message.edit_text("⏳ Đã gửi yêu cầu nạp", reply_markup=main_menu())
        await context.bot.send_message(
            ADMIN_ID,
            f"DUYỆT NẠP\nUser: {uid}\nTiền: {amt}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("DUYỆT", callback_data=f"ad_dep_ok_{uid}_{amt}"),
                InlineKeyboardButton("TỪ CHỐI", callback_data=f"ad_dep_no_{uid}_{amt}")
            ]])
        )

    elif data.startswith("ad_dep_ok"):
        _,_,uid2,amt = data.split("_")
        uid2, amt = int(uid2), int(amt)
        bonus = int(amt * 0.03)
        add_balance(uid2, amt + bonus)
        cur.execute("UPDATE users SET total_deposit=total_deposit+? WHERE user_id=?", (amt, uid2))
        conn.commit()
        await q.message.edit_text("Đã duyệt nạp")
        await context.bot.send_message(uid2, f"✅ Nạp thành công +{amt} + thưởng {bonus}", reply_markup=main_menu())

    # ---------- RÚT ----------
    elif data == "withdraw":
        await q.message.edit_text("Nhập số tiền muốn rút:")
        context.user_data["wd"] = True

    elif data == "cancel":
        context.user_data.clear()
        await q.message.edit_text("Đã hủy", reply_markup=main_menu())

    # ---------- SỰ KIỆN ----------
    elif data == "events":
        await q.message.edit_text(
            "🎉 Sự kiện:\n- Nạp lần đầu +100%\n- Nạp lần 2 +50%\n- Nạp lần 3 +25%\n- Lần đầu ngày +15%\n\n"
            "🎯 Tích lũy:\n≥1000 → +300\n≥5000 → +2000\n\n"
            "👥 Mời bạn:\nMỗi người +99\n3/ngày → +297\n20 → +300\n50 → +1000",
            reply_markup=main_menu()
        )

    # ---------- KHUYẾN MÃI ----------
    elif data == "promo":
        await q.message.edit_text(
            "🔥 Khuyến mãi:\n- Tân thủ: +58 (1 lần)\n- Mời lần đầu: +28 (1 lần)\n- Nạp thường: +3%",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Nhận tân thủ", callback_data="newbie")],
                                               [InlineKeyboardButton("⬅️ Quay lại", callback_data="back")]]))

    elif data == "newbie":
        if has_reward(uid, "newbie"):
            await q.message.edit_text("Bạn đã nhận rồi.", reply_markup=main_menu())
        else:
            add_balance(uid, 58)
            add_reward(uid, "newbie")
            await q.message.edit_text("🎁 Nhận thành công +58", reply_markup=main_menu())

    elif data == "back":
        await q.message.edit_text("Menu:", reply_markup=main_menu())

    # ---------- GIFTCODE ----------
    elif data == "giftcode":
        context.user_data["gift"] = True
        await q.message.edit_text("Nhập giftcode:")

    # ---------- CSKH ----------
    elif data == "support":
        context.user_data["support"] = True
        await q.message.edit_text("Nhập nội dung cần hỗ trợ:")

# ================= TEXT =================

async def text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    txt = update.message.text.strip()

    if context.user_data.get("wd"):
        amt = int(txt)
        u = get_user(uid)
        if u[1] < amt:
            await update.message.reply_text("❌ Không đủ số dư", reply_markup=main_menu())
            context.user_data.clear()
            return
        context.user_data["wd_amt"] = amt
        context.user_data["wd"] = False
        context.user_data["wd_bank"] = True
        await update.message.reply_text("Nhập STK / Ví:")

    elif context.user_data.get("wd_bank"):
        amt = context.user_data["wd_amt"]
        cur.execute("INSERT INTO withdrawals(user_id,amount,bank,status,created_at) VALUES (?,?,?,?,?)",
                    (uid, amt, txt, "pending", datetime.now().isoformat()))
        conn.commit()
        await update.message.reply_text("⏳ Đã gửi yêu cầu rút", reply_markup=main_menu())
        await context.bot.send_message(
            ADMIN_ID,
            f"DUYỆT RÚT\nUser: {uid}\nTiền: {amt}\nSTK: {txt}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("DUYỆT", callback_data=f"ad_wd_ok_{uid}_{amt}"),
                InlineKeyboardButton("TỪ CHỐI", callback_data=f"ad_wd_no_{uid}_{amt}")
            ]])
        )
        context.user_data.clear()

    elif context.user_data.get("gift"):
        cur.execute("SELECT * FROM giftcodes WHERE code=? AND used=0", (txt,))
        row = cur.fetchone()
        if not row:
            await update.message.reply_text("❌ Code không hợp lệ")
        else:
            add_balance(uid, row[1])
            cur.execute("UPDATE giftcodes SET used=1 WHERE code=?", (txt,))
            conn.commit()
            await update.message.reply_text(f"🎁 Nhận thành công +{row[1]}")
        context.user_data.clear()

    elif context.user_data.get("support"):
        await context.bot.send_message(ADMIN_ID, f"CSKH từ {uid}:\n{txt}")
        await update.message.reply_text("📨 Đã gửi hỗ trợ", reply_markup=main_menu())
        context.user_data.clear()

# ================= RUN =================

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(callbacks))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_input))

app.run_polling()
