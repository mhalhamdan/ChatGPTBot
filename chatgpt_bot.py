import discord
from discord import Intents
from credentials import DISCORD_TOKEN
from chatgpt import ChatGPT

TIMEOUT_IN_SECS = 30

client = discord.Client(intents=Intents.all())
chatgpt = ChatGPT()


def get_username(author: discord.Member):
    return f"<@{author.id}>"


async def ask_chatgpt(message: discord.Message,  prefix: str = None) -> None:
    if prefix:
        prompt = message.content.split(prefix)[1]
    else:
        prompt = message.content

    user = get_username(message.author)
    response = chatgpt.ask(user, prompt)
    await send_response(message, response)


async def send_response(message: discord.Message, response: str) -> None:
    while response:
        to_send = response[:1500]
        await message.reply(to_send)
        response = response[1500:]


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


    if message.content.startswith("-clear"):
        if not message.content.split()[0] == "-clear":
            return
        chatgpt.initalize_history()
        await message.reply("Successfully cleared the conversation history.")     

client.run(DISCORD_TOKEN)