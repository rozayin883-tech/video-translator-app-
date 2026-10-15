import os
import time
import threading
import uuid
import subprocess
from flask import Flask, render_template, request, jsonify, send_from_directory
import whisper
from deep_translator import GoogleTranslator
from gtts import gTTS

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

# โหลด Whisper AI Model (ប្រើ base model សម្រាប់ល្បឿនលឿននិងសមល្មម)
print("Loading Whisper AI Model...")
model = whisper.load_model("base")
print("Whisper AI Model Loaded Successfully!")

tasks = {}

@app.route('/')
def index():
    return render_template('index.html')

def process_video_ai(task_id, input_path, output_path):
    try:
        # ជំហានទី ១៖ ទាញយកសំឡេងចេញពីវីដេអូ (Extract Audio)
        tasks[task_id]['progress'] = 15
        tasks[task_id]['status_msg'] = 'กำลังแยกเสียงออกจากวิดีโอ...'
        audio_path = input_path.replace('.mp4', '.mp3')
        subprocess.run(['ffmpeg', '-y', '-i', input_path, '-q:a', '0', '-map', 'a', audio_path], check=True)

        # ជំហានទី ២៖ ប្រើប្រាស់ Whisper AI ដើម្បីស្តាប់និងបម្លែងសំឡេងចិនជាអត្ថបទ (STT)
        tasks[task_id]['progress'] = 40
        tasks[task_id]['status_msg'] = 'AI กำลังถอดเสียงภาษาจีน...'
        result = model.transcribe(audio_path, language="zh")
        chinese_text = result["text"]

        # ជំហានទី ៣៖ បកប្រែអត្ថបទពីចិនទៅជាភាសាខ្មែរ (Translation)
        tasks[task_id]['progress'] = 65
        tasks[task_id]['status_msg'] = 'กำลังแปลเป็นภาษาเขมร...'
        khmer_text = GoogleTranslator(source='zh-CN', target='km').translate(chinese_text)
        if not khmer_text:
            khmer_text = "សួស្តី នេះគឺជាការបកប្រែវីដេអូជាភាសាខ្មែរ"

        # ជំហានទី ៤៖ បង្កើតសំឡេងនិយាយ AI ភាសាខ្មែរ (Text-to-Speech)
        tasks[task_id]['progress'] = 80
        tasks[task_id]['status_msg'] = 'กำลังสร้างเสียงพูด AI ภาษาเขมร...'
        tts = gTTS(text=khmer_text, lang='km')
        khmer_audio_path = input_path.replace('.mp4', '_km.mp3')
        tts.save(khmer_audio_path)

        # ជំហានទី ៥៖ បញ្ចូលសំឡេងខ្មែរថ្មីជំនួសសំឡេងដើមក្នុងវីដេអូ (Muxing)
        tasks[task_id]['progress'] = 95
        tasks[task_id]['status_msg'] = 'กำลังรวมเสียงเข้ากับวิดีโอ...'
        subprocess.run([
            'ffmpeg', '-y', '-i', input_path, '-i', khmer_audio_path,
            '-c:v', 'copy', '-map', '0:v:0', '-map', '1:a:0',
            '-shortest', output_path
        ], check=True)

        tasks[task_id]['progress'] = 100
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['status_msg'] = 'แปลเสร็จสมบูรณ์!'
        tasks[task_id]['output_file'] = os.path.basename(output_path)

    except Exception as e:
        print("Error in AI processing:", e)
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['status_msg'] = str(e)

@app.route('/process', methods=['POST'])
def process_video():
    if 'video' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded'})
    
    file = request.files['video']
    if file:
        task_id = str(uuid.uuid4())
        filename = f"{task_id}_{file.filename}"
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"translated_{filename}")
        
        file.save(input_path)
        
        tasks[task_id] = {
            'status': 'processing',
            'progress': 5,
            'status_msg': 'กำลังอัปโหลดไฟล์...'
        }
        
        thread = threading.Thread(target=process_video_ai, args=(task_id, input_path, output_path))
        thread.start()
        
        return jsonify({'status': 'success', 'task_id': task_id})

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    if task_id in tasks:
        return jsonify(tasks[task_id])
    return jsonify({'status': 'not_found'})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
