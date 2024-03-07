import discord
from discord import Intents
from credentials import DISCORD_TOKEN
from chatgpt import ChatGPT
import random

TIMEOUT_IN_SECS = 30
DISCORD_MAX_CHARS = 1500

client = discord.Client(intents=Intents.all())
chatgpt = ChatGPT()

SIMPLE_USERNAME_CACHE = {}

def get_username(author: discord.Member):
    return f"<@{author.id}>"

async def debug_print() -> None:
    print("All message histories:")
    all_message_histories = chatgpt.message_histories
    for index, message_history in enumerate(all_message_histories):
        print(f"{index+1}. Message history for {message_history.name} ({message_history.id}) token count: {message_history.token_count}")
    print("------------------------------------\n")


async def ask_chatgpt(message: discord.Message,  prefix: str = None) -> None:
    if prefix:
        prompt = message.content.split(prefix)[1]
    else:
        prompt = message.content

    SIMPLE_USERNAME_CACHE[get_username(message.author)] = message.author.display_name

    response, files = chatgpt.ask(message, prompt)

    for author_id, display_name in SIMPLE_USERNAME_CACHE.items():
        if display_name in response:
            response = response.replace(display_name, author_id)

    await send_response(message, response, files)

    await debug_print()


async def send_response(message: discord.Message, response: str, files: list = None) -> None:

    while response:
        index = DISCORD_MAX_CHARS if len(response) <= DISCORD_MAX_CHARS else response[:DISCORD_MAX_CHARS].rindex(" ")
        to_send = response[:index]
        response = response[index:]

        await message.reply(to_send, files=files)

        # Send files only once
        if files: files = None
        

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message: discord.Message):

    # When mentioned or replied to 
    if message.mentions:
        if message.mentions[0].id == client.user.id:
            message.content = message.content.replace(f"<@{client.user.id}>", "")
            await ask_chatgpt(message)


    # Commands
    if message.content.startswith("-prompt") or message.content.startswith("-p"):
        prefix = message.content.split()[0]
        if not prefix == "-prompt" and not prefix == "-p":
            return
        await ask_chatgpt(message, prefix)


    if message.content.startswith("-system") or message.content.startswith("-s"):
        prefix = message.content.split()[0]
        if not prefix == "-system" and not prefix == "-s":
            return
        new_message = message.content.split(prefix)[1]
        if new_message.strip() == "default":
            new_message = ChatGPT.system_message
        chatgpt.change_system_message(message, new_message)
        await message.reply(f"Successfully set the new system message to: ```{chatgpt.system_message}```")


    if message.content.startswith("-clear"):
        if not message.content.split()[0] == "-clear":
            return
        chatgpt.clear_history(message)
        await message.reply("Successfully cleared the conversation history.")


    if message.content.startswith("-history"):
        if not message.content.split()[0] == "-history":
            return
        message_history = chatgpt.get_message_history(message)
        total_count = f"Total message token count: {message_history.token_count}\n"
        history = total_count + message_history.get_formatted_history()
        await send_response(message, history)


client.run(DISCORD_TOKEN)