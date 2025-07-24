import os
import logging
import datetime
import asyncio
from pytube import YouTube
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from apscheduler.schedulers.background import BackgroundScheduler

from future import query_gemini_api  # future.py'den import

# -------- CONFIG --------
BOT_TOKEN = "8124444810:AAG_805OuJhBdS8qHI5RQXSexGzD-EQ2a_E"
AUTHORIZED_ADMINS = ["6090879334", "6409436167"]
CHANNEL_ID = "@LoFiLyfe_MF"

# -------- LOGGING --------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def is_admin(user_id: str) -> bool:
    return user_id in AUTHORIZED_ADMINS


async def greet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=4)))
    hour = now.hour
    if 6 <= hour < 12:
        message = "🌅 Səhəriniz xeyir!"
    elif 12 <= hour < 17:
        message = "☀️ Günortanız xeyir!"
    elif 17 <= hour < 21:
        message = "🌇 Axşamınız xeyir!"
    else:
        message = "🌙 Gecəniz xeyrə qalsın!"
    await context.bot.send_message(chat_id=CHANNEL_ID, text=message)


def schedule_greetings(app):
    scheduler = BackgroundScheduler(timezone="Asia/Baku")
    scheduler.add_job(lambda: asyncio.run(greet_channel(app)), "cron", hour="8,14,20,23")
    scheduler.start()


async def greet_channel(app):
    async with app:
        await app.bot.send_message(chat_id=CHANNEL_ID, text="(Avtomatik salam göndərildi)")
        await greet(None, app)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktivdir. Komutları istifadə edə bilərsiniz.")


async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("Bu əmri istifadə etmək səlahiyyətiniz yoxdur.")
        return

    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Zəhmət olmasa göndərmək istədiyiniz mesajı yazın.")
        return

    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=text)
        await update.message.reply_text("Mesaj uğurla kanala göndərildi.")
    except Exception as e:
        logger.error(f"Mesaj göndərilərkən xəta baş verdi: {e}")
        await update.message.reply_text("Xəta baş verdi.")


async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("Bu əmri istifadə etmək səlahiyyətiniz yoxdur.")
        return

    if not context.args:
        await update.message.reply_text("Zəhmət olmasa YouTube video linki əlavə edin.")
        return

    url = context.args[0]
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').get_lowest_resolution()
        filename = stream.download(filename="video.mp4")

        if os.path.getsize(filename) > 50 * 1024 * 1024:
            await update.message.reply_text("⚠️ Video faylı çox böyükdür (maks. 50 MB).")
            os.remove(filename)
            return

        with open(filename, 'rb') as video_file:
            await context.bot.send_video(chat_id=update.effective_chat.id, video=video_file)

        os.remove(filename)

    except Exception as e:
        logger.error(f"Video yükləmə xətası: {e}")
        await update.message.reply_text("Xəta baş verdi. Linki və ya videonu yoxlayın.")


async def mp3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("Bu əmri istifadə etmək səlahiyyətiniz yoxdur.")
        return

    if not context.args:
        await update.message.reply_text("Zəhmət olmasa YouTube video linki əlavə edin.")
        return

    url = context.args[0]
    try:
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
        filename = audio_stream.download(filename="audio.mp4")

        os.system(f"ffmpeg -y -i {filename} -vn -ab 128k -ar 44100 -f mp3 audio.mp3")

        if os.path.getsize("audio.mp3") > 50 * 1024 * 1024:
            await update.message.reply_text("⚠️ Ses faylı çox böyükdür (maks. 50 MB).")
            os.remove(filename)
            os.remove("audio.mp3")
            return

        with open("audio.mp3", 'rb') as audio_file:
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=audio_file)

        os.remove(filename)
        os.remove("audio.mp3")

    except Exception as e:
        logger.error(f"MP3 yükləmə xətası: {e}")
        await update.message.reply_text("Xəta baş verdi. Linki və ya videonu yoxlayın.")


async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("Bu əmri istifadə etmək səlahiyyətiniz yoxdur.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Kick etmək üçün bir mesajı cavablandırın.")
        return

    user_to_kick = update.message.reply_to_message.from_user.id
    try:
        await update.effective_chat.kick_member(user_to_kick)
        await update.message.reply_text("İstifadəçi qovuldu.")
    except Exception as e:
        logger.error(f"Kick əmri xətası: {e}")
        await update.message.reply_text("Kick əmri icra edilə bilmədi.")


async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("Bu əmri istifadə etmək səlahiyyətiniz yoxdur.")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Promote etmək üçün bir mesajı cavablandırın.")
        return

    user_to_promote = update.message.reply_to_message.from_user.id
    try:
        await update.effective_chat.promote_member(
            user_to_promote,
            can_change_info=True,
            can_delete_messages=True,
            can_invite_users=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_promote_members=True,
        )
        await update.message.reply_text("İstifadəçi admin edildi.")
    except Exception as e:
        logger.error(f"Promote əmri xətası: {e}")
        await update.message.reply_text("Promote əmri icra edilə bilmədi.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and not update.message.text.startswith("/"):
        user_text = update.message.text
        response = await query_gemini_api(user_text)
        await update.message.reply_text(response)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Belə bir əmr mövcud deyil. Zəhmət olmasa doğru komutu istifadə edin.")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mesaj", mesaj))
    app.add_handler(CommandHandler("video", video))
    app.add_handler(CommandHandler("mp3", mp3))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("promote", promote))

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    schedule_greetings(app)

    app.run_polling()


if __name__ == "__main__":
    main()
