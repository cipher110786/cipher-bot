import discord
import aiohttp
import asyncio
import pandas as pd
import numpy as np
import ta
import random
import time

DISCORD_TOKEN = "YOUR_DISCORD_TOKEN"
CMC_API = "YOUR_CMC_API"
SIGNAL_CHANNEL = 123456789

client = discord.Client(intents=discord.Intents.default())

win_rate = {"wins":0,"loss":0}

last_coin = None

# ---------------------------------
# GET TOP 100 COINS
# ---------------------------------

async def get_top_coins():

    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

    headers = {"X-CMC_PRO_API_KEY":CMC_API}

    params = {"limit":100}

    async with aiohttp.ClientSession() as session:
        async with session.get(url,headers=headers,params=params) as resp:
            data = await resp.json()

    coins = []

    for coin in data["data"]:
        coins.append(coin["symbol"]+"USDT")

    return coins


# ---------------------------------
# BINANCE PRICE DATA
# ---------------------------------

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


# ---------------------------------
# ORDER BOOK PRESSURE
# ---------------------------------

async def order_book(symbol):

    url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=100"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()

    bids = sum([float(x[1]) for x in data["bids"]])

    asks = sum([float(x[1]) for x in data["asks"]])

    if bids > asks:
        return "BUY"
    else:
        return "SELL"


# ---------------------------------
# BTC DOMINANCE
# ---------------------------------

async def btc_dominance():

    url="https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"

    headers={"X-CMC_PRO_API_KEY":CMC_API}

    async with aiohttp.ClientSession() as session:
        async with session.get(url,headers=headers) as resp:
            data=await resp.json()

    dom=data["data"]["btc_dominance"]

    return dom


# ---------------------------------
# TECHNICAL ANALYSIS
# ---------------------------------

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


# ---------------------------------
# TRADE TYPE
# ---------------------------------

def trade_type():

    types=["⚡ SCALP","📈 INTRADAY","🌙 SWING"]

    return random.choice(types)


# ---------------------------------
# DISCORD SIGNAL
# ---------------------------------

def build_signal(symbol,signal,confidence,price,volume,rsi,order,trade):

    direction="🟢 BUY" if signal=="BUY" else "🔴 SELL"

    message=f"""

🚨 **AI GOD MODE SIGNAL**

Coin: **{symbol}**

Direction: {direction}

Trade Type: {trade}

Entry: {price}

AI Confidence: {confidence}%

Order Book Bias: {order}

Volume Spike: {volume}

RSI: {round(rsi,2)}

Take Profit:
TP1: {price*1.01}
TP2: {price*1.02}
TP3: {price*1.03}

Stop Loss:
{price*0.985}

Win Rate:
{win_rate["wins"]}/{win_rate["wins"]+win_rate["loss"]}

🤖 Institutional AI Engine
"""

    return message


# ---------------------------------
# ALTCOIN SEASON DETECTOR
# ---------------------------------

async def altcoin_season():

    dom = await btc_dominance()

    if dom < 50:
        return "🚀 ALTCOIN SEASON"

    elif dom > 60:
        return "🛑 BTC DOMINANCE"

    else:
        return "⚖️ BALANCED MARKET"


# ---------------------------------
# MAIN BOT LOOP
# ---------------------------------

async def trading_loop():

    await client.wait_until_ready()

    channel = client.get_channel(SIGNAL_CHANNEL)

    global last_coin

    while True:

        coins = await get_top_coins()

        coin = random.choice(coins)

        if coin == last_coin:
            continue

        last_coin = coin

        try:

            df = await get_klines(coin)

            signal,confidence,price,volume,rsi = analyze(df)

            if signal=="NEUTRAL":
                await asyncio.sleep(60)
                continue

            order = await order_book(coin)

            trade = trade_type()

            msg = build_signal(coin,signal,confidence,price,volume,rsi,order,trade)

            await channel.send(msg)

            await asyncio.sleep(600)

        except:

            await asyncio.sleep(60)


# ---------------------------------
# START BOT
# ---------------------------------

@client.event
async def on_ready():

    print("AI GOD MODE BOT ONLINE")

    client.loop.create_task(trading_loop())


client.run(DISCORD_TOKEN)
