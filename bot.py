import os
import telebot
import ccxt
import pandas as pd
import time

# --- AYARLAR (GitHub Secrets'tan okur) ---
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
    return 100 - (100 / (1 + rs))

def main():
    try:
        print("OKX Market verileri yükleniyor...")
        markets = exchange.load_markets()
        
        # Sadece USDT çiftlerini ve aktif olanları filtrele (Örn: BTC/USDT)
        symbols = [s for s in markets if '/USDT' in s and markets[s].get('active', True)]
        
        found_signals = []
        print(f"Toplam {len(symbols)} çift taranıyor, bu biraz sürebilir...")

        for symbol in symbols:
            try:
                # Son 100 mumu çek (1 saatlik - 1h)
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100)
                if len(ohlcv) < 30: continue
                
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                rsi_series = calculate_rsi(df['close'])
                
                if rsi_series.empty: continue
                last_rsi = round(rsi_series.iloc[-1], 2)

                # --- SENİN FİLTREN (20 ve 80) ---
                if last_rsi <= 20:
                    found_signals.append(f"🟢 *{symbol}* - RSI: {last_rsi} (Aşırı Satım)")
                elif last_rsi >= 80:
                    found_signals.append(f"🔴 *{symbol}* - RSI: {last_rsi} (Aşırı Alım)")
                
                # Borsa korumasına takılmamak için minik bekleme
                time.sleep(0.05) 

            except Exception:
                continue

        # Mesaj Gönderimi
        if found_signals:
            header = "🎯 *RSI KRİTİK SEVİYE SİNYALLERİ (1s)*\n\n"
            final_msg = header + "\n".join(found_signals)
            
            # Telegram mesaj sınırı uyarısı (Çok fazla sinyal varsa bölerek gönderir)
            if len(final_msg) > 4000:
                for i in range(0, len(found_signals), 15):
                    chunk = header + "\n".join(found_signals[i:i+15])
                    bot.send_message(CHAT_ID, chunk, parse_mode='Markdown')
            else:
                bot.send_message(CHAT_ID, final_msg, parse_mode='Markdown')
            print("Sinyaller gönderildi!")
        else:
            # Sinyal yoksa sadece log tutar, istersen buraya boş mesaj da ekleyebilirsin
            print("Kritik seviyede coin bulunamadı.")

    except Exception as e:
        print(f"Genel Hata: {e}")

if __name__ == "__main__":
    main()
