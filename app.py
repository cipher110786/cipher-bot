import discord
import requests
import pandas as pd
import os
from discord.ext import tasks
from ta.trend import MACD, EMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands

TOKEN = os.getenv("DISCORD_TOKEN")
CMC_API = os.getenv("CMC_API")

CMC_CHANNEL = int(os.getenv("CMC_CHANNEL"))
SIGNAL_CHANNEL = int(os.getenv("SIGNAL_CHANNEL"))
WHALE_CHANNEL = int(os.getenv("WHALE_CHANNEL"))
MARKET_CHANNEL = int(os.getenv("MARKET_CHANNEL"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

coins = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT"]

# -----------------------
# GET BINANCE DATA
# -----------------------

def get_klines(symbol):

    url=f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=150"

    data=requests.get(url).json()

    df=pd.DataFrame(data)

    df=df.iloc[:,0:6]

    df.columns=["time","open","high","low","close","volume"]

    df["close"]=df["close"].astype(float)
    df["high"]=df["high"].astype(float)
    df["low"]=df["low"].astype(float)
    df["volume"]=df["volume"].astype(float)

    return df


# -----------------------
# SIGNAL ENGINE
# -----------------------

def generate_signal(df):

    close=df["close"]

    macd=MACD(close)
    rsi=RSIIndicator(close)
    bb=BollingerBands(close)
    stoch=StochasticOscillator(df["high"],df["low"],close)
    ema=EMAIndicator(close,50)

    macd_line=macd.macd().iloc[-1]
    macd_signal=macd.macd_signal().iloc[-1]

    rsi_val=rsi.rsi().iloc[-1]
    stoch_val=stoch.stoch().iloc[-1]

    price=close.iloc[-1]
    ema_val=ema.ema_indicator().iloc[-1]

    bb_high=bb.bollinger_hband().iloc[-1]
    bb_low=bb.bollinger_lband().iloc[-1]

    score=0

    if macd_line > macd_signal:
        score+=1
    else:
        score-=1

    if rsi_val < 40:
        score+=1
    elif rsi_val > 60:
        score-=1

    if price < bb_low:
        score+=1
    elif price > bb_high:
        score-=1

    if stoch_val < 30:
        score+=1
    elif stoch_val > 70:
        score-=1

    if price > ema_val:
        score+=1
    else:
        score-=1

    if score >=3:
        return "BUY",score
    elif score <=-3:
        return "SELL",score
    else:
        return "HOLD",score


# -----------------------
# ORDERBOOK
# -----------------------

def order_book(symbol):

    url=f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=50"

    data=requests.get(url).json()

    bids=sum(float(x[1]) for x in data["bids"])
    asks=sum(float(x[1]) for x in data["asks"])

    if bids > asks*1.4:
        return "STRONG BUY PRESSURE"

    elif asks > bids*1.4:
        return "STRONG SELL PRESSURE"

    return "BALANCED"


# -----------------------
# CMC MARKET DATA
# -----------------------

def cmc_data():

    url="https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

    headers={"X-CMC_PRO_API_KEY":CMC_API}

    params={"limit":10,"convert":"USD"}

    r=requests.get(url,headers=headers,params=params).json()

    if "data" not in r:
        return None

    return r["data"]


# -----------------------
# BOT READY
# -----------------------

@client.event
async def on_ready():

    print("Elite Bot Connected")

    market_loop.start()


# -----------------------
# MAIN LOOP
# -----------------------

@tasks.loop(minutes=30)
async def market_loop():

    cmc_channel=client.get_channel(CMC_CHANNEL)
    signal_channel=client.get_channel(SIGNAL_CHANNEL)
    whale_channel=client.get_channel(WHALE_CHANNEL)
    market_channel=client.get_channel(MARKET_CHANNEL)

    # CMC UPDATE

    data=cmc_data()

    if data:

        text="**Top Market Update**\n\n"

        for coin in data[:5]:

            name=coin["symbol"]
            price=coin["quote"]["USD"]["price"]
            change=coin["quote"]["USD"]["percent_change_24h"]

            text+=f"{name}  ${price:.2f}  ({change:.2f}%)\n"

        await cmc_channel.send(text)


    # SIGNAL ENGINE

    for coin in coins:

        df=get_klines(coin)

        signal,score=generate_signal(df)

        pressure=order_book(coin)

        price=df["close"].iloc[-1]

        msg=f"""
**{coin} SIGNAL**

Price: {price}

Signal: {signal}

Confidence Score: {score}/5

Orderbook: {pressure}
"""

        await signal_channel.send(msg)


    # WHALE DETECTOR

    for coin in coins:

        df=get_klines(coin)

        vol=df["volume"].iloc[-1]
        avg=df["volume"].mean()

        if vol > avg*3:

            await whale_channel.send(
                f"🐋 Whale Volume Spike detected in {coin}\nVolume: {vol}"
            )


    # MARKET SNAPSHOT

    text="**Market Scan**\n"

    for coin in coins:

        df=get_klines(coin)

        price=df["close"].iloc[-1]

        text+=f"{coin} : {price}\n"

    await market_channel.send(text)


client.run(TOKEN)
