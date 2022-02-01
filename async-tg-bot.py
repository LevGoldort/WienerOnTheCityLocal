import logging
import configparser
import os
import figureway.staticmethods as static
import boto3
import json

import aiogram.types
import aiogram.utils.markdown as md
from aiogram.types import ContentType
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ParseMode
from aiogram.utils import executor


logging.basicConfig(level=logging.INFO)

cfg = configparser.ConfigParser()
cfg.read(os.path.join(os.path.dirname(__file__), 'config.cfg'))

API_TOKEN = cfg.get('DEFAULT', 'tg_api_key')


bot = Bot(token=API_TOKEN)

# For example use simple MemoryStorage for Dispatcher.
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# States
class Form(StatesGroup):
    name = State()  # Will be represented in storage as 'Form:name'
    age = State()  # Will be represented in storage as 'Form:age'
    gender = State()  # Will be represented in storage as 'Form:gender'
    loc = State()
    rank = State()


@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    """
    Conversation's entry point
    """
    # Set state
    await Form.loc.set()

    await message.reply("Hello! It is great time to find some figureway! "
                        "Please, send me your location, and I will proceed further! "
                        "If you want to stop everything, write cancel, and everything will be cancelled!")


# You can use state '*' if you need to handle all states
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    """
    Allow user to cancel any action
    """
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Everything is cancelled, even the things you love most.',
                        reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Form.loc, content_types=ContentType.LOCATION)
async def get_location(message: types.Message, state: FSMContext):
    """
    Process user location
    """
    async with state.proxy() as data:
        data['location'] = message.location

    cfg = configparser.ConfigParser()
    cfg.read(os.path.join(os.path.dirname(__file__), 'config.cfg'))
    city_list_path = cfg.get('INPUT_PATH', 'city_list', fallback='Wrong Config file')
    amazon_access_key_id = cfg.get('DEFAULT', 'aws_access_key_id')
    amazon_secret_key = cfg.get('DEFAULT', 'aws_secret_access_key')
    amazon_bucket_name = cfg.get('DEFAULT', 'aws_s3_bucket')
    city_list = static.load_city_list(city_list_path)

    closest_city = static.find_closest_city(message.location.latitude, message.location.longitude, city_list)

    if not closest_city:
        await Form.next()
        await message.reply('''The bot works only at cities, looks, 
                                        you are not near one. Come back from the city!''')
        return

    await message.reply('Trying to find a route near you in {}, '
                        'can take a minute, stay tuned!'.format(closest_city['name']))

    city_filepath = '/Static/' \
                    + closest_city['country'] \
                    + '/' \
                    + closest_city['lat'] \
                    + closest_city['lng'] \
                    + '.pickle'

    payload = {'city_lat': closest_city['lat'],
               'city_lon': closest_city['lng'],
               'user_lat': message.location.latitude,
               'user_lon': message.location.longitude,
               'country': closest_city['country'],
               'bucket': amazon_bucket_name}

    headers = {'content-type': 'application/json'}

    client = boto3.client('lambda')

    response = client.invoke(FunctionName='find_figure_way',
                             InvocationType='RequestResponse',
                             Payload=json.dumps(payload))

    way = response['Payload'].read().decode('UTF-8').replace("'", "\"")[1:-1]
    way2 = json.loads(way)['route']  # Parse the response

    await message.reply('Wow you are at {} {}'.format(type(way2), way2))


# Check age. Age gotta be digit
@dp.message_handler(lambda message: not message.location, state=Form.loc)
async def process_location_invalid(message: types.Message):
    """
    If age is invalid
    """
    return await message.reply("You should send location, please, send location!")


@dp.message_handler(lambda message: message.text.isdigit(), state=Form.age)
async def process_rank(message: types.Message, state: FSMContext):
    # Update state and data
    await Form.next()
    await state.update_data(age=int(message.text))

    # Configure ReplyKeyboardMarkup
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Male", "Female")
    markup.add("Other")

    await message.reply("What is your gender?", reply_markup=markup)


@dp.message_handler(lambda message: message.text not in ["Male", "Female", "Other"], state=Form.gender)
async def process_gender_invalid(message: types.Message):
    """
    In this example gender has to be one of: Male, Female, Other.
    """
    return await message.reply("Bad gender name. Choose your gender from the keyboard.")


@dp.message_handler(state=Form.gender)
async def process_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['gender'] = message.text

        # Remove keyboard
        markup = types.ReplyKeyboardRemove()

        # And send message
        await bot.send_message(
            message.chat.id,
            md.text(
                md.text('Hi! Nice to meet you,', md.bold(data['name'])),
                md.text('Age:', md.code(data['age'])),
                md.text('Gender:', data['gender']),
                sep='\n',
            ),
            reply_markup=markup,
            parse_mode=ParseMode.MARKDOWN,
        )

    # Finish conversation
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)