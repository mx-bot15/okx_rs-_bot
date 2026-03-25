import os
import telebot
import ccxt
import pandas as pd
import time

# --- GÜVENLİ AYARLAR (GitHub Secrets'tan okur) ---
API_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

bot = telebot.TeleBot(API_TOKEN)
exchange = ccxt.okx()

def calculate_rsi(data, window=14):
    """Wilder's Smoothing Method ile RSI hesaplar."""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def main():
    try:
        # Sembol listesi (İstersen buraya daha fazla ekleyebilirsin)
        symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
        results = []

        for symbol in symbols:
            # OKX'den son 100 mum verisini çek (1 saatlik periyot)
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # RSI Hesapla
            df['rsi'] = calculate_rsi(df['close'])
            last_rsi = round(df['rsi'].iloc[-1], 2)
            
            results.append(f"📊 *{symbol}*\nÖlçülen RSI: {last_rsi}")

        # Mesajı birleştir ve gönder
        final_msg = "🚀 *RSI Tarama Sonuçları (1s)*\n\n" + "\n\n".join(results)
        bot.send_message(CHAT_ID, final_msg, parse_mode='Markdown')
        print("Mesaj başarıyla gönderildi!")

    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    main()
