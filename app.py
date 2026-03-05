import discord
import aiohttp
import asyncio
import os

TOKEN = os.getenv("TOKEN")
CMC = os.getenv("CMC_API_KEY")
FMP = os.getenv("FMP_API_KEY")

ROLE = 1478820285263122572

CHANNEL = {
"psx":1478816955971665990,
"crypto":1478816867828240626,
"global":1478817069415010425,
"commod":1478816867828240626,
"whale":1478816921649545256
}

intents = discord.Intents.default()
bot = discord.Client(intents=intents)

# -------- CRYPTO --------

async def crypto():

 await bot.wait_until_ready()
 ch = bot.get_channel(CHANNEL["crypto"])

 url="https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

 headers={"X-CMC_PRO_API_KEY":CMC}

 params={"symbol":"BTC,ETH,SOL,BNB,XRP"}

 while not bot.is_closed():

  try:
   async with aiohttp.ClientSession() as s:
    async with s.get(url,headers=headers,params=params) as r:

     j=await r.json()

     btc=j["data"]["BTC"]["quote"]["USD"]["price"]
     eth=j["data"]["ETH"]["quote"]["USD"]["price"]
     sol=j["data"]["SOL"]["quote"]["USD"]["price"]

     msg=f"""
🪙 **CRYPTO MARKET**

BTC : ${btc:,.0f}
ETH : ${eth:,.0f}
SOL : ${sol:,.0f}

<@&{ROLE}>
"""

     await ch.send(msg)

  except Exception as e:
   print("Crypto error",e)

  await asyncio.sleep(900)

# -------- GLOBAL --------

async def global_markets():

 await bot.wait_until_ready()
 ch = bot.get_channel(CHANNEL["global"])

 while not bot.is_closed():

  try:
   async with aiohttp.ClientSession() as s:

    url=f"https://financialmodelingprep.com/api/v3/quote/%5EGSPC,%5EDJI,%5EIXIC?apikey={FMP}"

    async with s.get(url) as r:

     j=await r.json()

     sp=j[0]["price"]
     dj=j[1]["price"]
     nq=j[2]["price"]

     msg=f"""
🌍 **GLOBAL MARKETS**

S&P500 : {sp}
Dow Jones : {dj}
Nasdaq : {nq}

<@&{ROLE}>
"""

     await ch.send(msg)

  except Exception as e:
   print("Global error",e)

  await asyncio.sleep(1800)

# -------- COMMODITIES --------

async def commodities():

 await bot.wait_until_ready()
 ch = bot.get_channel(CHANNEL["commod"])

 while not bot.is_closed():

  try:
   async with aiohttp.ClientSession() as s:

    url="https://api.coincap.io/v2/assets"

    async with s.get(url) as r:

     j=await r.json()

     gold="n/a"
     silver="n/a"

     for a in j["data"]:

      if a["id"]=="bitcoin":
       btc=a["priceUsd"]

     msg=f"""
🛢 **COMMODITIES SNAPSHOT**

(Using crypto proxy)

BTC price (market risk proxy)

{btc}

<@&{ROLE}>
"""

     await ch.send(msg)

  except Exception as e:
   print("Commodity error",e)

  await asyncio.sleep(3600)

# -------- PSX --------

async def psx():

 await bot.wait_until_ready()
 ch = bot.get_channel(CHANNEL["psx"])

 while not bot.is_closed():

  try:
   async with aiohttp.ClientSession() as s:

    url="https://dps.psx.com.pk/indices/KSE100"

    async with s.get(url) as r:

     text=await r.text()

     if "data" in text:

      import json

      j=json.loads(text)

      val=j["data"]["value"]
      chg=j["data"]["change"]
      pct=j["data"]["percent_change"]

      msg=f"""
🇵🇰 **PSX MARKET**

KSE100 : {val}
Change : {chg} ({pct}%)

<@&{ROLE}>
"""

      await ch.send(msg)

  except Exception as e:
   print("PSX error",e)

  await asyncio.sleep(3600)

# -------- WHALE --------

async def whale():

 await bot.wait_until_ready()
 ch = bot.get_channel(CHANNEL["whale"])

 while not bot.is_closed():

  try:
   async with aiohttp.ClientSession() as s:

    url="https://api.binance.com/api/v3/trades?symbol=BTCUSDT&limit=20"

    async with s.get(url) as r:

     j=await r.json()

     for t in j:

      usd=float(t["price"])*float(t["qty"])

      if usd>1000000:

       msg=f"""
🐋 **BTC WHALE TRADE**

Value : ${usd:,.0f}

<@&{ROLE}>
"""

       await ch.send(msg)

  except Exception as e:
   print("Whale error",e)

  await asyncio.sleep(60)

@bot.event
async def on_ready():

 print("BOT CONNECTED:",bot.user)

 bot.loop.create_task(crypto())
 bot.loop.create_task(global_markets())
 bot.loop.create_task(commodities())
 bot.loop.create_task(psx())
 bot.loop.create_task(whale())

bot.run(TOKEN)
