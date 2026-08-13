import telebot
import threading
import time
import uuid
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from keep_alive import keep_alive  # 24/7 चलाने के लिए

API_TOKEN = '8794394167:AAHTK4F7wJogBBjEcUR_bf8-NHy4Pxvz19Y'
ADMIN_ID = 5687910029
CHANNEL_LINK = 'https://t.me/+5v-jy2esoPdmYTA9'
BOT_USERNAME = 'AMIT_DUBBERS_bot'

bot = telebot.TeleBot(API_TOKEN)
DB_FILE = "videos_database.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

video_database = load_db()

def auto_delete_and_notify(chat_id, message_id, delay=600):
    time.sleep(delay)
    try:
        bot.delete_message(chat_id, message_id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 चैनल जॉइन करें", url=CHANNEL_LINK))
        bot.send_message(
            chat_id,
            "⏳ समय समाप्त! वीडियो डिलीट हो गई है। ऐसी और वीडियो के लिए चैनल जॉइन करें:",
            reply_markup=markup
        )
    except Exception as e:
        print(f"Error: {e}")

@bot.message_handler(commands=['start'])
def handle_start(message):
    args = message.text.split()
    if len(args) > 1:
        vid_key = args[1]
        if vid_key in video_database:
            bot.send_message(message.chat.id, "⚠️ ध्यान दें: यह वीडियो 10 मिनट में डिलीट हो जाएगी।")
            sent = bot.send_video(message.chat.id, video_database[vid_key])
            threading.Thread(target=auto_delete_and_notify, args=(message.chat.id, sent.message_id, 600)).start()
        else:
            bot.send_message(message.chat.id, "❌ इनवैलिड लिंक।")
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 चैनल पर जाएं", url=CHANNEL_LINK))
        bot.send_message(message.chat.id, "वीडियो के लिए चैनल पर जाएँ:", reply_markup=markup)

@bot.message_handler(content_types=['video'])
def upload(message):
    if message.from_user.id != ADMIN_ID: return
    vid_id = uuid.uuid4().hex[:8]
    video_database[vid_id] = message.video.file_id
    save_db(video_database)
    link = f"https://t.me/{BOT_USERNAME}?start={vid_id}"
    bot.reply_to(message, f"✅ सेव हो गया!\n\nID: `{vid_id}`\nLink: `{link}`", parse_mode="Markdown")

keep_alive() # सर्वर को चालू रखने के लिए
bot.infinity_polling()
