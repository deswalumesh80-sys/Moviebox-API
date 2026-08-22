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
TMDB_KEY = "4b600a94b59fa8399f6b32df6ff09a5c"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Render keep-alive server
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot Engine Live")

    def log_message(self, format, *args):
        return

def start_http_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthServer)
    print(f"[HTTP] Server online on port {PORT}", flush=True)
    server.serve_forever()

# Fast & Safe TMDB Fetcher
def search_media(query):
    try:
        url = "https://api.themoviedb.org/3/search/multi"
        params = {"api_key": TMDB_KEY, "query": query, "include_adult": "false"}
        res = requests.get(url, params=params, timeout=7).json()
        items = []
        for row in res.get("results", []):
            m_type = row.get("media_type")
            if m_type not in ["movie", "tv"]:
                continue
            mid = row.get("id")
            title = row.get("title") or row.get("name") or row.get("original_title")
            year = (row.get("release_date") or row.get("first_air_date") or "2024")[:4]
            rating = round(row.get("vote_average", 0), 1)
            if mid and title:
                items.append({
                    "id": mid,
                    "type": m_type,
                    "title": title,
                    "year": year,
                    "rating": rating
                })
        return items[:6]
    except Exception as e:
        print(f"[SEARCH ERROR] {e}", flush=True)
        return []

@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("🔥 Trending Movies", callback_data="tr_mov"))
    markup.row(InlineKeyboardButton("⚡ Trending Series", callback_data="tr_tv"))
    bot.reply_to(
        message,
        "👋 **Movie Engine 100% Online!**\n\n"
        "Kisi bhi movie/series ka naam likhein (Jaise: *War, Animal, Jawan, Loki*):",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda c: c.data in ["tr_mov", "tr_tv"])
def handle_trending(call):
    m_type = "movie" if call.data == "tr_mov" else "tv"
    try:
        url = f"https://api.themoviedb.org/3/trending/{m_type}/day?api_key={TMDB_KEY}"
        res = requests.get(url, timeout=7).json()
        markup = InlineKeyboardMarkup()
        for item in res.get("results", [])[:6]:
            mid = item.get("id")
            title = item.get("title") or item.get("name")
            # Short callback data (Max 64 bytes safe)
            markup.row(InlineKeyboardButton(f"🎬 {title[:25]}", callback_data=f"p_{m_type[0]}_{mid}"))
        
        bot.edit_message_text(
            f"🔥 **Top Trending {m_type.upper()}:**\n\n👇 *Select karein stream ke liye:*",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )
    except Exception:
        bot.answer_callback_query(call.id, "Error loading trending feed.")

@bot.message_handler(func=lambda msg: True)
def handle_search(message):
    query = message.text.strip()
    status = bot.reply_to(message, f"🔍 *'{query}' search ho raha hai...*")
    
    results = search_media(query)
    
    if not results:
        bot.edit_message_text(
            f"❌ **'{query}' ka koi result nahi mila.**\nSpelling check karein.",
            chat_id=message.chat.id,
            message_id=status.message_id
        )
        return

    markup = InlineKeyboardMarkup()
    for item in results:
        type_icon = "🎬" if item["type"] == "movie" else "📺"
        short_title = (item["title"][:22] + "..") if len(item["title"]) > 22 else item["title"]
        btn_label = f"{type_icon} {short_title} ({item['year']}) ⭐ {item['rating']}"
        # Safe short callback_data format: p_m_12345 or p_t_12345
        markup.row(InlineKeyboardButton(btn_label, callback_data=f"p_{item['type'][0]}_{item['id']}"))

    bot.edit_message_text(
        f"🍿 **Results for:** `{query}`\n\n👇 *Play / Stream ke liye select karein:*",
        chat_id=message.chat.id,
        message_id=status.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("p_"))
def handle_player(call):
    parts = call.data.split("_")
    m_type = "movie" if parts[1] == "m" else "tv"
    media_id = parts[2]
    
    # 3 High-Speed Direct Embed Servers
    server1 = f"https://vidsrc.to/embed/{m_type}/{media_id}"
    server2 = f"https://multiembed.mov/?video_id={media_id}&tmdb=1"
    server3 = f"https://2embed.cc/embed/{media_id}" if m_type == "movie" else f"https://2embed.cc/embedtv/{media_id}&s=1&e=1"
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📱 ▶️ Play In Telegram (Direct)", web_app=WebAppInfo(url=server1)))
    markup.row(InlineKeyboardButton("⚡ Server 1: 1080p HD", url=server1))
    markup.row(InlineKeyboardButton("⚡ Server 2: Multi-Audio / Hindi", url=server2))
    markup.row(InlineKeyboardButton("⚡ Server 3: Fast Ultra Server", url=server3))
    markup.row(InlineKeyboardButton("❌ Close", callback_data="close_win"))

    bot.edit_message_text(
        "🍿 **Playback Servers Ready:**\n\n"
        "• Telegram ke andar dekhne ke liye **Play In Telegram** dabayein.\n"
        "• Direct browser streaming ke liye **Server 1, 2 ya 3** open karein.",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=markup
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data == "close_win")
def close_win(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    try:
        bot.remove_webhook()
    except Exception:
        pass

    web_thread = threading.Thread(target=start_http_server, daemon=True)
    web_thread.start()
    
    print("[BOT] Engine Running...", flush=True)
    bot.infinity_polling(timeout=20, long_polling_timeout=20, restart_on_change=False)
    
