import os
from aiogram.client.default import DefaultBotProperties
import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.enums import ParseMode

TOKEN = os.getenv("8210579716:AAGtgHEAz3IDcB2mQH9T92Cg7zpSKG1zPj8")
ADMIN_ID = 1331356868
CHANNEL_USERNAME = "@blacklord_uz"

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# ================= DATABASE =================

def load_db():
    if not os.path.exists("database.json"):
        return {"last_id": 0, "mods": []}
    with open("database.json", "r") as f:
        return json.load(f)

def save_db(data):
    with open("database.json", "w") as f:
        json.dump(data, f, indent=4)

def load_users():
    if not os.path.exists("users.json"):
        return {"users": []}
    with open("users.json", "r") as f:
        return json.load(f)

def save_users(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=4)

# ================= OBUNA =================

async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ================= START =================

@dp.message(Command("start"))
async def start(message: Message):
    users = load_users()
    if message.from_user.id not in users["users"]:
        users["users"].append(message.from_user.id)
        save_users(users)

    if not await check_sub(message.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Obuna bo‘lish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]
        ])
        return await message.answer("❌ Kanalga obuna bo‘ling!", reply_markup=kb)

    await show_mods(message)

# ================= MODLAR RO‘YXATI =================

async def show_mods(message):
    db = load_db()
    buttons = []

    for mod in db["mods"]:
        buttons.append([
            InlineKeyboardButton(text=mod["name"], callback_data=f"mod_{mod['id']}")
        ])

    if not buttons:
        return await message.answer("📭 Hozircha mod yo‘q")

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("📦 Modni tanlang:", reply_markup=kb)

# ================= MOD YUBORISH =================

@dp.callback_query(F.data.startswith("mod_"))
async def send_mod(callback: CallbackQuery):
    mod_id = int(callback.data.split("_")[1])
    db = load_db()

    for mod in db["mods"]:
        if mod["id"] == mod_id:

            await callback.message.answer_photo(
                mod["photo_id"],
                caption=mod["caption"]
            )

            await callback.message.answer_document(
                mod["file_id"]
            )
            break

    await callback.answer()

# ================= ADMIN PANEL =================

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Ruxsat yo‘q")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Mod qo‘shish", callback_data="add_mod")],
        [InlineKeyboardButton(text="🗑 Mod o‘chirish", callback_data="delete_mod")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="stats")],
        [InlineKeyboardButton(text="📢 Reklama", callback_data="broadcast")]
    ])

    await message.answer("👑 Admin panel", reply_markup=kb)

# ================= MOD QO‘SHISH =================

adding = {}

@dp.callback_query(F.data == "add_mod")
async def add_mod_start(callback: CallbackQuery):
    adding[callback.from_user.id] = {"step": "photo"}
    await callback.message.answer("📷 Rasm yuboring (caption yozmang)")
    await callback.answer()

@dp.callback_query(F.data == "broadcast")
async def broadcast_start(callback: CallbackQuery):
    adding["broadcast"] = True
    await callback.message.answer("📢 Yuboriladigan matnni yuboring")
    await callback.answer()

@dp.message()
async def all_messages_handler(message: Message):

    # ===== BROADCAST =====
    if adding.get("broadcast"):
        users = load_users()
        for user in users["users"]:
            try:
                await bot.send_message(user, message.text)
            except:
                pass

        adding.pop("broadcast")
        return await message.answer("✅ Reklama yuborildi")

    # ===== ADD MOD =====
    if message.from_user.id not in adding:
        return

    state = adding[message.from_user.id]

    if state["step"] == "photo" and message.photo:
        state["photo_id"] = message.photo[-1].file_id
        state["step"] = "caption"
        return await message.answer("📝 Endi matn yuboring")

    if state["step"] == "caption" and message.text:
        state["caption"] = message.text
        state["step"] = "file"
        return await message.answer("📦 Endi APK yuboring")

    if state["step"] == "file" and message.document:
        state["file_id"] = message.document.file_id

        db = load_db()
        db["last_id"] += 1

        db["mods"].append({
            "id": db["last_id"],
            "name": state["caption"][:30],
            "photo_id": state["photo_id"],
            "caption": state["caption"],
            "file_id": state["file_id"]
        })

        save_db(db)
        del adding[message.from_user.id]

        return await message.answer("✅ Mod saqlandi!")

# ================= MOD O‘CHIRISH =================

@dp.callback_query(F.data == "delete_mod")
async def delete_list(callback: CallbackQuery):
    db = load_db()
    text = "ID yuboring:\n"
    for mod in db["mods"]:
        text += f"{mod['id']} - {mod['name']}\n"
    await callback.message.answer(text)
    await callback.answer()

@dp.message(F.text.regexp(r"^\d+$"))
async def delete_confirm(message: Message):
    db = load_db()
    mod_id = int(message.text)

    for mod in db["mods"]:
        if mod["id"] == mod_id:
            db["mods"].remove(mod)
            save_db(db)
            return await message.answer("🗑 O‘chirildi")

# ================= STAT =================

@dp.callback_query(F.data == "stats")
async def stats(callback: CallbackQuery):
    users = load_users()
    db = load_db()
    await callback.message.answer(
        f"👥 Users: {len(users['users'])}\n📦 Modlar: {len(db['mods'])}"
    )
    await callback.answer()

# ================= MAIN =================

async def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable topilmadi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
