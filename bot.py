import ccxt
import telebot
import time

# --- AYARLAR ---
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1h'
RSI_PERIOD = 14
API_TOKEN = '7629531818:AAH97-mO75YqY11h2G8S-VqYy-N9S-Ait5M' # Senin Token
CHAT_ID = '6419572628' # Senin ID
bot = telebot.TeleBot(API_TOKEN)

def calculate_rsi_wilder(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    
    # İlk ortalamalar (Simple Moving Average)
    ma_up = up[:period+1].mean()
    ma_down = down[:period+1].mean()
    
    rsi = [0] * (period)
    
    # Wilder's Smoothing (Üstel Hareketli Ortalama benzeri)
    for i in range(period, len(series)):
        if i == period:
            current_ma_up = ma_up
            current_ma_down = ma_down
        else:
            current_ma_up = (current_ma_up * (period - 1) + up.iloc[i]) / period
            current_ma_down = (current_ma_down * (period - 1) + down.iloc[i]) / period
            
        rs = current_ma_up / current_ma_down if current_ma_down != 0 else 0
        rsi.append(100 - (100 / (1 + rs)))
    return rsi[-1]

def main():
    try:
        exchange = ccxt.okx()
        bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=100)
        import pandas as pd
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        rsi_value = calculate_rsi_wilder(df['close'], RSI_PERIOD)
        
        msg = f"📊 {SYMBOL} ({TIMEFRAME})\n💰 Fiyat: {df['close'].iloc[-1]}\n🔥 RSI: {rsi_value:.2f}"
        
        # Sadece 30 altı veya 70 üstü değil, çalıştığını görmek için her zaman atsın dersen:
        bot.send_message(CHAT_ID, msg)
        print(f"Mesaj gönderildi: {rsi_value}")

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    main()
