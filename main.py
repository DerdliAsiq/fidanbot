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

# Bot tokeni ve admin ID'leri doğrudan burada tanımlanıyor
BOT_TOKEN = "8124444810:AAG_805OuJhBdS8qHI5RQXSexGzD-EQ2a_E"
AUTHORIZED_ADMINS = ["6090879334", "6409436167"]

# Mesajların gönderileceği kanal ID'si
CHANNEL_ID = "@LoFiLyfe_MF"

# Loglama ayarları
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Selam mesajlarını otomatik zamanlayıcı ile gönderen fonksiyon
async def greet_channel(app):
    async with app:
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=4)))  # GMT+4 (Asia/Baku)
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
    # Sabah, öğlen, akşam ve gece saatlerinde selam gönder
    scheduler.add_job(lambda: asyncio.run(greet_channel(app)), "cron", hour="8,14,20,23")
    scheduler.start()

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktivdir. Komutları istifadə edə bilərsiniz.")

# /mesaj komutu - sadece adminler kullanabilir, mesaj kanala gönderilir
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

# /video komutu - YouTube linki alır, video kullanıcıya gönderilir (kanala değil)
async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Zəhmət olmasa YouTube video linki əlavə edin.")
        return

    url = context.args[0]

    try:
        yt = YouTube(url)
        # En düşük çözünürlükte mp4 video al
        stream = yt.streams.filter(progressive=True, file_extension='mp4').get_lowest_resolution()
        filename = stream.download(filename="video.mp4")

        # 50 MB'tan büyükse engelle
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

# /mp3 komutu - YouTube linkinden mp3 indirir, kullanıcıya gönderir (kanala değil)
async def mp3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Zəhmət olmasa YouTube audio linki əlavə edin.")
        return

    url = context.args[0]

    try:
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
        filename = stream.download(filename="audio.mp3")

        # 20 MB'tan büyükse engelle
        if os.path.getsize(filename) > 20 * 1024 * 1024:
            await update.message.reply_text("⚠️ Audio faylı çox böyükdür (maks. 20 MB).")
            os.remove(filename)
            return

        with open(filename, 'rb') as audio_file:
            await context.bot.send_audio(chat_id=update.effective_chat.id, audio=audio_file)

        os.remove(filename)

    except Exception as e:
        logger.error(f"Audio yükləmə xətası: {e}")
        await update.message.reply_text("Xəta baş verdi. Linki və ya audioyu yoxlayın.")

# /kick komutu - sadece admin kullanabilir, kullanıcıyı gruptan atar
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in AUTHORIZED_ADMINS:
        await update.message.reply_text("Bu əmri istifadə etmək səlahiyyətiniz yoxdur.")
        return

    if not context.args:
        await update.message.reply_text("Zəhmət olmasa atılacaq istifadəçinin ID və ya @username qeyd edin.")
        return

    target = context.args[0]

    try:
        await context.bot.ban_chat_member(chat_id=update.effective_chat.id, user_id=int(target))
        await update.message.reply_text(f"İstifadəçi {target} qrupdan atıldı.")
    except Exception as e:
        logger.error(f"Kullanıcı atma hatası: {e}")
        await update.message.reply_text("İstifadəçi atıla bilmədi. İD düzgün olduğundan əmin olun.")

# /promote komutu - sadece admin kullanabilir, kullanıcıyı admin yapar
async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in AUTHORIZED_ADMINS:
        await update.message.reply_text("Bu əmri istifadə etmək səlahiyyətiniz yoxdur.")
        return

    if not context.args:
        await update.message.reply_text("Zəhmət olmasa təyin olunacaq istifadəçinin ID və ya @username qeyd edin.")
        return

    target = context.args[0]

    try:
        await context.bot.promote_chat_member(
            chat_id=update.effective_chat.id,
            user_id=int(target),
            can_change_info=True,
            can_delete_messages=True,
            can_invite_users=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_promote_members=True
        )
        await update.message.reply_text(f"İstifadəçi {target} admin edildi.")
    except Exception as e:
        logger.error(f"Kullanıcı terfi ettirme hatası: {e}")
        await update.message.reply_text("İstifadəçi admin edilə bilmədi. İD düzgün olduğundan əmin olun.")

# Bilinmeyen komutlarda cevap
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Belə bir əmr mövcud deyil. Zəhmət olmasa doğru komutu istifadə edin.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Komutları ekle
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mesaj", mesaj))
    app.add_handler(CommandHandler("video", video))
    app.add_handler(CommandHandler("mp3", mp3))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("promote", promote))

    # Bilinmeyen komutları yakala
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Otomatik selamlamaları planla
    schedule_greetings(app)

    # Botu çalıştır
    app.run_polling()

if __name__ == "__main__":
    main()
