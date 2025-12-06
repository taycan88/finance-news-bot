import yfinance as yf
from datetime import datetime

tickers = ['AMZN', 'META', 'GOOGL', 'ASML', 'MSFT']

print(f"Current UTC time: {datetime.utcnow()}")

for t in tickers:
    print(f"\n--- {t} ---")
    try:
        ticker = yf.Ticker(t)
        news = ticker.news
        for n in news:
            content = n.get('content', {})
            title = content.get('title', n.get('title'))
            pub_date = content.get('pubDate') or n.get('providerPublishTime')
            print(f"  [{pub_date}] {title}")
    except Exception as e:
        print(f"Error: {e}")
