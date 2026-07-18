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

SENT_FILE = "/tmp/sent_vacancies.json"
CHECK_INTERVAL = 1800  # каждые 30 минут

def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_sent(sent):
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent)[-10000:], f)

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

def format_msg(text, chat, date, num):
    date_str = date.strftime("%d.%m %H:%M")
   preview = text[:4000] + ("..." if len(text) > 4000 else "")
    return (
        f"<b>#{num}</b>  |  {date_str}\n"
        f"@{chat}\n"
        f"{'─' * 30}\n"
        f"{preview}"
    )

async def check_once(client):
    sent = load_sent()
    new_msgs = []

    for chat in SOURCE_CHATS:
        try:
            print(f"Читаю @{chat}...")
            entity = await client.get_entity(chat)
            # Берём все сообщения без ограничения по времени
            async for msg in client.iter_messages(entity, limit=500):
                if not msg.text:
                    continue
                h = get_hash(msg.text)
                if h in sent:
                    continue
                new_msgs.append((msg.text, chat, msg.date, h))
        except Exception as e:
            print(f"Ошибка с @{chat}: {e}")

    if new_msgs:
        send_to_me(
            f"<b>Подборка {datetime.now().strftime('%d.%m %H:%M')}</b>\n"
            f"Новых: <b>{len(new_msgs)}</b>"
        )
        for i, (text, chat, date, h) in enumerate(new_msgs, 1):
            send_to_me(format_msg(text, chat, date, i))
            sent.add(h)
            await asyncio.sleep(1)
        save_sent(sent)
        print(f"Отправлено: {len(new_msgs)}")
    else:
        print("Новых сообщений нет")

async def main():
    if not SESSION_STRING:
        send_to_me("ОШИБКА: SESSION_STRING не задана!")
        return

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()

    is_auth = await client.is_user_authorized()
    if not is_auth:
        send_to_me("ОШИБКА: Сессия невалидна!")
        return

    print("Подключились успешно!")
    send_to_me("Парсер запущен! Рассылка каждые 30 минут, без повторов.")

    while True:
        await check_once(client)
        print("Следующая проверка через 30 минут...")
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
