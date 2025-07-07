#!/usr/bin/env python3
"""
Cloud deployment version for Google Cloud Run / Railway
"""
import os
import threading
import time
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "healthy",
        "service": "Guardian Discord Bot",
        "message": "Discord bots are running"
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

def start_discord_bots():
    """Start all Discord bots"""
    import subprocess
    import sys
    
    # Start main Guardian bot
    subprocess.Popen([sys.executable, "main.py"])
    time.sleep(5)
    
    # Start Purchase bot
    subprocess.Popen([sys.executable, "purchase_bot.py"])
    time.sleep(3)
    
    # Start Excel Help bot
    subprocess.Popen([sys.executable, "excel_help_bot.py"])

if __name__ == "__main__":
    # Start Discord bots in background
    bot_thread = threading.Thread(target=start_discord_bots, daemon=True)
    bot_thread.start()
    
    # Start web server (Google Cloud Run provides PORT environment variable)
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)