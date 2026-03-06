import discord
import aiohttp
import asyncio
import pandas as pd
import numpy as np
import ta
import random
import os

# ================================
# ENV VARIABLES (RAILWAY)
# ================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CMC_API = os.getenv("CMC_API")
SIGNAL_CHANNEL = int(os.getenv("SIGNAL_CHANNEL"))
ALERT_ROLE = os.getenv("ALERT_ROLE")  # optional role ping

# ================================
# DISCORD CLIENT
# ================================

intents = discord.Intents.default()
client = discord.Client(intents=intents)

win_rate = {"wins":0,"loss":0}
last_coin = None


# ================================
# GET TOP 100 COINS (CMC)
# ================================

async def get_top_coins():

    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

    headers = {"X-CMC_PRO_API_KEY":CMC_API}

    params = {"limit":100}

    async with aiohttp.ClientSession() as session:
        async with session.get(url,headers=headers,params=params) as resp:
            data = await resp.json()

    coins = []

    for coin in data["data"]:
        symbol = coin["symbol"]+"USDT"

        if symbol not in ["USDTUSDT","BUSDUSDT"]:
            coins.append(symbol)

    return coins


# ================================
# BINANCE KLINES
# ================================

async def get_klines(symbol):

    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=200"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    df = pd.DataFrame(data)

    df = df.iloc[:,:6]

    df.columns=["time","open","high","low","close","volume"]

    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)

    return df


# ================================
# ORDER BOOK BIAS
# ================================

async def order_book(symbol):

    url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=100"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    bids = sum([float(x[1]) for x in data["bids"]])
    asks = sum([float(x[1]) for x in data["asks"]])

    if bids > asks:
        return "🟢 BUY PRESSURE"
    else:
        return "🔴 SELL PRESSURE"


# ================================
# BTC DOMINANCE
# ================================

async def btc_dominance():

    url="https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"

    headers={"X-CMC_PRO_API_KEY":CMC_API}

    async with aiohttp.ClientSession() as session:
        async with session.get(url,headers=headers) as resp:
            data = await resp.json()

    return data["data"]["btc_dominance"]


# ================================
# ALTCOIN SEASON
# ================================

async def altcoin_season():

    dom = await btc_dominance()

    if dom < 50:
        return "🚀 ALTCOIN SEASON"
    elif dom > 60:
        return "🛑 BTC DOMINANCE"
    else:
        return "⚖️ BALANCED MARKET"


# ================================
# TECHNICAL ANALYSIS ENGINE
# ================================

def analyze(df):

    price = df["close"].iloc[-1]

    rsi = ta.momentum.RSIIndicator(df["close"]).rsi().iloc[-1]

    macd = ta.trend.MACD(df["close"]).macd_diff().iloc[-1]

    ema20 = ta.trend.EMAIndicator(df["close"],20).ema_indicator().iloc[-1]

    ema50 = ta.trend.EMAIndicator(df["close"],50).ema_indicator().iloc[-1]

    volume = df["volume"].iloc[-1]

    vol_avg = df["volume"].rolling(20).mean().iloc[-1]

    score = 0

    if rsi < 35:
        score += 1

    if macd > 0:
        score += 1

    if ema20 > ema50:
        score += 1

    if price > ema20:
        score += 1

    if volume > vol_avg:
        score += 1

    if score >= 4:
        signal = "BUY"

    elif score <= 1:
        signal = "SELL"

    else:
        signal = "NEUTRAL"

    confidence = score * 20

    volume_spike = volume > vol_avg

    return signal,confidence,price,volume,rsi,volume_spike


# ================================
# TRADE TYPE
# ================================

def trade_type():

    return random.choice(["⚡ SCALP","📈 INTRADAY","🌙 SWING"])


# ================================
# BUILD DISCORD MESSAGE
# ================================

def build_signal(symbol,signal,confidence,price,volume,rsi,order,trade,volume_spike,season):

    direction = "🟢 BUY" if signal=="BUY" else "🔴 SELL"

    spike = "🔥 YES" if volume_spike else "No"

    tp1 = round(price*1.01,6)
    tp2 = round(price*1.02,6)
    tp3 = round(price*1.03,6)

    sl = round(price*0.985,6)

    message = f"""
🚨 **AI GOD MODE SIGNAL**

Coin: **{symbol}**

Direction: {direction}

Trade Type: {trade}

Entry: {price}

Take Profit:
TP1: {tp1}
TP2: {tp2}
TP3: {tp3}

Stop Loss:
{sl}

AI Confidence: {confidence}%

RSI: {round(rsi,2)}

Volume Spike: {spike}

Order Book Bias: {order}

Market State:
{season}

Win Rate:
{win_rate["wins"]}/{win_rate["wins"]+win_rate["loss"]}

🤖 Institutional AI Trading Engine
"""

    return message


# ================================
# MAIN TRADING LOOP
# ================================

async def trading_loop():

    await client.wait_until_ready()

    channel = await client.fetch_channel(SIGNAL_CHANNEL)

    global last_coin

    while True:

        try:

            coins = await get_top_coins()

            coin = random.choice(coins)

            if coin == last_coin:
                await asyncio.sleep(10)
                continue

            last_coin = coin

            df = await get_klines(coin)

            signal,confidence,price,volume,rsi,volume_spike = analyze(df)

            if signal == "NEUTRAL":
                await asyncio.sleep(60)
                continue

            order = await order_book(coin)

            trade = trade_type()

            season = await altcoin_season()

            msg = build_signal(
                coin,signal,confidence,price,volume,rsi,order,trade,volume_spike,season
            )

            if ALERT_ROLE:
                msg = f"<@&{ALERT_ROLE}> " + msg

            await channel.send(msg)

            await asyncio.sleep(600)

        except Exception as e:

            print("BOT ERROR:",e)

            await asyncio.sleep(60)


# ================================
# BOT READY
# ================================

@client.event
async def on_ready():

    print("🚀 AI GOD MODE BOT ONLINE")

    client.loop.create_task(trading_loop())


client.run(DISCORD_TOKEN)
