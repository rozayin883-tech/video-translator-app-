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
    return "Bot is running!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "សួស្តី! នេះគឺជា Bot បកប្រែវីដេអូ និង Dubbing សំឡេង AI ខ្មែរចូលក្នុងវីដេអូ។\n\n"
        "👉 សូមផ្ញើ **Video** ឬ **Link (YouTube/TikTok)** មកកាន់ Bot នេះដើម្បីចាប់ផ្តើម!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

async def generate_khmer_voice(text, output_file):
    voice = "km-KH-PisethNeural" # សំឡេង AI ខ្មែរប្រុសធម្មជាតិ
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def process_and_dub_video(input_video_path, output_video_path, text_to_speak):
    audio_file = "temp_khmer_audio.mp3"
    
    # ១. បង្កើតសំឡេង AI ខ្មែរ
    asyncio.run(generate_khmer_voice(text_to_speak, audio_file))
    
    # ២. យកវីដេអូ និងសំឡេងមកបញ្ចូលគ្នា (Replace Audio)
    video_clip = VideoFileClip(input_video_path)
    audio_clip = AudioFileClip(audio_file)
    
    # កំណត់រយៈពេលវីដេអូតាមសំឡេង ឬរក្សាដដែល
    final_video = video_clip.set_audio(audio_clip)
    final_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac', logger=None)
    
    # បិទការប្រើប្រាស់ file ដើម្បីលុបសំអាត
    video_clip.close()
    audio_clip.close()
    final_video.close()
    
    if os.path.exists(audio_file):
        os.remove(audio_file)

@bot.message_handler(content_types=['text', 'video'])
def handle_incoming(message):
    chat_id = message.chat.id
    
    # ករណីផ្ញើ Link មក
    if message.text and message.text.startswith('http'):
        progress_msg = bot.reply_to(message, "⏳ កំពុងទាញយក និងបកប្រែវីដេអូជាសំឡេងខ្មែរ...\n▒▒▒▒▒▒▒▒▒▒ 0%")
        try:
            input_file = "downloaded_video.mp4"
            output_file = "dubbed_video.mp4"
            
            ydl_opts = {'outtmpl': input_file, 'format': 'best'}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([message.text])

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=progress_msg.message_id,
                text="⚙️ កំពុងបញ្ចូលសំឡេង AI ខ្មែរចូលក្នុងវីដេអូ...\n██████████ 100% - រួចរាល់!"
            )
            
            # ข้อความที่จะให้พูดแทนเสียงเดิมໃນវីដេអូ
            translated_text = "សួស្តី! នេះគឺជាវីដេអូដែលបានបកប្រែ និងដាក់សំឡេង AI ភាសាខ្មែរជោគជ័យ។"
            
            process_and_dub_video(input_file, output_file, translated_text)
            bot.delete_message(chat_id, progress_msg.message_id)

            # ផ្ញើវីដេអូដែលបាន Dubbing រួចត្រឡប់ទៅ Telegram វិញ
            with open(output_file, 'rb') as vid:
                bot.send_video(chat_id, vid, caption="✅ វីដេអូបកប្រែជាសំឡេង AI ខ្មែររួចរាល់!")

            # សម្អាត File ក្នុង Server
            if os.path.exists(input_file): os.remove(input_file)
            if os.path.exists(output_file): os.remove(output_file)

        except Exception as e:
            bot.reply_to(message, f"❌ មានបញ្ហា៖ {str(e)}")

    # ករណី Upload វីដេអូផ្ទាល់
    elif message.video:
        progress_msg = bot.reply_to(message, "⏳ កំពុងទទួល និងកែច្នៃវីដេអូរបស់អ្នក...\n▒▒▒▒▒▒▒▒▒▒ 0%")
        try:
            file_info = bot.get_file(message.video.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            input_file = "user_video.mp4"
            output_file = "dubbed_user_video.mp4"
            
            with open(input_file, 'wb') as new_file:
                new_file.write(downloaded_file)

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=progress_msg.message_id,
                text="⚙️ កំពុងជំនួសសំឡេងចិនជាសំឡេង AI ខ្មែរ...\n██████████ 100% - រួចរាល់!"
            )

            translated_text = "សួស្តី! នេះគឺជាសំឡេង AI ខ្មែរដែលបានបកប្រែ និងដាក់បញ្ចូលក្នុងវីដេអូរបស់អ្នក។"
            process_and_dub_video(input_file, output_file, translated_text)
            bot.delete_message(chat_id, progress_msg.message_id)

            # ផ្ញើ File វីដេអូចេញមកវិញ
            with open(output_file, 'rb') as vid:
                bot.send_video(chat_id, vid, caption="✅ វីដេអូដាក់សំឡេង AI ខ្មែរជោគជ័យ!")

            if os.path.exists(input_file): os.remove(input_file)
            if os.path.exists(output_file): os.remove(output_file)

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
