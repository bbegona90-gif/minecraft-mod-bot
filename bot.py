import asyncio
import json
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.enums import ChatMemberStatus

TOKEN = os.getenv("8210579716:AAGtgHEAz3IDcB2mQH9T92Cg7zpSKG1zPj8")
CHANNEL_USERNAME = "@blacklord_uz"   # kanal username
ADMIN_ID = 1331356868  # admin id

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_FILE = "mods.json"
USERS_FILE = "users.json"

# Fayllarni yaratish
for file in [DB_FILE, USERS_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)

def load(file):
    with open(file, "r") as f:
        return json.load(f)

def save(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def save_user(user_id):
    users = load(USERS_FILE)
    if str(user_id) not in users:
        users[str(user_id)] = True
        save(USERS_FILE, users)

adding_mod = {}
broadcast_mode = False

# ================= START =================
@dp.message(Command("start"))
async def start_handler(message: Message):
    save_user(message.from_user.id)
    await message.answer("🔥 Minecraft Mod Botga xush kelibsiz!")

# ================= ADMIN PANEL =================
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Mod qo‘shish", callback_data="add_mod")],
            [InlineKeyboardButton(text="🗑 Mod o‘chirish", callback_data="delete_mod")],
            [InlineKeyboardButton(text="📊 Statistika", callback_data="stats")],
            [InlineKeyboardButton(text="📣 Broadcast", callback_data="broadcast")]
        ]
    )

    await message.answer("⚙ ADMIN PANEL", reply_markup=keyboard)

# ================= MOD QO‘SHISH =================
@dp.callback_query(F.data == "add_mod")
async def add_mod_button(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    adding_mod[callback.from_user.id] = {}
    await callback.message.answer("Rasmni caption bilan yuboring")

@dp.message(F.photo)
async def get_photo(message: Message):
    if message.from_user.id in adding_mod:
        adding_mod[message.from_user.id]["photo"] = message.photo[-1].file_id
        adding_mod[message.from_user.id]["caption"] = message.caption or ""
        await message.answer("Endi APK faylni yuboring")

@dp.message(F.document)
async def get_apk(message: Message):
    if message.from_user.id in adding_mod:
        data = load(DB_FILE)
        mod_id = str(len(data) + 1)

        data[mod_id] = {
            "photo": adding_mod[message.from_user.id]["photo"],
            "caption": adding_mod[message.from_user.id]["caption"],
            "file": message.document.file_id,
            "downloads": 0
        }

        save(DB_FILE, data)
        del adding_mod[message.from_user.id]
        await message.answer("✅ Mod saqlandi!")

# ================= MOD O‘CHIRISH =================
@dp.callback_query(F.data == "delete_mod")
async def show_mods(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    data = load(DB_FILE)

    if not data:
        await callback.message.answer("Modlar yo‘q ❌")
        return

    keyboard = []
    for mod_id in data:
        keyboard.append(
            [InlineKeyboardButton(
                text=f"🗑 O‘chirish ID {mod_id}",
                callback_data=f"delete_{mod_id}"
            )]
        )

    await callback.message.answer(
        "O‘chirmoqchi bo‘lgan modni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@dp.callback_query(F.data.startswith("delete_"))
async def delete_selected(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    mod_id = callback.data.split("_")[1]
    data = load(DB_FILE)

    if mod_id in data:
        del data[mod_id]
        save(DB_FILE, data)
        await callback.message.answer("✅ Mod o‘chirildi!")

# ================= DOWNLOAD =================
@dp.callback_query(F.data.startswith("download_"))
async def download(callback: CallbackQuery):
    mod_id = callback.data.split("_")[1]
    data = load(DB_FILE)

    member = await bot.get_chat_member(CHANNEL_USERNAME, callback.from_user.id)

    if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="🔔 Obuna bo‘lish",
                    url=f"https://t.me/{CHANNEL_USERNAME[1:]}"
                )]
            ]
        )
        await callback.message.answer("Avval kanalga obuna bo‘ling ❗", reply_markup=keyboard)
        return

    if mod_id in data:
        mod = data[mod_id]
        mod["downloads"] += 1
        save(DB_FILE, data)

        await callback.message.answer_photo(
            photo=mod["photo"],
            caption=mod["caption"]
        )

        await callback.message.answer_document(
            document=mod["file"],
            caption="📦 APK yuklab oling"
        )

        await callback.answer("Yuklab olindi ✅")

# ================= STATISTIKA =================
@dp.callback_query(F.data == "stats")
async def stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    data = load(DB_FILE)
    users = load(USERS_FILE)
    total_downloads = sum(mod["downloads"] for mod in data.values())

    text = f"""
📊 Statistika

👤 Foydalanuvchilar: {len(users)}
📦 Modlar: {len(data)}
⬇️ Yuklab olish: {total_downloads}
"""
    await callback.message.answer(text)

# ================= BROADCAST =================
@dp.callback_query(F.data == "broadcast")
async def broadcast_start(callback: CallbackQuery):
    global broadcast_mode
    if callback.from_user.id != ADMIN_ID:
        return

    broadcast_mode = True
    await callback.message.answer("📣 Yubormoqchi bo‘lgan xabarni yuboring")

@dp.message()
async def handle_messages(message: Message):
    global broadcast_mode
    save_user(message.from_user.id)

    if broadcast_mode and message.from_user.id == ADMIN_ID:
        users = load(USERS_FILE)
        success = 0

        for user_id in users:
            try:
                await message.copy_to(int(user_id))
                success += 1
            except:
                pass

        broadcast_mode = False
        await message.answer(f"✅ Broadcast tugadi!\nYuborildi: {success}")

# ================= RUN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
