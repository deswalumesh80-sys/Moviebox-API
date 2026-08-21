import os
import asyncio
import requests
from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Exact Credentials from Screenshot
API_ID = 38398715
API_HASH = "6d70e41f8c67908ed547e31c2cfe9c3a"
BOT_TOKEN = "7843197474:AAHB-SHdt3XsSk_ZULtkwYvTSa-BIQ_DAKc"
PORT = int(os.environ.get("PORT", 8080))

bot = Client("toji_movie_engine", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Health Check server for Render
async def handle_ping(request):
    return web.Response(text="Movie Bot Engine is Online!", status=200)

def search_shins_moviebox(query):
    try:
        url = f"https://api.themoviedb.org/3/search/multi?query={query}&api_key=4b600a94b59fa8399f6b32df6ff09a5c"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=8).json()
        return res.get("results", [])[:6]
    except Exception:
        return []

@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(c, m):
    await m.reply_text(
        "🥷 **#Toji Movie Engine Online**\n\n"
        "🍿 *Kisi bhi movie ya series ka naam likhkar bhejein:*"
    )

@bot.on_message(filters.private & ~filters.command("start"))
async def handle_search(c, m):
    query = m.text.strip()
    status_msg = await m.reply_text(f"🔍 **'{query}' dhoondh rahe hain...**")
    
    results = search_shins_moviebox(query)
    
    if not results:
        return await status_msg.edit_text("❌ **Koi result nahi mila!** Spelling check karein.")
    
    buttons = []
    for item in results:
        title = item.get("title") or item.get("name") or item.get("original_title")
        media_type = item.get("media_type", "movie")
        media_id = item.get("id")
        
        if title and media_id:
            stream_url = f"https://vidsrc.to/embed/{media_type}/{media_id}"
            short_title = (title[:28] + "..") if len(title) > 28 else title
            buttons.append([InlineKeyboardButton(f"🎬 {short_title} ({media_type.upper()})", url=stream_url)])
    
    if not buttons:
        return await status_msg.edit_text("❌ **Koi playable stream nahi mila!**")
        
    await status_msg.edit_text(
        f"🍿 **Results for:** `{query}`\n\n⚡ *Source: Multi-Cloud Streaming Engine*",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

async def main():
    await start_web_server()
    await bot.start()
    print(">>> Bot Started Successfully!")
    await idle()
    await bot.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    
