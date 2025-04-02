from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext
from PIL import Image, ImageDraw, ImageFont
import io
import aiohttp
import requests

BASE_IMAGE_PATH = "360_F_87970620_Tdgw6WYdWnrZHn2uQwJpVDH4vr4PINSc.jpg"
TOKEN = "7943959800:AAH6eUvuVdLlRt1oj2OkaWjhsBu79X9hg5w"
calculations = {}
AUTHORIZED_USERS = [7849588349, 7622786853]
is_active = False
active_calc = {}  # Added this to track active calculators per user
NEWS_API_KEY = "ddd5ffbab4374ba2bb089233d321fcc3"
NEWS_API_URL = "https://newsapi.org/v2/everything"


async def fetch_technology_news():
    async with aiohttp.ClientSession() as session:
        params = {
            "apiKey": NEWS_API_KEY,
            "q": "technology OR tech",
            "language": "en",
            "pageSize": 5,
        }
        async with session.get(NEWS_API_URL, params=params) as response:
            data = await response.json()
            if data["status"] == "ok":
                articles = data["articles"]
                news_list = [f"**{article['title']}**\n{article['description']}\nRead more: {article['url']}" for
                             article in articles]
                return "\n\n".join(news_list)
            else:
                return "مشکلی پیش آمده و نتونستم اخبار رو دریافت کنم."


async def fetch_iran_news():
    params = {
        "apiKey": NEWS_API_KEY,
        "q": "Iran",
        "language": "fa",
        "pageSize": 5,
    }
    response = requests.get(NEWS_API_URL, params=params)
    data = response.json()
    if data["status"] == "ok":
        articles = data["articles"]
        news_list = [f"**{article['title']}**\n{article['description']}\nRead more: {article['url']}" for article in
                     articles]
        return "\n\n".join(news_list)
    else:
        return "مشکلی پیش آمده و نتونستم اخبار ایران رو دریافت کنم."


async def irannews(update: Update, context: CallbackContext):
    news = await fetch_iran_news()
    await update.message.reply_text(f"📰 اخبار روز ایران:\n\n{news}")


async def welcome(update: Update, context: CallbackContext):
    new_user = update.message.new_chat_members[0]
    user_name = new_user.first_name
    image_path = "2025-04-02 00.58.19.jpg"
    img = Image.open(image_path).convert("RGBA")
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf", 35)
    draw = ImageDraw.Draw(img)
    #text = f"Welcome {user_name}"
    text = ""
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_position = ((img.width - text_width) // 2, img.height - text_height - 100)
    draw.text(text_position, text, font=font, fill="white")
    user_profile_photo = await context.bot.get_user_profile_photos(new_user.id, limit=1)
    if user_profile_photo.photos:
        photo_file = await user_profile_photo.photos[0][-1].get_file()
        with io.BytesIO() as photo_buffer:
            await photo_file.download_to_memory(photo_buffer)
            photo_buffer.seek(0)
            user_img = Image.open(photo_buffer).convert("RGBA")
            size = (350, 350)
            user_img = user_img.resize(size)
            mask = Image.new("L", size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, size[0], size[1]), fill=255)
            user_img.putalpha(mask)
            img.paste(user_img, ((img.width - size[0]) // 2, (img.height - size[1]) // 3), user_img)
    with io.BytesIO() as output:
        img.save(output, format="PNG")
        output.seek(0)
        await update.message.reply_photo(photo=output)
        await update.message.reply_text(f"Hi @{new_user.username} \nWelcome to BaxUp Friends🤍✨",
                                        parse_mode="MarkdownV2")


async def on_message(update: Update, context: CallbackContext):
    if update.message.text:  # فقط وقتی پیام حاوی متن باشد اجرا شود
        text = update.message.text.lower()
        banned_words = ["کص ننت", "حروم زاده", "کص ننه", "https", "http"]
        if any(word in text for word in banned_words):
            await update.message.delete()


async def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ شما اجازه استفاده از ربات را ندارید.")
        return
    global is_active
    is_active = True
    await update.message.reply_text("✅ ربات فعال شد!")


async def off(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ شما اجازه استفاده از این دستور را ندارید.")
        return
    global is_active
    is_active = False
    active_calc.clear()  # Clear active calculator data for all users
    await update.message.reply_text("❌ بات غیرفعال شد.")


def get_calc_keyboard(user_id):
    buttons = [
        ["7", "8", "9", "÷"],
        ["4", "5", "6", "×"],
        ["1", "2", "3", "-"],
        ["C", "0", "=", "+"]
    ]
    keyboard = [[InlineKeyboardButton(text, callback_data=f"calc_{user_id}_{text}") for text in row] for row in buttons]
    return InlineKeyboardMarkup(keyboard)


async def start_calc(update: Update, context: CallbackContext):
    if not is_active:
        await update.message.reply_text("❌ ربات غیرفعال است.")
        return
    user_id = update.message.from_user.id
    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ شما اجازه استفاده از این دستور را ندارید.")
        return
    if user_id in active_calc and active_calc[user_id]:
        await update.message.reply_text("❌ شما قبلاً ماشین حساب را فعال کرده‌اید.")
        return
    active_calc[user_id] = True  # Mark the calculator as active for this user
    calculations[user_id] = ""
    reply_markup = get_calc_keyboard(user_id)
    await update.message.reply_text("🧮 **ماشین حساب شیشه‌ای**\n\n🔢 عدد یا عملیات وارد کنید:", reply_markup=reply_markup)


async def handle_calc(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    if not is_active or user_id not in active_calc or not active_calc[user_id]:
        await query.answer("❌ ربات غیرفعال است.")
        return

    data = query.data.split("_")[2]
    if user_id not in calculations:
        calculations[user_id] = ""
    if data == "C":
        calculations[user_id] = ""
    elif data == "=":
        try:
            result = eval(calculations[user_id].replace("×", "*").replace("÷", "/"))
            calculations[user_id] = str(result)
        except:
            calculations[user_id] = "خطا!"
    else:
        calculations[user_id] += data
    reply_markup = get_calc_keyboard(user_id)
    new_text = f"🧮 **ماشین حساب شیشه‌ای**\n\n🔢 `{calculations[user_id]}`"
    if query.message.text != new_text:
        try:
            await query.message.edit_text(new_text, reply_markup=reply_markup)
        except AttributeError:
            await query.answer("❌ ربات غیرفعال است.")


async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "📜 دستورهای ربات:\n\n"
        "دستورات عمومی:\n"
        "✅ /irannews: دریافت اخبار روز ایران.\n"
        "✅ /calc: شروع استفاده از ماشین حساب شیشه‌ای.\n"
        "✅ /help: نمایش این دستورالعمل.\n\n"
        "دستورات ویژه مدیران:\n"
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

    print("🚀 ربات آماده است!")
    app.run_polling()


if __name__ == "__main__":
    main()
