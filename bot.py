"""
========================================
 КАРМАН СТУДЕНТА — Парсер вакансий
========================================
"""
import asyncio
import json
import os
import hashlib
from datetime import datetime, timedelta, timezone
import requests
from telethon import TelegramClient

# ============================================================
# НАСТРОЙКИ
# ============================================================
BOT_TOKEN = "8474485805:AAFbTDADlq2tFXKWcWNa5GIzS_Y4NfOLI88"
MY_CHAT_ID = 5054407561
API_ID = 2040
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
SENT_FILE = "sent_vacancies.json"
CHECK_INTERVAL = 3600  # каждый час

# ============================================================
# ФУНКЦИИ
# ============================================================
def load_sent() -> set:
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_sent(sent: set):
    with open(SENT_FILE, "w") as f:
        json.dump(list(sent)[-5000:], f)

def get_hash(text: str) -> str:
    return hashlib.md5(text.strip().encode()).hexdigest()

def send_to_me(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": MY_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
        }, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def is_vacancy(text: str) -> bool:
    t = text.lower()
    if any(w.lower() in t for w in EXCLUDE_KEYWORDS):
        return False
    return any(w.lower() in t for w in KEYWORDS)

def format_vacancy(text: str, chat: str, date: datetime, num: int) -> str:
    date_str = date.strftime("%d.%m %H:%M")
    preview = text[:800] + ("..." if len(text) > 800 else "")
    return (
        f"💼 <b>Вакансия #{num}</b> | {date_str}\n"
        f"📢 @{chat}\n"
        f"{'─' * 30}\n"
        f"{preview}"
    )

async def check_once(client: TelegramClient):
    sent = load_sent()
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    new_vacancies = []
    
    for chat in SOURCE_CHATS:
        try:
            print(f"🔍 Читаю @{chat}...")
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
            print(f"⚠️ Ошибка с @{chat}: {e}")
    
    if new_vacancies:
        send_to_me(
            f"🕐 <b>Подборка вакансий</b> — {datetime.now().strftime('%d.%m %H:%M')}\n"
            f"Новых вакансий: <b>{len(new_vacancies)}</b>"
        )
        for i, (text, chat, date, h) in enumerate(new_vacancies, 1):
            send_to_me(format_vacancy(text, chat, date, i))
            sent.add(h)
            await asyncio.sleep(0.5)
        save_sent(sent)
        print(f"✅ Отправлено: {len(new_vacancies)}")
    else:
        print("ℹ️ Новых вакансий нет")

async def main():
    print("🚀 Парсер запущен!")
    send_to_me(
        "🚀 <b>Карман студента — парсер запущен!</b>\n"
        "Буду присылать вакансии каждый час.\n"
        f"Слежу за: {', '.join('@' + c for c in SOURCE_CHATS)}"
    )
    
    phone_number = os.getenv('PHONE_NUMBER', '89021445391')
    client = TelegramClient("vacancy_session", API_ID, API_HASH)
    await client.start(phone=phone_number)
    
    while True:
        await check_once(client)
        print("⏳ Следующая проверка через час...")
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
