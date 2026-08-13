import telebot
import threading
import time
import uuid
import json
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from keep_alive import keep_alive  # To keep server alive 24/7

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
        markup.add(InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK))
        bot.send_message(
            chat_id,
            "⏳ Time is up! The video has been deleted. Join our channel for more videos:",
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
            video_data = video_database[vid_key]
            
            # Support for old database structure (if stored as string file_id)
            if isinstance(video_data, dict):
                file_id = video_data.get("file_id")
                caption_text = video_data.get("caption", "")
            else:
                file_id = video_data
                caption_text = ""

            bot.send_message(message.chat.id, "⚠️ Note: This video will be deleted in 10 minutes.")
            
            # Sending video with original caption/title
            sent = bot.send_video(message.chat.id, file_id, caption=caption_text)
            threading.Thread(target=auto_delete_and_notify, args=(message.chat.id, sent.message_id, 600)).start()
        else:
            bot.send_message(message.chat.id, "❌ Invalid link.")
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Go to Channel", url=CHANNEL_LINK))
        bot.send_message(message.chat.id, "Visit our channel for videos:", reply_markup=markup)

@bot.message_handler(content_types=['video'])
def upload(message):
    if message.from_user.id != ADMIN_ID:
        return
    vid_id = uuid.uuid4().hex[:8]
    
    # Save video file_id and caption
    video_database[vid_id] = {
        "file_id": message.video.file_id,
        "caption": message.caption if message.caption else ""
    }
    save_db(video_database)
    
    link = f"https://t.me/{BOT_USERNAME}?start={vid_id}"
    bot.reply_to(message, f"✅ Saved successfully!\n\nID: `{vid_id}`\nLink: `{link}`", parse_mode="Markdown")

keep_alive()  # To keep bot running
bot.infinity_polling()


