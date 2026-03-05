import discord
import requests
import os
from discord.ext import commands, tasks

TOKEN = os.getenv("DISCORD_TOKEN")
CMC_API = os.getenv("CMC_API_KEY")

CMC_CHANNEL = int(os.getenv("CMC_CHANNEL"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def get_prices():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"

    headers = {
        "Accepts": "application/json",
        "X-CMC_PRO_API_KEY": CMC_API,
    }

    params = {
        "symbol": "BTC,ETH,BNB",
        "convert": "USD"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        btc = data["data"]["BTC"]["quote"]["USD"]
        eth = data["data"]["ETH"]["quote"]["USD"]
        bnb = data["data"]["BNB"]["quote"]["USD"]

        msg = f"""
🚨 **Crypto Market Update**

🟠 **BTC**
Price: ${btc['price']:.2f}
24h: {btc['percent_change_24h']:.2f}%

🟣 **ETH**
Price: ${eth['price']:.2f}
24h: {eth['percent_change_24h']:.2f}%

🟡 **BNB**
Price: ${bnb['price']:.2f}
24h: {bnb['percent_change_24h']:.2f}%
"""

        return msg

    except Exception as e:
        print("CMC ERROR:", e)
        return None


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    market_update.start()


@tasks.loop(minutes=30)
async def market_update():
    channel = bot.get_channel(CMC_CHANNEL)

    if not channel:
        print("Channel not found")
        return

    data = get_prices()

    if data:
        await channel.send(data)
    else:
        await channel.send("⚠️ Market API error.")


bot.run(TOKEN)
