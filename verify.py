import yfinance as yf
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_news_fetch():
    tickers = ['AMZN', 'META', 'GOOGL', 'ASML', 'MSFT']
    print(f"Testing news fetch for: {tickers}")
    
    for ticker_symbol in tickers:
        try:
            print(f"\n--- Checking {ticker_symbol} ---")
            ticker = yf.Ticker(ticker_symbol)
            news = ticker.news
            if news:
                print(f"Success! Found {len(news)} articles.")
                # Debug: print keys of the first item
                first_item = news[0]
                print(f"First item keys: {first_item.keys()}")
                print(f"First item content: {first_item}")
            else:
                print("No news found (this might be normal if provider returns empty, but rare for big tech).")
        except Exception as e:
            print(f"Error fetching {ticker_symbol}: {e}")

if __name__ == "__main__":
    test_news_fetch()
