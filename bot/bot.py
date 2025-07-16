import os
import logging
import requests
import csv
from rapidfuzz import process, fuzz
import dateparser
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
)

load_dotenv()

API_TOKEN = os.getenv("TRAVELPAYOUTS_API_TOKEN")
PARTNER_ID = os.getenv("TRAVELPAYOUTS_PARTNER_ID")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

# States for conversation
LANGUAGE, COUNTRY, CURRENCY, MAIN_MENU = range(4)
FLIGHT_TYPE, FLIGHT_ORIGIN, FLIGHT_ORIGIN_CHOICE, FLIGHT_DEST, FLIGHT_DEST_CHOICE, FLIGHT_DEPART, FLIGHT_RETURN = range(4, 11)
HOTEL_CITY, HOTEL_CITY_CHOICE, HOTEL_CHECKIN, HOTEL_CHECKOUT = range(11, 15)

# --- Load airport data for fuzzy matching ---
def load_airport_city_list():
    airports = []
    with open(os.path.join(os.path.dirname(__file__), 'airports.csv'), encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            # OpenFlights: 1=name, 2=city, 3=country, 4=IATA, 5=ICAO
            if len(row) > 4 and row[4] and row[2]:
                # Only include airports with 'International' in their name
                if 'international' in row[1].lower():
                    airports.append({
                        'city': row[2],
                        'iata': row[4],
                        'name': row[1],
                        'country': row[3]
                    })
    return airports

AIRPORT_CITY_LIST = load_airport_city_list()

# --- Fuzzy suggestion utility ---
def suggest_cities(user_input, limit=5):
    choices = [f"{a['city']} ({a['iata']})" for a in AIRPORT_CITY_LIST]
    results = process.extract(user_input, choices, scorer=fuzz.WRatio, limit=limit)
    return [AIRPORT_CITY_LIST[choices.index(match[0])] for match in results if match[1] > 60]  # threshold

# --- Language, Country, Currency options ---
LANGUAGES = [
    ("English", "en"), ("Español", "es"), ("Русский", "ru"), ("Українська", "uk"),
    ("Português", "pt"), ("Italiano", "it"), ("Türkçe", "tr"),("বাংলা", "bn"), ("हिन्दी", "hi"), ("اردو", "ur")
]
COUNTRIES = ["United States", "United Kingdom", "Germany", "France", "Italy", "Spain","Bangladesh", "India", "Turkey", "Pakistan"]
CURRENCIES = ["USD", "EUR", "GBP", "BDT",  "INR", "TRY", "PKR"]

# --- Main Menu Keyboard ---
MAIN_MENU_KEYBOARD = ReplyKeyboardMarkup([
    ["🏠 Main Menu", "🔎 Search Flights", "🏨 Search Hotels"],
    ["🚗 Car & Bike Rentals", "🚆 Trains & Buses"],
    ["🛬 Transfers & Airport Services", "🌐 Buy eSIM"],
    ["🎟️ Tours & Activities", "❌ Cancel"]
], resize_keyboard=True)

# --- Onboarding ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_buttons = [[KeyboardButton(l[0])] for l in LANGUAGES]
    await update.message.reply_text(
        "Please select language.\nPor favor, seleccione el idioma.\nПожалуйста, выберите язык.\nБудь ласка, виберіть мову.\nPor favor selecionar o idioma.\nSi prega di selezionare la lingua.\nLütfen dil seçin.\nकृपया एक भाषा चुनिए।",
        reply_markup=ReplyKeyboardMarkup(lang_buttons, one_time_keyboard=True, resize_keyboard=True)
    )
    return LANGUAGE

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['language'] = update.message.text
    country_buttons = [[KeyboardButton(c)] for c in COUNTRIES]
    await update.message.reply_text(
        "Please, select your country 🌐",
        reply_markup=ReplyKeyboardMarkup(country_buttons, one_time_keyboard=True, resize_keyboard=True)
    )
    return COUNTRY

async def set_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['country'] = update.message.text
    currency_buttons = [[KeyboardButton(c)] for c in CURRENCIES]
    await update.message.reply_text(
        "Choose your currency 💱",
        reply_markup=ReplyKeyboardMarkup(currency_buttons, one_time_keyboard=True, resize_keyboard=True)
    )
    return CURRENCY

async def set_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['currency'] = update.message.text
    user = update.effective_user
    await update.message.reply_text(
        f"Hi {user.first_name}! 👋 Welcome to Global360World bot. Here is what I can do:\n"
        "– Search for cheapest flights 🔎\n"
        "– Track tickets prices 👀\n"
        "– Notify about price changes 🔔\n"
        "Shall we start? 👇",
        reply_markup=MAIN_MENU_KEYBOARD
    )
    return MAIN_MENU

# --- Main Menu ---
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in ["🏠 Main Menu", "/start"]:
        await update.message.reply_text(
            "What would you like to do next?",
            reply_markup=MAIN_MENU_KEYBOARD
        )
        return MAIN_MENU
    elif text in ["🔎 Search Flights", "Search Flights"]:
        await update.message.reply_text(
            "Please select the type of search 👇",
            reply_markup=ReplyKeyboardMarkup([
                ["One Way", "Return"],
                ["Multi-city"]
            ], one_time_keyboard=True, resize_keyboard=True)
        )
        return FLIGHT_TYPE
    elif text in ["🏨 Search Hotels", "Search Hotels"]:
        await update.message.reply_text(
            "🏨 What's your hotel city? For example, Milan.",
            reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True, one_time_keyboard=True)
        )
        return HOTEL_CITY
    elif text == "❌ Cancel":
        await cancel(update, context)
        return ConversationHandler.END
    else:
        await update.message.reply_text("This feature is coming soon!", reply_markup=MAIN_MENU_KEYBOARD)
        return MAIN_MENU

# --- Flight Search Flow ---
async def flight_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if t == "One Way":
        context.user_data['flight_type'] = 'one_way'
        await update.message.reply_text("🏠 What's your departure city? For example, Milan.")
        return FLIGHT_ORIGIN
    elif t == "Return":
        context.user_data['flight_type'] = 'return'
        await update.message.reply_text("🏠 What's your departure city? For example, Milan.")
        return FLIGHT_ORIGIN
    else:
        await update.message.reply_text("Multi-city search coming soon!")
        return FLIGHT_TYPE

async def flight_origin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city_input = update.message.text.strip()
    airports = suggest_cities(city_input)
    if not airports:
        await update.message.reply_text("City not found. Please try again with a different name.")
        return FLIGHT_ORIGIN
    if len(airports) == 1:
        airport = airports[0]
        context.user_data['origin'] = airport['iata']
        await update.message.reply_text(f"Good choice! {airport['city']} ({airport['iata']}) selected.\n🛫 What's your destination? For example, Cologne.")
        return FLIGHT_DEST
    # Multiple matches, show as keyboard
    context.user_data['airport_options'] = airports
    options = [f"{a['city']} ({a['iata']})" for a in airports]
    keyboard = [[option] for option in options]
    await update.message.reply_text(
        "Please choose the city from the list 👇",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return FLIGHT_ORIGIN_CHOICE

async def flight_origin_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = update.message.text.strip()
    airports = context.user_data.get('airport_options', [])
    for a in airports:
        if user_choice == f"{a['city']} ({a['iata']})":
            context.user_data['origin'] = a['iata']
            await update.message.reply_text(f"Good choice! {a['city']} ({a['iata']}) selected.\n🛫 What's your destination? For example, Cologne.", reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True, one_time_keyboard=True))
            return FLIGHT_DEST
    await update.message.reply_text("Invalid choice. Please select a city from the keyboard.")
    return FLIGHT_ORIGIN_CHOICE

async def flight_dest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city_input = update.message.text.strip()
    airports = suggest_cities(city_input)
    if not airports:
        await update.message.reply_text("City not found. Please try again with a different name.")
        return FLIGHT_DEST
    if len(airports) == 1:
        airport = airports[0]
        context.user_data['destination'] = airport['iata']
        await update.message.reply_text('Good choice! Specify the date of departure (e.g.: "May 16", "20.06" or "April").')
        return FLIGHT_DEPART
    # Multiple matches, show as keyboard
    context.user_data['airport_options'] = airports
    options = [f"{a['city']} ({a['iata']})" for a in airports]
    keyboard = [[option] for option in options]
    await update.message.reply_text(
        "Please choose the city from the list 👇",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return FLIGHT_DEST_CHOICE

async def flight_dest_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = update.message.text.strip()
    airports = context.user_data.get('airport_options', [])
    for a in airports:
        if user_choice == f"{a['city']} ({a['iata']})":
            context.user_data['destination'] = a['iata']
            await update.message.reply_text('Good choice! Specify the date of departure (e.g.: "May 16", "20.06" or "April").', reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True, one_time_keyboard=True))
            return FLIGHT_DEPART
    await update.message.reply_text("Invalid choice. Please select a city from the keyboard.")
    return FLIGHT_DEST_CHOICE

async def flight_depart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    parsed_date = dateparser.parse(user_input, settings={'PREFER_DATES_FROM': 'future'})
    if not parsed_date:
        await update.message.reply_text("Sorry, I couldn't understand the date. Please try again (e.g.: \"May 16\" or \"20.06\").")
        return FLIGHT_DEPART
    departure_at = parsed_date.strftime('%Y-%m-%d')
    context.user_data['departure_at'] = departure_at
    if context.user_data.get('flight_type') == 'return':
        await update.message.reply_text('Great! Specify the date of return flight (e.g.: May 16 or 26.06).')
        return FLIGHT_RETURN
    else:
        await show_flight_results(update, context)
        return MAIN_MENU

async def flight_return(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    parsed_date = dateparser.parse(user_input, settings={'PREFER_DATES_FROM': 'future'})
    if not parsed_date:
        await update.message.reply_text("Sorry, I couldn't understand the date. Please try again (e.g.: May 16 or 26.06).")
        return FLIGHT_RETURN
    return_at = parsed_date.strftime('%Y-%m-%d')
    context.user_data['return_at'] = return_at
    await show_flight_results(update, context)
    return MAIN_MENU

async def show_flight_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    origin = context.user_data['origin']
    destination = context.user_data['destination']
    departure_at = context.user_data['departure_at']
    return_at = context.user_data.get('return_at')
    currency = context.user_data.get('currency', 'usd').lower()
    params = {
        "origin": origin,
        "destination": destination,
        "departure_at": departure_at,
        "currency": currency,
        "limit": 10,
        "one_way": "true" if not return_at else "false",
        "market": "us"
    }
    if return_at:
        params["return_at"] = return_at
    url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
    headers = {"X-Access-Token": API_TOKEN}
    r = requests.get(url, headers=headers, params=params)
    data = r.json()
    flights = data.get("data", [])
    if not flights:
        await update.message.reply_text("No flights found.")
        return

    # Show up to 5 flights with separator
    for idx, f in enumerate(flights[:5]):
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
            f"✈️ <b>Flight:</b> {origin} → {destination}\n"
            f"<b>Airline:</b> {airline} {flight_number}\n"
            f"<b>Departure:</b> {dep}\n"
            f"<b>Price:</b> {price} {currency.upper()}\n"
            f"<a href='{booking_link}'>Book Now</a>" if booking_link else ""
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        # Add separator except after the last card
        if idx < min(4, len(flights)-1):
            await update.message.reply_text("_______________________________")
    # Show nearby hotels
    await show_hotel_results(update, context, destination, departure_at)
    await update.message.reply_text("What would you like to do next?", reply_markup=MAIN_MENU_KEYBOARD)

# --- Hotel Search Flow ---
async def hotel_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city_input = update.message.text.strip()
    suggestions = suggest_cities(city_input)
    if not suggestions:
        await update.message.reply_text("City not found. Please try again with a different name.")
        return HOTEL_CITY
    if len(suggestions) == 1:
        city = suggestions[0]
        context.user_data['hotel_city'] = city['city']
        await update.message.reply_text("Enter check-in date (e.g.: May 16 or 20.06):")
        return HOTEL_CHECKIN
    context.user_data['hotel_options'] = suggestions
    options = [f"{a['city']} ({a['iata']})" for a in suggestions]
    keyboard = [[option] for option in options]
    await update.message.reply_text(
        "Please choose the city from the list 👇",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return HOTEL_CITY_CHOICE

async def hotel_city_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = update.message.text.strip()
    options = context.user_data.get('hotel_options', [])
    for a in options:
        if user_choice == f"{a['city']} ({a['iata']})":
            context.user_data['hotel_city'] = a['city']
            await update.message.reply_text("Enter check-in date (e.g.: May 16 or 20.06):", reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True, one_time_keyboard=True))
            return HOTEL_CHECKIN
    await update.message.reply_text("Invalid choice. Please select a city from the keyboard.")
    return HOTEL_CITY_CHOICE

async def hotel_checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    parsed_date = dateparser.parse(user_input, settings={'PREFER_DATES_FROM': 'future'})
    if not parsed_date:
        await update.message.reply_text("Sorry, I couldn't understand the date. Please try again (e.g.: May 16 or 20.06).")
        return HOTEL_CHECKIN
    check_in = parsed_date.strftime('%Y-%m-%d')
    context.user_data['hotel_checkin'] = check_in
    await update.message.reply_text("Enter check-out date (e.g.: May 18 or 22.06):")
    return HOTEL_CHECKOUT

async def hotel_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    parsed_date = dateparser.parse(user_input, settings={'PREFER_DATES_FROM': 'future'})
    if not parsed_date:
        await update.message.reply_text("Sorry, I couldn't understand the date. Please try again (e.g.: May 18 or 22.06).")
        return HOTEL_CHECKOUT
    check_out = parsed_date.strftime('%Y-%m-%d')
    context.user_data['hotel_checkout'] = check_out
    await show_hotel_results(update, context, context.user_data['hotel_city'], context.user_data['hotel_checkin'], check_out)
    return MAIN_MENU

async def show_hotel_results(update, context, city, check_in, check_out=None):
    url = "https://api.travelpayouts.com/v2/hotels/search"
    headers = {"X-Access-Token": API_TOKEN}
    params = {
        "location": city,
        "check_in": check_in,
        "currency": context.user_data.get('currency', 'usd').lower(),
        "adults": 2,
        "limit": 5
    }
    if check_out:
        params["check_out"] = check_out
    r = requests.get(url, headers=headers, params=params)
    data = r.json()
    hotels = data.get("results", [])
    if not hotels:
        await update.message.reply_text("No hotels found.")
        return
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
            f"🏨 <b>Hotel:</b> {name}\n"
            f"<b>Check-in:</b> {check_in}\n"
            f"<b>Check-out:</b> {check_out if check_out else '-'}\n"
            f"<b>Price:</b> {price} {context.user_data.get('currency', 'USD').upper()}\n"
            f"<a href='{url}'>Book Now</a>" if url else ""
        )
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    await update.message.reply_text("What would you like to do next?", reply_markup=MAIN_MENU_KEYBOARD)

# --- Cancel handler ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_language)],
            COUNTRY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_country)],
            CURRENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_currency)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            FLIGHT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_type)],
            FLIGHT_ORIGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_origin)],
            FLIGHT_ORIGIN_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_origin_choice)],
            FLIGHT_DEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_dest)],
            FLIGHT_DEST_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_dest_choice)],
            FLIGHT_DEPART: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_depart)],
            FLIGHT_RETURN: [MessageHandler(filters.TEXT & ~filters.COMMAND, flight_return)],
            HOTEL_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, hotel_city)],
            HOTEL_CITY_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, hotel_city_choice)],
            HOTEL_CHECKIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, hotel_checkin)],
            HOTEL_CHECKOUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, hotel_checkout)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)]
    )

    app.add_handler(conv_handler)
    app.run_polling() 