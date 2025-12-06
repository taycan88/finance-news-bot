import yfinance as yf
import requests
import time
import json
import os
import logging
from datetime import datetime

# Configuration
# Intentamos leer de variables de entorno (Mejor para GitHub Actions), si no, usamos los valores hardcodeados (Local)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8563713892:AAEYJwvHcMw6qKN8hMg1PkcCgRtD20VOISQ")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1659649643")
TICKERS = ['AMZN', 'META', 'GOOGL', 'ASML', 'MSFT']
STATE_FILE = "state.json"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_sent_news():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return set(json.load(f))
        except json.JSONDecodeError:
            return set()
    return set()

def save_sent_news(sent_news):
    with open(STATE_FILE, 'w') as f:
        json.dump(list(sent_news), f)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Telegram message: {e}")
        return False

def fetch_and_process_news(sent_news):
    new_articles_count = 0
    for ticker_symbol in TICKERS:
        logging.info(f"Checking news for {ticker_symbol}...")
        try:
            ticker = yf.Ticker(ticker_symbol)
            news_items = ticker.news
            
            for item in news_items:
                # Handle nested structure
                if 'content' in item:
                    content = item['content']
                    article_id = item.get('id')
                    title = content.get('title', 'No Title')
                    link = content.get('clickThroughUrl', {}).get('url')
                    if not link:
                        link = content.get('canonicalUrl', {}).get('url')
                    publisher = content.get('provider', {}).get('displayName', 'Unknown')
                    pub_date = content.get('pubDate', '')
                    time_str = pub_date.replace('T', ' ').replace('Z', '')
                else:
                    # Fallback
                    article_id = item.get('uuid') or item.get('link')
                    title = item.get('title', 'No Title')
                    link = item.get('link', '')
                    publisher = item.get('publisher', 'Unknown')
                    publish_time = item.get('providerPublishTime', 0)
                    time_str = datetime.fromtimestamp(publish_time).strftime("%Y-%m-%d %H:%M") if publish_time else "Recent"

                # Use URL as the unique identifier (more robust than ID for users seeing "same URL")
                unique_id = link
                if not unique_id:
                     unique_id = article_id # Fallback
                
                if unique_id not in sent_news:
                    message = (
                        f"<b>{title}</b>\n\n"
                        f"Target: #{ticker_symbol}\n"
                        f"Source: {publisher}\n"
                        f"Time: {time_str}\n\n"
                        f"{link}"
                    )
                    
                    logging.info(f"Sending news: {title}")
                    if send_telegram_message(message):
                        sent_news.add(unique_id)
                        new_articles_count += 1
                        time.sleep(1) # Rate limiting
        
        except Exception as e:
            logging.error(f"Error fetching news for {ticker_symbol}: {e}")
            
    return new_articles_count

def main():
    logging.info("Starting Finance News Bot (Single Execution)...")
    sent_news = load_sent_news()
    
    count = fetch_and_process_news(sent_news)
    
    if count > 0:
        save_sent_news(sent_news)
        logging.info(f"Sent {count} new articles. State updated.")
    else:
        logging.info("No new articles found.")

    logging.info("Execution finished.")

if __name__ == "__main__":
    main()
