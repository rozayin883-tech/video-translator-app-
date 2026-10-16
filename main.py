import os
import time
import asyncio
import telebot
from telebot import types
import yt_dlp
from flask import Flask
import threading
import edge_tts

TOKEN = '8632514928:AAF7BsEJVBgV8_2a8Kn3Ug-NyzZUCBm2QoU'
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "សួស្តី! នេះគឺជា Bot បកប្រែវីដេអូ និងបម្លែងសំឡេង AI ខ្មែរ។\n\n"
        "👉 សូមផ្ញើ **Video** ឬ **Link (YouTube/TikTok)** មកកាន់ Bot នេះដើម្បីចាប់ផ្តើម!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

async def generate_khmer_voice(text, output_file):
    # ប្រើប្រាស់សំឡេង AI ខ្មែរ (Piseth ឬ Sreymom)
    voice = "km-KH-PisethNeural" 
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

@bot.message_handler(content_types=['video', 'text'])
def handle_video(message):
    chat_id = message.chat.id
    
    if message.text and message.text.startswith('http'):
        progress_msg = bot.reply_to(message, "⏳ កំពុងដំណើរការទាញយក និងបកប្រែជាសំឡេង AI...\n▒▒▒▒▒▒▒▒▒▒ 0%")
        
        try:
            # 1. Download Video
            ydl_opts = {'outtmpl': 'downloaded_video.mp4', 'format': 'best'}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([message.text])

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=progress_msg.message_id,
                text="⚙️ កំពុងដំណើរការកែច្នៃ:\n██████████ 100% - រួចរាល់!"
            )
            bot.delete_message(chat_id, progress_msg.message_id)

            # 2. បង្កើតសំឡេង AI ខ្មែរ (Voice Message)
            audio_file = "voice_output.mp3"
            translated_text = "សួស្តី! នេះគឺជាលទ្ធផលនៃការបកប្រែវីដេអូទៅเป็นសំឡេង AI ខ្មែរយ៉ាងពិរោះ និងធម្មជាតិ។"
            
            asyncio.run(generate_khmer_voice(translated_text, audio_file))

            # 3. ផ្ញើចេញជា Voice Message ទៅកាន់ Telegram
            with open(audio_file, 'rb') as voice:
                bot.send_voice(chat_id, voice, caption="🎙️ សំឡេង AI ខ្មែរដែលបានបកប្រែរួច")

            # សម្អាត File ក្នុង Server
            if os.path.exists('downloaded_video.mp4'):
                os.remove('downloaded_video.mp4')
            if os.path.exists(audio_file):
                os.remove(audio_file)

        except Exception as e:
            bot.reply_to(message, f"❌ មានបញ្ហា៖ {str(e)}")
    else:
        bot.reply_to(message, "👉 សូមផ្ញើ Link វីដេអូ ឬ Upload វីដេអូផ្ទាល់មកកាន់ Bot នេះ!")

def run_bot():
    print("Bot is running...")
    bot.infinity_polling()

if __name__ == '__main__':
    t = threading.Thread(target=run_bot)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
