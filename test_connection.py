import requests
import logging

TELEGRAM_BOT_TOKEN = "8563713892:AAEYJwvHcMw6qKN8hMg1PkcCgRtD20VOISQ"
TELEGRAM_CHAT_ID = "1659649643"

def send_test_message():
    message = "🔔 <b>Test de Conexión</b>\n\nSi lees esto, el bot tiene acceso correcto a tu Telegram."
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    print(f"Sending test message to {TELEGRAM_CHAT_ID}...")
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("YES! Message sent successfully!")
        return True
    except Exception as e:
        print(f"NO! Failed to send message: {e}")
        return False

if __name__ == "__main__":
    send_test_message()
