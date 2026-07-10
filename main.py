import os
import asyncio
from datetime import datetime
import logging
import gspread
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, types, html
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Импортируем инструменты для веб-сервера
from aiohttp import web

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class AppointmentStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_contact = State()
    waiting_for_time = State()
    waiting_for_comment = State()

def append_to_sheet(data: dict):
    gc = gspread.service_account(filename='credentials.json')
    sh = gc.open(GOOGLE_SHEET_NAME)
    worksheet = sh.get_worksheet(0)
    
    current_date = datetime.now().strftime("%d.%m.%Y %H:%M")
    row_to_insert = [
        current_date,
        data.get('name'),
        data.get('contact'),
        data.get('preferred_time'),
        data.get('comment'),
        "Новая"
    ]
    worksheet.append_row(row_to_insert)

# --- ВЕБ-СЕРВЕР ДЛЯ UPTIMEROBOT ---

async def handle_ping(request):
    """Хендлер, который отвечает UptimeRobot, что всё ок"""
    return web.Response(text="Bot is alive and running!", status=200)

async def start_web_server():
    """Запуск фонового веб-сервера на порту, который выдает Render"""
    app = web.Application()
    app.router.add_get('/', handle_ping) # При GET-запросе на главную страницу отдаем статус 200
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render автоматически передает номер порта в переменную окружения PORT. 
    # Если запускаем локально, по умолчанию будет порт 8080.
    port = int(os.getenv("PORT", 8080)) 
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f" Фоновый веб-сервер для UptimeRobot запущен на порту {port}")

# --- ХЕНДЛЕРЫ БОТА ---

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Приветствую! Как доктор может к вам обращаться? Введите ваше имя:")
    await state.set_state(AppointmentStates.waiting_for_name)

@dp.message(AppointmentStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Отлично! Теперь укажите ваш телефон:", reply_markup=kb)
    await state.set_state(AppointmentStates.waiting_for_contact)

@dp.message(AppointmentStates.waiting_for_contact)
async def process_contact(message: types.Message, state: FSMContext):
    contact_info = message.contact.phone_number if message.contact else message.text
    username = f" (@{message.from_user.username})" if message.from_user.username else ""
    await state.update_data(contact=f"{contact_info}{username}")
    await message.answer("В какой день и время вам было бы удобнее всего подойти к доктору?", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AppointmentStates.waiting_for_time)

@dp.message(AppointmentStates.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    await state.update_data(preferred_time=message.text)
    await message.answer("Опишите кратко, что вас беспокоит (или цель визита):")
    await state.set_state(AppointmentStates.waiting_for_comment)

@dp.message(AppointmentStates.waiting_for_comment)
async def process_comment(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    user_data = await state.get_data()
    
    admin_message = (
        f"🦷 <b>НОВАЯ ЗАЯВКА</b> 🦷\n\n"
        f"👤 <b>Пациент:</b> {html.quote(user_data['name'])}\n"
        f"📞 <b>Контакты:</b> {html.quote(user_data['contact'])}\n"
        f"📅 <b>Время:</b> {html.quote(user_data['preferred_time'])}\n"
        f"💬 <b>Жалоба:</b> {html.quote(user_data['comment'])}\n"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Ошибка отправки в ТГ админу: {e}")

    try:
        await asyncio.to_thread(append_to_sheet, user_data)
    except Exception as e:
        logging.error(f"Ошибка записи в Google Sheets: {e}")

    await message.answer(
        "✨ <b>Ваша заявка успешно принята!</b>\n\n"
        "Доктор или менеджер свяжутся с вами в ближайшее время. Будьте здоровы!",
        parse_mode="HTML"
    )
    await state.clear()

async def main():
    # 1. Сначала запускаем фоновый веб-сервер
    await start_web_server()
    
    # 2. Затем запускаем стандартный поллинг бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())