#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import figureway.wiener as wiener
import figureway.static_methods as static
import os

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

GENDER, PHOTO, LOCATION, BIO = range(4)
LOC = 0
tel_aviv_osm = "/Users/levgoldort/Downloads/planet_34.683,31.975_34.986,32.166.osm.pbf"
ams_osm='/Users/levgoldort/Downloads/planet_4.89,52.282_5.124,52.388.osm.pbf'
penis_dict = [{"direction": -1, "length": 1},
              {"direction": 1, "length": 1},
              {"direction": 1, "length": 1},
              {"direction": -1, "length": 2},
              {"direction": 1, "length": 1},
              {"direction": 1, "length": 2},
              {"direction": -1, "length": 1},
              {"direction": 1, "length": 1},
              {"direction": 1, "length": 1}
              ]


def start(update: Update, context: CallbackContext) -> int:
    """Starts the conversation and asks the user about their gender."""
    reply_keyboard = [['RU', 'EN', 'NL']]

    update.message.reply_text(
        'Hello, time to build some figure way! '
        'Send /cancel to stop talking to me.\n\n'
        'Please, send your location to proceed. ',
    )

    return LOC


def loc(update: Update, context: CallbackContext) -> int:
    """Stores the location and asks for some info about the user."""
    user = update.message.from_user
    user_location = update.message.location
    print("Start Location for %s: %f / %f", user.first_name, user_location.latitude, user_location.longitude)
    logger.info(
        "Start Location for %s: %f / %f", user.first_name, user_location.latitude, user_location.longitude
    )

    city_list = static.load_city_list('./figureway/Static_data/cities.json')
    closest_city = static.find_closest_city(user_location.latitude, user_location.longitude, city_list)
    print(closest_city)
    if not closest_city:
        update.message.reply_text('The bot works only at cities, looks, you are not near one. Come back from the city!')
        return ConversationHandler.END

    city_filepath = './figureway/Static_data/City_data/'+closest_city['name']+'.pickle'
    print(city_filepath)

    if not os.path.isfile(city_filepath):
        update.message.reply_text('Apparently, you are in {}, we are not working in this city yet, but we will! Try again later'.format(closest_city['name']))
        return ConversationHandler.END
    else:
        crossroads = static.load_crossroads(city_filepath)

    cl = wiener.FigureWayFinder(penis_dict, 1000, 0.5, 45, crossroads)
    cl.find_figure_way(user_location.latitude, user_location.longitude)

    if cl.ways_found:
        update.message.reply_text(
            'Is this way looks like what you wanted?')
        update.message.reply_text(cl.ways_found[0])
    else:
        update.message.reply_text(
            'Unfortunately, there are no such way around you, try to sin less, and god will love you more.'
        )

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("2010752312:AAGXT9jJbpDYwCFwKMnEdtiLUV2wBQADGAM")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LOC: [
                MessageHandler(Filters.location, loc),
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


def temp():


if __name__ == '__main__':
    main()
