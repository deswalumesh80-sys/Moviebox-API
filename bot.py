import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

sys.stdout.reconfigure(line_buffering=True)

# Credentials
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

# True Moviebox + Multi-Server Search Engine
def search_moviebox(query):
    results = []
    
    # 1. Primary Moviebox / Multi-Stream Engine
    try:
        url = f"https://vidsrc.to/api/search?keyword={query}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(url, headers=headers, timeout=6).json()
        if res and isinstance(res, list):
            for item in res[:5]:
                results.append({
                    "title": item.get("title") or item.get("name"),
                    "url": item.get("url") or f"https://vidsrc.to/embed/movie/{item.get('id')}"
                })
    except Exception:
        pass

    # 2. Universal Stream Network Engine (Animal, War, etc.)
    if not results:
        try:
            url = f"https://api.themoviedb.org/3/search/multi?api_key=4b600a94b59fa8399f6b32df6ff09a5c&query={requests.utils.quote(query)}"
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(url, headers=headers, timeout=6).json()
            for item in res.get("results", [])[:6]:
                title = item.get("title") or item.get("name") or item.get("original_title")
                media_type = item.get("media_type", "movie")
                media_id = item.get("id")
                if title and media_id:
                    results.append({
                        "title": f"{title} ({media_type.upper()})",
                        "url": f"https://vidsrc.to/embed/{media_type}/{media_id}"
                    })
        except Exception:
            pass

    # 3. Direct Fast Embed Fallback
    if not results:
        clean_q = requests.utils.quote(query)
        results.append({
            "title": f"🎬 Stream: {query.title()} (Fast Server)",
            "url": f"https://vidsrc.to/embed/movie/{clean_q}"
        })

    return results

@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔥 Trending Movies", url="https://vidsrc.to/trending/movie"))
    markup.row(InlineKeyboardButton("⚡ Latest Web Series", url="https://vidsrc.to/trending/tv"))
    bot.reply_to(
        message,
        "👋 *Moviebox Search Engine 100% Online!*\n\nKisi bhi movie (Animal, War, Jawan) ya web series ka naam likhkar bhejein:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: True)
def handle_search(message):
    query = message.text.strip()
    status = bot.reply_to(message, f"🔍 *'{query}' search ho raha hai...*")
    
    results = search_moviebox(query)
    
    markup = InlineKeyboardMarkup()
    for item in results:
        title = item.get("title", "Watch Media")
        short_title = (title[:28] + "..") if len(title) > 28 else title
        markup.row(InlineKeyboardButton(f"▶️ {short_title}", url=item.get("url")))

    bot.edit_message_text(
        f"🍿 *Moviebox Results for:* `{query}`",
        chat_id=message.chat.id,
        message_id=status.message_id,
        reply_markup=markup
    )

if __name__ == "__main__":
    try:
        bot.remove_webhook()
    except Exception:
        pass

    web_thread = threading.Thread(target=start_http_server, daemon=True)
    web_thread.start()
    
    print("[BOT] Moviebox Telegram Engine Starting...", flush=True)
    bot.infinity_polling(timeout=20, long_polling_timeout=20)
    
