import os
import time
import threading
import uuid
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

# កន្លែងផ្ទុកស្ថានភាព Task នីមួយៗ
tasks = {}

@app.route('/')
def index():
    return render_template('index.html')

def background_process(task_id, duration):
    total_sec = 35
    if duration > 60 and duration <= 120:
        total_sec = 55
    elif duration > 120:
        total_sec = 80

    for i in range(1, total_sec + 1):
        time.sleep(1)
        progress = int((i / total_sec) * 100)
        if progress > 99:
            progress = 99
        tasks[task_id]['progress'] = progress
        tasks[task_id]['remaining'] = total_sec - i

    tasks[task_id]['progress'] = 100
    tasks[task_id]['status'] = 'completed'
    tasks[task_id]['remaining'] = 0

@app.route('/process', methods=['POST'])
def process_video():
    if 'video' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file'})
    
    file = request.files['video']
    duration = float(request.form.get('duration', 30))
    
    if file:
        task_id = str(uuid.uuid4())
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        tasks[task_id] = {
            'status': 'processing',
            'progress': 0,
            'remaining': 35,
            'filename': file.filename
        }
        
        thread = threading.Thread(target=background_process, args=(task_id, duration))
        thread.start()
        
        return jsonify({'status': 'success', 'task_id': task_id})

@app.route('/status/<task_id>', methods=['GET'])
def get_status(task_id):
    if task_id in tasks:
        return jsonify(tasks[task_id])
    return jsonify({'status': 'not_found'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
