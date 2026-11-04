import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Payment settings
# Для Telegram Payments Provider Token
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")

# Для CryptoBot API
CRYPTOBOT_API_TOKEN = os.getenv("CRYPTOBOT_API_TOKEN", "")
CRYPTOBOT_SHOP_ID = os.getenv("CRYPTOBOT_SHOP_ID", "")

# Для ЮMoney
YOOMONEY_WALLET = os.getenv("YOOMONEY_WALLET", "")
YOOMONEY_API_KEY = os.getenv("YOOMONEY_API_KEY", "")

# DB settings
DATABASE_PATH = "bot_database.db"

# Categories/Tariffs (ID, name, price in RUB)
CATEGORIES = {
    "1day": {"name": "1 день", "price": 100},
    "7days": {"name": "7 дней", "price": 500},
    "30days": {"name": "30 дней", "price": 1500},
}

# Download link for SKTrade
SKTRADE_DOWNLOAD_LINK = "https://example.com/sktrade-download"

# Support contact
SUPPORT_USERNAME = "@support_user"
