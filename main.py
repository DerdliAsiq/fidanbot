import os
import logging
import datetime
import asyncio
from pytube import YouTube
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from apscheduler.schedulers.background import BackgroundScheduler
import future

# --- Sabitler ---
BOT_TOKEN = "8124444810:AAG_805OuJhBdS8qHI5RQXSexGzD-EQ2a_E"
AUTHORIZED_ADMINS = ["6090879334", "6409436167"]
CHANNEL_ID = "@LoFiLyfe_MF"

# --- Loglama ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Selam mesajları ---
async def greet_channel(app):
    async with app:
        await app.bot.send_message(chat_id=CHANNEL_ID, text="(Avtomatik salam göndərildi)")
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
        await app.bot.send_message(chat_id=CHANNEL_ID, text=message)

def schedule_greetings(app):
    scheduler = BackgroundScheduler(timezone="Asia/Baku")
    scheduler.add_job(lambda: asyncio.run(greet_channel(app)), "cron", hour="8,14,20,23")
    scheduler.start()

# --- Komutlar ---

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktivdir. Komutları istifadə edə bilərsiniz.")

# /mesaj komutu - sadece admin kanala mesaj gönderir
async def mesaj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in AUTHORIZED_ADMINS:
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

# /video komutu - admin, Youtube linkinden video indirip kullanıcaya yollar
async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in AUTHORIZED_ADMINS:
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

# /mp3 komutu - admin, Youtube linkinden mp3 indirip kullanıcıya yollar
async def mp3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in AUTHORIZED_ADMINS:
        await update.message.reply_text("Bu əmri istifadə etmək səlahiyyətiniz yoxdur.")
        return

    if not context.args:
        await update.message.reply_text("Zəhmət olmasa YouTube linki əlavə edin.")
        return

    url = context.args[0]

    try:
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
        filename = audio_stream.download(filename="audio.mp4")

        # mp4 uzantılı ses dosyasını mp3 olarak gönderiyoruz
        mp3_filename = filename.rsplit('.', 1)[0] + ".mp3"
        # ffmpeg kullanarak dönüştür (ffmpeg yüklü olmalı)
        import subprocess
        subprocess.run([
            "ffmpeg", "-y", "-i", filename,
            "-vn", "-ab", "128k", "-ar", "44100", "-f", "mp3", mp3_filename
        ], check=True)

        with open(mp3_filename, 'rb') as audio_file:
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=audio_file)

        os.remove(filename)
        os.remove(mp3_filename)

    except Exception as e:
        logger.error(f"Mp3 yükləmə xətası: {e}")
        await update.message.reply_text("Xəta baş verdi. Linki və ya sesi yoxlayın.")

# /kick komutu - admin, kullanıcıyı grup veya kanalından atar
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in AUTHORIZED_ADMINS:
        await update.message.reply_text("Bu əmri istifadə etmək səlahiyyətiniz yoxdur.")
        return

    if not context.args:
        await update.message.reply_text("Zəhmət olmasa atmaq istədiyiniz istifadəçinin @id və ya istifadəçi adını yazın.")
        return

    user_to_kick = context.args[0]

    try:
        # @username veya ID şeklinde user
        chat = update.effective_chat
        if user_to_kick.startswith('@'):
            member = await chat.get_member(user_to_kick[1:])
        else:
            member = await chat.get_member(int(user_to_kick))

        await chat.kick_member(member.user.id)
        await update.message.reply_text(f"{user_to_kick} istifadəçisi qrupdan/kanaaldan atıldı.")

    except Exception as e:
        logger.error(f"Kick əmri xəta verdi: {e}")
        await update.message.reply_text("İstifadəçi atıla bilmədi.")

# /promote komutu - admin, kullanıcıya admin yetkisi verir
async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in AUTHORIZED_ADMINS:
        await update.message.reply_text("Bu əmri istifadə etmək səlahiyyətiniz yoxdur.")
        return

    if not context.args:
        await update.message.reply_text("Zəhmət olmasa təyin etmək istədiyiniz istifadəçinin @id və ya istifadəçi adını yazın.")
        return

    user_to_promote = context.args[0]

    try:
        chat = update.effective_chat
        if user_to_promote.startswith('@'):
            member = await chat.get_member(user_to_promote[1:])
        else:
            member = await chat.get_member(int(user_to_promote))

        await chat.promote_member(
            user_id=member.user.id,
            can_change_info=True,
            can_delete_messages=True,
            can_invite_users=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_promote_members=True
        )
        await update.message.reply_text(f"{user_to_promote} istifadəçisinə admin hüquqları verildi.")
    except Exception as e:
        logger.error(f"Promote əmri xəta verdi: {e}")
        await update.message.reply_text("İstifadəçi admin edilə bilmədi.")

# Sohbet mesajları (kullanıcılardan gelen metinlere cevap verir)
async def sohbet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Komut değil, düz mesaj ise cevap verir
    if update.message.text.startswith("/"):
        return

    user_text = update.message.text
    cevap = await future.sohbet_response(user_text)
    await update.message.reply_text(cevap)

# Bilinmeyen komut
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Belə bir əmr mövcud deyil. Zəhmət olmasa doğru komutu istifadə edin.")

# --- Ana fonksiyon ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Komutlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mesaj", mesaj))
    app.add_handler(CommandHandler("video", video))
    app.add_handler(CommandHandler("mp3", mp3))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("promote", promote))

    # Sohbet (sadece düz mesajlar, komut değil)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, sohbet))

    # Bilinmeyen komutlar
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Selam mesajlarını zamanla
    schedule_greetings(app)

    app.run_polling()

if __name__ == "__main__":
    main()
