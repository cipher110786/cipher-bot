import discord
from discord.ext import tasks
import requests
import pandas as pd
import os
import ta
import random
import time

TOKEN=os.getenv("DISCORD_TOKEN")

SIGNALS_CHANNEL=int(os.getenv("SIGNALS_CHANNEL"))
CMC_CHANNEL=int(os.getenv("CMC_CHANNEL"))
MARKET_CHANNEL=int(os.getenv("MARKET_CHANNEL"))
WHALE_CHANNEL=int(os.getenv("WHALE_CHANNEL"))

ALERT_ROLE_ID=os.getenv("ALERT_ROLE_ID")

CMC_KEY=os.getenv("CMC_API_KEY")

client=discord.Client(intents=discord.Intents.default())

signals_history=[]

# --------------------------------

def get_top_coins():

    url="https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

    headers={"X-CMC_PRO_API_KEY":CMC_KEY}

    params={"limit":50}

    data=requests.get(url,headers=headers,params=params).json()

    coins=[]

    for c in data["data"]:

        symbol=c["symbol"]

        if symbol not in ["USDT","USDC","BUSD"]:

            coins.append(symbol+"USDT")

    return coins

# --------------------------------

def get_klines(symbol):

    url=f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=200"

    data=requests.get(url).json()

    df=pd.DataFrame(data)

    df=df.iloc[:,:6]

    df.columns=["time","open","high","low","close","volume"]

    df=df.astype(float)

    return df

# --------------------------------

def apply_indicators(df):

    df["rsi"]=ta.momentum.RSIIndicator(df["close"]).rsi()

    macd=ta.trend.MACD(df["close"])

    df["macd"]=macd.macd()

    df["macd_signal"]=macd.macd_signal()

    bb=ta.volatility.BollingerBands(df["close"])

    df["bb_high"]=bb.bollinger_hband()

    df["bb_low"]=bb.bollinger_lband()

    df["ema50"]=ta.trend.EMAIndicator(df["close"],50).ema_indicator()

    df["ema200"]=ta.trend.EMAIndicator(df["close"],200).ema_indicator()

    stoch=ta.momentum.StochasticOscillator(df["high"],df["low"],df["close"])

    df["stoch"]=stoch.stoch()

    return df

# --------------------------------

def orderbook(symbol):

    url=f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=100"

    data=requests.get(url).json()

    bids=sum(float(x[1]) for x in data["bids"])

    asks=sum(float(x[1]) for x in data["asks"])

    return bids,asks

# --------------------------------

def ai_confidence(df,signal):

    score=0

    last=df.iloc[-1]

    if signal=="BUY":

        if last["rsi"]<35:
            score+=20

        if last["macd"]>last["macd_signal"]:
            score+=20

        if last["close"]<last["bb_low"]:
            score+=20

        if last["ema50"]>last["ema200"]:
            score+=20

        if last["stoch"]<20:
            score+=20

    if signal=="SELL":

        if last["rsi"]>65:
            score+=20

        if last["macd"]<last["macd_signal"]:
            score+=20

        if last["close"]>last["bb_high"]:
            score+=20

        if last["ema50"]<last["ema200"]:
            score+=20

        if last["stoch"]>80:
            score+=20

    return score

# --------------------------------

def btc_dominance():

    url="https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"

    headers={"X-CMC_PRO_API_KEY":CMC_KEY}

    data=requests.get(url,headers=headers).json()

    dom=data["data"]["btc_dominance"]

    if dom>52:

        return f"⚡ BTC Dominance Rising: {dom:.2f}%"

    else:

        return f"🚀 Altcoins Strengthening: {dom:.2f}%"

# --------------------------------

def generate_signal(symbol):

    df=get_klines(symbol)

    df=apply_indicators(df)

    last=df.iloc[-1]

    signal=None

    if last["rsi"]<35 and last["macd"]>last["macd_signal"]:
        signal="BUY"

    if last["rsi"]>65 and last["macd"]<last["macd_signal"]:
        signal="SELL"

    if not signal:
        return None

    confidence=ai_confidence(df,signal)

    if confidence<60:
        return None

    price=last["close"]

    tp=price*1.03 if signal=="BUY" else price*0.97

    sl=price*0.97 if signal=="BUY" else price*1.03

    bids,asks=orderbook(symbol)

    whale="Neutral"

    if bids>asks*1.5:
        whale="🐳 Buy Wall"

    if asks>bids*1.5:
        whale="🐳 Sell Wall"

    trade=random.choice(["Scalp","Intraday","Swing"])

    msg=f"""
<@&{ALERT_ROLE_ID}>

🚨 **AI TRADING SIGNAL**

Coin: {symbol}

Signal: {'🟢 BUY' if signal=='BUY' else '🔴 SELL'}

Trade Type: {trade}

Entry: {round(price,4)}

TP: {round(tp,4)}

SL: {round(sl,4)}

Confidence: {confidence}%

Orderbook: {whale}
"""

    return msg

# --------------------------------

@client.event
async def on_ready():

    print("Elite Market Bot Running")

    scanner.start()

# --------------------------------

@tasks.loop(minutes=5)
async def scanner():

    signals_channel=client.get_channel(SIGNALS_CHANNEL)

    cmc_channel=client.get_channel(CMC_CHANNEL)

    coins=get_top_coins()

    symbol=random.choice(coins)

    signal=generate_signal(symbol)

    if signal:

        await signals_channel.send(signal)

    dominance=btc_dominance()

    await cmc_channel.send(f"📊 MARKET UPDATE\n\n{dominance}")

# --------------------------------

client.run(TOKEN)
