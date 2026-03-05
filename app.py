import discord
import requests
import asyncio
import os
import random

TOKEN = os.getenv("DISCORD_TOKEN")

CRYPTO_CHANNEL = int(os.getenv("CRYPTO_CHANNEL"))
CMC_CHANNEL = int(os.getenv("CMC_CHANNEL"))
NEWS_CHANNEL = int(os.getenv("NEWS_CHANNEL"))
WHALE_CHANNEL = int(os.getenv("WHALE_CHANNEL"))

CMC_API_KEY = os.getenv("CMC_API_KEY")

intents = discord.Intents.default()
client = discord.Client(intents=intents)


# -------- CRYPTO PRICES (BINANCE) --------

def get_crypto():
    btc = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()
    eth = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT").json()
    sol = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=SOLUSDT").json()

    return btc["price"], eth["price"], sol["price"]


# -------- CMC TOP COINS --------

def cmc_top():

    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"

    headers = {
        "X-CMC_PRO_API_KEY": CMC_API_KEY
    }

    params = {
        "limit": 5,
        "convert": "USD"
    }

    r = requests.get(url, headers=headers, params=params).json()

    coins = r["data"]

    text = ""

    for c in coins:

        name = c["name"]
        price = c["quote"]["USD"]["price"]
        change = c["quote"]["USD"]["percent_change_24h"]

        text += f"{name} ${price:.2f} ({change:.2f}%)\n"

    return text


# -------- NEWS --------

def market_news():

    news = [
        "Bitcoin volatility increasing today",
        "Altcoins gaining momentum",
        "Institutional investors accumulating BTC",
        "Crypto trading volume rising this week"
    ]

    return random.choice(news)


# -------- WHALE --------

def whale():

    coins = ["BTC", "ETH", "USDT"]
    exchanges = ["Binance", "Coinbase", "Kraken"]

    amount = random.randint(2000,15000)

    c = random.choice(coins)
    e1 = random.choice(exchanges)
    e2 = random.choice(exchanges)

    return f"{amount} {c} moved from {e1} → {e2}"


# -------- LOOP --------

async def loop_updates():

    await client.wait_until_ready()

    while not client.is_closed():

        try:

            crypto_channel = client.get_channel(CRYPTO_CHANNEL)
            cmc_channel = client.get_channel(CMC_CHANNEL)
            news_channel = client.get_channel(NEWS_CHANNEL)
            whale_channel = client.get_channel(WHALE_CHANNEL)

            btc,eth,sol = get_crypto()

            embed = discord.Embed(
                title="🚨 Crypto Market Update",
                color=0x00ff99
            )

            embed.add_field(name="BTC",value=f"${btc}",inline=True)
            embed.add_field(name="ETH",value=f"${eth}",inline=True)
            embed.add_field(name="SOL",value=f"${sol}",inline=True)

            await crypto_channel.send(embed=embed)

            cmc = cmc_top()

            embed2 = discord.Embed(
                title="📊 Top Coins (CoinMarketCap)",
                description=cmc,
                color=0xffcc00
            )

            await cmc_channel.send(embed=embed2)

            embed3 = discord.Embed(
                title="📰 Market News",
                description=market_news(),
                color=0x3498db
            )

            await news_channel.send(embed=embed3)

            embed4 = discord.Embed(
                title="🐋 Whale Alert",
                description=whale(),
                color=0xe74c3c
            )

            await whale_channel.send(embed=embed4)

            print("Updates sent")

        except Exception as e:
            print("Error:", e)

        await asyncio.sleep(1800)   # 30 minutes


@client.event
async def on_ready():

    print(f"Logged in as {client.user}")

    client.loop.create_task(loop_updates())


client.run(TOKEN)
