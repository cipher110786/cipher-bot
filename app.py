import discord
from discord.ext import tasks
import requests
import os
import pandas as pd
import numpy as np

TOKEN = os.getenv("DISCORD_TOKEN")
CMC_API = os.getenv("CMC_API")

CMC_CHANNEL = int(os.getenv("CMC_CHANNEL"))
SIGNAL_CHANNEL = int(os.getenv("SIGNAL_CHANNEL"))
WHALE_CHANNEL = int(os.getenv("WHALE_CHANNEL"))
MARKET_CHANNEL = int(os.getenv("MARKET_CHANNEL"))

client = discord.Client(intents=discord.Intents.default())


def get_candles(symbol):

    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}USDT&interval=15m&limit=100"
    data = requests.get(url).json()

    closes = [float(c[4]) for c in data]

    return pd.Series(closes)


def MACD(series):

    ema12 = series.ewm(span=12).mean()
    ema26 = series.ewm(span=26).mean()

    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()

    return macd.iloc[-1], signal.iloc[-1]


def bollinger(series):

    sma = series.rolling(20).mean()
    std = series.rolling(20).std()

    upper = sma + (std * 2)
    lower = sma - (std * 2)

    price = series.iloc[-1]

    if price > upper.iloc[-1]:
        return "OVERBOUGHT"

    if price < lower.iloc[-1]:
        return "OVERSOLD"

    return "NORMAL"


def stochastic_rsi(series):

    delta = series.diff()

    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

    rs = gain / loss

    rsi = 100 - (100 / (1 + rs))

    stoch = (rsi - rsi.rolling(14).min()) / (rsi.rolling(14).max() - rsi.rolling(14).min())

    return stoch.iloc[-1]


def order_book(symbol):

    try:
        url = f"https://api.binance.com/api/v3/depth?symbol={symbol}USDT&limit=50"
        data = requests.get(url).json()

        bids = sum(float(b[1]) for b in data["bids"])
        asks = sum(float(a[1]) for a in data["asks"])

        if bids > asks:
            return "BUY"

        return "SELL"

    except:
        return "UNKNOWN"


@client.event
async def on_ready():

    print("Bot connected")

    market_loop.start()


@tasks.loop(minutes=30)
async def market_loop():

    headers = {"X-CMC_PRO_API_KEY": CMC_API}

    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

    params = {"limit": 100, "convert": "USD"}

    data = requests.get(url, headers=headers, params=params).json()["data"]

    cmc = client.get_channel(CMC_CHANNEL)
    signals = client.get_channel(SIGNAL_CHANNEL)
    whale = client.get_channel(WHALE_CHANNEL)
    market = client.get_channel(MARKET_CHANNEL)

    cmc_msg = "📊 **Top Market Coins**\n\n"
    signal_msg = "🤖 **AI Trading Signals**\n\n"
    whale_msg = "🐋 **High Volume Activity**\n\n"

    for coin in data[:40]:

        symbol = coin["symbol"]
        price = coin["quote"]["USD"]["price"]
        change = coin["quote"]["USD"]["percent_change_24h"]
        volume = coin["quote"]["USD"]["volume_24h"]

        emoji = "🟢" if change > 0 else "🔴"

        cmc_msg += f"{emoji} {symbol} ${price:.2f} ({change:.2f}%)\n"

        try:

            series = get_candles(symbol)

            macd, signal = MACD(series)
            bb = bollinger(series)
            stoch = stochastic_rsi(series)
            book = order_book(symbol)

            if macd > signal and stoch < 0.2 and bb == "OVERSOLD" and book == "BUY":

                signal_msg += f"🚀 BUY {symbol}\nMACD Bullish\nStochRSI Oversold\nOrderBook BUY\n\n"

            if macd < signal and stoch > 0.8 and bb == "OVERBOUGHT" and book == "SELL":

                signal_msg += f"📉 SELL {symbol}\nMACD Bearish\nStochRSI Overbought\nOrderBook SELL\n\n"

        except:
            pass

        if volume > 800000000:

            whale_msg += f"{symbol} Volume ${volume:,.0f}\n"

    await cmc.send(cmc_msg)

    if len(signal_msg) > 40:
        await signals.send(signal_msg)

    if len(whale_msg) > 30:
        await whale.send(whale_msg)

    await market.send("🌎 Market scan completed. Signals generated.")


client.run(TOKEN)
