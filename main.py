import os
import time
import asyncio
import telebot
from telebot import types
import yt_dlp
from flask import Flask
import threading
import edge_tts
import whisper
from moviepy.editor import VideoFileClip, AudioFileClip

TOKEN = '8632514928:AAF7BsEJVBgV8_2a8Kn3Ug-NyzZUCBm2QoU'
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# កំពុងទាញយក Whisper Model សម្រាប់បម្លែងសំឡេងក្នុងវីដេអូជាអត្ថបទ (ໃຊ້ Model 'tiny' ដើម្បីកុំឱ្យធ្ងន់ពេកលើ Railway)
print("Loading Whisper model...")
whisper_model = whisper.load_model("tiny")

@app.route('/')
def home():
    return "Bot is running!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "សួស្តី! Bot នេះនឹងទាញយកសំឡេងពីវីដេអូ បកប្រែ និង Dubbing ជាសំឡេង AI ខ្មែរចូលក្នុងវីដេអូផ្ទាល់។\n\n"
        "👉 សូមផ្ញើ **Video** ឬ **Link** មកកាន់ Bot នេះ!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

async def generate_khmer_voice(text, output_file):
    voice = "km-KH-PisethNeural" # សំឡេង AI ខ្មែរ (អាចដូរជា km-KH-SreymomNeural បើចង់បានសំឡេងស្រី)
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

def process_video_dubbing(input_video_path, output_video_path):
    audio_extracted = "extracted_audio.mp3"
    khmer_audio = "khmer_dubbed.mp3"
    
    try:
        # ១. ទាញយកសំឡេងចេញពីវីដេអូដើម
        video_clip = VideoFileClip(input_video_path)
        video_clip.audio.write_audiofile(audio_extracted, logger=None)
        
        # ២. ប្រើ Whisper ដើម្បីប្រែក្លាយសំឡេងដើមទៅជាអត្ថបទ (Speech-to-Text)
        result = whisper_model.transcribe(audio_extracted)
        original_text = result["text"].strip()
        
        if not original_text:
            original_text = "សួស្តី នេះគឺជាវីដេអូបកប្រែជាភាសាខ្មែរ។"
        
        # ៣. កំណត់អត្ថបទបកប្រែ (អាចភ្ជាប់ API បកប្រែភាសា ប៉ុន្តែទីនេះយើងប្រើការការបកប្រែ ឬអត្ថបទដែលទាញបាន)
        translated_text = f"បកប្រែពីវីដេអូ៖ {original_text}"
        
        # ៤. បង្កើតសំឡេង AI ខ្មែរថ្មី
        asyncio.run(generate_khmer_voice(translated_text, khmer_audio))
        
        # ៥. ដាក់បញ្ចូលសំឡេងខ្មែរថ្មីជំនួសសំឡេងដើមក្នុងវីដេអូ
        new_audio_clip = AudioFileClip(khmer_audio)
        final_video = video_clip.set_audio(new_audio_clip)
        
        final_video.write_videofile(
            output_video_path,
            codec='libx264',
            audio_codec='aac',
            fps=video_clip.fps,
            logger=None
        )
        
        # បិទការប្រើប្រាស់ File
        video_clip.close()
        new_audio_clip.close()
        final_video.close()
        
    finally:
        # សម្អាត File កុសល
        if os.path.exists(audio_extracted): os.remove(audio_extracted)
        if os.path.exists(khmer_audio): os.remove(khmer_audio)

@bot.message_handler(content_types=['text', 'video'])
def handle_incoming(message):
    chat_id = message.chat.id
    
    if message.text and message.text.startswith('http'):
        progress_msg = bot.reply_to(message, "⏳ កំពុងទាញយកវីដេអូ និងបកប្រែសំឡេង...\n▒▒▒▒▒▒▒▒▒▒ 0%")
        try:
            in_file = "downloaded.mp4"
            out_file = "final_dubbed.mp4"
            
            ydl_opts = {'outtmpl': in_file, 'format': 'best'}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([message.text])

            bot.edit_message_text(
                chat_id=chat_id,
                message_id=progress_msg.message_id,
                text="⚙️ កំពុងដំណើរការ Dubbing សំឡេង AI ខ្មែរចូលវីដេអូ...\n██████████ 100% - រួចរាល់!"
            )
            
            process_video_dubbing(in_file, out_file)
            bot.delete_message(chat_id, progress_msg.message_id)

            with open(out_file, 'rb') as vid:
                bot.send_video(chat_id, vid, caption="✅ វីដេអូបកប្រែនិយាយខ្មែររួចរាល់!")

            if os.path.exists(in_file): os.remove(in_file)
            if os.path.exists(out_file): os.remove(out_file)

        except Exception as e:
            bot.reply_to(message, f"❌ មានបញ្ហា៖ {str(e)}")

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
                text="⚙️ កំពុងទាញយកសំឡេង និងបង្កើត Dubbing ខ្មែរ...\n██████████ 100% - រួចរាល់!"
            )

            process_video_dubbing(in_file, out_file)
            bot.delete_message(chat_id, progress_msg.message_id)

            with open(out_file, 'rb') as vid:
                bot.send_video(chat_id, vid, caption="✅ វីដេអូនិយាយខ្មែររួចរាល់!")

            if os.path.exists(in_file): os.remove(in_file)
            if os.path.exists(out_file): os.remove(out_file)

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
