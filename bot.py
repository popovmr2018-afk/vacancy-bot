import asyncio
import json
import os
import hashlib
from datetime import datetime, timedelta, timezone
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession

BOT_TOKEN      = os.environ.get("BOT_TOKEN", "")
MY_CHAT_ID     = int(os.environ.get("MY_CHAT_ID", "5054407561"))
SESSION_STRING = os.environ.get("SESSION_STRING", "")

API_ID   = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"

SOURCE_CHATS = [
    "muravey_100",
    "personnelnskchas",
    "rabota154NsK",
]

KEYWORDS = [
    "подработка", "подработать", "студент", "студентам",
    "part-time", "неполный день", "гибкий график",
    "свободный график", "курьер", "промоутер", "аниматор",
    "расклейщик", "раздача", "опрос", "анкетирование",
    "кассир", "официант", "бармен", "репетитор",
    "няня", "помощник", "грузчик", "упаковщик",
]

EXCLUDE_KEYWORDS = [
    "опыт от 3", "опыт от 5", "стаж от 3", "стаж от 5",
]

SENT_FILE = "/tmp/sent_vacancies.json"
CHECK_INTERVAL = 3600

def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent)[-5000:], f)

def get_hash(text):
    return hashlib.md5(text.strip().encode()).hexdigest()

def send_to_me(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": MY_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
        }, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def is_vacancy(text):
    t = text.lower()
    if any(w.lower() in t for w in EXCLUDE_KEYWORDS):
        return False
    return any(w.lower() in t for w in KEYWORDS)

def format_vacancy(text, chat, date, num):
    date_str = date.strftime("%d.%m %H:%M")
    preview = text[:800] + ("..." if len(text) > 800 else "")
    return (
        f"<b>Вакансия #{num}</b>  |  {date_str}\n"
        f"@{chat}\n"
        f"{'─' * 30}\n"
        f"{preview}"
    )

async def check_once(client):
    sent = load_sent()
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    new_vacancies = []

    for chat in SOURCE_CHATS:
        try:
            print(f"Читаю @{chat}...")
            entity = await client.get_entity(chat)
            async for msg in client.iter_messages(entity, limit=100):
                if msg.date < since:
                    break
                if not msg.text:
                    continue
                h = get_hash(msg.text)
                if h in sent:
                    continue
                if is_vacancy(msg.text):
                    new_vacancies.append((msg.text, chat, msg.date, h))
        except Exception as e:
            print(f"Ошибка с @{chat}: {e}")

    if new_vacancies:
        send_to_me(
            f"<b>Подборка вакансий</b> — {datetime.now().strftime('%d.%m %H:%M')}\n"
            f"Новых: <b>{len(new_vacancies)}</b>"
        )
        for i, (text, chat, date, h) in enumerate(new_vacancies, 1):
            send_to_me(format_vacancy(text, chat, date, i))
            sent.add(h)
            await asyncio.sleep(1)
        save_sent(sent)
        print(f"Отправлено: {len(new_vacancies)}")
    else:
        print("Новых вакансий нет")

async def main():
    print(f"SESSION_STRING задана: {bool(SESSION_STRING)}")
    print(f"Длина SESSION_STRING: {len(SESSION_STRING)}")

    if not SESSION_STRING:
        print("ОШИБКА: SESSION_STRING не задана!")
        send_to_me("ОШИБКА: SESSION_STRING не задана в переменных Railway!")
        return

    print("Подключаемся через StringSession...")
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()

    is_auth = await client.is_user_authorized()
    print(f"Авторизован: {is_auth}")

    if not is_auth:
        print("ОШИБКА: Сессия невалидна!")
        send_to_me("ОШИБКА: Сессия невалидна! Нужно сгенерировать SESSION_STRING заново.")
        return

    print("Успешно подключились!")
    send_to_me("Парсер запущен! Буду присылать вакансии каждый час.")

    while True:
        await check_once(client)
        print("Следующая проверка через час...")
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
