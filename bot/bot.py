import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

load_dotenv()

API_TOKEN = os.getenv("TRAVELPAYOUTS_API_TOKEN")
PARTNER_ID = os.getenv("TRAVELPAYOUTS_PARTNER_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

# States for conversation
FLIGHT_ORIGIN, FLIGHT_DEST, FLIGHT_DATE = range(5)
HOTEL_LOCATION, HOTEL_CHECKIN, HOTEL_CHECKOUT = range(3, 6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the Travel Bot!\n"
        "/flight - Search for flights\n"
        "/hotel - Search for hotels\n"
        "/help - Show help"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commands:\n"
        "/flight - Search for flights\n"
        "/hotel - Search for hotels\n"
        "/help - Show this help message"
    )

# --- Flight search conversation ---
async def flight_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter origin airport code (e.g. NYC):")
    return FLIGHT_ORIGIN

async def flight_origin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['origin'] = update.message.text.strip().upper()
    await update.message.reply_text("Enter destination airport code (e.g. LON):")
    return FLIGHT_DEST

async def flight_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['destination'] = update.message.text.strip().upper()
    await update.message.reply_text("Enter departure date (YYYY-MM-DD):")
    return FLIGHT_DATE

async def flight_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    origin = context.user_data['origin']
    destination = context.user_data['destination']
    departure_at = update.message.text.strip()
    url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
    headers = {"X-Access-Token": API_TOKEN}
    params = {
        "origin": origin,
        "destination": destination,
        "departure_at": departure_at,
        "currency": "usd",
        "limit": 5,
        "one_way": "true",
        "market": "us"
    }
    r = requests.get(url, headers=headers, params=params)
    data = r.json()
    flights = data.get("data", [])
    if not flights:
        await update.message.reply_text("No flights found.")
        return ConversationHandler.END
    for f in flights:
        price = f.get("price")
        airline = f.get("airline")
        flight_number = f.get("flight_number")
        dep = f.get("departure_at")
        link = f.get("link", "")
        if link:
            if "?" in link:
                link += f"&partner_id={PARTNER_ID}"
            else:
                link += f"?partner_id={PARTNER_ID}"
            booking_link = f"https://www.aviasales.com{link}"
        else:
            booking_link = ""
        msg = (
            f"Flight: {origin} → {destination}\n"
            f"Airline: {airline} {flight_number}\n"
            f"Departure: {dep}\n"
            f"Price: {price} USD\n"
            f"[Book Now]({booking_link})" if booking_link else ""
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    return ConversationHandler.END

# --- Hotel search conversation ---
async def hotel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter hotel location (city or airport code):")
    return HOTEL_LOCATION

async def hotel_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['location'] = update.message.text.strip()
    await update.message.reply_text("Enter check-in date (YYYY-MM-DD):")
    return HOTEL_CHECKIN

async def hotel_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['check_in'] = update.message.text.strip()
    await update.message.reply_text("Enter check-out date (YYYY-MM-DD):")
    return HOTEL_CHECKOUT

async def hotel_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    location = context.user_data['location']
    check_in = context.user_data['check_in']
    check_out = update.message.text.strip()
    url = "https://api.travelpayouts.com/v2/hotels/search"
    headers = {"X-Access-Token": API_TOKEN}
    params = {
        "location": location,
        "check_in": check_in,
        "check_out": check_out,
        "currency": "usd",
        "adults": 2,
        "limit": 5
    }
    r = requests.get(url, headers=headers, params=params)
    data = r.json()
    hotels = data.get("results", [])
    if not hotels:
        await update.message.reply_text("No hotels found.")
        return ConversationHandler.END
    for h in hotels:
        name = h.get("name")
        price = h.get("price")
        url = h.get("booking_url", "")
        if url:
            if "?" in url:
                url += f"&partner_id={PARTNER_ID}"
            else:
                url += f"?partner_id={PARTNER_ID}"
        msg = (
            f"Hotel: {name}\n"
            f"Check-in: {check_in}\n"
            f"Check-out: {check_out}\n"
            f"Price: {price} USD\n"
            f"[Book Now]({url})" if url else ""
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Flight search conversation
    flight_conv = ConversationHandler(
        entry_points=[CommandHandler("flight", flight_start)],
        states={
            FLIGHT_ORIGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_origin)],
            FLIGHT_DEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_dest)],
            FLIGHT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_date)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Hotel search conversation
    hotel_conv = ConversationHandler(
        entry_points=[CommandHandler("hotel", hotel_start)],
        states={
            HOTEL_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, hotel_location)],
            HOTEL_CHECKIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, hotel_checkin)],
            HOTEL_CHECKOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, hotel_checkout)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(flight_conv)
    app.add_handler(hotel_conv)

    app.run_polling() 