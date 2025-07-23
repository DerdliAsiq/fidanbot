import asyncio
import logging
import datetime
from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Telegram bot token
BOT_TOKEN = "8124444810:AAG_805OuJhBdS8qHI5RQXSexGzD-EQ2a_E"

# Yetkili admin kullanıcı ID'leri
AUTHORIZED_ADMINS = [6090879334, 6409436167]

# Telegram kanal ID’si (güncelleyebilirsin)
CHANNEL_ID = "@LoFiLyfe_Music"

# Günlük selamlar
GREETINGS = {
    "morning": "🌅 Sabahınız xeyir, dostlar! Yeni günə pozitiv başlayın!",
    "afternoon": "🌞 Günortanız xeyir! Enerjinizi yüksək tutun!",
    "evening": "🌇 Axşamınız xeyir! Gün necə keçdi?",
    "night": "🌙 Gecəniz xeyrə qalsın, yuxularınız şirin olsun!"
}

# Günlük selam mesajını gönderme işlevi
async def send_greeting(context: ContextTypes.DEFAULT_TYPE, time_of_day: str):
    if time_of_day in GREETINGS:
        message = GREETINGS[time_of_day]
        await context.bot.send_message(chat_id=CHANNEL_ID, text=message)

# Manuel selamlama komutu
async def greet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_ADMINS:
        await update.message.reply_text("❌ Bu əmri işlətmək üçün icazəniz yoxdur.")
        return

    if not context.args:
        await update.message.reply_text("İstifadə: /greet_morning | /greet_afternoon | /greet_evening | /greet_night")
        return

    command = update.message.text.lower()
    for key in GREETINGS:
        if key in command:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=GREETINGS[key])
            await update.message.reply_text(f"✅ {key} mesajı göndərildi.")
            return

    await update.message.reply_text("❌ Doğru bir zaman belirleyin: morning, afternoon, evening, night.")

# Yetkilendirme kontrolü gerektiren komut dekoratörü
def admin_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in AUTHORIZED_ADMINS:
            await update.message.reply_text("❌ Bu əmri işlətmək üçün icazəniz yoxdur.")
            return
        return await func(update, context)
    return wrapper

# Admin: Kullanıcı at
@admin_required
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ İstifadə: /kick <istifadəçi_id>")
        return
    try:
        user_id = int(context.args[0])
        await context.bot.ban_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        await update.message.reply_text(f"✅ {user_id} atıldı.")
    except Exception as e:
        await update.message.reply_text(f"❌ Hata: {e}")

# Admin: Kanal adı dəyiş
@admin_required
async def change_channel_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ İstifadə: /set_title <yeni_ad>")
        return
    new_title = " ".join(context.args)
    try:
        await context.bot.set_chat_title(chat_id=CHANNEL_ID, title=new_title)
        await update.message.reply_text(f"✅ Kanal adı dəyişdirildi: {new_title}")
    except Exception as e:
        await update.message.reply_text(f"❌ Hata: {e}")

# Admin: Başqa adminə icazə ver
@admin_required
async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ İstifadə: /promote <istifadəçi_id>")
        return
    try:
        user_id = int(context.args[0])
        await context.bot.promote_chat_member(
            chat_id=CHANNEL_ID,
            user_id=user_id,
            can_manage_chat=True,
            can_post_messages=True,
            can_edit_messages=True,
            can_delete_messages=True,
        )
        await update.message.reply_text(f"✅ {user_id} admin olaraq təyin edildi.")
    except Exception as e:
        await update.message.reply_text(f"❌ Hata: {e}")

def setup_jobs(scheduler: AsyncIOScheduler, app: Application):
    scheduler.add_job(
        send_greeting,
        CronTrigger(hour=8, minute=0, timezone="Asia/Baku"),
        args=[app.bot, "morning"],
    )
    scheduler.add_job(
        send_greeting,
        CronTrigger(hour=13, minute=0, timezone="Asia/Baku"),
        args=[app.bot, "afternoon"],
    )
    scheduler.add_job(
        send_greeting,
        CronTrigger(hour=18, minute=0, timezone="Asia/Baku"),
        args=[app.bot, "evening"],
    )
    scheduler.add_job(
        send_greeting,
        CronTrigger(hour=22, minute=0, timezone="Asia/Baku"),
        args=[app.bot, "night"],
    )

def main():
    logging.basicConfig(level=logging.INFO)
    scheduler = AsyncIOScheduler()

    app = Application.builder().token(BOT_TOKEN).build()

    # Komutlar
    app.add_handler(CommandHandler("greet", greet_command))
    app.add_handler(CommandHandler("kick", kick))
    app.add_handler(CommandHandler("set_title", change_channel_name))
    app.add_handler(CommandHandler("promote", promote))

    setup_jobs(scheduler, app)

    # Scheduler'ı başlat
    scheduler.start()

    # Botu çalıştır
    print("Bot başladı...")
    app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
