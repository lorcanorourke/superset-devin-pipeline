import os, threading
from flask import Flask, request, jsonify
from orchestrator import run_automation
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"})

@app.route("/webhook", methods=["POST"])
def github_webhook():
    data = request.json
    if data.get("action") == "labeled":
        label_name = data.get("label", {}).get("name", "")
        if label_name == "devin-task":
            thread = threading.Thread(target=run_automation)
            thread.start()
            return jsonify({"message": "Devin automation started"}), 200
    return jsonify({"message": "No action taken"}), 200

@app.route("/trigger", methods=["POST"])
def manual_trigger():
    thread = threading.Thread(target=run_automation)
    thread.start()
    return jsonify({"message": "Automation triggered"}), 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)