#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""
"""

import logging
import figureway.wiener as wiener
import figureway.staticmethods as static
import os
import configparser
import boto3
import botocore
import pickle

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


class wienerTgBot:

    def __init__(self):

        cfg = configparser.ConfigParser()
        cfg.read(os.path.join(os.path.dirname(__file__), 'config.cfg'))
        city_list_path = cfg.get('INPUT_PATH', 'city_list', fallback='Wrong Config file')

        self.amazon_access_key_id = cfg.get('DEFAULT', 'aws_access_key_id')
        self.amazon_secret_key = cfg.get('DEFAULT', 'aws_secret_access_key')
        self.amazon_bucket_name = cfg.get('DEFAULT', 'aws_s3_bucket')

        city_list = static.load_city_list(city_list_path)

        # Create the Updater and pass it your bot's token.
        tg_api_key = cfg.get('DEFAULT', 'tg_api_key')
        updater = Updater(tg_api_key)

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

        cfg = configparser.ConfigParser()
        cfg.read(os.path.join(os.path.dirname(__file__), 'config.cfg'))
        city_list_path = cfg.get('INPUT_PATH', 'city_list', fallback='Wrong Config file')

        amazon_access_key_id = cfg.get('DEFAULT', 'aws_access_key_id')
        amazon_secret_key = cfg.get('DEFAULT', 'aws_secret_access_key')
        amazon_bucket_name = cfg.get('DEFAULT', 'aws_s3_bucket')

        city_list = static.load_city_list(city_list_path)
        closest_city = static.find_closest_city(user_location.latitude, user_location.longitude, city_list)
        if not closest_city:
            update.message.reply_text('The bot works only at cities, looks, you are not near one. Come back from the city!')
            return ConversationHandler.END

        city_filepath = '/Static/' + closest_city['country'] + '/' + closest_city['lat'] + closest_city['lng'] +'.pickle'

        session = boto3.Session(aws_access_key_id=amazon_access_key_id, aws_secret_access_key=amazon_secret_key)
        s3 = session.resource('s3')

        try:
            obj = s3.Object(amazon_bucket_name, city_filepath)
            obj.load()

        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                update.message.reply_text(
                    'Apparently, you are in {}, we are not working in this city yet, but we will! Try again later'.format(
                        closest_city['name']))
                return ConversationHandler.END
            else:
                update.message.reply_text(
                    'Apparently, you are in {}, But something gone wrong, we will fix it!'.format(
                        closest_city['name']))
                return ConversationHandler.END
        else:
            crossroads_pickle = obj.get()['Body'].read()
            crossroads = pickle.loads(crossroads_pickle)

        #
        #
        #
        # if not os.path.isfile(city_filepath):
        #     update.message.reply_text('Apparently, you are in {}, we are not working in this city yet, but we will! Try again later'.format(closest_city['name']))
        #     return ConversationHandler.END
        # else:
        #     crossroads = static.load_crossroads(city_filepath)

        cl = wiener.FigureWayFinder(penis_dict, 2000, 0.5, 45, crossroads)
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


def main2() -> None:
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


def main():
    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(os.path.dirname(__file__), 'config.cfg'))
    city_list_path = cfg.get('INPUT_PATH', 'city_list', fallback='Wrong Config file')

    destination_type = cfg.get('OUTPUT_PATH', 'destination_type', fallback='Wrong Config file')
    destination_path = cfg.get('OUTPUT_PATH', 'destination_path', fallback='Wrong Config file')

    amazon_access_key_id = cfg.get('DEFAULT', 'aws_access_key_id')
    amazon_secret_key = cfg.get('DEFAULT', 'aws_secret_access_key')
    amazon_bucket_name = cfg.get('DEFAULT', 'aws_s3_bucket')



if __name__ == '__main__':
    main2()
