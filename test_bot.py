import os
import discord
from discord import Intents
from chatgpt_wrapper import ChatGPT
from credentials import DISCORD_TOKEN

TIMEOUT_IN_SECS = 30

client = discord.Client(intents=Intents.all())

chatgpt = ChatGPT(timeout=TIMEOUT_IN_SECS)

def ask(prompt: str) -> str:
    prompt = prompt.split("-prompt")[1]
    print(prompt)
    response = chatgpt.ask(prompt)
    return response

# if __name__ == "__main__":
#     response = ask("-prompt list")
#     print(response)

# @client.event
# async def on_ready():
#     print(f'{client.user} has connected to Discord!')

# @client.event
# async def on_message(message: discord.Message):

#     # if message.content.startswith("-prompt"):
#     #     response = ask(message.content)
#     #     message.reply(response)        

#     if message.content.startswith("-new"):
#         os.system("!new")
#         message.reply("Successfully cleared the conversation history.")     

#     if message.content.startswith("-session"):
#         os.system("!session")
#         message.reply("Successfully refreshed the session token.")     

# client.run(DISCORD_TOKEN)