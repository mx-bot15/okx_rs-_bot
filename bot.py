import ccxt
import pandas as pd
import requests
import os
import time

# API Bilgileri (GitHub Secrets'dan çekilir)
API_KEY = os.getenv('OKX_API_KEY')
SECRET_KEY = os.getenv('OKX_SECRET_KEY')
PASSPHRASE = os.getenv('OKX_PASSPHRASE')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def run_scanner():
    exchange = ccxt.okx({'apiKey': API_KEY, 'secret': SECRET_KEY, 'password': PASSPHRASE})
    markets = exchange.load_markets()
    symbols = [s for s in markets if '/USDT' in s and markets[s]['active']]
    
    for symbol in symbols:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            rsi_series = get_rsi(df['close'])
            last_rsi = rsi_series.iloc[-1]
            
            if last_rsi < 30:
                msg = f"🔥 RSI AL SİNYALİ: {symbol} - RSI: {last_rsi:.2f}"
                requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}")
            elif last_rsi > 70:
                msg = f"❄️ RSI SAT SİNYALİ: {symbol} - RSI: {last_rsi:.2f}"
                requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}")
        except:
            continue

if name == "main":
    run_scanner()
