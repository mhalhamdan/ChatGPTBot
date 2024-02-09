import json
import openai
import tiktoken
from credentials import OPENAI_API_TOKEN
from tools import addition_tool, add
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice
from openai.types.chat import ChatCompletionMessageToolCall

MAX_TOKENS = 1024+256

openai.api_key = OPENAI_API_TOKEN

class BaseGPT:

    model = None
    encoding = None
    system_message = "You are a helpful assistant in a group chat. You may receive messages from more than one username, the username is a regular string, may or may not contain numbers or emojis. You may respond to a user by addressing their username in your response but it is not necessary."

    def __init__(self, max_return_tokens=1024) -> None:
        self.message_history = []
        self.max_return_tokens = max_return_tokens
        self.token_count = 0        
        self.initalize_history()


    def _count_tokens(self, text: str):
        tokens = self.encoding.encode(text)
        return len(tokens)

    
    def _exceeds_token_limit(self, user: str, text: str) -> bool:
        new_token_count = self._count_tokens(text) + self._count_tokens(user)
        if self.token_count + new_token_count >= MAX_TOKENS - self.max_return_tokens:
            return True
        return False
    

    def _remove_oldest_message(self):
        message = self.message_history.pop(1)  # We don't want to delete the system message so we use index 1 (since system message is at 0)
        self.token_count -= self._count_tokens(message["role"])
        self.token_count -= self._count_tokens(message["content"])
        message = self.message_history.pop(1)  # We delete twice because of the pairing of assistant and user messages being back to back
        self.token_count -= self._count_tokens(message["role"])
        self.token_count -= self._count_tokens(message["content"])


    def _add_message_to_history(self, message: str, type: str):
        self.token_count += self._count_tokens(message)
        self.token_count += self._count_tokens(type)
        self.message_history.append(
            {"role": type, "content": message}
        )

    def _handle_tool_call(self, tool_call: ChatCompletionMessageToolCall):
        name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        match name:
            case "add":
                func = add


        result = func(**arguments)
        return f"Used {name} function and got result {result}."   

    def _handle_response(self, choice: Choice) -> str:
        if choice.finish_reason == "tool_calls":
            return self._handle_tool_call(choice.message.tool_calls[0])
        
        return choice.message.content


    def _ask(self, user: str, prompt: str, create_params: dict) -> str:
        while self._exceeds_token_limit(user, prompt):
            self._remove_oldest_message()

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
            role, content = line["role"], line["content"]
            if role == "user":
                role = content[:21]
                content = content[22:]
            result += f"{role}: {content}\n\n"

        return result

class ChatGPT(BaseGPT):

    model = "gpt-4-turbo-preview"
    encoding = tiktoken.encoding_for_model(model)

    tools = [
        addition_tool
    ]

    def ask(self, user: str, prompt: str) -> str:

        params = dict(
            model=self.model,
            messages=self.message_history,
            max_tokens=self.max_return_tokens,
            tools=[addition_tool],
            tool_choice="auto"
        )
        
    
        return self._ask(user, prompt, params)
