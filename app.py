import discord
import aiohttp
import asyncio
import pandas as pd
import numpy as np
import ta
import random
import os

# ===============================
# ENV VARIABLES (Railway)
# ===============================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CMC_API = os.getenv("CMC_API")
SIGNAL_CHANNEL = int(os.getenv("SIGNAL_CHANNEL"))
ALERT_ROLE = os.getenv("ALERT_ROLE")

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN not set")

if not CMC_API:
    raise ValueError("CMC_API not set")

if not SIGNAL_CHANNEL:
    raise ValueError("SIGNAL_CHANNEL not set")


# ===============================
# DISCORD CLIENT
# ===============================

intents = discord.Intents.default()
client = discord.Client(intents=intents)

win_rate = {"wins":0,"loss":0}
last_coin = None


# ===============================
# GET TOP 100 COINS (CMC)
# ===============================

async def get_top_coins():

    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

    headers = {"X-CMC_PRO_API_KEY":CMC_API}

    params = {"limit":100}

    async with aiohttp.ClientSession() as session:
        async with session.get(url,headers=headers,params=params) as resp:

            data = await resp.json()

    coins = []

    if "data" not in data:
        return []

    for coin in data["data"]:
        symbol = coin["symbol"]+"USDT"
        coins.append(symbol)

    return coins


# ===============================
# BINANCE KLINE DATA
# ===============================

async def get_klines(symbol):

    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=200"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    df = pd.DataFrame(data)

    df = df.iloc[:,:6]

    df.columns=["time","open","high","low","close","volume"]

    df["close"]=df["close"].astype(float)
    df["volume"]=df["volume"].astype(float)

    return df


# ===============================
# ORDER BOOK PRESSURE
# ===============================

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


# ===============================
# BTC DOMINANCE
# ===============================

async def btc_dominance():

    url="https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"

    headers={"X-CMC_PRO_API_KEY":CMC_API}

    async with aiohttp.ClientSession() as session:
        async with session.get(url,headers=headers) as resp:
            data=await resp.json()

    dom=data["data"]["btc_dominance"]

    return dom


# ===============================
# ALTCOIN SEASON DETECTOR
# ===============================

async def altcoin_season():

    dom = await btc_dominance()

    if dom < 50:
        return "🚀 ALTCOIN SEASON"

    elif dom > 60:
        return "🛑 BTC DOMINANCE"

    else:
        return "⚖️ BALANCED MARKET"


# ===============================
# TECHNICAL ANALYSIS
# ===============================

def analyze(df):

    rsi = ta.momentum.RSIIndicator(df["close"]).rsi().iloc[-1]

    macd = ta.trend.MACD(df["close"]).macd_diff().iloc[-1]

    ema20 = ta.trend.EMAIndicator(df["close"],20).ema_indicator().iloc[-1]

    ema50 = ta.trend.EMAIndicator(df["close"],50).ema_indicator().iloc[-1]

    price = df["close"].iloc[-1]

    volume = df["volume"].iloc[-1]

    score = 0

    if rsi < 35:
        score += 1

    if macd > 0:
        score += 1

    if ema20 > ema50:
        score += 1

    if price > ema20:
        score += 1

    if score >=3:
        signal="BUY"

    elif score<=1:
        signal="SELL"

    else:
        signal="NEUTRAL"

    confidence = score*25

    return signal,confidence,price,volume,rsi


# ===============================
# TRADE TYPE
# ===============================

def trade_type():

    types=["⚡ SCALP","📈 INTRADAY","🌙 SWING"]

    return random.choice(types)


# ===============================
# BUILD DISCORD MESSAGE
# ===============================

def build_signal(symbol,signal,confidence,price,volume,rsi,order,trade,market):

    direction="🟢 BUY" if signal=="BUY" else "🔴 SELL"

    msg=f"""

🚨 **AI GOD MODE SIGNAL**

Coin: **{symbol}**

Direction: {direction}

Trade Type: {trade}

Entry: {round(price,6)}

AI Confidence: {confidence}%

Order Book Bias: {order}

Market State: {market}

Volume: {round(volume,2)}

RSI: {round(rsi,2)}

🎯 Take Profit

TP1: {round(price*1.01,6)}
TP2: {round(price*1.02,6)}
TP3: {round(price*1.03,6)}

🛑 Stop Loss

{round(price*0.985,6)}

📊 Win Rate
{win_rate["wins"]}/{win_rate["wins"]+win_rate["loss"]}

🤖 Institutional AI Engine
"""

    return msg


# ===============================
# MAIN BOT LOOP
# ===============================

async def trading_loop():

    await client.wait_until_ready()

    channel = client.get_channel(SIGNAL_CHANNEL)

    global last_coin

    while True:

        try:

            coins = await get_top_coins()

            if not coins:
                await asyncio.sleep(120)
                continue

            coin = random.choice(coins)

            if coin == last_coin:
                continue

            last_coin = coin

            df = await get_klines(coin)

            signal,confidence,price,volume,rsi = analyze(df)

            if signal=="NEUTRAL":
                await asyncio.sleep(60)
                continue

            order = await order_book(coin)

            trade = trade_type()

            market = await altcoin_season()

            msg = build_signal(coin,signal,confidence,price,volume,rsi,order,trade,market)

            if ALERT_ROLE:
                msg = f"<@&{ALERT_ROLE}> {msg}"

            await channel.send(msg)

            await asyncio.sleep(600)

        except Exception as e:

            print("BOT ERROR:",e)

            await asyncio.sleep(60)


# ===============================
# DISCORD READY EVENT
# ===============================

@client.event
async def on_ready():

    print("🚀 AI GOD MODE BOT ONLINE")

    client.loop.create_task(trading_loop())


# ===============================
# START BOT
# ===============================

client.run(DISCORD_TOKEN)
