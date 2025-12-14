import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from config import BOT_TOKEN

bot = Bot(token = BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
          "🏀 Привет!\n\n"
        "Я бот для фанатов Los Angeles Lakers.\n"
        "Здесь будут матчи, результаты и состав команды."
    )

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())