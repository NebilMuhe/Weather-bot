from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
import os
import requests
import datetime as dt
import logging
from dotenv import load_dotenv

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.environ["TOKEN"]
API_KEY = os.environ["API_KEY"]

START_ROUTES, END_ROUTES, WEATHER_ROUTE = range(3)
ONE, TWO = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = """
    Hello {name}
🌦️ Welcome to the WeatherBot! 🌦️

I'm here to provide you with up-to-date weather information for any city in the world. 
Just type the name of the city you're interested in, and I will fetch the latest weather data for you.

Here are some commands you can use:

- /weather [city]: Get the current weather conditions for a specific city.
- /help: Display a list of available commands and how to use them.
- /start: Start a new conversation with me.
- Use Start button specified below and type the name of the city.

Feel free to ask me about the weather anytime! Just type /weather followed by the city name (e.g., /weather New York).

Stay informed and stay dry! ☔️"""

    name = update.effective_user.full_name
    keyboard = [
        [InlineKeyboardButton("Start", callback_data=str(ONE))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(update.effective_user.id, text=welcome_message.format(name=name), reply_markup=reply_markup)
    return START_ROUTES


async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    welcome_message = """
    Hello {name}
🌦️ Welcome to the WeatherBot! 🌦️

I'm here to provide you with up-to-date weather information for any city in the world. 
Just type the name of the city you're interested in, and I will fetch the latest weather data for you.

Here are some commands you can use:

- /weather [city]: Get the current weather conditions for a specific city.
- /help: Display a list of available commands and how to use them.
- /start: Start a new conversation with me.
- Use Start button specified below and type the name of the city.

Feel free to ask me about the weather anytime! Just type /weather followed by the city name (e.g., /weather New York).

Stay informed and stay dry! ☔️"""

    name = update.effective_user.full_name
    keyboard = [
        [InlineKeyboardButton("Start", callback_data=str(ONE))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    await query.edit_message_text(text=welcome_message.format(name=name), reply_markup=reply_markup)


def kelvin_to_celsius_fahrenit(kelvin):
    celsius = kelvin - 273.15
    fahrenit = celsius*(9/5) + 32
    return celsius, fahrenit


async def user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Please type the name of the city")
    return WEATHER_ROUTE


def weather_condition(city):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric'

    response = requests.get(url).json()

    if response["cod"] == '404' or city.lower() == 'start' or city.lower() == 'stop':
        return False
    temp = response["main"]["temp"]
    temp_celsius, temp_fahrenit = kelvin_to_celsius_fahrenit(temp)
    humidity = response["main"]["humidity"]
    wind_speed = response['wind']['speed']
    description = response['weather'][0]['description']
    sun_rise = dt.datetime.utcfromtimestamp(
        response['sys']['sunrise'] + response['timezone'])
    sun_set = dt.datetime.utcfromtimestamp(
        response['sys']['sunset'] + response['timezone'])
    country = response["sys"]["country"]

    result = f"""{city.upper()}, {country}

🌡️ Temprature in {city}:{temp_celsius:.2f}°C or {temp_fahrenit:.2f}°F

💧 Humidity in {city}: {humidity}%

💨 Wind Speed in {city}: {wind_speed}m/s

🌥️ General Weather in {city}: {description}

🌅 Sun rise in {city} AT:  {sun_rise}

🌇 Sun set in {city} AT:  {sun_set}
"""
    return result


async def weather_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        city = ' '.join(context.args)
    else:
        city = update.message.text

    response = weather_condition(city)

    if not response:
        keys = [
            [InlineKeyboardButton("Start", callback_data="start")]
        ]
        reply = InlineKeyboardMarkup(keys)
        await update.message.reply_text("This City does not exist or type properly. \n To try again please use the start button.", reply_markup=reply)
        return START_ROUTES

    keyboard = [
        [
            InlineKeyboardButton("Continue", callback_data="continue"),
        ],
        [
            InlineKeyboardButton("Done", callback_data="done"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    print(response)
    await update.message.reply_text(text=response, reply_markup=reply_markup)

    return END_ROUTES


async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = ' '.join(context.args)
    print(city)

    response = weather_condition(city)

    if not response:
        await update.message.reply_text("This City Does not exist")
        return ConversationHandler.END

    keyboard = [
        [
            InlineKeyboardButton("Continue", callback_data="continue"),
        ],
        [
            InlineKeyboardButton("Done", callback_data="done"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    print(response)
    await update.message.reply_text(text=response, reply_markup=reply_markup)

    return END_ROUTES


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Thank you for using this bot.")
    return ConversationHandler.END


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help = """
- `/start`: Start a new conversation with me.
- `/weather [city]`: Get the current weather conditions for a specific city.
- `/help`: Display this help message.
        """
    await context.bot.send_message(update.effective_chat.id, text=help)


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler(
            "start", start)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(
                    user_input, pattern=str(ONE)),
                CallbackQueryHandler(user_input, pattern="continue"),
                CallbackQueryHandler(start_over, pattern="start"),
                CommandHandler("weather", weather_details),
            ],
            WEATHER_ROUTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND,
                               weather_details)
            ],
            END_ROUTES: [
                CallbackQueryHandler(end, pattern="done"),
                CallbackQueryHandler(user_input, pattern="continue"),
                # CallbackQueryHandler(start_over, pattern="^" + str(ONE) + "$"),
                # CallbackQueryHandler(end, pattern="^" + str(TWO) + "$"),
            ],
        },
        fallbacks=[MessageHandler(
            filters.TEXT & ~filters.COMMAND, start), CommandHandler("start", start), CommandHandler("help", help)],
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()
