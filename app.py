import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# កំណត់ទំហំអតិបរមាដល់ 200MB ដើម្បីអាច Upload វីដេអូរយៈពេល ១ ដល់ ៦ នាទីបានស្រួល
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_video():
    if 'video' not in request.files:
        return redirect(request.url)
    
    file = request.files['video']
    if file.filename == '':
        return redirect(request.url)
    
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        # ទីនេះអាចភ្ជាប់ទៅកាន់ AI Script សម្រាប់បកប្រែវីដេអូជាសំឡេង AI ភាសាខ្មែរ
        return render_template('result.html', filename=file.filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
