import discord
from discord import Intents
from credentials import DISCORD_TOKEN
from chatgpt import ChatGPT

TIMEOUT_IN_SECS = 30
DISCORD_MAX_CHARS = 1500

client = discord.Client(intents=Intents.all())
chatgpt = ChatGPT()

SIMPLE_USERNAME_CACHE = {}

def get_username(author: discord.Member):
    return f"<@{author.id}>"


async def ask_chatgpt(message: discord.Message,  prefix: str = None) -> None:
    if prefix:
        prompt = message.content.split(prefix)[1]
    else:
        prompt = message.content

    SIMPLE_USERNAME_CACHE[get_username(message.author)] = message.author.display_name

    response = chatgpt.ask(message.author.display_name, prompt)

    for author_id, display_name in SIMPLE_USERNAME_CACHE.items():
        if display_name in response:
            response = response.replace(display_name, author_id)

    await send_response(message, response)


async def send_response(message: discord.Message, response: str) -> None:

    while response:
        index = DISCORD_MAX_CHARS if len(response) <= DISCORD_MAX_CHARS else response[:DISCORD_MAX_CHARS].rindex(" ")
        to_send = response[:index]
        response = response[index:]
        
        files = chatgpt._pop_all_attachments() if chatgpt.attachments else None
        await message.reply(to_send, files=files)
        

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
        chatgpt.change_system_message(new_message)
        await message.reply(f"Successfully set the new system message to: ```{chatgpt.system_message}```")


    if message.content.startswith("-clear"):
        if not message.content.split()[0] == "-clear":
            return
        chatgpt.initalize_history()
        await message.reply("Successfully cleared the conversation history.")


    if message.content.startswith("-history"):
        if not message.content.split()[0] == "-history":
            return
        history = chatgpt.get_formatted_history(chatgpt.message_history)
        await send_response(message, history)


client.run(DISCORD_TOKEN)