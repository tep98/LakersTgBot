import httpx
from datetime import date, timedelta, datetime
from config import NBA_API_KEY
from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import commonteamroster
import asyncio

BASE_URL = "https://api.balldontlie.io/v1"
HEADERS = {"Authorization": NBA_API_KEY}

# Кэш ID команд и матчей
_TEAM_ID_CACHE = {}
_GAMES_CACHE = {}


async def get_team_id(team_full_name: str, default_id=None):
    """Получаем ID команды по имени с fallback на default_id"""
    if team_full_name in _TEAM_ID_CACHE:
        return _TEAM_ID_CACHE[team_full_name], None

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{BASE_URL}/teams", headers=HEADERS)

        if response.status_code != 200:
            raise Exception(f"Bad status {response.status_code}")

        teams = response.json().get("data", [])
        for team in teams:
            if team["full_name"].lower() == team_full_name.lower():
                _TEAM_ID_CACHE[team_full_name] = team["id"]
                return team["id"], None

    except Exception as e:
        error_msg = f"Failed to fetch team id for {team_full_name}: {e}"
        print(error_msg)

    # fallback на default
    _TEAM_ID_CACHE[team_full_name] = default_id
    return default_id, f"Используется дефолтный ID команды. {error_msg if 'error_msg' in locals() else ''}"


async def get_upcoming_games(team_id, days_ahead=30, limit=5):
    """Получаем ближайшие матчи команды с кэшированием"""
    cache_key = f"upcoming_{team_id}"
    now = datetime.now()

    # проверка кэша (5 минут)
    if cache_key in _GAMES_CACHE:
        data, timestamp = _GAMES_CACHE[cache_key]
        if (now - timestamp).total_seconds() < 300:
            return data, None

    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    params = {
        "team_ids[]": team_id,
        "start_date": today.isoformat(),
        "end_date": end_date.isoformat(),
        "per_page": limit
    }

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{BASE_URL}/games", headers=HEADERS, params=params)

        if response.status_code != 200:
            return [], f"NBA API error: {response.text}"

        data = response.json().get("data", [])
        _GAMES_CACHE[cache_key] = (data, now)
        return data, None

    except Exception as e:
        return [], f"Error fetching upcoming games: {e}"


async def get_recent_games(team_id, days_back=30, limit=5):
    """Получаем последние сыгранные матчи с кэшированием"""
    cache_key = f"recent_{team_id}"
    now = datetime.now()

    if cache_key in _GAMES_CACHE:
        data, timestamp = _GAMES_CACHE[cache_key]
        if (now - timestamp).total_seconds() < 300:
            return data, None

    today = date.today()
    start_date = today - timedelta(days=days_back)

    params = {
        "team_ids[]": team_id,
        "start_date": start_date.isoformat(),
        "end_date": today.isoformat(),
        "per_page": limit
    }

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{BASE_URL}/games", headers=HEADERS, params=params)

        if response.status_code != 200:
            return [], f"NBA API error: {response.text}"

        data = response.json().get("data", [])
        _GAMES_CACHE[cache_key] = (data, now)
        return data, None

    except Exception as e:
        return [], f"Error fetching recent games: {e}"



def format_game_basic(game, team_id):
    # Определяем домашний или гостевой матч
    is_home = game["home_team"]["id"] == team_id

    # Соперник
    opponent = game["visitor_team"]["full_name"] if is_home else game["home_team"]["full_name"]

    # Дата без времени, буквенный месяц
    game_date = datetime.fromisoformat(game["date"])
    now = datetime.now()
    if game_date.year == now.year:
        date_str = game_date.strftime("%b %d")  # Nov 14
    else:
        date_str = game_date.strftime("%b %d %Y")  # Nov 14 2025

    # Компактная строка
    location = "H" if is_home else "A"  # H = Home, A = Away
    return f"{date_str} | {location} | vs {opponent}"


def format_game_result(game, team_id):
    # Определяем домашний или гостевой матч
    is_home = game["home_team"]["id"] == team_id

    # Счёт команды и соперника
    team_score = game["home_team_score"] if is_home else game["visitor_team_score"]
    opponent_score = game["visitor_team_score"] if is_home else game["home_team_score"]

    # Результат
    result = "Win" if team_score > opponent_score else "Lose"

    # Соперник
    opponent = game["visitor_team"]["full_name"] if is_home else game["home_team"]["full_name"]

    # Дата без времени
    game_date = datetime.fromisoformat(game["date"])
    now = datetime.now()

    # Форматируем дату: буквенный месяц, если год совпадает с текущим — не пишем год
    if game_date.year == now.year:
        date_str = game_date.strftime("%b %d")  # Nov 14
    else:
        date_str = game_date.strftime("%b %d %Y")  # Nov 14 2025

    # Компактная строка
    location = "H" if is_home else "A"  # H = Home, A = Away
    return f"{date_str} | {location} | {result} {team_score}-{opponent_score} vs {opponent}"

async def get_team_roster(team_name: str):
    try:
        team_info = [t for t in teams.get_teams() if t['full_name'] == team_name]
        if not team_info:
            return [], [], f"Команда {team_name} не найдена"

        team_id = team_info[0]['id']
        roster_data = await asyncio.to_thread(lambda: commonteamroster.CommonTeamRoster(team_id=team_id).get_dict())
        roster_list = roster_data['resultSets'][0]['rowSet']  # Игроки
        coaches_list = roster_data['resultSets'][1]['rowSet']  # Тренеры

        players_list = [format_player(p) for p in roster_list]

        # c = ['TEAM_ID', 'SEASON', 'COACH_ID', 'FIRST_NAME', 'LAST_NAME', 'COACH_NAME', 'IS_ASSISTANT', 'COACH_TYPE', 'SORT_SEQUENCE']
        coaches_list_formatted = [f"{c[5]} - {c[7]}" for c in coaches_list] # Имя Фамилия - роль

        return players_list, coaches_list_formatted, None

    except Exception as e:
        return [], [], f"Ошибка при получении данных: {e}"


def format_team_roster(players, coaches):
    """
    Формирует компактный текст для бота с игроками и тренерами
    """
    text = "🏀 Состав команды:\n\n"
    if players:
        text += "Игроки:\n" + "\n".join(players) + "\n\n"
    else:
        text += "Игроки: нет данных\n\n"

    if coaches:
        text += "Тренерский штаб:\n" + "\n".join(coaches)
    else:
        text += "Тренерский штаб: нет данных"

    return text


def format_player(p):
    # [TeamID, Season, LeagueID, PLAYER_NAME, FirstName, LastName, Jersey, Position, Height, Weight, DOB, Age, Exp, School, PlayerID, Notes]
    name = p[3]
    jersey = p[6]
    position = p[7]
    height = convert_height_to_meters(p[8])
    weight = convert_weight_to_kg(p[9])
    age = int(p[11]) if p[11] else "N/A"
    return f"{name} | #{jersey} | {position} | {height}, {weight} | {age} лет"

def convert_height_to_meters(height_str):
    try:
        feet, inches = map(int, height_str.split('-'))
        return f"{(feet*0.3048 + inches*0.0254):.2f} м"
    except Exception:
        return height_str

def convert_weight_to_kg(weight_lbs):
    try:
        return f"{int(weight_lbs)*0.453592:.0f} кг"
    except Exception:
        return weight_lbs
