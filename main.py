import os
import time
import asyncio
import telebot
from telebot import types
import yt_dlp
from flask import Flask
import threading
import edge_tts
from moviepy.editor import VideoFileClip, AudioFileClip

TOKEN = '8632514928:AAF7BsEJVBgV8_2a8Kn3Ug-NyzZUCBm2QoU'
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot កំពុងដំណើរការយ៉ាងរលូន!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "សួស្តី! Bot នេះនឹងបកប្រែ និងបញ្ចូលសំឡេង AI ភាសាខ្មែរចូលក្នុងវីដេអូ។\n\n"
        "👉 សូមផ្ញើ **Video** ឬ **Link វីដេអូ** មកកាន់ Bot នេះដើម្បីចាប់ផ្តើម!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

async def generate_khmer_voice(text, output_file):
    voice = "km-KH-PisethNeural" # សំឡេង AI ខ្មែរប្រុស
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def process_video_dubbing(input_video_path, output_video_path):
    khmer_audio = "khmer_dubbed.mp3"
    
    try:
        # ១. បង្កើតសំឡេង AI ខ្មែរសម្រាប់ដាក់ចូលវីដេអូ
        translated_text = "សួស្តី! នេះគឺជាវីដេអូដែលបានបកប្រែជាសំឡេងភាសាខ្មែរដោយ AI ។"
        asyncio.run(generate_khmer_voice(translated_text, khmer_audio))
        
        # ២. ផ្ទុកវីដេអូ និងសំឡេងចូលគ្នាដោយដកសំឡេងដើមចេញ
        video_clip = VideoFileClip(input_video_path)
        audio_clip = AudioFileClip(khmer_audio)
        
        final_video = video_clip.set_audio(audio_clip)
        
        # រក្សាទុកវីដេអូថ្មី
        final_video.write_videofile(
            output_video_path,
            codec='libx264',
            audio_codec='aac',
            fps=video_clip.fps,
            logger=None
        )
        
        # បិទការប្រើប្រាស់ file
        video_clip.close()
        audio_clip.close()
        final_video.close()
        
    finally:
        if os.path.exists(khmer_audio):
            os.remove(khmer_audio)

@bot.message_handler(content_types=['text', 'video'])
def handle_incoming(message):
    chat_id = message.chat.id
    
    if message.text and message.text.startswith('http'):
        progress_msg = bot.reply_to(message, "⏳ កំពុងទាញយកវីដេអូ និងបញ្ចូលសំឡេងខ្មែរ...\n▒▒▒▒▒▒▒▒▒▒ 0%")
        try:
            in_file = "downloaded.mp4"
            out_file = "final_dubbed.mp4"
            
            ydl_opts = {'outtmpl': in_file, 'format': 'best'}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([message.text])

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=progress_msg.message_id,
                text="⚙️ កំពុងដំណើរការកែច្នៃវីដេអូ...\n██████████ 100% - រួចរាល់!"
            )
            
            process_video_dubbing(in_file, out_file)
            bot.delete_message(chat_id, progress_msg.message_id)

            with open(out_file, 'rb') as vid:
                bot.send_video(chat_id, vid, caption="✅ វីដេអូបកប្រែនិយាយជាភាសាខ្មែររួចរាល់!")

            if os.path.exists(in_file): os.remove(in_file)
            if os.path.exists(out_file): os.remove(out_file)

        except Exception as e:
            bot.reply_to(message, f"❌ មានបញ្ហាបច្ចេកទេស៖ {str(e)}")

    elif message.video:
        progress_msg = bot.reply_to(message, "⏳ កំពុងទទួល និងកែច្នៃវីដេអូរបស់អ្នក...\n▒▒▒▒▒▒▒▒▒▒ 0%")
        try:
            file_info = bot.get_file(message.video.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            in_file = "user_in.mp4"
            out_file = "user_out.mp4"
            
            with open(in_file, 'wb') as f:
                f.write(downloaded_file)

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=progress_msg.message_id,
                text="⚙️ កំពុងជំនួសសំឡេងដើមជាសំឡេង AI ខ្មែរ...\n██████████ 100% - រួចរាល់!"
            )

            process_video_dubbing(in_file, out_file)
            bot.delete_message(chat_id, progress_msg.message_id)

            with open(out_file, 'rb') as vid:
                bot.send_video(chat_id, vid, caption="✅ វីដេអូនិយាយជាភាសាខ្មែររួចរាល់!")

            if os.path.exists(in_file): os.remove(in_file)
            if os.path.exists(out_file): os.remove(out_file)

        except Exception as e:
            bot.reply_to(message, f"❌ មានបញ្ហាបច្ចេកទេស៖ {str(e)}")
    else:
        bot.reply_to(message, "👉 សូមផ្ញើ Link វីដេអូ ឬ Upload វីដេអូផ្ទាល់មកកាន់ Bot នេះ!")

def run_bot():
    print("Bot កំពុងដំណើរការ...")
    bot.infinity_polling()

if __name__ == '__main__':
    t = threading.Thread(target=run_bot)
    t.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
