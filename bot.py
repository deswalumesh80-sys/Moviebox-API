import os
import sys
import asyncio
import json
import requests
from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Flush prints immediately for Render logs
sys.stdout.reconfigure(line_buffering=True)

# Exact Telegram Credentials
API_ID = 38398715
API_HASH = "6d70e41f8c67908ed547e31c2cfe9c3a"
BOT_TOKEN = "7843197474:AAHB-SHdt3XsSk_ZULtkwYvTSa-BIQ_DAKc"
PORT = int(os.environ.get("PORT", 8080))

bot = Client(
    "moviebox_live_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

async def handle_ping(request):
    return web.Response(text="Moviebox API Server is Live & Healthy!", status=200)

def get_movie_results(query):
    try:
        url = f"https://api.themoviedb.org/3/search/multi?query={query}&api_key=4b600a94b59fa8399f6b32df6ff09a5c"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=8).json()
        items = res.get("results", [])
        if items:
            return items[:6]
    except Exception:
        pass
    return []

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(c, m):
    buttons = [
        [InlineKeyboardButton("🔥 Trending Movies", callback_data="trending_movies")],
        [InlineKeyboardButton("⚡ Latest Web Series", callback_data="latest_series")]
    ]
    await m.reply_text(
        "👋 **Moviebox Network Bot Online!**\n\n"
        "🎬 *Movie ya Web Series ka naam bhejein:*",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@bot.on_callback_query(filters.regex("trending_movies"))
async def trending_callback(c, q):
    buttons = [
        [InlineKeyboardButton("🎬 Watch Trending Feed", url="https://vidsrc.to/trending/movie")]
    ]
    await q.message.edit_text("🔥 **Top Trending Movies:**", reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query(filters.regex("latest_series"))
async def series_callback(c, q):
    buttons = [
        [InlineKeyboardButton("📺 Watch Series Feed", url="https://vidsrc.to/trending/tv")]
    ]
    await q.message.edit_text("⚡ **Latest Web Series:**", reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_message(filters.private & ~filters.command("start"))
async def search_handler(c, m):
    query = m.text.strip()
    status_msg = await m.reply_text(f"🔍 **'{query}' search ho raha hai...**")
    
    results = get_movie_results(query)
    
    if not results:
        return await status_msg.edit_text("❌ **Koi file nahi mili!** Spelling check karein.")
    
    buttons = []
    for item in results:
        title = item.get("title") or item.get("name") or item.get("original_title") or "Play"
        media_type = item.get("media_type", "movie")
        media_id = item.get("id")
        
        if media_id:
            stream_url = f"https://vidsrc.to/embed/{media_type}/{media_id}"
            short_title = (title[:26] + "..") if len(title) > 26 else title
            buttons.append([InlineKeyboardButton(f"▶️ {short_title} ({media_type.upper()})", url=stream_url)])
    
    if not buttons:
        return await status_msg.edit_text("❌ **Stream link generate nahi hua.**")
        
    await status_msg.edit_text(
        f"🍿 **Results for:** `{query}`",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def main():
    # 1. Start Web Server
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f">>> Web Server listening on port {PORT}", flush=True)

    # 2. Start Telegram Bot
    await bot.start()
    print(">>> Moviebox API Bot is fully Online and Ready!", flush=True)
    
    await idle()
    await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
                
