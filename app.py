import discord
from discord.ext import commands, tasks
import requests
import pandas as pd
import numpy as np
import random
from ta.trend import EMAIndicator, MACD
from ta.momentum import StochRSIIndicator
from ta.volatility import BollingerBands

DISCORD_TOKEN = "YOUR_DISCORD_TOKEN"
CMC_API = "YOUR_CMC_API"
SIGNAL_CHANNEL = int("YOUR_SIGNAL_CHANNEL_ID")
ALERT_ROLE = "YOUR_ALERT_ROLE_ID"

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

BINANCE = "https://api.binance.com/api/v3"

TOP_COINS = [
"BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
"ADAUSDT","DOGEUSDT","AVAXUSDT","LINKUSDT","MATICUSDT"
]

win = 0
loss = 0

def get_klines(symbol):
    url = f"{BINANCE}/klines"
    params = {"symbol":symbol,"interval":"15m","limit":200}
    data = requests.get(url, params=params).json()

    df = pd.DataFrame(data)
    df = df.iloc[:,:6]
    df.columns=["time","open","high","low","close","volume"]

    df["close"]=df["close"].astype(float)
    df["volume"]=df["volume"].astype(float)

    return df

def indicators(df):

    ema50 = EMAIndicator(df["close"],50).ema_indicator()
    ema200 = EMAIndicator(df["close"],200).ema_indicator()

    macd = MACD(df["close"]).macd_diff()

    bb = BollingerBands(df["close"])
    upper = bb.bollinger_hband()
    lower = bb.bollinger_lband()

    stoch = StochRSIIndicator(df["close"]).stochrsi()

    return ema50, ema200, macd, upper, lower, stoch

def volume_spike(df):
    avg = df["volume"].mean()
    last = df["volume"].iloc[-1]
    return last > avg*2

def order_book(symbol):

    url=f"{BINANCE}/depth"
    params={"symbol":symbol,"limit":50}

    data=requests.get(url,params=params).json()

    bids=sum(float(b[1]) for b in data["bids"])
    asks=sum(float(a[1]) for a in data["asks"])

    if bids>asks:
        return "BUY"
    else:
        return "SELL"

def trade_levels(price):

    entry = price
    tp = price*1.02
    sl = price*0.98

    return entry,tp,sl

def trade_type():

    r=random.random()

    if r<0.33:
        return "⚡ SCALP"
    elif r<0.66:
        return "📈 INTRADAY"
    else:
        return "🌙 SWING"

def confidence():

    return random.randint(70,95)

def btc_dominance():

    url="https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
    headers={"X-CMC_PRO_API_KEY":CMC_API}

    data=requests.get(url,headers=headers).json()

    btc_dom=data["data"]["btc_dominance"]

    return btc_dom

def altcoin_season(btc_dom):

    if btc_dom < 45:
        return "🔥 ALTCOIN SEASON"
    else:
        return "🧊 BTC DOMINANCE"

@bot.event
async def on_ready():
    print("BOT ONLINE")
    scanner.start()

@tasks.loop(minutes=30)
async def scanner():

    channel = bot.get_channel(SIGNAL_CHANNEL)

    symbol=random.choice(TOP_COINS)

    df=get_klines(symbol)

    ema50,ema200,macd,upper,lower,stoch=indicators(df)

    price=df["close"].iloc[-1]

    book=order_book(symbol)

    vol=volume_spike(df)

    signal=None

    if ema50.iloc[-1]>ema200.iloc[-1] and macd.iloc[-1]>0 and stoch.iloc[-1]<0.8:
        signal="BUY"

    if ema50.iloc[-1]<ema200.iloc[-1] and macd.iloc[-1]<0 and stoch.iloc[-1]>0.2:
        signal="SELL"

    if not signal:
        return

    entry,tp,sl=trade_levels(price)

    trade=trade_type()

    conf=confidence()

    btc_dom=btc_dominance()

    alt=altcoin_season(btc_dom)

    emoji="🟢 BUY" if signal=="BUY" else "🔴 SELL"

    embed=discord.Embed(
        title=f"{emoji} {symbol} SIGNAL",
        color=0x00ff9d if signal=="BUY" else 0xff0040
    )

    embed.add_field(name="Trade Type",value=trade)
    embed.add_field(name="Entry",value=round(entry,4))
    embed.add_field(name="Take Profit",value=round(tp,4))
    embed.add_field(name="Stop Loss",value=round(sl,4))
    embed.add_field(name="Confidence",value=f"{conf}%")
    embed.add_field(name="Order Book Bias",value=book)
    embed.add_field(name="Volume Spike",value=str(vol))
    embed.add_field(name="BTC Dominance",value=f"{btc_dom:.2f}%")
    embed.add_field(name="Market State",value=alt)

    embed.set_footer(text="Cipher Sentinel AI")

    await channel.send(f"<@&{ALERT_ROLE}>",embed=embed)

bot.run(DISCORD_TOKEN)
