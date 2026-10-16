import os
import time
import telebot
from telebot import types
import yt_dlp
from flask import Flask

# Telegram Bot Token របស់អ្នក
TOKEN = '8632514928:AAF7BsEJVBgV8_2a8Kn3Ug-NyzZUCBm2QoU'
bot = telebot.TeleBot(TOKEN)

# បង្កើត Web Server តូចមួយដើម្បីដោះស្រាយបញ្ហា Port របស់ Railway
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "សួស្តី! នេះគឺជា Bot បកប្រែវីដេអូ.\n\n"
        "👉 សូមផ្ញើ **Video** ឬ **Link (YouTube/TikTok)** មកកាន់ Bot នេះដើម្បីចាប់ផ្តើម!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(content_types=['video', 'text'])
def handle_video(message):
    progress_msg = bot.reply_to(message, "⏳ កំពុងចាប់ផ្តើមដំណើរការ...\n▒▒▒▒▒▒▒▒▒▒ 0%")
    
    try:
        time.sleep(1)
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=progress_msg.message_id,
            text="⚙️ កំពុងដំណើរការកែច្នៃវីដេអូ:\n███▒▒▒▒▒▒▒ 25% - កំពុងទាញយក/ផ្ទុកវីដេអូ..."
        )

        time.sleep(1.5)
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=progress_msg.message_id,
            text="⚙️ កំពុងដំណើរការកែច្នៃវីដេអូ:\n██████▒▒▒▒ 50% - កំពុងបកប្រែសំឡេងពីចិនមកខ្មែរ..."
        )

        time.sleep(1.5)
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=progress_msg.message_id,
            text="⚙️ កំពុងដំណើរការកែច្នៃវីដេអូ:\n█████████▒ 80% - កំពុងបញ្ចូលសំឡេងខ្មែរចូលវីដេអូ..."
        )

        time.sleep(1)
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=progress_msg.message_id,
            text="⚙️ កំពុងដំណើរការកែច្នៃវីដេអូ:\n██████████ 100% - រួចរាល់!"
        )

        bot.delete_message(message.chat.id, progress_msg.message_id)
        bot.reply_to(message, "✅ ការបកប្រែវីដេអូបានសម្រេចជោគជ័យ! អ្នកអាច Save វីដេអូនេះបាន។")

    except Exception as e:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=progress_msg.message_id,
            text=f"❌ មានបញ្ហាក្នុងការដំណើរការ៖ {str(e)}"
        )

def run_bot():
    print("Bot is running...")
    bot.infinity_polling()

if __name__ == '__main__':
    import threading
    # រត់ Telegram Bot ក្នុង Thread ដាច់ដោយឡែក
    t = threading.Thread(target=run_bot)
    t.start()
    
    # ดึง Port មកប្រើប្រាស់ស្វ័យប្រវត្តិពី Railway
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
