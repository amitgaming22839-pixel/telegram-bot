import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler, 
    MessageHandler, ContextTypes, ConversationHandler, filters
)

# --- CONFIGURATION ---
BOT_TOKEN = "8794394167:AAHTK4F7wJogBBjEcUR_bf8-NHy4Pxvz19Y" 
ADMIN_ID = 5687910029
BOT_USERNAME = "AMIT_DUBBERS_bot" 
CHANNEL_LINK = "https://t.me/+5v-jy2esoPdmYTA9" 

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("anime_bot.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anime (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            anime_id INTEGER, 
            file_id TEXT, 
            caption TEXT,
            FOREIGN KEY (anime_id) REFERENCES anime (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        payload = context.args[0] 
        if payload.startswith("anime_"):
            anime_id = payload.split("_")[1]
            await send_anime_videos(update, anime_id)
            return
        elif payload.startswith("vid_"):
            video_file_id = payload.replace("vid_", "")
            await update.message.reply_video(video=video_file_id)
            return

    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("📢 Join My Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("🎬 Free Anime", callback_data="show_anime_list")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Namaste {user.first_name}! Main aapka Anime Bot hoon.\nNiche diye gaye options me se select karein:",
        reply_markup=reply_markup
    )

async def send_anime_videos(update: Update, anime_id: str):
    conn = sqlite3.connect("anime_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, caption FROM videos WHERE anime_id = ?", (anime_id,))
    videos = cursor.fetchall()
    conn.close()

    if not videos:
        await update.effective_message.reply_text("❌ Is Anime folder me abhi koi video nahi hai.")
        return

    await update.effective_message.reply_text("📽️ Videos bhej raha hoon, kripya wait karein...")
    for file_id, caption in videos:
        await update.effective_message.reply_video(
            video=file_id,
            caption=caption or ""
        )

# --- BUTTON HANDLER ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "show_anime_list":
        conn = sqlite3.connect("anime_bot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM anime")
        anime_list = cursor.fetchall()
        conn.close()

        if not anime_list:
            await query.edit_message_text("Abhi koi Anime available nahi hai. Admin jald hi add karenge!")
            return

        keyboard = []
        for a_id, a_name in anime_list:
            deep_link = f"https://t.me/{BOT_USERNAME}?start=anime_{a_id}"
            keyboard.append([InlineKeyboardButton(f"📁 {a_name}", url=deep_link)])
        
        keyboard.append([InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")])
        
        await query.edit_message_text(
            "Niche se apna favorite Anime select karein:", 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "main_menu":
        keyboard = [
            [InlineKeyboardButton("📢 Join My Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("🎬 Free Anime", callback_data="show_anime_list")]
        ]
        await query.edit_message_text("Main Menu:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- NORMAL VIDEO HANDLER FOR ADMIN (Bina /addanime ke video bhejne par) ---
async def handle_normal_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    video = update.message.video or update.message.document
    file_id = video.file_id

    share_link = f"https://t.me/{BOT_USERNAME}?start=vid_{file_id}"
    
    msg = (
        "✅ **Single Video Received!**\n\n"
        f"🆔 **File ID:** `{file_id}`\n\n"
        f"🔗 **Direct Share Link:**\n`{share_link}`\n\n"
        f"👉 **Masked Link:**\n<a href='{share_link}'>▶️ CLICK HERE TO WATCH VIDEO</a>"
    )

    keyboard = [[InlineKeyboardButton("🚀 Open Video", url=share_link)]]
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

# --- FOLDER ADD CONVERSATION (/addanime) ---
WAITING_NAME, WAITING_VID = 1, 2

async def add_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Ye command sirf Admin ke liye hai!")
        return ConversationHandler.END

    await update.message.reply_text("Kripya Anime/Folder ka naam batayein (jaise: Naruto):")
    return WAITING_NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    anime_name = update.message.text.strip()
    
    conn = sqlite3.connect("anime_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO anime (name) VALUES (?)", (anime_name,))
    conn.commit()
    
    cursor.execute("SELECT id FROM anime WHERE name = ?", (anime_name,))
    a_id = cursor.fetchone()[0]
    conn.close()

    context.user_data['a_id'] = a_id
    context.user_data['a_name'] = anime_name

    await update.message.reply_text(
        f"✅ Folder Ban Gaya: *{anime_name}*\n\n"
        "Ab is folder me jitni bhi videos bhejna chahte hain, bhejte rahein.\n"
        "Finish karne ke liye `/done` likhein.",
        parse_mode="Markdown"
    )
    return WAITING_VID

async def receive_vid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    a_id = context.user_data.get('a_id')
    video = update.message.video or update.message.document
    file_id = video.file_id
    caption = update.message.caption or ""

    conn = sqlite3.connect("anime_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO videos (anime_id, file_id, caption) VALUES (?, ?, ?)", (a_id, file_id, caption))
    conn.commit()
    conn.close()

    await update.message.reply_text("✅ Video folder me save ho gayi! Aur videos bhejein ya `/done` likhein.")
    return WAITING_VID

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    a_id = context.user_data.get('a_id')
    a_name = context.user_data.get('a_name', 'Anime')
    
    share_link = f"https://t.me/{BOT_USERNAME}?start=anime_{a_id}"
    
    message = (
        f"🎉 **{a_name}** Folder Ready Ho Gaya!\n\n"
        f"🔗 **Normal Link:**\n`{share_link}`\n\n"
        f"👉 **Masked Link:**\n<a href='{share_link}'>▶️ WATCH {a_name}</a>"
    )
    
    keyboard = [[InlineKeyboardButton("🚀 Start Bot Directly", url=share_link)]]
    await update.message.reply_text(message, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Process cancel ho gaya.")
    return ConversationHandler.END

# --- MAIN ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addanime", add_anime)],
        states={
            WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            WAITING_VID: [
                MessageHandler(filters.VIDEO | filters.Document.VIDEO, receive_vid),
                CommandHandler("done", done)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.VIDEO | filters.Document.VIDEO, handle_normal_video))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot Running...")
    app.run_polling()



