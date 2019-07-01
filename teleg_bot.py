from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import aiogram.utils.markdown as md
from aiogram.types import ParseMode
import geocoder
import requests
import math


def is_this_place(place):
    g = geocoder.yandex(place)
    return g.ok


def get_coordinates(place):
    g = geocoder.yandex(place)
    return g.latlng


def taxi_how_much(place1, place2):
    g = get_coordinates(place1)
    lat1 = g[0]
    lon1 = g[1]
    g = get_coordinates(place2)
    lat2 = g[0]
    lon2 = g[1]
    url = f'https://taxi-routeinfo.taxi.yandex.net/taxi_info?rll={lon1},{lat1}~{lon2},{lat2}&clid=cosines-pi&apikey=db20c13720eb4597adca7031e10efba2'
    r = requests.get(url)
    return r.json()['options'][0]['price_text']


def degreesToRadians(degrees):
    return degrees * math.pi / 180


def distanceInKm(lat1, lon1, lat2, lon2):
    earthRadiusKm = 6371
    lat1=float(lat1)
    lat2=float(lat2)
    lon1=float(lon1)
    lon2=float(lon2)
    dLat = degreesToRadians(lat2 - lat1)
    dLon = degreesToRadians(lon2 - lon1)
    lat1 = degreesToRadians(lat1)
    lat2 = degreesToRadians(lat2)
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.sin(dLon/2) * math.sin(dLon/2) * math.cos(lat1) * math.cos(lat2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earthRadiusKm * c


class Form(StatesGroup):
    where_from = State()
    where_to = State()



storage = MemoryStorage()
bot = Bot(token="895447723:AAFfHZJi4XYLmx9P7hmaCw6qgX62sOJ7f2Q")
dp = Dispatcher(bot, storage=storage)

button_start = KeyboardButton('Заказать такси')

start = ReplyKeyboardMarkup()
start.add(button_start)


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await Form.where_from.set()
    await bot.send_message(message.from_user.id, "Откуда вы хотите добраться?", reply_markup=ReplyKeyboardRemove())


@dp.message_handler(lambda message: not is_this_place(message.text), state=Form.where_from)
async def failed_process_from(message: types.Message):
    return await message.reply("Мы не знаем такого метса :(\nТак откуда вы хотите добраться?")


@dp.message_handler(state=Form.where_from)
async def process_start_command_to(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['where_from'] = message.text

    await Form.next()
    await bot.send_message(message.from_user.id, "Куда вы хотите добраться?")


@dp.message_handler(lambda message: not is_this_place(message.text), state=Form.where_to)
async def failed_process_to(message: types.Message):
    return await message.reply("Мы не знаем такого метса :(\nТак куда вы хотите добраться?")


@dp.message_handler(state=Form.where_to)
async def process_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['where_to'] = message.text
        markup = ReplyKeyboardMarkup()
        markup.add(KeyboardButton('Верно'))
        markup.add(KeyboardButton('Не верно'))
        # And send message
        await bot.send_message(message.chat.id, md.text(
            md.text('Вы хотите добраться из: \n', md.bold(data['where_from'])),
            md.text('в:\n', md.bold(data['where_to'])),
            md.text('Верно?'),
            sep='\n'), parse_mode=ParseMode.MARKDOWN, reply_markup=markup)

        # Finish conversation
        data.state = None


@dp.message_handler()
async def echo_message(message: types.Message, state: FSMContext):
    if message.text == 'Верно':
        async with state.proxy() as data:
            taxi_price = taxi_how_much(data['where_from'],data['where_to'])
            markup = ReplyKeyboardMarkup()
            markup.add(KeyboardButton('Заново'))
            coords1 = get_coordinates(data['where_from'])
            lat1 = coords1[0]
            lon1 = coords1[1]
            coords2 = get_coordinates(data['where_to'])
            lat2 = coords2[0]
            lon2 = coords2[1]
            dist = distanceInKm(lat1, lon1, lat2, lon2)
            response = f"Цена на такси: {taxi_price}\nРасстояние для аэротакси: {dist} км"
            await bot.send_message(message.from_user.id, response , reply_markup=markup)
    if message.text == 'Не верно' or message.text == 'Заново':
        await bot.send_message(message.from_user.id, "Начинём заново")
        await process_start_command(message=message)


executor.start_polling(dp)

