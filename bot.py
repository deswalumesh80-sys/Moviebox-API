import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

sys.stdout.reconfigure(line_buffering=True)

# Exact Credentials
BOT_TOKEN = "8966860464:AAF3FDxZi5l9IR7IxiqK2LAo2qn_zqxVowA"
PORT = int(os.environ.get("PORT", 8080))

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
    print(f"[HTTP] Render Server running on port {PORT}", flush=True)
    server.serve_forever()

# Advanced TMDB + Multi-Source Search
def search_titles(query):
    try:
        url = f"https://api.themoviedb.org/3/search/multi?api_key=4b600a94b59fa8399f6b32df6ff09a5c&query={requests.utils.quote(query)}"
        res = requests.get(url, timeout=6).json()
        results = []
        for item in res.get("results", [])[:6]:
            title = item.get("title") or item.get("name") or item.get("original_title")
            media_type = item.get("media_type", "movie")
            media_id = item.get("id")
            release = item.get("release_date") or item.get("first_air_date") or ""
            year = release.split("-")[0] if release else "N/A"
            overview = item.get("overview", "No synopsis available.")[:150]
            if title and media_id:
                results.append({
                    "id": media_id,
                    "title": title,
                    "year": year,
                    "type": media_type,
                    "desc": overview
                })
        return results
    except Exception as e:
        print(f"[SEARCH ERROR] {e}", flush=True)
        return []

@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔥 Trending Movies", url="https://vidsrc.to/trending/movie"))
    markup.row(InlineKeyboardButton("⚡ Trending Series", url="https://vidsrc.to/trending/tv"))
    bot.reply_to(
        message,
        "👋 *Moviebox Multi-Server Engine Online!*\n\n"
        "Kisi bhi Movie ya Web Series ka naam likhein (Jaise: *Animal, War, Jawan, Loki*):",
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: True)
def handle_search(message):
    query = message.text.strip()
    status = bot.reply_to(message, f"🔍 *'{query}' ke multiple results search ho rahe hain...*")
    
    results = search_titles(query)
    
    if not results:
        # Direct fallback server
        clean_q = requests.utils.quote(query)
        markup = InlineKeyboardMarkup()
        stream_url = f"https://vidsrc.to/embed/movie/{clean_q}"
        markup.row(InlineKeyboardButton("▶️ Play In-App (Direct)", web_app=WebAppInfo(url=stream_url)))
        bot.edit_message_text(
            f"🎬 *Single Server Result for:* `{query}`",
            chat_id=message.chat.id,
            message_id=status.message_id,
            reply_markup=markup
        )
        return

    markup = InlineKeyboardMarkup()
    for item in results:
        btn_text = f"🎬 {item['title']} ({item['year']}) - [{item['type'].upper()}]"
        markup.row(InlineKeyboardButton(btn_text, callback_data=f"sel_{item['type']}_{item['id']}"))

    bot.edit_message_text(
        f"🍿 *Top Results found for:* `{query}`\n\n👇 *Apni movie/series select karein (Multi-Servers & Quality ke liye):*",
        chat_id=message.chat.id,
        message_id=status.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("sel_"))
def handle_movie_selection(call):
    _, media_type, media_id = call.data.split("_")
    
    # 4 Fast Streaming Servers
    server1_vidsrc = f"https://vidsrc.to/embed/{media_type}/{media_id}"
    server2_super = f"https://multiembed.mov/?video_id={media_id}&tmdb=1"
    server3_auto = f"https://2embed.cc/embed/{media_id}" if media_type == "movie" else f"https://2embed.cc/embedtv/{media_id}&s=1&e=1"
    
    markup = InlineKeyboardMarkup()
    # In-App Telegram Web Player (Runs inside Telegram app)
    markup.row(InlineKeyboardButton("📱 ▶️ Play In Telegram (Web Player)", web_app=WebAppInfo(url=server1_vidsrc)))
    markup.row(InlineKeyboardButton("⚡ Server 1: 1080p HD (Fast)", url=server1_vidsrc))
    markup.row(InlineKeyboardButton("⚡ Server 2: Multi-Language / Hindi", url=server2_super))
    markup.row(InlineKeyboardButton("⚡ Server 3: 4K Ultra Server", url=server3_auto))
    
    bot.edit_message_text(
        "🎬 *Playback & Quality Options:*\n\n"
        "• Telegram ke andar dekhne ke liye **Play In Telegram** dabayein.\n"
        "• High speed streaming ke liye **Server 1, 2 ya 3** select karein.",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )

if __name__ == "__main__":
    try:
        bot.remove_webhook()
    except Exception:
        pass

    web_thread = threading.Thread(target=start_http_server, daemon=True)
    web_thread.start()
    
    print("[BOT] Moviebox Engine Live...", flush=True)
    bot.infinity_polling(timeout=20, long_polling_timeout=20)
    
