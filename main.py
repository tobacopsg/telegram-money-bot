import asyncio, logging, random, time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite

TOKEN = "8209807211:AAEuUJmNHk4TzDAdLSxYMKZ7WljYSxe3U5g"
ADMIN_ID = 6050668835

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ================= DB =================

async def init_db():
    async with aiosqlite.connect("data.db") as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            ref INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_check INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS deposit(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid INTEGER,
            amount INTEGER,
            status TEXT
        );

        CREATE TABLE IF NOT EXISTS withdraw(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid INTEGER,
            amount INTEGER,
            status TEXT
        );

        CREATE TABLE IF NOT EXISTS giftcode(
            code TEXT PRIMARY KEY,
            value INTEGER,
            uses INTEGER
        );
        """)
        await db.commit()

# ================= UI =================

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Nạp tiền", callback_data="nap"),
         InlineKeyboardButton(text="🏧 Rút tiền", callback_data="rut")],
        [InlineKeyboardButton(text="📅 Điểm danh", callback_data="checkin"),
         InlineKeyboardButton(text="👥 Mời bạn", callback_data="ref")],
        [InlineKeyboardButton(text="🎯 Nhiệm vụ", callback_data="task"),
         InlineKeyboardButton(text="🏆 Đua top", callback_data="top")],
        [InlineKeyboardButton(text="🎁 Giftcode", callback_data="gift"),
         InlineKeyboardButton(text="📞 CSKH", callback_data="cskh")],
        [InlineKeyboardButton(text="🧾 Đăng ký đại lý", callback_data="agency")],
        [InlineKeyboardButton(text="💳 Số dư", callback_data="balance")]
    ])

# ================= START =================

@dp.message(CommandStart())
async def start(m: types.Message):
    async with aiosqlite.connect("data.db") as db:
        await db.execute("INSERT OR IGNORE INTO users(id) VALUES(?)", (m.from_user.id,))
        await db.commit()

    await m.answer("🤖 OKVIP BOT KHUYẾN MÃI KÍNH CHÀO\nChọn chức năng:", reply_markup=main_menu())

# ================= BALANCE =================

@dp.callback_query(lambda c: c.data=="balance")
async def balance(c: types.CallbackQuery):
    async with aiosqlite.connect("data.db") as db:
        cur = await db.execute("SELECT balance FROM users WHERE id=?", (c.from_user.id,))
        bal = (await cur.fetchone())[0]
    await c.message.answer(f"💳 Số dư: {bal:,} VNĐ")

# ================= DEPOSIT =================

@dp.callback_query(lambda c: c.data=="nap")
async def nap(c: types.CallbackQuery):
    await c.message.answer("💰 Nhập số tiền muốn nạp:")

@dp.message(lambda m: m.text.isdigit())
async def nap_process(m: types.Message):
    amount = int(m.text)
    async with aiosqlite.connect("data.db") as db:
        await db.execute("INSERT INTO deposit(uid,amount,status) VALUES(?,?,?)",
                         (m.from_user.id, amount, "pending"))
        await db.commit()

    await bot.send_message(ADMIN_ID,
        f"🔔 Nạp mới\nUID:{m.from_user.id}\n💰 {amount:,}\n/duyet_{m.from_user.id}_{amount}\n/huy_{m.from_user.id}_{amount}")
    await m.answer("⏳ Đã gửi yêu cầu nạp, chờ admin duyệt")

# ================= ADMIN APPROVE =================

@dp.message(lambda m: m.text.startswith("/duyet_"))
async def duyet(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    _, uid, amt = m.text.split("_")
    uid, amt = int(uid), int(amt)

    async with aiosqlite.connect("data.db") as db:
        await db.execute("UPDATE users SET balance = balance + ? + (?*30/100) WHERE id=?",
                         (amt, amt, uid))
        await db.commit()

    await bot.send_message(uid, f"✅ Nạp thành công {amt:,} +30% thưởng")

@dp.message(lambda m: m.text.startswith("/huy_"))
async def huy(m: types.Message):
    if m.from_user.id != ADMIN_ID: return
    _, uid, amt = m.text.split("_")
    await bot.send_message(int(uid), f"❌ Giao dịch nạp {amt} bị hủy")

# ================= WITHDRAW =================

@dp.callback_query(lambda c: c.data=="rut")
async def rut(c: types.CallbackQuery):
    await c.message.answer("🏧 Nhập số tiền muốn rút (tối thiểu 200k):")

@dp.message(lambda m: m.text.isdigit())
async def rut_process(m: types.Message):
    amt = int(m.text)
    if amt < 200000:
        return await m.answer("❌ Rút tối thiểu 200k")

    async with aiosqlite.connect("data.db") as db:
        cur = await db.execute("SELECT balance FROM users WHERE id=?", (m.from_user.id,))
        bal = (await cur.fetchone())[0]
        if bal < amt:
            return await m.answer("❌ Không đủ số dư")

        await db.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amt, m.from_user.id))
        await db.commit()

    await bot.send_message(ADMIN_ID,
        f"🏧 Yêu cầu rút\nUID:{m.from_user.id}\n💰 {amt:,}")
    await m.answer("⏳ Đã gửi yêu cầu rút")

# ================= CHECKIN =================

@dp.callback_query(lambda c: c.data=="checkin")
async def checkin(c: types.CallbackQuery):
    now = int(time.time())
    async with aiosqlite.connect("data.db") as db:
        cur = await db.execute("SELECT streak,last_check FROM users WHERE id=?", (c.from_user.id,))
        streak,last = await cur.fetchone()

        if now - last < 86400:
            return await c.message.answer("❌ Hôm nay đã điểm danh")

        streak += 1
        reward = 5000
        if streak == 3: reward = 50000
        if streak == 7: reward = 200000
        if streak == 30: reward = 1500000

        await db.execute("UPDATE users SET streak=?, last_check=?, balance=balance+? WHERE id=?",
                         (streak, now, reward, c.from_user.id))
        await db.commit()

    await c.message.answer(f"✅ Điểm danh ngày {streak}\n🎁 Nhận {reward:,}")

# ================= REF =================

@dp.callback_query(lambda c: c.data=="ref")
async def ref(c: types.CallbackQuery):
    link = f"https://t.me/YOUR_BOT?start={c.from_user.id}"
    await c.message.answer(f"👥 Link mời:\n{link}\n🎁 Mỗi người nạp ≥50k nhận 99k")

# ================= TOP FAKE =================

@dp.callback_query(lambda c: c.data=="top")
async def top(c: types.CallbackQuery):
    fake = [
        ("🥇 VIP_01", 18_500_000),
        ("🥈 VIP_02", 14_200_000),
        ("🥉 VIP_03", 10_000_000),
        ("⭐ VIP_04", 7_500_000),
        ("⭐ VIP_05", 5_000_000)
    ]
    txt="🏆 BXH TOP\n\n"
    for n,(u,m) in enumerate(fake,1):
        txt+=f"{n}. {u}: {m:,}\n"
    await c.message.answer(txt)

# ================= GIFTCODE =================

@dp.callback_query(lambda c: c.data=="gift")
async def gift(c: types.CallbackQuery):
    await c.message.answer("🎁 Nhập giftcode:")

@dp.message(lambda m: len(m.text)<=20)
async def gift_process(m: types.Message):
    async with aiosqlite.connect("data.db") as db:
        cur = await db.execute("SELECT value,uses FROM giftcode WHERE code=?", (m.text,))
        row = await cur.fetchone()
        if not row: return await m.answer("❌ Code không tồn tại")
        val,uses = row
        if uses<=0: return await m.answer("❌ Code đã hết")

        await db.execute("UPDATE giftcode SET uses=uses-1 WHERE code=?", (m.text,))
        await db.execute("UPDATE users SET balance=balance+? WHERE id=?", (val,m.from_user.id))
        await db.commit()

    await m.answer(f"🎉 Nhận {val:,}")

# ================= CSKH =================

@dp.callback_query(lambda c: c.data=="cskh")
async def cskh(c: types.CallbackQuery):
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Nạp",callback_data="cs_nap")],
        [InlineKeyboardButton(text="🏧 Rút",callback_data="cs_rut")],
        [InlineKeyboardButton(text="🎁 KM",callback_data="cs_km")],
        [InlineKeyboardButton(text="📣 Sự kiện",callback_data="cs_event")],
        [InlineKeyboardButton(text="🤝 Đại lý",callback_data="cs_agency")]
    ])
    await c.message.answer("📞 CSKH – chọn mục:",reply_markup=kb)

# ================= AGENCY =================

@dp.callback_query(lambda c: c.data=="agency")
async def agency(c: types.CallbackQuery):
    await c.message.answer("🧾 Gửi form đăng ký đại lý:\nTên | SĐT | Doanh thu dự kiến")

# ================= RUN =================

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__=="__main__":
    asyncio.run(main())

