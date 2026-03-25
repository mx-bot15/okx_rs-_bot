import os
import ccxt
import pandas as pd
import pandas_ta as ta
import requests
import time

# GitHub Secrets'dan gelecek veriler
OKX_API_KEY = os.getenv('OKX_API_KEY')
OKX_SECRET_KEY = os.getenv('OKX_SECRET_KEY')
OKX_PASSPHRASE = os.getenv('OKX_PASSPHRASE')
TG_TOKEN = os.getenv('TELEGRAM_TOKEN')
TG_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# OKX Bağlantı Yapılandırması
exchange = ccxt.okx({
    'apiKey': OKX_API_KEY,
    'secret': OKX_SECRET_KEY,
    'password': OKX_PASSPHRASE,
    'enableRateLimit': True,
})

def send_tg(msg):
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={TG_CHAT_ID}&text={msg}&parse_mode=Markdown"
        requests.get(url, timeout=10)
    except:
        pass

def get_all_usdt_pairs():
    try:
        exchange.load_markets()
        # Sadece USDT ile biten ve AKTİF olan spot pariteleri çekiyoruz
        pairs = [symbol for symbol, market in exchange.markets.items() 
                 if symbol.endswith('/USDT') and market['active'] and market['type'] == 'spot']
        return pairs
    except Exception as e:
        send_tg(f"❌ Market verisi çekilirken hata: {str(e)}")
        return []

def check_rsi_zirhli(symbol):
    try:
        # 1 saatlik mumlar, son 100 adet
        bars = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100)
        if not bars or len(bars) < 20:
            return None
            
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['close'] = df['close'].astype(float)
        
        # RSI 14 hesapla
        df['rsi'] = ta.rsi(df['close'], length=14)
        current_rsi = df['rsi'].iloc[-1]
        
        # Sadece RSI 20 ve altındaysa sinyal ver
        if current_rsi <= 20:
            return f"🚨 *{symbol}* \n📉 RSI: {current_rsi:.2f}\n📍 Durum: Aşırı Satış (Dip)"
            
    except:
        # Herhangi bir hata (bağlantı, veri eksikliği vs.) durumunda kodu durdurma, pas geç.
        return None

def main():
    all_pairs = get_all_usdt_pairs()
    if not all_pairs:
        return

    # Tarama başladığında bildirim istersen alttaki satırı açabilirsin
    # send_tg(f"🔍 Tarama başladı: {len(all_pairs)} parite kontrol ediliyor...")
    
    hits = []
    for symbol in all_pairs:
        result = check_rsi_zirhli(symbol)
        if result:
            hits.append(result)
        time.sleep(0.1) # OKX'i yormayalım

    if hits:
        full_report = "🚀 OKX RSI 20 FIRSATLARI 🚀\n\n" + "\n\n".join(hits)
        send_tg(full_report)
    else:
        print("Uygun fırsat bulunamadı.")

if name == "main":
    main()
