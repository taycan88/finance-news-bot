import yfinance as yf
import requests
import time
import json
import os
import logging
from datetime import datetime, timedelta

import google.generativeai as genai

# Configuration
# Intentamos leer de variables de entorno, pero si estan vacias (GitHub Actions sin secrets), usamos los valores hardcodeados
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    TELEGRAM_BOT_TOKEN = "8563713892:AAEYJwvHcMw6qKN8hMg1PkcCgRtD20VOISQ"

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
if not TELEGRAM_CHAT_ID:
    TELEGRAM_CHAT_ID = "1659649643"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 
TICKERS = ['AMZN', 'META', 'GOOGL', 'ASML', 'MSFT']
STATE_FILE = "state.json"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# AI Setup
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.0-flash')
        logging.info("Gemini AI configured successfully.")
    except Exception as e:
        logging.error(f"Failed to configure Gemini AI: {e}")
        model = None
else:
    logging.warning("GEMINI_API_KEY not found. AI filtering will be disabled.")
    model = None

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

def analyze_relevance(ticker, title):
    if not model:
        return True # Default to sending if AI is down
    
    try:
        prompt = (
            f"Act as a financial analyst. Does the news title '{title}' have a material impact "
            f"on the stock valuation or business outlook of {ticker}? "
            "Reply strictly with YES or NO."
        )
        response = model.generate_content(prompt)
        answer = response.text.strip().upper()
        
        if "YES" in answer:
            return True
        else:
            logging.info(f"AI Filtered out: {title} (Impact: Low/None)")
            return False
    except Exception as e:
        logging.error(f"AI Analysis failed for {title}: {e}")
        return True # Fallback to sending

def fetch_and_process_news(sent_news):
    new_articles_count = 0
    cutoff_time = datetime.now() - timedelta(hours=24) # Safety net
    
    # List to collect all potential messages: (datetime, unique_id, message_text, title)
    collected_messages = []

    seen_this_run = set()

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

                # Normalize Link (remove query params for better dedupe)
                if link and '?' in link:
                    link = link.split('?')[0]
                
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

                if article_dt and article_dt < cutoff_time:
                   continue

                unique_id = link or item.get('id') or item.get('uuid')
                
                if unique_id:
                    # Dedupe Logic
                    if unique_id in sent_news:
                        continue
                    if unique_id in seen_this_run:
                        continue
                    
                    seen_this_run.add(unique_id)

                    # AI CHECK
                    if not analyze_relevance(ticker_symbol, title):
                        sent_news.add(unique_id) # Mark as read so we don't re-check forever
                        continue
                    
                    publisher = content.get('provider', {}).get('displayName') or item.get('publisher', 'Unknown')
                    time_str = article_dt.strftime("%Y-%m-%d %H:%M") if article_dt else "Recent"

                    message = (
                        f"<b>{title}</b>\n\n"
                        f"Target: #{ticker_symbol}\n"
                        f"Source: {publisher}\n"
                        f"Time: {time_str}\n\n"
                        f"{link}"
                    )
                    
                    # Add to collection for sorting
                    # Standardize article_dt for sorting. If None, use min time to put it first (or max to last)
                    # Using timestamp 0 for safety if None, though logic above requires article_dt or "Recent"
                    sort_key = article_dt if article_dt else datetime.min
                    collected_messages.append({
                        'dt': sort_key,
                        'id': unique_id,
                        'msg': message,
                        'title': title
                    })
        
        except Exception as e:
            logging.error(f"Error fetching news for {ticker_symbol}: {e}")
            
    # SORTING: Oldest to Newest
    collected_messages.sort(key=lambda x: x['dt'])
    
    # SENDING
    if collected_messages:
        logging.info(f"Found {len(collected_messages)} relevant articles. Sending in chronological order...")
        for item in collected_messages:
            logging.info(f"Sending news ({item['dt']}): {item['title']}")
            if send_telegram_message(item['msg']):
                sent_news.add(item['id'])
                new_articles_count += 1
                time.sleep(1)
            
    return new_articles_count

def main():
    logging.info("Starting Finance News Bot...")
    # send_telegram_message("📢 Bot started! Checking for news...") # Debug msg
    
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
