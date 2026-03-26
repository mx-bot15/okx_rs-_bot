import os
import telebot
import asyncio
import ccxt.async_support as ccxt # Async desteği geldi
import pandas as pd

API_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

bot = telebot.TeleBot(API_TOKEN)

def calculate_rsi(series, period=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=period - 1, adjust=False).mean()
    ema_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ema_up / (ema_down + 1e-10) # 0'a bölünme hatasını engeller
    return 100 - (100 / (1 + rs))

async def fetch_and_check(exchange, symbol):
    try:
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100)
        if len(ohlcv) < 50: return None
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        rsi_values = calculate_rsi(df['close'])
        last_rsi = round(rsi_values.iloc[-1], 2)

        if 1 < last_rsi <= 20:
            return f"🟢 *{symbol}* - RSI: {last_rsi}"
        elif 80 <= last_rsi < 99:
            return f"🔴 *{symbol}* - RSI: {last_rsi}"
    except:
        return None

async def main():
    exchange = ccxt.okx({'enableRateLimit': True})
    try:
        markets = await exchange.load_markets()
        # Sadece aktif USDT pariteleri
        symbols = [s for s in markets if '/USDT' in s and markets[s].get('active', True)]
        
        # Pariteleri 20'şerli gruplar halinde tara (Rate limit yememek için)
        tasks = [fetch_and_check(exchange, symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        
        found_signals = [r for r in results if r is not None]

        if found_signals:
            msg = "🎯 *HASSAS RSI SİNYALLERİ (1s)*\n\n" + "\n".join(found_signals)
            bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
        else:
            print("Kritik seviye bulunamadı.")
    except Exception as e:
        print(f"Hata: {e}")
    finally:
        await exchange.close()

if name == "main":
    asyncio.run(main())
