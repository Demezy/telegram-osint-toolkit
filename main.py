import asyncio
from telethon import TelegramClient
from telethon.tl.types import User
from fuzzywuzzy import process
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.completion import FuzzyWordCompleter
from config import API_ID, API_HASH, SESSION_NAME


# Initialize Telegram client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


# Get all chats
async def get_all_chats():
    async with client:
        dialogs = await client.get_dialogs()
        chats = [dialog for dialog in dialogs if dialog.is_group or dialog.is_channel]
    return chats


# Fuzzy select chats interactively
async def interactive_fuzzy_select_chats(chats):
    chat_titles = [chat.title for chat in chats]
    completer = FuzzyWordCompleter(chat_titles)
    selected_titles = []

    session = PromptSession()

    while True:
        with patch_stdout():
            user_input = await session.prompt_async(
                "Type chat name (or 'done' to finish): ", completer=completer
            )
        if user_input.lower() == "done":
            break
        matched_titles = process.extract(user_input, chat_titles, limit=5)
        for title, score in matched_titles:
            if score > 75 and title not in selected_titles:
                selected_titles.append(title)
                print(f"Selected: {title}")

    selected_chats = [chat for chat in chats if chat.title in selected_titles]
    return selected_chats


# Dump all chat participants into a processing pool
async def get_chat_participants(chats):
    users = {}
    async with client:
        for chat in chats:
            participants = await client.get_participants(chat)
            for user in participants:
                users[user.id] = user
    return users.values()


def process_users(users, func=None):
    for user in users:
        if func:
            func(user)


async def main():
    chats = await get_all_chats()
    selected_chats = await interactive_fuzzy_select_chats(chats)
    users = await get_chat_participants(selected_chats)
    process_users(users, print)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # For environments where an event loop is already running
        asyncio.create_task(main())
    else:
        # For typical script execution
        loop.run_until_complete(main())
