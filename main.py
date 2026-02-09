# ===== OKVIP TELE BOT – PRO MAX =====
import asyncio, logging, random, aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from datetime import datetime, timedelta

TOKEN = "8209807211:AAEuUJmNHk4TzDAdLSxYMKZ7WljYSxe3U5g"
ADMIN_ID = 6050668835

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= DATABASE =================

async def db():
    return await aiosqlite.connect("bot.db")

async def init_db():
    async with await db() as con:
        await con.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            ref INTEGER DEFAULT 0,
            ref_count INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_check TEXT,
            lock INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS deposit(uid INTEGER, amount INTEGER);
        CREATE TABLE IF NOT EXISTS withdraw(uid INTEGER, amount INTEGER, info TEXT);

        CREATE TABLE IF NOT EXISTS gift(code TEXT PRIMARY KEY, value INTEGER, uses INTEGER);

        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT,
            reward INTEGER,
            condition INTEGER
        );

        CREATE TABLE IF NOT EXISTS event_done(uid INTEGER, event_id INTEGER);

        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
        """)
        await con.execute("INSERT OR IGNORE INTO settings VALUES('bank','Chưa cấu hình')")
        await con.commit()

# ================= KEYBOARD =================

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Nạp tiền", callback_data="deposit"),
         InlineKeyboardButton(text="🏧 Rút tiền", callback_data="withdraw")],
        [InlineKeyboardButton(text="🎁 Điểm danh", callback_data="checkin"),
         InlineKeyboardButton(text="👥 Mời bạn", callback_data="ref")],
        [InlineKeyboardButton(text="🎟 Gift Code", callback_data="gift"),
         InlineKeyboardButton(text="🎉 Sự kiện", callback_data="event")],
        [InlineKeyboardButton(text="🏆 Đua top", callback_data="top"),
         InlineKeyboardButton(text="🤝 Đại lý", callback_data="agent")],
        [InlineKeyboardButton(text="💬 CSKH", callback_data="support")]
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Duyệt nạp", callback_data="ad_dep"),
         InlineKeyboardButton(text="🏧 Duyệt rút", callback_data="ad_wd")],
        [InlineKeyboardButton(text="🎟 Tạo gift", callback_data="ad_gift"),
         InlineKeyboardButton(text="🎉 Tạo sự kiện", callback_data="ad_event")],
        [InlineKeyboardButton(text="🏦 Set ngân hàng", callback_data="ad_bank"),
         InlineKeyboardButton(text="🔒 Khoá user", callback_data="ad_lock")],
        [InlineKeyboardButton(text="🔄 Reset user", callback_data="ad_reset")]
    ])

def approve_kb(uid, amount, t):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Duyệt", callback_data=f"ok:{t}:{uid}:{amount}"),
        InlineKeyboardButton(text="❌ Huỷ", callback_data=f"deny:{t}:{uid}")
    ]])

# ================= START =================

@dp.message(CommandStart())
async def start(m: Message):
    ref = m.text.split()
    async with await db() as con:
        await con.execute("INSERT OR IGNORE INTO users(id) VALUES(?)", (m.from_user.id,))
        if len(ref) > 1:
            await con.execute("UPDATE users SET ref=? WHERE id=?", (int(ref[1]), m.from_user.id))
        await con.commit()

    if m.from_user.id == ADMIN_ID:
        await m.answer("🔥 ADMIN PANEL 🔥", reply_markup=admin_menu())
    else:
        await m.answer("🔥 OKVIP BOT KHUYẾN MÃI KÍNH CHÀO 🔥", reply_markup=main_menu())

# ================= AUTO CHECK LOCK =================

async def check_lock(uid):
    async with await db() as con:
        cur = await con.execute("SELECT lock FROM users WHERE id=?", (uid,))
        return (await cur.fetchone())[0]

# ================= ĐIỂM DANH =================

@dp.callback_query(F.data == "checkin")
async def checkin(c: CallbackQuery):
    uid = c.from_user.id
    today = datetime.now().strftime("%Y-%m-%d")

    async with await db() as con:
        cur = await con.execute("SELECT last_check, streak FROM users WHERE id=?", (uid,))
        last, streak = await cur.fetchone()

        if last == today:
            return await c.answer("Hôm nay đã điểm danh", show_alert=True)

        if last == (datetime.now()-timedelta(days=1)).strftime("%Y-%m-%d"):
            streak += 1
        else:
            streak = 1

        reward = 0
        if streak == 3: reward = 50000
        if streak == 7: reward = 200000
        if streak == 30: reward = 1500000

        await con.execute("UPDATE users SET last_check=?, streak=?, balance=balance+? WHERE id=?",
                          (today, streak, reward, uid))
        await con.commit()

    await c.message.answer(f"✅ Điểm danh thành công\n🔥 {streak} ngày\n🎁 +{reward:,}đ")

# ================= MỜI BẠN AUTO THƯỞNG =================

async def handle_ref(uid, amount):
    if amount < 50000: return
    async with await db() as con:
        cur = await con.execute("SELECT ref FROM users WHERE id=?", (uid,))
        ref = (await cur.fetchone())[0]
        if ref:
            await con.execute("UPDATE users SET ref_count=ref_count+1 WHERE id=?", (ref,))
            cur = await con.execute("SELECT ref_count FROM users WHERE id=?", (ref,))
            c = (await cur.fetchone())[0]

            if c % 3 == 0:
                await con.execute("UPDATE users SET balance=balance+297000 WHERE id=?", (ref,))

            await con.execute("UPDATE users SET balance=balance+99000 WHERE id=?", (ref,))

        await con.execute("UPDATE users SET balance=balance+99000 WHERE id=?", (uid,))
        await con.commit()

# ================= NẠP =================

@dp.callback_query(F.data == "deposit")
async def deposit(c: CallbackQuery):
    if await check_lock(c.from_user.id):
        return await c.answer("Đang xử lý giao dịch khác", show_alert=True)
    await c.message.answer("💰 Nhập số tiền nạp:")
    dp.message.register(get_dep)

async def get_dep(m: Message):
    if not m.text.isdigit(): return
    amount = int(m.text)

    async with await db() as con:
        await con.execute("UPDATE users SET lock=1 WHERE id=?", (m.from_user.id,))
        await con.execute("INSERT INTO deposit VALUES(?,?)", (m.from_user.id, amount))
        await con.commit()

    await bot.send_message(ADMIN_ID,
        f"💰 YÊU CẦU NẠP\nUser: {m.from_user.id}\nTiền: {amount:,}",
        reply_markup=approve_kb(m.from_user.id, amount, "dep"))

    await m.answer("⏳ Đã gửi yêu cầu, chờ duyệt")

# ================= ADMIN DUYỆT =================

@dp.callback_query(F.data.startswith("ok"))
async def ok(c: CallbackQuery):
    _, t, uid, amount = c.data.split(":")
    uid, amount = int(uid), int(amount)

    async with await db() as con:
        if t == "dep":
            await con.execute("UPDATE users SET balance=balance+?, lock=0 WHERE id=?", (amount, uid))
            await handle_ref(uid, amount)
        else:
            await con.execute("UPDATE users SET balance=balance-?, lock=0 WHERE id=?", (amount, uid))
        await con.commit()

    await bot.send_message(uid, f"✅ Giao dịch thành công {amount:,}đ")
    await c.message.edit_text("Đã duyệt")

# ================= CHẠY =================

async def main():
    logging.basicConfig(level=logging.INFO)
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

