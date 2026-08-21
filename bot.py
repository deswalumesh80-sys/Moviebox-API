import os
import asyncio
import requests
from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Telegram Credentials
API_ID = 38398715
API_HASH = "6d70e41f8c67908ed547e31c2cfe9c3a"
BOT_TOKEN = "8588875170:AAE-2TF39moR_LksMVaYbxG5JLHB-pASoQM"
PORT = int(os.environ.get("PORT", 8080))

bot = Client("moviebox_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Render ke liye Health Check Server
async def handle_ping(request):
    return web.Response(text="Moviebox Bot Engine is Running!", status=200)

# Moviebox API Search Logic
def search_moviebox(query):
    try:
        url = f"https://moviebox.phimapi.com/api/search?keyword={query}"
        res = requests.get(url, timeout=10).json()
        items = res.get("data", {}).get("items", [])
        return items[:6]
    except Exception:
        return []

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(c, m):
    await m.reply_text(
        "🥷 **#Toji Moviebox Engine Online**\n\n"
        "🍿 *Kisi bhi movie ya web series ka naam likhkar bhejein:*"
    )

@bot.on_message(filters.private & ~filters.command("start"))
async def handle_search(c, m):
    query = m.text.strip()
    status_msg = await m.reply_text(f"🔍 **'{query}' search ho raha hai...**")
    
    results = search_moviebox(query)
    
    if not results:
        return await status_msg.edit_text("❌ **Koi file nahi mili!** Kripya spelling check karein.")
    
    buttons = []
    for item in results:
        title = item.get("name") or item.get("origin_name")
        slug = item.get("slug")
        link = f"https://moviebox.phimapi.com/movie/{slug}"
        short_title = (title[:30] + "..") if len(title) > 30 else title
        buttons.append([InlineKeyboardButton(f"🎬 {short_title}", url=link)])
    
    await status_msg.edit_text(
        f"🍿 **Results for:** `{query}`\n\n⚡ *Provided by #Toji Moviebox Engine*",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def main():
    # Web server start (Render keep-alive)
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    
    # Bot start
    await bot.start()
    print(">>> Moviebox Bot is Live!")
    await idle()
    await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
  
