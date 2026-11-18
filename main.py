
import os
import time
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def send_alert(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message
    }, timeout=15).raise_for_status()

if __name__ == "__main__":
    send_alert("🚀 FOMO Meme Hunter attivo! Test riuscito.")
  
