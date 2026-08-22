import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

sys.stdout.reconfigure(line_buffering=True)

BOT_TOKEN = "8966860464:AAF3FDxZi5l9IR7IxiqK2LAo2qn_zqxVowA"
PORT = int(os.environ.get("PORT", 8080))
RESULTS_PER_PAGE = 5

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Render keep-alive server
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Moviebox Engine Online & Active")

    def log_message(self, format, *args):
        return

def start_http_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthServer)
    print(f"[HTTP] Server running on port {PORT}", flush=True)
    server.serve_forever()

# 100% Dynamic API Search Engine
def search_live_media(query):
    try:
        url = f"https://api.themoviedb.org/3/search/multi?api_key=4b600a94b59fa8399f6b32df6ff09a5c&query={requests.utils.quote(query)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=8).json()
        raw_items = res.get("results", [])
        
        parsed_results = []
        for item in raw_items:
            media_type = item.get("media_type")
            if media_type not in ["movie", "tv"]:
                continue
                
            title = item.get("title") or item.get("name") or item.get("original_title")
            media_id = item.get("id")
            release = item.get("release_date") or item.get("first_air_date") or ""
            year = release.split("-")[0] if release else "N/A"
            rating = item.get("vote_average", 0)
            
            if title and media_id:
                parsed_results.append({
                    "id": media_id,
                    "title": title,
                    "year": year,
                    "type": media_type,
                    "rating": round(rating, 1)
                })
        return parsed_results
    except Exception as e:
        print(f"[SEARCH ERROR] {e}", flush=True)
        return []

def build_pagination_markup(results, query, page=1):
    markup = InlineKeyboardMarkup()
    total_results = len(results)
    total_pages = (total_results + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE
    
    start_idx = (page - 1) * RESULTS_PER_PAGE
    end_idx = start_idx + RESULTS_PER_PAGE
    current_items = results[start_idx:end_idx]
    
    for item in current_items:
        type_label = "MOVIE" if item["type"] == "movie" else "SERIES"
        btn_text = f"🎬 {item['title']} ({item['year']}) ⭐ {item['rating']} [{type_label}]"
        # Shorten button text if needed
        if len(btn_text) > 40:
            btn_text = f"🎬 {item['title'][:22]}.. ({item['year']}) [{type_label}]"
        markup.row(InlineKeyboardButton(btn_text, callback_data=f"play_{item['type']}_{item['id']}"))
    
    # Dynamic Navigation Row (Only show if multiple pages exist)
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Back", callback_data=f"page_{query}_{page - 1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"📄 Page {page}/{total_pages}", callback_data="noop"))
    
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{query}_{page + 1}"))
        
    if total_pages > 1:
        markup.row(*nav_buttons)
        
    return markup, total_pages

@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔥 Trending Feed", url="https://vidsrc.to/trending/movie"))
    bot.reply_to(
        message,
        "👋 *Moviebox Dynamic Search Engine Live!*\n\n"
        "Kisi bhi movie ya web series ka naam bhejein (Jaise: *Animal, War, Loki, Stranger Things*):",
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: True)
def handle_search(message):
    query = message.text.strip()
    status = bot.reply_to(message, f"🔍 *Searching for '{query}' across servers...*")
    
    results = search_live_media(query)
    
    if not results:
        bot.edit_message_text(
            f"❌ **'{query}' ka koi result nahi mila.** Kripya sahi spelling check karein.",
            chat_id=message.chat.id,
            message_id=status.message_id
        )
        return

    markup, total_pages = build_pagination_markup(results, query, page=1)
    
    bot.edit_message_text(
        f"🍿 **Results for:** `{query}`\n"
        f"📊 **Total Matches Found:** `{len(results)}`\n\n"
        f"👇 *Play karne ke liye movie/series select karein:*",
        chat_id=message.chat.id,
        message_id=status.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("page_"))
def handle_pagination(call):
    _, query, page_str = call.data.split("_")
    page = int(page_str)
    
    results = search_live_media(query)
    if not results:
        bot.answer_callback_query(call.id, "Session expired, please search again.")
        return
        
    markup, _ = build_pagination_markup(results, query, page=page)
    
    bot.edit_message_text(
        f"🍿 **Results for:** `{query}`\n"
        f"📊 **Total Matches Found:** `{len(results)}`\n\n"
        f"👇 *Play karne ke liye movie/series select karein:*",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("play_"))
def handle_play_options(call):
    _, media_type, media_id = call.data.split("_")
    
    # Dynamic Servers for playback
    server1 = f"https://vidsrc.to/embed/{media_type}/{media_id}"
    server2 = f"https://multiembed.mov/?video_id={media_id}&tmdb=1"
    server3 = f"https://2embed.cc/embed/{media_id}" if media_type == "movie" else f"https://2embed.cc/embedtv/{media_id}&s=1&e=1"
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📱 ▶️ Play In Telegram (Web App)", web_app=WebAppInfo(url=server1)))
    markup.row(InlineKeyboardButton("⚡ Server 1: 1080p HD", url=server1))
    markup.row(InlineKeyboardButton("⚡ Server 2: Multi-Language / Hindi", url=server2))
    markup.row(InlineKeyboardButton("⚡ Server 3: 4K Stream", url=server3))
    markup.row(InlineKeyboardButton("❌ Close", callback_data="close_box"))
    
    bot.edit_message_text(
        "🎬 **Select Playback Server:**\n\n"
        "• Telegram ke andar play karne ke liye **Play In Telegram** dabayein.\n"
        "• High speed ke liye **Server 1, 2 ya 3** choose karein.",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "close_box")
def close_window(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "noop")
def noop_handler(call):
    bot.answer_callback_query(call.id)

if __name__ == "__main__":
    try:
        bot.remove_webhook()
    except Exception:
        pass

    web_thread = threading.Thread(target=start_http_server, daemon=True)
    web_thread.start()
    
    print("[BOT] Moviebox Dynamic Engine Online & Polling...", flush=True)
    bot.infinity_polling(timeout=20, long_polling_timeout=20, restart_on_change=False)
    
