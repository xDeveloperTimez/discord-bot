#!/usr/bin/env python3
"""
Simplified cloud deployment for Google Cloud Run
Only runs main bot with essential features
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
        "message": "Discord bot is running"
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/ping')
def ping():
    return jsonify({"status": "pong"})

def start_main_bot():
    """Start only the main Guardian bot"""
    import subprocess
    import sys
    
    # Start main Guardian bot only
    subprocess.Popen([sys.executable, "main.py"])

if __name__ == "__main__":
    # Start main bot in background
    bot_thread = threading.Thread(target=start_main_bot, daemon=True)
    bot_thread.start()
    
    # Start web server (Google Cloud Run provides PORT environment variable)
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting simplified server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)