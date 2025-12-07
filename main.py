import yfinance as yf
import requests
import time
import json
import os
import logging
from datetime import datetime, timedelta

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
    cutoff_time = datetime.now() - timedelta(hours=24) # Safety net: Don't go back further than 24h

    for ticker_symbol in TICKERS:
        logging.info(f"Checking news for {ticker_symbol}...")
        try:
            ticker = yf.Ticker(ticker_symbol)
            news_items = ticker.news
            
            for item in news_items:
                # Handle nested structure
                content = item.get('content', {})
                if not content: content = item

                title = content.get('title', item.get('title', 'No Title'))
                
                # Get Link (Unique ID)
                link = (content.get('clickThroughUrl') or {}).get('url')
                if not link: link = (content.get('canonicalUrl') or {}).get('url')
                if not link: link = item.get('link')
                
                # Get Date
                pub_date = content.get('pubDate') or item.get('providerPublishTime')
                article_dt = None

                try:
                    if isinstance(pub_date, int):
                         article_dt = datetime.fromtimestamp(pub_date)
                    elif isinstance(pub_date, str):
                         # Handle typical ISO formats
                         # Example: '2025-12-06T18:35:00Z'
                         clean_date = pub_date.replace('Z', '')
                         if '.' in clean_date: clean_date = clean_date.split('.')[0]
                         article_dt = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S")
                except Exception as e:
                    logging.warning(f"Date parse error for {title}: {e}")
                    continue

                # Filter by Time (Safety Net)
                if article_dt and article_dt < cutoff_time:
                   continue

                # Deduplicate by Link (or ID fallback)
                unique_id = link or item.get('id') or item.get('uuid')
                
                if unique_id and unique_id not in sent_news:
                    publisher = content.get('provider', {}).get('displayName') or item.get('publisher', 'Unknown')
                    time_str = article_dt.strftime("%Y-%m-%d %H:%M") if article_dt else "Recent"

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
                        time.sleep(1) 
        
        except Exception as e:
            logging.error(f"Error fetching news for {ticker_symbol}: {e}")
            
    return new_articles_count

def main():
    logging.info("Starting Finance News Bot...")
    
    # LOAD STATE
    sent_news = load_sent_news()
    logging.info(f"Loaded {len(sent_news)} previously sent articles.")
    
    # Run process
    count = fetch_and_process_news(sent_news)
    
    # SAVE STATE
    if count > 0:
        save_sent_news(sent_news)
        logging.info(f"Sent {count} new articles. State updated.")
    else:
        logging.info("No new articles found.")

    logging.info("Execution finished.")

if __name__ == "__main__":
    main()
