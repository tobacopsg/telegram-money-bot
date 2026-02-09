import asyncio, logging, os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import aiosqlite

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 123456789

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== STATE =====
class Form(StatesGroup):
    nap = State()
    rut = State()

# ===== DB =====
async def init_db():
    async with aiosqlite.connect("data.db") as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            balance INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS deposit(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid INTEGER,
            amount INTEGER,
            status TEXT
        );
        """)
        await db.commit()

# ===== UI =====
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("💰 Nạp tiền", callback_data="nap"),
         InlineKeyboardButton("🏧 Rút tiền", callback_data="rut")],
        [InlineKeyboardButton("💳 Số dư", callback_data="balance")]
    ])

# ===== START =====
@dp.message(CommandStart())
async def start(m: types.Message):
    async with aiosqlite.connect("data.db") as db:
        await db.execute("INSERT OR IGNORE INTO users(id) VALUES(?)", (m.from_user.id,))
        await db.commit()
    await m.answer("🤖 OKVIP BOT KHUYẾN MÃI KÍNH CHÀO", reply_markup=main_menu())

# ===== BALANCE =====
@dp.callback_query(lambda c: c.data=="balance")
async def balance(c: types.CallbackQuery):
    async with aiosqlite.connect("data.db") as db:
        cur = await db.execute("SELECT balance FROM users WHERE id=?", (c.from_user.id,))
        bal = (await cur.fetchone())[0]
    await c.message.answer(f"💳 Số dư: {bal:,} VNĐ")

# ===== NẠP =====
@dp.callback_query(lambda c: c.data=="nap")
async def nap(c: types.CallbackQuery, state: FSMContext):
    await state.set_state(Form.nap)
    await c.message.answer("💰 Nhập số tiền cần nạp (1 = 1.000đ):")

@dp.message(Form.nap)
async def nap_process(m: types.Message, state: FSMContext):
    if not m.text.isdigit():
        return await m.answer("❌ Nhập số hợp lệ")

    amount = int(m.text) * 1000
    bonus = int(amount * 0.03)
    total = amount + bonus

    async with aiosqlite.connect("data.db") as db:
        cur = await db.execute("INSERT INTO deposit(uid,amount,status) VALUES (?,?,?)",
                               (m.from_user.id, amount, "pending"))
        await db.commit()
        dep_id = cur.lastrowid

    await state.clear()

    text = (
        "🏦 THÔNG TIN CHUYỂN KHOẢN\n\n"
        "Ngân hàng: MB BANK\n"
        "Chủ TK: NGUYEN VAN A\n"
        "STK: 0123456789\n"
        f"Nội dung: OKVIP {m.from_user.id}\n\n"
        f"💰 Số tiền: {amount:,} VNĐ\n"
        f"🎁 Thưởng +3%: {bonus:,} VNĐ\n"
        f"👉 Nhận: {total:,} VNĐ"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ ĐÃ CHUYỂN", callback_data=f"confirm_{dep_id}")],
        [InlineKeyboardButton("❌ HỦY GIAO DỊCH", callback_data=f"cancel_{dep_id}")]
    ])

    await m.answer(text, reply_markup=kb)

@dp.callback_query(lambda c: c.data.startswith("confirm_"))
async def confirm_nap(c: types.CallbackQuery):
    dep_id = int(c.data.split("_")[1])

    async with aiosqlite.connect("data.db") as db:
        cur = await db.execute("SELECT uid,amount FROM deposit WHERE id=? AND status='pending'", (dep_id,))
        row = await cur.fetchone()
        if not row:
            return await c.message.answer("❌ Giao dịch không tồn tại hoặc đã xử lý")

    uid, amount = row

    await bot.send_message(
        ADMIN_ID,
        f"🔔 DUYỆT NẠP\nUID: {uid}\n💰 {amount:,}\n"
        f"/duyet_{dep_id}\n/huy_{dep_id}"
    )

    await c.message.answer("⏳ Đã gửi admin duyệt")

@dp.callback_query(lambda c: c.data.startswith("cancel_"))
async def cancel_nap(c: types.CallbackQuery):
    dep_id = int(c.data.split("_")[1])
    async with aiosqlite.connect("data.db") as db:
        await db.execute("UPDATE deposit SET status='cancel' WHERE id=?", (dep_id,))
        await db.commit()
    await c.message.answer("❌ Đã hủy giao dịch")

# ===== ADMIN DUYỆT =====
@dp.message(lambda m: m.text.startswith("/duyet_"))
async def admin_duyet(m: types.Message):
    if m.from_user.id != ADMIN_ID:
        return

    dep_id = int(m.text.split("_")[1])

    async with aiosqlite.connect("data.db") as db:
        cur = await db.execute("SELECT uid,amount FROM deposit WHERE id=? AND status='pending'", (dep_id,))
        row = await cur.fetchone()
        if not row:
            return await m.answer("❌ Giao dịch không hợp lệ")

        uid, amount = row
        bonus = int(amount * 0.03)
        total = amount + bonus

        await db.execute("UPDATE deposit SET status='done' WHERE id=?", (dep_id,))
        await db.execute("UPDATE users SET balance = balance + ? WHERE id=?", (total, uid))
        await db.commit()

    await bot.send_message(uid, f"✅ Nạp thành công {total:,} VNĐ")
    await m.answer("Đã duyệt")

@dp.message(lambda m: m.text.startswith("/huy_"))
async def admin_huy(m: types.Message):
    if m.from_user.id != ADMIN_ID:
        return
    dep_id = int(m.text.split("_")[1])

    async with aiosqlite.connect("data.db") as db:
        await db.execute("UPDATE deposit SET status='cancel' WHERE id=?", (dep_id,))
        await db.commit()

    await m.answer("Đã hủy")

# ===== RUN =====
async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
