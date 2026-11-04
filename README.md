# SKTrade Telegram Bot

Telegram-бот для автоматической продажи ключей программы SKTrade с ручным пополнением баланса ключей администратором.

## 📁 Структура проекта

```
SKTradeBOT/
├── bot.py              # Основной код бота
├── database.py         # Работа с SQLite базой данных
├── config.py           # Конфигурация бота
├── requirements.txt    # Зависимости Python
├── .env.example        # Пример файла с переменными окружения
├── .env                # Ваш файл с секретами (создается локально)
└── README.md           # Этот файл
```

## 🚀 Локальный запуск

### 1. Установка зависимостей

Убедитесь, что у вас установлен Python 3.9 или выше.

```bash
# Клонируйте или скачайте проект
cd SKTradeBOT

# Создайте виртуальное окружение
python -m venv venv

# Активируйте виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните его:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Откройте `.env` файл и заполните:

- `BOT_TOKEN` — токен вашего бота (получить у @BotFather)
- `ADMIN_ID` — ваш Telegram ID (узнать у @userinfobot)
- `PAYMENT_PROVIDER_TOKEN` — токен для Telegram Payments (опционально)

### 3. Получение BOT_TOKEN

1. Откройте Telegram и найдите @BotFather
2. Отправьте `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен в `.env`

### 4. Получение ADMIN_ID

1. Откройте Telegram и найдите @userinfobot
2. Отправьте боту любое сообщение
3. Он пришлет ваш ID, скопируйте его в `.env`

### 5. Настройка Telegram Payments (опционально)

Если хотите использовать встроенные платежи Telegram:

1. Напишите @BotFather
2. Отправьте `/payments`
3. Выберите "New Payment"
4. Следуйте инструкциям для подключения платежного провайдера
5. Полученный токен добавьте в `.env` как `PAYMENT_PROVIDER_TOKEN`

**Важно:** Для работы Telegram Payments бот должен быть опубликован (не может работать в приватном режиме).

### 6. Запуск бота

```bash
python bot.py
```

Бот запустится и начнет отвечать на сообщения.

## 📊 Использование бота

### Для пользователя

- `/start` — Главное меню
- 🛒 Купить ключ — Выбор категории и покупка
- 📦 Наличие товара — Проверка доступности ключей
- 👤 Мой профиль — Просмотр купленных ключей
- 📥 Скачать SKTrade — Ссылка на скачивание программы
- 💬 Поддержка — Контакты поддержки

### Для администратора

- `/admin` — Панель администратора
- ➕ Добавить ключи — Добавление новых ключей в базу
- 📊 Статистика — Просмотр статистики продаж

## 🌐 Деплой на Render.com (бесплатно)

### 1. Подготовка к деплою

1. Загрузите проект на GitHub
2. Убедитесь, что `.env` НЕ загружен в Git (добавлен в `.gitignore`)

### 2. Создание .gitignore

Создайте файл `.gitignore` в корне проекта:

```
venv/
.env
bot_database.db
__pycache__/
*.pyc
```

### 3. Деплой на Render

1. Зарегистрируйтесь на [render.com](https://render.com)
2. Нажмите "New +" -> "Web Service"
3. Подключите ваш GitHub репозиторий
4. Настройки:

   - **Name**: sktrade-bot
   - **Region**: любой (например, Frankfurt)
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`

5. Добавьте переменные окружения (Environment Variables):

   - `BOT_TOKEN` — ваш токен бота
   - `ADMIN_ID` — ваш Telegram ID
   - `PAYMENT_PROVIDER_TOKEN` — (если используется)

6. Нажмите "Create Web Service"

### 4. Настройка базы данных

Render использует файловую систему только для чтения, поэтому SQLite не будет работать после перезапуска. Для продакшена лучше использовать PostgreSQL:

```python
# Замените в database.py sqlite3 на psycopg2
# Добавьте в requirements.txt: psycopg2-binary==2.9.9
```

Затем добавьте в Render PostgreSQL Database:
1. New + -> PostgreSQL
2. Создайте базу данных
3. Добавьте переменную `DATABASE_URL` в настройки Web Service

## 🌐 Деплой на Koyeb (бесплатно)

### 1. Подготовка

1. Зарегистрируйтесь на [koyeb.com](https://koyeb.com)
2. Установите Koyeb CLI (опционально)

### 2. Деплой через Git

1. Создайте файл `Procfile` в корне проекта:

```
web: python bot.py
```

2. Загрузите проект на GitHub
3. В Koyeb: Deploy -> Git
4. Выберите ваш репозиторий
5. Настройки:

   - **Name**: sktrade-bot
   - **Region**: любой
   - **Build**: Docker или Buildpack
   - **Command**: `python bot.py`

6. Добавьте переменные окружения (Environment Variables)

7. Нажмите "Deploy"

## 🔧 Дополнительная настройка

### Изменение категорий и цен

Откройте `config.py` и измените словарь `CATEGORIES`:

```python
CATEGORIES = {
    "1day": {"name": "1 день", "price": 100},
    "7days": {"name": "7 дней", "price": 500},
    "30days": {"name": "30 дней", "price": 1500},
    "90days": {"name": "90 дней", "price": 4000},  # Новый тариф
}
```

### Изменение ссылки на скачивание

В `config.py` измените:

```python
SKTRADE_DOWNLOAD_LINK = "https://your-link.com/sktrade"
```

### Изменение контакта поддержки

В `config.py` измените:

```python
SUPPORT_USERNAME = "@your_support"
```

## 📝 Важные замечания

1. **Telegram Payments** требуют, чтобы бот был опубликован и имел SSL-сертификат
2. **SQLite** подходит для разработки, но для продакшена лучше использовать PostgreSQL
3. **Не передавайте** `.env` файл никому — он содержит секретные данные
4. **Резервное копирование** базы данных: периодически копируйте `bot_database.db`

## 🐛 Решение проблем

### Бот не запускается

Проверьте:
- Установлены ли зависимости (`pip install -r requirements.txt`)
- Правильный ли токен в `.env`
- Запущен ли виртуальное окружение

### Ошибки с базой данных

Удалите `bot_database.db` и перезапустите бота — база создастся заново.

### Telegram Payments не работают

- Убедитесь, что бот опубликован
- Проверьте, что `PAYMENT_PROVIDER_TOKEN` указан верно
- Telegram Payments работают только с SSL (https)

## 📞 Поддержка

Если возникли вопросы или проблемы:
- GitHub Issues в репозитории проекта
- Telegram: указанный в боте контакт поддержки

## 📄 Лицензия

Этот проект предоставляется как есть для образовательных целей.
