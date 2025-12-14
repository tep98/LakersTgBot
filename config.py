import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
NBA_API_KEY = os.getenv("NBA_API_KEY")
print(NBA_API_KEY)