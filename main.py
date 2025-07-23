import os
import logging
import datetime
import pytz
import re
import tempfile
import asyncio
from dotenv import load_dotenv
from telegram import Update, ChatAdministratorRights
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    ContextTypes, CallbackContext
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import yt_dlp

# Yükləmə
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
AUTHORIZED_ADMINS = [int(i) for i in os.getenv("AUTHORIZED_ADMINS").split()]

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BAKU = pytz.timezone("Asia/Baku")

def is_authorized(user_id: int) -> bool:
    return user_id in AUTHORIZED_ADMINS

def normalize_chat_id(chat_str):
    if re.match(r"^-?\d+$", chat_str):
        return int(chat_str)
    return chat_str

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salam! Mən kanal idarəetmə botuyam 🎵")

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Sənin səlahiyyətin yoxdur.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("İstifadə: /kick @kanal @istifadəçi")
        return

    kanal_raw = context.args[0]
    user_raw = context.args[1]

    chat_id = normalize_chat_id(kanal_raw)
    username = user_raw.replace("@", "")

    try:
        user = await context.bot.get_chat_member(chat_id, username)
        await context.bot.ban_chat_member(chat_id, user.user.id)
        await update.message.reply_text(f"{user_raw} kanaldan çıxarıldı.")
    except Exception as e:
        await update.message.reply_text(f"Xəta baş verdi: {e}")

async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Sənin səlahiyyətin yoxdur.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("İstifadə: /promote @kanal @istifadəçi")
        return

    kanal_raw = context.args[0]
    user_raw = context.args[1]

    chat_id = normalize_chat_id(kanal_raw)
    username = user_raw.replace("@", "")

    try:
        user = await context.bot.get_chat_member(chat_id, username)
        await context.bot.promote_chat_member(
            chat_id=chat_id,
            user_id=user.user.id,
            privileges=ChatAdministratorRights(
                is_anonymous=False,
                can_manage_chat=True,
                can_post_messages=True,
                can_edit_messages=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_invite_users=True,
                can_change_info=True,
                can_pin_messages=True
            )
        )
        await update.message.reply_text(f"{user_raw} admin edildi.")
    except Exception as e:
        await update.message.reply_text(f"Xəta baş verdi: {e}")

async def rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Sənin səlahiyyətin yoxdur.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("İstifadə: /rename @kanal Yeni Kanal Adı")
        return

    kanal_raw = context.args[0]
    yeni_ad = " ".join(context.args[1:])

    chat_id = normalize_chat_id(kanal_raw)

    try:
        await context.bot.set_chat_title(chat_id=chat_id, title=yeni_ad)
        await update.message.reply_text(f"{kanal_raw} kanalının adı dəyişdirildi: {yeni_ad}")
    except Exception as e:
        await update.message.reply_text(f"Xəta baş verdi: {e}")

async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Sənin səlahiyyətin yoxdur.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("İstifadə: /mesaj @kanal İstədiyiniz mesaj")
        return

    kanal_raw = context.args[0]
    chat_id = normalize_chat_id(kanal_raw)
    mesaj_text = " ".join(context.args[1:])

    try:
        await context.bot.send_message(chat_id=chat_id, text=mesaj_text)
        await update.message.reply_text(f"Mesaj göndərildi: {mesaj_text}")
    except Exception as e:
        await update.message.reply_text(f"Xəta baş verdi: {e}")

async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("Sənin səlahiyyətin yoxdur.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("İstifadə: /video <YouTube və ya TikTok linki>")
        return

    url = context.args[0]

    msg = await update.message.reply_text("Video yüklənir, zəhmət olmasa gözləyin...")

    ydl_opts = {
        'format': 'mp4[height<=480]+bestaudio/best[ext=mp4]/best',
        'outtmpl': tempfile.gettempdir() + '/%(id)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
    }

    loop = asyncio.get_event_loop()

    try:
        def download_video():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        file_path = await loop.run_in_executor(None, download_video)

        await msg.edit_text("Video yükləndi, göndərilir...")

        with open(file_path, 'rb') as video_file:
            await context.bot.send_video(chat_id=update.effective_chat.id, video=video_file)

        await msg.delete()

        # İstersen dosya silme işlemi ekleyebilirsin:
        # os.remove(file_path)

    except Exception as e:
        await msg.edit_text(f"Video yüklənərkən xəta baş verdi: {e}")

async def send_greeting(context: CallbackContext):
    hour = datetime.datetime.now(BAKU).hour
    text = None
    if hour == 8:
        text = "🌅 Səhəriniz xeyir! ☀️"
    elif hour == 13:
        text = "Günortanız xeyir!"
    elif hour == 18:
        text = "🌇 Axşamınız xeyir!"
    elif hour == 23:
        text = "🌙 Gecəniz xeyrə qalsın!"
    else:
        return

    channel_list = [
        "@LoFiLyfe_Music",
    ]

    for ch in channel_list:
        try:
            await context.bot.send_message(chat_id=ch, text=text)
        except Exception as e:
            logging.error(f"Salam mesajı göndərilərkən xəta: {e}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    scheduler = AsyncIOScheduler(timezone=BAKU)
    for h in [8, 13, 18, 23]:
        scheduler.add_job(send_greeting, 'cron', hour=h, minute=0, args=[app.job_queue])
    scheduler.start()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("promote", promote))
    app.add_handler(CommandHandler("rename", rename))
    app.add_handler(CommandHandler("mesaj", mesaj))
    app.add_handler(CommandHandler("video", video))

    print("Bot işə düşdü...")
    app.run_polling()

if __name__ == "__main__":
    main()
