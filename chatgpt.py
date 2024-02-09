import json
import openai
import tiktoken
from typing import List
from credentials import OPENAI_API_TOKEN
from tools import generate_speech, text_to_speech_tool, generate_image, generate_image_tool
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice
from openai.types.chat import ChatCompletionMessageToolCall

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

    def __init__(self, max_return_tokens=1024*4) -> None:
        self.message_history = []
        self.max_return_tokens = max_return_tokens
        self.token_count = 0        
        self.initalize_history()

    def _add_attachment(self, attachment):
        self.attachments.append(attachment)

    def _pop_attachment(self):
        return self.attachments.pop()

    def _count_tokens(self, text: str):
        tokens = self.encoding.encode(text)
        return len(tokens)
    
    def _count_tokens_dict(self, object: dict):
        if type(object) != dict: return PLACEHOLDER_SIZE_FOR_OBJECT
        return sum([self._count_tokens(k) + self._count_tokens(v) for k, v in object.items()])

    def _exceeds_token_limit(self, user: str, text: str) -> bool:
        new_token_count = self._count_tokens(text) + self._count_tokens(user)
        if self.token_count + new_token_count >= MAX_TOKENS - self.max_return_tokens:
            return True
        return False
    
    def _exceeds_token_limit_dict(self, message: dict) -> bool:
        new_token_count = self._count_tokens_dict(message) if type(message) == dict else PLACEHOLDER_SIZE_FOR_OBJECT
        if self.token_count + new_token_count >= MAX_TOKENS - self.max_return_tokens:
            return True
        return False

    def _remove_oldest_message(self):
        message = self.message_history.pop(1)  # We don't want to delete the system message so we use index 1 (since system message is at 0)
        for key, value in message.items():
            self.token_count -= self._count_tokens(key)
            self.token_count -= self._count_tokens(value)

    def _add_to_history(self, object: dict):
        while self._exceeds_token_limit_dict(object):
            self._remove_oldest_message()

        self.token_count += self._count_tokens_dict(object)

        self.message_history.append(object)
    
    def _add_message_to_history(self, message: str, type: str):
        self._add_to_history({
            "role": type, 
            "content": message
        })
    
    def _add_tool_message_to_history(self, tool_call_id: str, function_name: str, result: str):
        tool_call_message = {
            "tool_call_id": tool_call_id,
            "role": "tool",
            "name": function_name,
            "content": result
        }

        self._add_to_history(tool_call_message)

    def _handle_tool_calls(self, tool_calls: List[ChatCompletionMessageToolCall]):
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            function_to_call = AVAILABLE_FUNCTIONS[function_name]
            result = function_to_call(**arguments)

            if type(result) == tuple:
                result, attachment = result[0], result[1]
                self._add_attachment(attachment)

            self._add_tool_message_to_history(
                tool_call_id=tool_call.id,
                function_name=function_name,
                result=str(result)
            )

        second_response = openai.chat.completions.create(
            model=self.model,
            messages=self.message_history,
            max_tokens=self.max_return_tokens)
                
        return second_response.choices[0].message.content

    def _handle_response(self, choice: Choice) -> str:
        if choice.message.tool_calls:
            # self.message_history.append(choice.message)
            self._add_to_history(choice.message)
            return self._handle_tool_calls(choice.message.tool_calls)
        
        return choice.message.content


    def _ask(self, user: str, prompt: str, create_params: dict) -> str:

        self._add_message_to_history(user + ": " + prompt, "user")

        response = openai.chat.completions.create(**create_params)

        message = self._handle_response(response.choices[0])

        self._add_message_to_history(message, "assistant")

        return message

    def ask(self, user: str, prompt: str) -> str:
       pass

    def initalize_history(self) -> None:
        self.message_history = [{"role": "system", "content": self.system_message}]
        self.token_count = self._count_tokens("system") + self._count_tokens(self.system_message)


    def switch_model(self, model: str) -> None:
        if model == "chatgpt":
            self.model = "gpt-3.5-turbo"
        elif model == "gpt3":
            self.model = "text-davinci-003"
        else:
            raise ValueError(f"Unknown model name: {model}. Available models are: chatgpt and gpt3")
        
        self.encoding = tiktoken.get_encoding(self.model)

        self.initalize_history()

    
    def change_system_message(self, new_message: str) -> None:
        self.system_message = new_message

        self.initalize_history()


    @staticmethod
    def get_formatted_history(history: list) -> str:

        result = ""

        for line in history:
            try:
                role, content = line["role"], line["content"]
                if role == "user":
                    role = content[:21]
                    content = content[22:]
                result += f"{role}: {content}\n\n"
            except:
                result += str(line) + "\n\n"

        return result

class ChatGPT(BaseGPT):

    model = "gpt-4-turbo-preview"
    encoding = tiktoken.encoding_for_model(model)

    tools = [
        generate_image_tool, text_to_speech_tool
    ]

    def ask(self, user: str, prompt: str) -> str:

        params = dict(
            model=self.model,
            messages=self.message_history,
            max_tokens=self.max_return_tokens,
            tools=self.tools,
            tool_choice="auto"
        )

        return self._ask(user, prompt, params)
