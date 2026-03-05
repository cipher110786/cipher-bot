import discord
import aiohttp
import os
import asyncio
from discord.ext import commands, tasks

# Environment Variables from Railway
TOKEN = os.getenv("DISCORD_TOKEN")
CMC_API = os.getenv("CMC_API_KEY")
CMC_CHANNEL_ID = int(os.getenv("CMC_CHANNEL"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# -------- ASYNC DATA FETCHING -------- #

async def get_cmc_prices():
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
        # Using aiohttp instead of requests to prevent bot lag
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=10) as response:
                data = await response.json()
                
                # Check if API returned an error
                if response.status != 200:
                    print(f"CMC API Error: {data['status']['error_message']}")
                    return None

                d = data["data"]
                btc = d["BTC"]["quote"]["USD"]
                eth = d["ETH"]["quote"]["USD"]
                bnb = d["BNB"]["quote"]["USD"]

                return f"""
🚨 **Crypto Market Update**

🟠 **BTC**
Price: `${btc['price']:,.2f}`
24h: `{btc['percent_change_24h']:+.2f}%`

🟣 **ETH**
Price: `${eth['price']:,.2f}`
24h: `{eth['percent_change_24h']:+.2f}%`

🟡 **BNB**
Price: `${bnb['price']:,.2f}`
24h: `{bnb['percent_change_24h']:+.2f}%`
"""
    except Exception as e:
        print(f"CMC Fetch Error: {e}")
        return None

# -------- BOT TASKS -------- #

@bot.event
async def on_ready():
    print(f"✅ Cipher Sentinel is live on Railway as {bot.user}")
    if not market_update.is_running():
        market_update.start()

@tasks.loop(minutes=30)
async def market_update():
    channel = bot.get_channel(CMC_CHANNEL_ID)
    if not channel:
        print(f"❌ Error: Channel {CMC_CHANNEL_ID} not found.")
        return

    message_content = await get_cmc_prices()
    
    if message_content:
        await channel.send(message_content)
    else:
        # Only notify once to avoid spamming error messages
        print("⚠️ Market API error - Check CMC API Key or Credits.")

bot.run(TOKEN)
