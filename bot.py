import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

sys.stdout.reconfigure(line_buffering=True)

# Credentials
BOT_TOKEN = "7843197474:AAHB-SHdt3XsSk_ZULtkwYvTSa-BIQ_DAKc"
PORT = int(os.environ.get("PORT", 8080))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Render Health Check Web Server
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Moviebox Engine Online")

    def log_message(self, format, *args):
        return

def run_web():
    server = HTTPServer(('0.0.0.0', PORT), SimpleHandler)
    print(f"[HTTP] Server running on port {PORT}", flush=True)
    server.serve_forever()

def search_movie(query):
    try:
        url = f"https://api.themoviedb.org/3/search/multi?query={query}&api_key=4b600a94b59fa8399f6b32df6ff09a5c"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=8).json()
        return res.get("results", [])[:6]
    except Exception as e:
        print(f"Error: {e}", flush=True)
        return []

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔥 Trending Movies", url="https://vidsrc.to/trending/movie"))
    markup.row(InlineKeyboardButton("⚡ Latest Series", url="https://vidsrc.to/trending/tv"))
    bot.reply_to(
        message,
        "👋 *Moviebox Search Engine Online!*\n\nKisi bhi movie ya web series ka naam bhejein:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: True)
def handle_query(message):
    query = message.text.strip()
    status_msg = bot.reply_to(message, f"🔍 *'{query}' search ho raha hai...*")
    
    results = search_movie(query)
    
    if not results:
        bot.edit_message_text("❌ *Koi result nahi mila!* Spelling check karein.", chat_id=message.chat.id, message_id=status_msg.message_id)
        return

    markup = InlineKeyboardMarkup()
    for item in results:
        title = item.get("title") or item.get("name") or item.get("original_title") or "Watch"
        media_type = item.get("media_type", "movie")
        media_id = item.get("id")
        
        if media_id:
            stream_url = f"https://vidsrc.to/embed/{media_type}/{media_id}"
            short_title = (title[:26] + "..") if len(title) > 26 else title
            markup.row(InlineKeyboardButton(f"▶️ {short_title} ({media_type.upper()})", url=stream_url))

    bot.edit_message_text(
        f"🍿 *Results for:* `{query}`",
        chat_id=message.chat.id,
        message_id=status_msg.message_id,
        reply_markup=markup
    )

if __name__ == "__main__":
    # Start HTTP server for Render in background thread
    t = threading.Thread(target=run_web, daemon=True)
    t.start()
    
    print("[BOT] Telegram Bot is Live & Polling...", flush=True)
    bot.infinity_polling(timeout=20, long_polling_timeout=20)
    
