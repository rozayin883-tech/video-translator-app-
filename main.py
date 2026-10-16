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
        "សួស្តី! នេះគឺជា Bot បកប្រែវីដេអូជាសំឡេង AI ខ្មែរ។\n\n"
        "👉 សូមផ្ញើ **Video** ឬ **Link (YouTube/TikTok)** មកកាន់ Bot នេះដើម្បីចាប់ផ្តើម!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

async def generate_khmer_voice(text, output_file):
    voice = "km-KH-PisethNeural" 
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

@bot.message_handler(content_types=['text', 'video'])
def handle_incoming(message):
    chat_id = message.chat.id
    
    if message.text and message.text.startswith('http'):
        progress_msg = bot.reply_to(message, "⏳ កំពុងទាញយកវីដេអូ...\n▒▒▒▒▒▒▒▒▒▒ 0%")
        try:
            video_file = "downloaded_video.mp4"
            audio_file = "voice_output.mp3"
            
            ydl_opts = {'outtmpl': video_file, 'format': 'best'}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([message.text])

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=progress_msg.message_id,
                text="⚙️ កกำลังបង្កើតសំឡេង AI ខ្មែរ...\n██████████ 100% - រួចរាល់!"
            )
            
            translated_text = "សួស្តី! នេះគឺជាសំឡេង AI ខ្មែរដែលបានបកប្រែពីវីដេអូរបស់អ្នក។"
            asyncio.run(generate_khmer_voice(translated_text, audio_file))
            
            bot.delete_message(chat_id, progress_msg.message_id)

            # ផ្ញើទាំងវីដេអូ និងសំឡេង AI ជូនអ្នក
            with open(video_file, 'rb') as vid:
                bot.send_video(chat_id, vid, caption="✅ វីដេអូដើមរបស់អ្នក")
                
            with open(audio_file, 'rb') as aud:
                bot.send_voice(chat_id, aud, caption="🎙️ សំឡេងបកប្រែ AI ខ្មែរ")

            if os.path.exists(video_file): os.remove(video_file)
            if os.path.exists(audio_file): os.remove(audio_file)

        except Exception as e:
            bot.reply_to(message, f"❌ មានបញ្ហា៖ {str(e)}")

    elif message.video:
        progress_msg = bot.reply_to(message, "⏳ កំពុងទទួលវីដេអូរបស់អ្នក...\n▒▒▒▒▒▒▒▒▒▒ 0%")
        try:
            file_info = bot.get_file(message.video.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            video_file = "user_video.mp4"
            audio_file = "voice_output.mp3"
            
            with open(video_file, 'wb') as new_file:
                new_file.write(downloaded_file)

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=progress_msg.message_id,
                text="⚙️ កំពុងបង្កើតសំឡេង AI ខ្មែរ...\n██████████ 100% - រួចរាល់!"
            )

            translated_text = "សួស្តី! នេះគឺជាសំឡេង AI ខ្មែរដែលបានបកប្រែពីវីដេអូរបស់អ្នក។"
            asyncio.run(generate_khmer_voice(translated_text, audio_file))
            
            bot.delete_message(chat_id, progress_msg.message_id)

            with open(video_file, 'rb') as vid:
                bot.send_video(chat_id, vid, caption="✅ វីដេអូរបស់អ្នក")
                
            with open(audio_file, 'rb') as aud:
                bot.send_voice(chat_id, aud, caption="🎙️ សំឡេងបកប្រែ AI ខ្មែរ")

            if os.path.exists(video_file): os.remove(video_file)
            if os.path.exists(audio_file): os.remove(audio_file)

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
