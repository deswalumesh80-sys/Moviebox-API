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

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Render keep-alive server
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Toji Engine Active")

    def log_message(self, format, *args):
        return

def start_http_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthServer)
    print(f"[HTTP] Server listening on port {PORT}", flush=True)
    server.serve_forever()

# TMDB Core Data
def get_tmdb_data(query):
    try:
        url = f"https://api.themoviedb.org/3/search/multi?api_key=4b600a94b59fa8399f6b32df6ff09a5c&query={requests.utils.quote(query)}"
        res = requests.get(url, timeout=6).json()
        return res.get("results", [])[:1]
    except Exception:
        return []

@bot.message_handler(commands=['start'])
def handle_start(message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("⚡ Quick Help", callback_data="help"), InlineKeyboardButton("👑 Admin Support", url="https://t.me/BotFather"))
    markup.row(InlineKeyboardButton("💡 Movie Ideas", callback_data="ideas"), InlineKeyboardButton("💳 Upgrade Plan", callback_data="upgrade"))
    
    caption = (
        "🥷 I am **#Toji v2.1**\n"
        "⚡ **Unlimited files**\n"
        "📥 **Get instant file**\n"
        "💯 **100% Free, always**\n"
        "👤 By **The Filmy Men**"
    )
    bot.reply_to(message, caption, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["help", "ideas", "upgrade"])
def handle_menu_clicks(call):
    if call.data == "upgrade":
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("1 Month - ₹50", callback_data="pay_50"), InlineKeyboardButton("2 Month - ₹90", callback_data="pay_90"))
        markup.row(InlineKeyboardButton("3 Month - ₹140", callback_data="pay_140"), InlineKeyboardButton("4 Month - ₹190", callback_data="pay_190"))
        bot.edit_message_text("🌸 **Premium Plans & Pricing** 🌸\n\n✅ Instant Movies\n✅ No Ads & Scan Audio\n\n👇 *Select Plan:*", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
    else:
        bot.answer_callback_query(call.id, "Feature active! Type movie name to search.")

@bot.message_handler(func=lambda msg: True)
def handle_search(message):
    query = message.text.strip()
    status = bot.reply_to(message, f"🔍 *'{query}' search ho raha hai...*")
    
    items = get_tmdb_data(query)
    title = query.title()
    year = "2024"
    
    if items:
        title = items[0].get("title") or items[0].get("name") or query.title()
        rel = items[0].get("release_date") or items[0].get("first_air_date") or "2024"
        year = rel.split("-")[0]

    # Generating True Toji-Style Multi-Quality File Results
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📦 📥 Get All Files 📥", callback_data=f"all_{title}"))
    markup.row(InlineKeyboardButton(f"📁 2.21 GB | {title} ({year}) Hindi 1080p.mkv", callback_data=f"file_1080_{title}"))
    markup.row(InlineKeyboardButton(f"📁 1.22 GB | {title} ({year}) Hindi 720p.mkv", callback_data=f"file_720_{title}"))
    markup.row(InlineKeyboardButton(f"📁 480 MB | {title} ({year}) Dual Audio 480p.mkv", callback_data=f"file_480_{title}"))
    markup.row(InlineKeyboardButton("📄 Total 138 Pages", callback_data="pages"), InlineKeyboardButton("Next ➡️", callback_data="next"))

    bot.edit_message_text(
        f"🍿 **Requested By:** {message.from_user.first_name}\n\n👇 **Select file to download/stream:**",
        chat_id=message.chat.id,
        message_id=status.message_id,
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("file_") or call.data.startswith("all_"))
def send_stream_card(call):
    name = call.data.split("_")[-1]
    
    # Fast Stream Embed
    stream_url = f"https://vidsrc.to/embed/movie/{requests.utils.quote(name)}"
    
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("▶️ Download | Stream", web_app=WebAppInfo(url=stream_url)))
    markup.row(InlineKeyboardButton("🔊 Scan Audio", callback_data="audio_ok"))
    markup.row(InlineKeyboardButton("❌ Close", callback_data="close_card"))
    
    caption = (
        f"🎬 **{name} (Original Print) .mkv**\n\n"
        f"⚡ **Powered By:** `The Filmy Men`\n\n"
        f"✨ *Click Download / Stream to watch directly in Telegram.*"
    )
    bot.edit_message_text(caption, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "close_card")
def close_popup(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    # Force kill old hanging webhook sessions to prevent Error 409
    try:
        bot.remove_webhook()
    except Exception:
        pass

    # Start Render Port Server
    web_thread = threading.Thread(target=start_http_server, daemon=True)
    web_thread.start()
    
    print("[BOT] Toji Engine Online & Polling...", flush=True)
    bot.infinity_polling(timeout=20, long_polling_timeout=20, restart_on_change=False)
    
