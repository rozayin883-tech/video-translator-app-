from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/translate", methods=["POST"])
def translate():
    data = request.json
    link = data.get("link")
    return jsonify({"status": "success", "message": "បានទទួល Link វីដេអូរួចរាល់! កំពុងដំណើរការបកប្រែ..."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
