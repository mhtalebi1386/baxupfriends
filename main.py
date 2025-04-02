from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
from PIL import Image, ImageDraw, ImageFont
import io
import aiohttp
import requests

TOKEN = "7943959800:AAH6eUvuVdLlRt1oj2OkaWjhsBu79X9hg5w"
NEWS_API_KEY = "ddd5ffbab4374ba2bb089233d321fcc3"
NEWS_API_URL = "https://newsapi.org/v2/everything"
AUTHORIZED_USERS = [7849588349, 7622786853]
is_active = False
calculations = {}
active_calc = {}

async def fetch_news(query, language):
    async with aiohttp.ClientSession() as session:
        params = {"apiKey": NEWS_API_KEY, "q": query, "language": language, "pageSize": 5}
        async with session.get(NEWS_API_URL, params=params) as response:
            data = await response.json()
            if data["status"] == "ok":
                return "\n\n".join([f"**{article['title']}**\n{article['description']}\nلینک خبر: {article['url']}" for article in data["articles"]])
            return "متأسفانه در دریافت اخبار مشکلی پیش آمد."

async def irannews(update: Update, context: CallbackContext):
    if not is_active:
        await update.message.reply_text("❌ ربات در حال حاضر غیرفعال است.")
        return
    news = await fetch_iran_news()
    await update.message.reply_text(f"📰 اخبار روز ایران:\n\n{news}")



async def welcome(update: Update, context: CallbackContext):
    new_user = update.message.new_chat_members[0]
    user_name = new_user.first_name
    image_path = "2025-04-02 00.58.19.jpg"
    img = Image.open(image_path).convert("RGBA")
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf", 35)
    draw = ImageDraw.Draw(img)
    text = ""
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_position = ((img.width - (text_bbox[2] - text_bbox[0])) // 2, img.height - (text_bbox[3] - text_bbox[1]) - 100)
    draw.text(text_position, text, font=font, fill="white")
    user_profile_photo = await context.bot.get_user_profile_photos(new_user.id, limit=1)
    if user_profile_photo.photos:
        photo_file = await user_profile_photo.photos[0][-1].get_file()
        with io.BytesIO() as photo_buffer:
            await photo_file.download_to_memory(photo_buffer)
            photo_buffer.seek(0)
            user_img = Image.open(photo_buffer).convert("RGBA").resize((350, 350))
            mask = Image.new("L", (350, 350), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 350, 350), fill=255)
            user_img.putalpha(mask)
            img.paste(user_img, ((img.width - 350) // 2, (img.height - 350) // 3), user_img)
    with io.BytesIO() as output:
        img.save(output, format="PNG")
        output.seek(0)
        await update.message.reply_photo(photo=output)
        await update.message.reply_text(f"سلام @{new_user.username} \nبه گروه ما خوش آمدید! ✨", parse_mode="MarkdownV2")

async def on_message(update: Update, context: CallbackContext):
    if update.message.text:
        if any(word in update.message.text.lower() for word in ["کص ننت", "حروم زاده", "کص ننه", "https", "http"]):
            await update.message.delete()

async def start(update: Update, context: CallbackContext):
    if update.message.from_user.id not in AUTHORIZED_USERS:
        await update.message.reply_text("شما اجازه استفاده از این دستور را ندارید.")
        return
    global is_active
    is_active = True
    await update.message.reply_text("ربات فعال شد.")

async def off(update: Update, context: CallbackContext):
    if update.message.from_user.id not in AUTHORIZED_USERS:
        await update.message.reply_text("شما اجازه استفاده از این دستور را ندارید.")
        return
    global is_active
    is_active = False
    active_calc.clear()
    await update.message.reply_text("ربات غیرفعال شد.")

def get_calc_keyboard(user_id):
    buttons = [["7", "8", "9", "÷"], ["4", "5", "6", "×"], ["1", "2", "3", "-"], ["C", "0", "=", "+"]]
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=f"calc_{user_id}_{text}") for text in row] for row in buttons])

async def start_calc(update: Update, context: CallbackContext):
    if not is_active:
        await update.message.reply_text("❌ ربات در حال حاضر غیرفعال است.")
        return
    user_id = update.message.from_user.id
    if user_id in active_calc and active_calc[user_id]:
        await update.message.reply_text("❌ شما قبلاً ماشین حساب را فعال کرده‌اید.")
        return
    active_calc[user_id] = True
    calculations[user_id] = ""
    reply_markup = get_calc_keyboard(user_id)
    await update.message.reply_text("🧮 **ماشین حساب شیشه‌ای**\n\n🔢 عدد یا عملیات وارد کنید:", reply_markup=reply_markup)




async def handle_calc(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    if not is_active or user_id not in active_calc or not active_calc[user_id]:
        await query.answer("ربات غیرفعال است.")
        return
    data = query.data.split("_")[2]
    if user_id not in calculations:
        calculations[user_id] = ""
    if data == "C":
        calculations[user_id] = ""
    elif data == "=":
        try:
            calculations[user_id] = str(eval(calculations[user_id].replace("×", "*").replace("÷", "/")))
        except:
            calculations[user_id] = "خطا!"
    else:
        calculations[user_id] += data
    try:
        await query.message.edit_text(f"🧮 ماشین حساب شیشه‌ای\n\n🔢 `{calculations[user_id]}`", reply_markup=get_calc_keyboard(user_id))
    except:
        await query.answer("ربات غیرفعال است.")

async def help_command(update: Update, context: CallbackContext):
    if not is_active:
        await update.message.reply_text("❌ ربات در حال حاضر غیرفعال است.")
        return
    await update.message.reply_text(
        "📜 دستورهای ربات:\n\n"
        "✅ /irannews: دریافت اخبار روز ایران.\n"
        "✅ /calc: شروع استفاده از ماشین حساب شیشه‌ای.\n"
        "✅ /help: نمایش این دستورالعمل.\n\n"
        "🔹 مدیران:\n"
        "✅ /start: فعال‌سازی ربات.\n"
        "✅ /off: غیرفعال‌سازی ربات."
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("irannews", irannews))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("off", off))
    app.add_handler(CommandHandler("calc", start_calc))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_calc, pattern="^calc_.*"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    print("🚀 ربات آماده به کار است!")
    app.run_polling()

if __name__ == "__main__":
    main()
