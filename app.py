import discord
import os
import requests
import pandas as pd
import numpy as np
import random
import ta
from discord.ext import tasks

TOKEN=os.getenv("DISCORD_TOKEN")
SIGNAL_CHANNEL=int(os.getenv("SIGNAL_CHANNEL"))
ROLE=os.getenv("ALERT_ROLE_ID")
CMC_KEY=os.getenv("CMC_API_KEY")

COINS=os.getenv("COINS").split(",")

intents=discord.Intents.default()
client=discord.Client(intents=intents)

# -----------------------------
# Binance Market Data
# -----------------------------

def get_klines(symbol,interval="15m",limit=120):

    url=f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    data=requests.get(url).json()

    df=pd.DataFrame(data)

    df=df.iloc[:,:6]

    df.columns=["time","open","high","low","close","volume"]

    df["close"]=df["close"].astype(float)
    df["volume"]=df["volume"].astype(float)

    return df

# -----------------------------
# Orderbook Whale Detection
# -----------------------------

def whale_signal(symbol):

    url=f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=50"

    data=requests.get(url).json()

    bids=sum(float(b[1]) for b in data["bids"])
    asks=sum(float(a[1]) for a in data["asks"])

    if bids>asks*1.5:
        return "🐳 Strong Buy Pressure"

    elif asks>bids*1.5:
        return "🐳 Strong Sell Pressure"

    else:
        return "Balanced Flow"

# -----------------------------
# CoinMarketCap Bias
# -----------------------------

def market_bias():

    url="https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"

    headers={"X-CMC_PRO_API_KEY":CMC_KEY}

    data=requests.get(url,headers=headers).json()

    btc_dom=data["data"]["btc_dominance"]

    if btc_dom>50:
        return "BTC Dominance Market"

    else:
        return "Altcoin Expansion"

# -----------------------------
# AI SIGNAL ENGINE
# -----------------------------

def analyze(symbol):

    df=get_klines(symbol)

    df["ema20"]=ta.trend.ema_indicator(df["close"],20)
    df["ema50"]=ta.trend.ema_indicator(df["close"],50)
    df["ema200"]=ta.trend.ema_indicator(df["close"],200)

    df["rsi"]=ta.momentum.rsi(df["close"],14)

    macd=ta.trend.MACD(df["close"])
    df["macd"]=macd.macd()

    bb=ta.volatility.BollingerBands(df["close"])
    df["bb_high"]=bb.bollinger_hband()
    df["bb_low"]=bb.bollinger_lband()

    df["stoch"]=ta.momentum.stochrsi(df["close"])

    latest=df.iloc[-1]

    score=0
    reasons=[]

    # EMA trend
    if latest["ema20"]>latest["ema50"]:
        score+=1
        reasons.append("EMA Bullish")

    if latest["ema50"]>latest["ema200"]:
        score+=1
        reasons.append("Trend Strong")

    # RSI
    if latest["rsi"]<35:
        score+=1
        reasons.append("RSI Oversold")

    if latest["rsi"]>70:
        score-=1
        reasons.append("RSI Overbought")

    # MACD
    if latest["macd"]>0:
        score+=1
        reasons.append("MACD Positive")

    # Bollinger
    if latest["close"]<latest["bb_low"]:
        score+=1
        reasons.append("BB Bounce")

    # Volume spike
    vol_avg=df["volume"].rolling(20).mean().iloc[-1]

    if latest["volume"]>vol_avg*2:
        score+=1
        reasons.append("Volume Spike")

    price=latest["close"]

    if score>=4:

        trade="Swing 📈"
        signal="🟢 BUY"

        entry=price
        tp=round(price*1.05,4)
        sl=round(price*0.97,4)

    elif score>=2:

        trade="Intraday ⚡"
        signal="🟢 BUY"

        entry=price
        tp=round(price*1.03,4)
        sl=round(price*0.98,4)

    elif score<=-2:

        trade="Scalp 🔥"
        signal="🔴 SELL"

        entry=price
        tp=round(price*0.97,4)
        sl=round(price*1.02,4)

    else:
        return None

    whale=whale_signal(symbol)

    confidence=min(100,50+score*10)

    return{
        "symbol":symbol,
        "signal":signal,
        "entry":entry,
        "tp":tp,
        "sl":sl,
        "trade":trade,
        "reasons":", ".join(reasons),
        "whale":whale,
        "confidence":confidence
    }

# -----------------------------
# SCANNER LOOP
# -----------------------------

@tasks.loop(minutes=5)

async def scanner():

    channel=client.get_channel(SIGNAL_CHANNEL)

    coin=random.choice(COINS)

    result=analyze(coin)

    if result:

        bias=market_bias()

        msg=f"""
<@&{ROLE}>

🚨 **AI MARKET SIGNAL**

Coin: {result['symbol']}
Signal: {result['signal']}

Trade Type: {result['trade']}

Entry: {result['entry']}
Take Profit: {result['tp']}
Stop Loss: {result['sl']}

AI Confidence: {result['confidence']}%

Indicators:
{result['reasons']}

Order Flow:
{result['whale']}

Market Bias:
{bias}
"""

        await channel.send(msg)

# -----------------------------
# READY
# -----------------------------

@client.event

async def on_ready():

    print("Institutional AI Trading Bot Online")

    scanner.start()

client.run(TOKEN)
