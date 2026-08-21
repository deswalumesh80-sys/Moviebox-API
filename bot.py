import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

sys.stdout.reconfigure(line_buffering=True)

# Brand New Fresh Token
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
    print(f"[HTTP] Render Server bound successfully to port {PORT}", flush=True)
    server.serve_forever()

def fetch_media(query):
    try:
        url = f"https://api.themoviedb.org/3/search/multi?query={query}&api_key=4b600a94b59fa8399f6b32df6ff09a5c"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=6).json()
        return res.get("results", [])[:6]
    except Exception as e:
        print(f"[SEARCH ERROR] {e}", flush=True)
        return []

@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔥 Trending Movies", url="https://vidsrc.to/trending/movie"))
    markup.row(InlineKeyboardButton("⚡ Latest Web Series", url="https://vidsrc.to/trending/tv"))
    bot.reply_to(
        message,
        "👋 *Moviebox Engine 100% Online!*\n\nKisi bhi movie ya web series ka naam likhein:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda msg: True)
def handle_search(message):
    query = message.text.strip()
    status = bot.reply_to(message, f"🔍 *'{query}' search ho raha hai...*")
    
    results = fetch_media(query)
    
    if not results:
        bot.edit_message_text("❌ *Koi result nahi mila!* Spelling check karein.", chat_id=message.chat.id, message_id=status.message_id)
        return

    markup = InlineKeyboardMarkup()
    for item in results:
        title = item.get("title") or item.get("name") or item.get("original_title") or "Watch Now"
        media_type = item.get("media_type", "movie")
        media_id = item.get("id")
        
        if media_id:
            stream_link = f"https://vidsrc.to/embed/{media_type}/{media_id}"
            short_name = (title[:26] + "..") if len(title) > 26 else title
            markup.row(InlineKeyboardButton(f"▶️ {short_name} ({media_type.upper()})", url=stream_link))

    bot.edit_message_text(
        f"🍿 *Results for:* `{query}`",
        chat_id=message.chat.id,
        message_id=status.message_id,
        reply_markup=markup
    )

if __name__ == "__main__":
    # Clear old webhooks if any
    try:
        bot.remove_webhook()
    except Exception:
        pass

    # Start HTTP Server in Thread
    web_thread = threading.Thread(target=start_http_server, daemon=True)
    web_thread.start()
    
    # Start Polling
    print("[BOT] Moviebox Telegram Engine Starting...", flush=True)
    bot.infinity_polling(timeout=20, long_polling_timeout=20)
    
