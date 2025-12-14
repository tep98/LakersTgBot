import httpx
from datetime import date, timedelta, datetime

from config import NBA_API_KEY

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
