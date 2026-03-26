import asyncio
import ccxt.async_support as ccxt
import pandas as pd
import telebot
import os

# Telegram Bilgileri
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
bot = telebot.TeleBot(TOKEN)

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    for i in range(period, len(prices)):
        avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + loss.iloc[i]) / period

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

async def fetch_and_calculate(exchange, symbol):
    try:
        # Her coin için 250 mum çekiyoruz (Hassasiyet için şart)
        bars = await exchange.fetch_ohlcv(symbol, timeframe='1h', limit=250)
        if len(bars) < 50: return None
        
        df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['rsi'] = calculate_rsi(df['close'])
        last_rsi = round(df['rsi'].iloc[-1], 2)
        
        if last_rsi <= 20:
            return f"🟢 {symbol} - RSI: {last_rsi} (DİP)"
        elif last_rsi >= 80:
            return f"🔴 {symbol} - RSI: {last_rsi} (TEPE)"
    except:
        return None
    return None

async def run_bot():
    exchange = ccxt.okx({'enableRateLimit': True})
    print("Marketler taranıyor (Asenkron)...")
    
    markets = await exchange.load_markets()
    symbols = [s for s in markets if '/USDT' in s and markets[s].get('active')]
    
    # AYNI ANDA ÇALIŞTIRMA (Turbo Mod)
    tasks = [fetch_and_calculate(exchange, symbol) for symbol in symbols]
    results = await asyncio.gather(*tasks)
    
    await exchange.close()
    
    # Sonuçları filtrele ve gönder
    found_signals = [r for r in results if r is not None]
    
    if found_signals:
        mesaj = "🎯 OKX TR ASENKRON TARAMA (20-80)\n\n" + "\n".join(found_signals)
        if len(mesaj) > 4000:
            for x in range(0, len(mesaj), 4000):
                bot.send_message(CHAT_ID, mesaj[x:x+4000], parse_mode='Markdown')
        else:
            bot.send_message(CHAT_ID, mesaj, parse_mode='Markdown')
    else:
        print("Kritik seviyede coin yok.")

if __name__ == "__main__":
    asyncio.run(run_bot())
