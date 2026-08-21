import os
import asyncio
import json
import requests
from aiohttp import web
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Telegram Configuration
API_ID = 38398715
API_HASH = "6d70e41f8c67908ed547e31c2cfe9c3a"
BOT_TOKEN = "7843197474:AAHB-SHdt3XsSk_ZULtkwYvTSa-BIQ_DAKc"
PORT = int(os.environ.get("PORT", 8080))

bot = Client("moviebox_api_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Health check route for Render
async def handle_ping(request):
    return web.Response(text="Moviebox API Server is Active!", status=200)

def get_movie_results(query):
    # 1. Search via Multi-Cloud API Engine
    try:
        url = f"https://api.themoviedb.org/3/search/multi?query={query}&api_key=4b600a94b59fa8399f6b32df6ff09a5c"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=8).json()
        items = res.get("results", [])
        if items:
            return items[:6]
    except Exception:
        pass

    # 2. Search via Local home.json database from repo
    try:
        if os.path.exists("home.json"):
            with open("home.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                matched = []
                for item in data.get("items", []):
                    title = item.get("title", "")
                    if query.lower() in title.lower():
                        matched.append(item)
                if matched:
                    return matched[:6]
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
        "👋 **Welcome to Moviebox Network Bot!**\n\n"
        "🎬 *Aap yahan kisi bhi Movie ya Web Series ka naam likhkar search kar sakte hain.*\n\n"
        "👇 *Neeche diye gaye buttons se trending content dekhein:*",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@bot.on_callback_query(filters.regex("trending_movies"))
async def trending_callback(c, q):
    buttons = [
        [InlineKeyboardButton("🎬 Watch Trending Feed 1", url="https://vidsrc.to/trending/movie")],
        [InlineKeyboardButton("🎬 Watch Trending Feed 2", url="https://vidsrc.to/movie")]
    ]
    await q.message.edit_text(
        "🔥 **Top Trending Movies List:**\n\nDirect stream karne ke liye server select karein:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@bot.on_callback_query(filters.regex("latest_series"))
async def series_callback(c, q):
    buttons = [
        [InlineKeyboardButton("📺 Watch Series Feed 1", url="https://vidsrc.to/trending/tv")],
        [InlineKeyboardButton("📺 Watch Series Feed 2", url="https://vidsrc.to/tv")]
    ]
    await q.message.edit_text(
        "⚡ **Latest Web Series & Shows:**\n\nDirect play karne ke liye select karein:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@bot.on_message(filters.private & ~filters.command("start"))
async def search_handler(c, m):
    query = m.text.strip()
    status_msg = await m.reply_text(f"🔍 **'{query}' ko Moviebox API par search kiya ja raha hai...**")
    
    results = get_movie_results(query)
    
    if not results:
        return await status_msg.edit_text("❌ **Koi movie/series nahi mili!** Kripya sahi spelling likhein.")
    
    buttons = []
    for item in results:
        title = item.get("title") or item.get("name") or item.get("original_title") or "Play Media"
        media_type = item.get("media_type", "movie")
        media_id = item.get("id")
        
        if media_id:
            stream_url = f"https://vidsrc.to/embed/{media_type}/{media_id}"
            short_title = (title[:26] + "..") if len(title) > 26 else title
            buttons.append([InlineKeyboardButton(f"▶️ {short_title} ({media_type.upper()})", url=stream_url)])
    
    if not buttons:
        return await status_msg.edit_text("❌ **Playable links generate nahi ho sake.**")
        
    await status_msg.edit_text(
        f"🍿 **Search Results for:** `{query}`\n\n⚡ *Powered by Moviebox Engine*",
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
    print(">>> Moviebox API Bot is fully Online and Listening!")
    await idle()
    await bot.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    
