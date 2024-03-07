import json
import openai
import tiktoken
from typing import List
from credentials import OPENAI_API_TOKEN
from tools import generate_speech, text_to_speech_tool, generate_image, generate_image_tool
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice
from openai.types.chat import ChatCompletionMessageToolCall
from discord import Message
from message_history import MessageHistory

MAX_TOKENS = 1024*12
PLACEHOLDER_SIZE_FOR_OBJECT = 128

openai.api_key = OPENAI_API_TOKEN

AVAILABLE_FUNCTIONS = {
    "tts": generate_speech,
    "generate_image": generate_image
}

class BaseGPT:

    model = None
    encoding = None
    system_message = "You are a helpful assistant in a group chat. You may receive messages from more than one username, the username is a regular string, may or may not contain numbers or emojis. You may respond to a user by addressing their username in your response but it is not necessary."
    attachments = []

    def __init__(self) -> None:
        self.message_histories = []


    def _handle_response(self, choice: Choice, message_history: MessageHistory) -> str:
        if not choice.message.tool_calls:
            return choice.message.content
    
        message_history._add_to_history(choice.message)

        for tool_call in choice.message.tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            function_to_call = AVAILABLE_FUNCTIONS[function_name]
            result = function_to_call(**arguments)

            if type(result) == tuple:
                result, attachment = result[0], result[1]
                message_history._add_attachment(attachment)

            message_history._add_tool_message_to_history(
                tool_call_id=tool_call.id,
                function_name=function_name,
                result=str(result)
            ) 

        second_response = openai.chat.completions.create(
            model=self.model,
            messages=message_history.messages,
            max_tokens=message_history.max_return_tokens)
                
        return second_response.choices[0].message.content


    def _ask(self, message: Message, prompt: str, create_params: dict) -> str:

        message_history = self.get_message_history(message)

        message_history._add_message_to_history(message.author.display_name + ": " + prompt, "user")

        create_params.update(
            messages=message_history.messages, 
            max_tokens=message_history.max_return_tokens)

        response = openai.chat.completions.create(**create_params)

        message = self._handle_response(response.choices[0], message_history)

        message_history._add_message_to_history(message, "assistant")

        files = message_history._pop_all_attachments() if message_history.attachments else None

        return message, files


    def ask(self, user: str, prompt: str) -> str:
       pass


    def get_message_history(self, message: Message) -> MessageHistory:

        id = message.author.id if not message.guild else message.guild.id

        message_history = next((x for x in self.message_histories if x.id == id), None)
        if not message_history:
            name = message.author.display_name if not message.guild else message.guild.name
            message_history = MessageHistory(id, name, self.encoding)
            message_history._initialize_history()
            self.message_histories.append(message_history)

        return message_history


    def clear_history(self, message: Message) -> None:
        message_history = self.get_message_history(message)
        message_history._initialize_history()


    def change_system_message(self, message: Message, new_message: str) -> None:
        message_history = self.get_message_history(message)
        message_history.system_message = new_message
        message_history._initialize_history()


class ChatGPT(BaseGPT):

    model = "gpt-4-turbo-preview"
    encoding = tiktoken.encoding_for_model(model)

    tools = [
        generate_image_tool, text_to_speech_tool
    ]

    def ask(self, message: Message, prompt: str) -> str:

        params = dict(
            model=self.model,
            tools=self.tools,
            tool_choice="auto"
        )

        return self._ask(message, prompt, params)
