import yfinance as yf
import requests
import time
import json
import os
import logging
from datetime import datetime, timedelta

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8563713892:AAEYJwvHcMw6qKN8hMg1PkcCgRtD20VOISQ")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1659649643")
TICKERS = ['AMZN', 'META', 'GOOGL', 'ASML', 'MSFT']

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
    # CATCH UP: Look back 24 HOURS (1440 mins)
    cutoff_time = datetime.utcnow() - timedelta(minutes=1440)

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
                link = content.get('clickThroughUrl', {}).get('url')
                if not link: link = content.get('canonicalUrl', {}).get('url')
                if not link: link = item.get('link')
                
                # Get Date
                pub_date = content.get('pubDate') or item.get('providerPublishTime')
                article_dt = None

                try:
                    if isinstance(pub_date, int):
                         article_dt = datetime.fromtimestamp(pub_date)
                    elif isinstance(pub_date, str):
                         clean_date = pub_date.replace('Z', '')
                         if '.' in clean_date: clean_date = clean_date.split('.')[0]
                         article_dt = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S")
                except Exception as e:
                    logging.warning(f"Date parse error for {title}: {e}")
                    continue

                # Filter by Time
                if article_dt and article_dt < cutoff_time:
                    logging.info(f"Skipping old article: {title} ({article_dt})")
                    continue

                # Deduplicate by Link
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
    logging.info("Starting Catch Up (24 hours)...")
    sent_news = set()
    count = fetch_and_process_news(sent_news)
    
    if count > 0:
        logging.info(f"Sent {count} catch-up articles.")
    else:
        logging.info("No new articles found in the last 24h.")

if __name__ == "__main__":
    main()
