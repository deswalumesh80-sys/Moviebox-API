import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Ensure logs are flushed immediately
sys.stdout.reconfigure(line_buffering=True)

BOT_TOKEN = "8966860464:AAF3FDxZi5l9IR7IxiqK2LAo2qn_zqxVowA"
PORT = int(os.environ.get("PORT", 8080))
TMDB_KEY = "4b600a94b59fa8399f6b32df6ff09a5c"
RESULTS_PER_PAGE = 5

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Render keep-alive server
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Moviebox Engine 100% Operational")

    def log_message(self, format, *args):
        return

def start_http_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthServer)
    print(f"[HTTP] Render Server listening on port {PORT}", flush=True)
    server.serve_forever()

# Robust Multi-Search API Engine
def search_live_media(query):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    results = []
    seen_ids = set()

    # 1. Direct Movie Search
    try:
        url = "https://api.themoviedb.org/3/search/movie"
        params = {"api_key": TMDB_KEY, "query": query, "include_adult": "false"}
        res = requests.get(url, params=params, headers=headers, timeout=8).json()
        for item in res.get("results", []):
            mid = item.get("id")
            if mid and mid not in seen_ids:
                seen_ids.add(mid)
                results.append({
                    "id": mid,
                    "title": item.get("title") or item.get("original_title"),
                    "year": (item.get("release_date") or "N/A")[:4],
                    "type": "movie",
                    "rating": round(item.get("vote_average", 0), 1)
                })
    except Exception as e:
        print(f"[ERROR MOVIE SEARCH] {e}", flush=True)

    # 2. TV / Series Search
    try:
        url = "https://api.themoviedb.org/3/search/tv"
        params = {"api_key": TMDB_KEY, "query": query, "include_adult": "false"}
        res = requests.get(url, params=params, headers=headers, timeout=8).json()
        for item in res.get("results", []):
            mid = item.get("id")
            if mid and mid not in seen_ids:
                seen_ids.add(mid)
                results.append({
                    "id": mid,
                    "title": item.get("name") or item.get("original_name"),
                    "year": (item.get("first_air_date") or "N/A")[:4],
                    "type": "tv",
                    "rating": round(item.get("vote_average", 0), 1)
                })
    except Exception as e:
        print(f"[ERROR TV SEARCH] {e}", flush=True)

    return results

# Live Trending Feed Fetcher
def fetch_trending_feed():
    try:
        url = f"https://api.themoviedb.org/3/trending/all/day?api_key={TMDB_KEY}"
        res = requests.get(url, timeout=8).json()
        items = []
        for item in res.get("results", [])[:8]:
            mid = item.get("id")
            title = item.get("title") or item.get("name")
            mtype = item.get("media_type", "movie")
            year = (item.get("release_date") or item.get("first_air_date") or "2024")[:4]
            if title and mid:
                items.append({
                    "id": mid,
                    "title": title,
                    "type": mtype,
                    "year": year,
                    "rating": round(item.get("vote_average", 0), 1)
                })
        return items
    except Exception:
        return []

def build_pagination_markup(results, query, page=1):
    markup = InlineKeyboardMarkup()
    total_results = len(results)
    total_pages = max(1, (total_results + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE)
    
    start_idx = (page - 1) * RESULTS_PER_PAGE
    end_idx = start_idx + RESULTS_PER_PAGE
    current_items = results[start_idx:end_idx]
    
    for item in current_items:
        type_tag = "🎬 MOVIE" if item["type"] == "movie" else "📺 SERIES"
        btn_title = f"{item['title']} ({item['year']}) ⭐ {item['rating']}"
        if len(btn_title) > 38:
            btn_title = f"{item['title'][:22]}.. ({item['year']}) ⭐ {item['rating']}"
        markup.row(InlineKeyboardButton(f"{type_tag} | {btn_title}", callback_data=f"play_{item['type']}_{item['id']}"))
    
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"pg_{query[:15]}_{page - 1}"))
    if total_pages > 1:
        nav_buttons.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"pg_{query[:15]}_{page + 1}"))
        
    if nav_buttons:
        markup.row(*nav_buttons)
        
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔥 Trending Movies & Series", callback_data="open_trending"))
    bot.reply_to(
        message,
        "👋 **Welcome to Moviebox AI Engine!**\n\n"
        "⚡ *Kisi bhi movie ya web series ka naam likhkar bhejein (Jaise: Animal, War, Salaar, Loki):*\n\n"
        "👇 *Ya trending list dekhne ke liye button dabayein:*",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "open_trending")
def show_trending(call):
    items = fetch_trending_feed()
    if not items:
        bot.answer_callback_query(call.id, "Trending feed update ho raha hai...")
        return

    markup = InlineKeyboardMarkup()
    for item in items:
        type_tag = "🎬" if item["type"] == "movie" else "📺"
        markup.row(InlineKeyboardButton(f"{type_tag} {item['title']} ({item['year']}) ⭐ {item['rating']}", callback_data=f"play_{item['type']}_{item['id']}"))
    
    markup.row(InlineKeyboardButton("❌ Close", callback_data="close_box"))

    bot.edit_message_text(
        "🔥 **Aaj Ka Top Trending Content:**\n\n👇 *Play karne ke liye select karein:*",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: True)
def handle_search(message):
    query = message.text.strip()
    status = bot.reply_to(message, f"🔍 *'{query}' search kiya ja raha hai...*")
    
    results = search_live_media(query)
    
    if not results:
        bot.edit_message_text(
            f"❌ **'{query}' ka koi result nahi mila.**\n\nKripya sahi spelling likhein ya dusra naam search karein.",
            chat_id=message.chat.id,
            message_id=status.message_id
        )
        return

    markup = build_pagination_markup(results, query, page=1)
    
    bot.edit_message_text(
        f"🍿 **Results for:** `{query}`\n"
        f"📊 **Total Matches:** `{len(results)}`\n\n"
        f"👇 *Play karne ke liye movie/series chunein:*",
        chat_id=message.chat.id,
        message_id=status.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("pg_"))
def handle_pages(call):
    parts = call.data.split("_")
    page = int(parts[2])
    query = parts[1]
    
    results = search_live_media(query)
    if not results:
        bot.answer_callback_query(call.id, "Session expired, dubara search karein.")
        return
        
    markup = build_pagination_markup(results, query, page=page)
    bot.edit_message_text(
        f"🍿 **Results for:** `{query}`\n"
        f"📊 **Total Matches:** `{len(results)}`\n\n"
        f"👇 *Play karne ke liye movie/series chunein:*",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("play_"))
def handle_play_options(call):
    _, media_type, media_id = call.data.split("_")
    
    # 3 High-Speed Direct Stream Servers
    server1 = f"https://vidsrc.to/embed/{media_type}/{media_id}"
    server2 = f"https://multiembed.mov/?video_id={media_id}&tmdb=1"
    server3 = f"https://2embed.cc/embed/{media_id}" if media_type == "movie" else f"https://2embed.cc/embedtv/{media_id}&s=1&e=1"
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📱 ▶️ Play In Telegram (Instant)", web_app=WebAppInfo(url=server1)))
    markup.row(InlineKeyboardButton("⚡ Server 1: 1080p HD", url=server1))
    markup.row(InlineKeyboardButton("⚡ Server 2: Multi-Language / Hindi", url=server2))
    markup.row(InlineKeyboardButton("⚡ Server 3: Fast Ultra Stream", url=server3))
    markup.row(InlineKeyboardButton("⬅️ Back to Menu", callback_data="open_trending"))

    bot.edit_message_text(
        "🎬 **Select Playback Server:**\n\n"
        "• Telegram ke andar dekhne ke liye **Play In Telegram** dabayein.\n"
        "• Direct browser streaming ke liye **Server 1, 2 ya 3** choose karein.",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "close_box")
def close_window(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "noop")
def noop(call):
    bot.answer_callback_query(call.id)

if __name__ == "__main__":
    try:
        bot.remove_webhook()
    except Exception:
        pass

    web_thread = threading.Thread(target=start_http_server, daemon=True)
    web_thread.start()
    
    print("[BOT] Moviebox Live Engine Running...", flush=True)
    bot.infinity_polling(timeout=20, long_polling_timeout=20, restart_on_change=False)
    
