from aiogram import executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Dispatcher
from aiogram.types import Message
from aiogram.types import ChatType, InputMediaPhoto
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.exceptions import MessageToDeleteNotFound, Throttled
import random
import asyncio
import requests
import json

import config


from loader import bot, dp
from keyboards import reply as reply
from keyboards import inl as inl
from data import sql as databs

from state import states
from config import link_channel

import sqlite3
db = sqlite3.connect('db.db', check_same_thread=False)
sql = db.cursor()


async def add_track(m: Message):
    await m.reply('Куда добавить этот трек?', reply_markup=await inl.add_file())

async def get_track(m: Message):
    await databs.check_user(m)
    pas = m.get_args()
    id = sql.execute('SELECT * FROM files WHERE link = ?;', (pas,)).fetchone()
    if id is None:
        await m.answer('❌ Файл не найден')
        return
    await databs.add_count(pas)
    if id[5] == 'single':
        await m.answer_audio(id[1], caption=f'<a href="{link_channel}"></a>', parse_mode='HTML')
    elif id[5] == 'album':
        if id[1] == None:
            await m.answer('В этом альбоме нет ни одного трека')
            return
        await m.answer(f'Начинаю выгрузку альбома <b>{id[3]} - {id[2]}</b>', parse_mode='HTML')
        all = id[1]
        for i in all.split(',')[:-1]:
            await m.answer_audio(i, caption=f'<a href="{link_channel}"></a>', parse_mode='HTML')
        await m.answer('Альбом выгружен')
    if m.from_user.id in config.admins:
        count = sql.execute('SELECT * FROM files WHERE link = ?;', (pas,)).fetchone()[4]
        await m.answer(f'Статистика: {count}')

async def adm(m):
    await m.answer('Админ панель', reply_markup=inl.adm)

async def change_link_channel(m, state):
    await state.finish()
    global link_channel
    link_channel = m.text
    await m.answer('Успешно!')

async def mailing(m, state):
    await m.answer(m.text, reply_markup=inl.mail)
    await state.finish()

async def newAlbum_title(m, state):
    await state.finish()
    await state.update_data(title=m.text)
    await m.answer('Теперь артиста(-ов)')
    await states.newAlbum.artist.set()

async def newAlbum_artist(m, state):
    data = await state.get_data()
    await state.finish()
    chars = 'abcdefghyjklmnopqrstuvwxyz'
    chars += chars.upper()
    chars += '1234567890'
    pas = ''.join(random.sample(chars, 6))
    sql.execute('INSERT INTO files (link, id, title, artist, count, type) VALUES (?, ?, ?, ?, ?, ?);',(pas, None, data['title'], m.text, 0, 'album',))
    db.commit()
    await m.answer(f'Добавлено\nLink: https://t.me/{config.username_bot}?start={pas}')

async def editFile_link(m, state):
    if '=' in m.text:
        link = m.text.split('=')[1]
    else:
        link = m.text
    if sql.execute('SELECT * FROM files WHERE link = ?;', (link,)).fetchone() is None:
        await m.answer('Не найдено, повторите попытку', reply_markup=inl.cancel)
        return
    if sql.execute('SELECT * FROM files WHERE link = ?;', (link,)).fetchone()[5] != 'single':
        await m.answer('Это не сингл', reply_markup=inl.cancel)
        return
    await state.update_data(link=link)
    await m.answer('Теперь отправь мне новый файл', reply_markup=inl.cancel)
    await states.editFile.file.set()

async def editFile_file(m, state):
    link = await state.get_data()
    await state.finish()
    link = link['link']
    sql.execute('UPDATE files SET id = ? WHERE link = ?', (m.audio.file_id, link,))
    db.commit()
    await m.answer(f'Успешно изменено!\n\nhttps://t.me/{config.username_bot}?start={link}')

def startup(dp: Dispatcher):
    dp.register_message_handler(add_track, content_types=['audio'], chat_type=[ChatType.PRIVATE], is_admin=True)
    dp.register_message_handler(adm, commands=['adm'], chat_type=[ChatType.PRIVATE], is_admin=True)
    dp.register_message_handler(get_track, commands=['start'], chat_type=[ChatType.PRIVATE])

    dp.register_message_handler(change_link_channel, state=states.link.link, is_admin=True)
    dp.register_message_handler(mailing, state=states.mailing.text, is_admin=True)
    dp.register_message_handler(newAlbum_title, state=states.newAlbum.title, is_admin=True)
    dp.register_message_handler(newAlbum_artist, state=states.newAlbum.artist, is_admin=True)
    dp.register_message_handler(editFile_link, state=states.editFile.link, is_admin=True)
    dp.register_message_handler(editFile_file, content_types='audio', state=states.editFile.file, is_admin=True)