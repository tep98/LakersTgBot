import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from config import BOT_TOKEN
from api.nba_api import get_team_id, get_upcoming_games, format_game_basic, format_game_result, get_recent_games, format_team_roster, get_team_roster

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

TEAM_NAME = "Los Angeles Lakers"
DEFAULT_TEAM_ID = 14

count_of_previous_days = 30
count_of_previous_games = 5
count_of_upcoming_days = 30
count_of_upcoming_games = 5

print("bot started!")

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "🏀 Привет!\n\n"
        "Я бот для фанатов Los Angeles Lakers.\n"
        "Здесь будут матчи, результаты и состав команды.\n\n"
        "Доступные команды:\n"
        "/info — общая информация о команде\n"
        "/team — информация о составе команды\n"
        "/next_games — ближайшие 5 матчей команды\n"
        "/last_results — последние 5 сыгранных матчей\n"
        "/events — информация о близжайших событиях"
    )


@dp.message(Command(commands=["next_games"]))
async def next_games(message: types.Message):
    await fetch_and_format_games(message, get_upcoming_games, "Ближайшие матчи", format_game_basic, count_of_upcoming_days, count_of_upcoming_games)

@dp.message(Command(commands=["last_results"]))
async def last_results(message: types.Message):
    await fetch_and_format_games(message, get_recent_games, "Последние результаты", format_game_result, count_of_previous_days, count_of_previous_games)


async def fetch_and_format_games(message, get_games_func, header, format_func, count_of_days, count_of_games):
    team_id, team_error = await get_team_id(TEAM_NAME, DEFAULT_TEAM_ID)
    games, games_error = await get_games_func(team_id, count_of_days, count_of_games)

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
async def team(message: types.Message):
    team_name = "Los Angeles Lakers"
    players, coaches, error = await get_team_roster(team_name)

    if error:
        await message.answer(f"⚠️ Ошибка при получении состава: {error}")
        return

    text = f"🏀 Состав команды <b>{team_name}</b>:\n\n{format_team_roster(players, coaches)}"

    await message.answer(text, parse_mode="HTML")


@dp.message(Command(commands=["info"]))
async def info(message: types.Message):
    text = (
        "<b>🏀 Los Angeles Lakers</b>\n\n"
        "<b>Город:</b> Лос-Анджелес\n"
        "<b>Лига:</b> NBA\n"
        "<b>Текущий сезон:</b> 2024–2025\n"
        "<b>Конференция:</b> Западная\n"
        "<b>Дивизион:</b> Тихоокеанский\n"
        "<b>Основан:</b> 1946 год\n"
        "<b>Домашняя арена:</b> «Crypto\u200b.com Arena»\n"
        "<b>Участие:</b> NBA Regular Season\n\n"
        "<b>Los Angeles Lakers</b> — команда легенд: <i>Мэджик Джонсон</i>, <i>Карим Абдул-Джаббар</i>, <i>Коби Брайант</i>, <i>Шакил О’Нил</i> и <i>Леброн Джеймс</i> творили историю NBA, принося титулы и создавая эпохи. \nОдна из самых титулованных команд в истории NBA и одна из самых популярных команд в мире."
        
        "\n\n<i>/team - узнать подробнее о текущем составе команды</i>"
    )
    await message.answer(text, parse_mode="HTML")


@dp.message(Command(commands=["events"]))
async def events(message: types.Message):
    text = (
        "<b>🏟️ Источники с анонсами мероприятий Los Angeles Lakers:</b>\n\n"
        "📅 Расписание и официальные события:\n"
        "• Официальный сайт команды: nba.com/lakers\n"
        "• Расписание матчей: nba.com/lakers/schedule\n\n"
        "📣 Социальные сети:\n"
        "• Twitter: twitter.com/Lakers\n"
        "• Instagram: instagram.com/lakers\n"
        "• Facebook: facebook.com/Lakers\n\n"
        "<i>В этих источниках публикуются встречи фанатов, мероприятия и акции.</i>\n"
        "<i>/next_games - посмотреть близжайшие матчи</i>"
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)





async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
