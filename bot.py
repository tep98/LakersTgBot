import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from config import BOT_TOKEN
from api.nba_api import get_team_id, get_upcoming_games, format_game_basic, format_game_result, get_recent_games, format_team_roster, get_team_roster

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

TEAM_NAME = "Los Angeles Lakers"
DEFAULT_TEAM_ID = 14

print("bot started!")

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "🏀 Привет!\n\n"
        "Я бот для фанатов Los Angeles Lakers.\n"
        "Здесь будут матчи, результаты и состав команды.\n\n"
        "Доступные команды:\n"
        "/next_games — ближайшие 5 матчей команды\n"
        "/last_results — последние 5 сыгранных матчей\n"
        "/team — информация о составе команды\n"
    )


@dp.message(Command(commands=["next_games"]))
async def next_games(message: types.Message):
    await fetch_and_format_games(message, get_upcoming_games, "Ближайшие матчи", format_game_basic)

@dp.message(Command(commands=["last_results"]))
async def last_results(message: types.Message):
    await fetch_and_format_games(message, get_recent_games, "Последние результаты", format_game_result)


async def fetch_and_format_games(message, get_games_func, header, format_func):
    team_id, team_error = await get_team_id(TEAM_NAME, DEFAULT_TEAM_ID)
    games, games_error = await get_games_func(team_id)

    if team_error:
        await message.answer(f"⚠️ Внимание: {team_error}")
    if games_error:
        await message.answer(f"⚠️ Внимание: {games_error}")
    if not games:
        await message.answer("Нет матчей.")
        return

    text = f"🏀 {header} Los Angeles Lakers:\n\nH = Home (домашний матч), A = Away (гостевой матч)\n\n"
    text += "\n".join(format_func(g, team_id) for g in games)
    await message.answer(text)


@dp.message(Command(commands=["team"]))
async def team_info(message: types.Message):
    team_name = "Los Angeles Lakers"
    players, coaches, error = await get_team_roster(team_name)

    if error:
        await message.answer(f"⚠️ Ошибка при получении состава: {error}")
        return

    text = format_team_roster(players, coaches)
    await message.answer(text)



async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
