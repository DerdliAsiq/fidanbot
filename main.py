# bot.py

import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ChatActions
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from pytube import YouTube
from pydub import AudioSegment
import asyncio
import datetime

# === AYARLAR ===
BOT_TOKEN = "8124444810:AAG_805OuJhBdS8qHI5RQXSexGzD-EQ2a_E"
AUTHORIZED_ADMINS = [6090879334, 6409436167]  # Telegram ID'ler

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

CHANNEL_ID = -1002848039271  # LoFiLyfe_MF kanalı

# === SELAMLAMA SAATLERİ ===
GREETINGS = {
    "morning": (8, "🌄 Sabahınız xeyir! Yeni gün sizə bol enerji və uğur gətirsin!"),
    "afternoon": (13, "🌞 Günortanız xeyir! Gününüz məhsuldar keçsin!"),
    "evening": (18, "🌇 Axşamınız xeyir! Günün yorğunluğu geridə qalsın!"),
    "night": (23, "🌙 Gecəniz xeyrə qalsın! Rahat istirahətlər!")
}

# === SELAMLAMA SCHEDULE ===
async def scheduled_greetings():
    while True:
        now = datetime.datetime.now()
        for key, (hour, message) in GREETINGS.items():
            if now.hour == hour and now.minute == 0:
                await bot.send_message(CHANNEL_ID, message)
        await asyncio.sleep(60)

# === KOMUT: /video ===
@dp.message_handler(Command("video"))
async def video_handler(message: types.Message):
    url = message.get_args()
    if not url.startswith("http"):
        await message.reply("❌ Xəta baş verdi. Linki yoxlayın.")
        return
    try:
        await message.reply("⏳ Video endirilir, zəhmət olmasa gözləyin...")
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        file_path = stream.download(filename="video.mp4")
        await bot.send_chat_action(message.from_user.id, ChatActions.UPLOAD_VIDEO)
        await bot.send_video(chat_id=message.from_user.id, video=open(file_path, 'rb'), caption=yt.title)
        os.remove(file_path)
    except Exception as e:
        logging.exception(e)
        await message.reply("❌ Video yüklənərkən xəta baş verdi.")

# === KOMUT: /mp3 ===
@dp.message_handler(Command("mp3"))
async def mp3_handler(message: types.Message):
    url = message.get_args()
    if not url.startswith("http"):
        await message.reply("❌ Xəta baş verdi. Linki yoxlayın.")
        return
    try:
        await message.reply("🎵 MP3 hazırlanır, bir az gözləyin...")
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()
        out_file = stream.download(filename="temp_audio.mp4")
        mp3_file = "audio.mp3"
        AudioSegment.from_file(out_file).export(mp3_file, format="mp3")
        await bot.send_chat_action(message.from_user.id, ChatActions.UPLOAD_AUDIO)
        await bot.send_audio(chat_id=message.from_user.id, audio=open(mp3_file, 'rb'), title=yt.title)
        os.remove(out_file)
        os.remove(mp3_file)
    except Exception as e:
        logging.exception(e)
        await message.reply("❌ MP3 yüklənərkən xəta baş verdi.")

# === KOMUT: /kick ===
@dp.message_handler(Command("kick"))
async def kick_handler(message: types.Message):
    if message.from_user.id not in AUTHORIZED_ADMINS:
        await message.reply("❌ İcazəniz yoxdur.")
        return
    if not message.reply_to_message:
        await message.reply("Lütfən atılacaq istifadəçiyə cavab verin.")
        return
    try:
        await bot.kick_chat_member(chat_id=CHANNEL_ID, user_id=message.reply_to_message.from_user.id)
        await message.reply("✅ İstifadəçi atıldı.")
    except Exception as e:
        logging.exception(e)
        await message.reply("❌ İstifadəçi atıla bilmədi.")

# === KOMUT: /promote ===
@dp.message_handler(Command("promote"))
async def promote_handler(message: types.Message):
    if message.from_user.id not in AUTHORIZED_ADMINS:
        await message.reply("❌ İcazəniz yoxdur.")
        return
    if not message.reply_to_message:
        await message.reply("Lütfən yüksəldiləcək istifadəçiyə cavab verin.")
        return
    try:
        await bot.promote_chat_member(
            chat_id=CHANNEL_ID,
            user_id=message.reply_to_message.from_user.id,
            can_manage_chat=True,
            can_change_info=True,
            can_post_messages=True,
            can_edit_messages=True,
            can_invite_users=True,
            can_delete_messages=True
        )
        await message.reply("✅ İstifadəçi admin edildi.")
    except Exception as e:
        logging.exception(e)
        await message.reply("❌ İstifadəçi admin edilə bilmədi.")

# === KOMUT: /mesaj ===
@dp.message_handler(Command("mesaj"))
async def mesaj_handler(message: types.Message):
    if message.from_user.id not in AUTHORIZED_ADMINS:
        await message.reply("❌ İcazəniz yoxdur.")
        return
    text = message.get_args()
    if not text:
        await message.reply("Mesaj yazılmayıb.")
        return
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=text)
        await message.reply("✅ Mesaj göndərildi.")
    except Exception as e:
        logging.exception(e)
        await message.reply("❌ Mesaj göndərilə bilmədi.")

# === HATALI KOMUTLAR ===
@dp.message_handler()
async def unknown_command(message: types.Message):
    if message.text.startswith("/"):
        await message.reply("❓ Tanınmayan komut.")

# === BOTU BAŞLAT ===
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_greetings())
    executor.start_polling(dp, skip_updates=True)
