import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
PHONE_NUMBER = "89021445391"

async def main():
    session = StringSession()
    client = TelegramClient(session, API_ID, API_HASH)
    
    await client.connect()
    
    if not await client.is_user_authorized():
        await client.send_code_request(PHONE_NUMBER)
        code = input("Введи код из Telegram: ")
        await client.sign_in(PHONE_NUMBER, code)
    
    print("\n✅ Сессия создана!")
    print("\nСкопируй эту строку и добавь в переменную SESSION_STRING:")
    print(session.save())

if __name__ == "__main__":
    asyncio.run(main())
