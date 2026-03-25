import os
import telebot
import ccxt
import pandas as pd
import time

API_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

bot = telebot.TeleBot(API_TOKEN)
exchange = ccxt.okx()

def calculate_rsi(series, period=14):
    # TradingView (Wilder's) RSI Hesaplama Yöntemi
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return 100 - (100 / (1 + rs))

def main():
    try:
        markets = exchange.load_markets()
        symbols = [s for s in markets if '/USDT' in s and markets[s].get('active', True)]
        found_signals = []

        for symbol in symbols:
            try:
                # Daha fazla veri çekiyoruz (100 yerine 200) ki hesaplama doğru olsun
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=200)
                if len(ohlcv) < 50: continue
                
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                rsi_values = calculate_rsi(df['close'])
                last_rsi = round(rsi_values.iloc[-1], 2)

                # Mantıksız değerleri (0 veya 100 gibi) filtrele
                if last_rsi <= 20 and last_rsi > 1:
                    found_signals.append(f"🟢 *{symbol}* - RSI: {last_rsi}")
                elif last_rsi >= 80 and last_rsi < 99:
                    found_signals.append(f"🔴 *{symbol}* - RSI: {last_rsi}")
                
                time.sleep(0.05)
            except:
                continue

        if found_signals:
            msg = "🎯 *HASSAS RSI SİNYALLERİ (1s)*\n\n" + "\n".join(found_signals)
            bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
        else:
            print("Kritik seviye bulunamadı.")
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    main()
