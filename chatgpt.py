import openai
import tiktoken
from credentials import OPENAI_API_TOKEN

MAX_TOKENS = 4096-1024

openai.api_key = OPENAI_API_TOKEN

class ChatGPT():

    def __init__(self, max_return_tokens=1024) -> None:
        self.message_history = []
        self.max_return_tokens = max_return_tokens
        self.system_message = "You are a helpful assistant in a group chat. You may receive messages from more than one username, the username is a long string of numbers encased by <@>. Like <@263306098512101376>. You may respond to a user by addressing their username in your response but it is not necessary."
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
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

    def ask(self, user: str, prompt: str) -> str:
        while self._exceeds_token_limit(user, prompt):
            self._remove_oldest_message()

        self._add_message_to_history(user + ":" + prompt, "user")

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=self.message_history,
                max_tokens=self.max_return_tokens
            )
        except:
            self._remove_oldest_message()

        message_response = response['choices'][0]['message']['content']

        self._add_message_to_history(message_response, "assistant")

        return message_response
    
    def initalize_history(self) -> None:
        self.message_history = [{"role": "system", "content": self.system_message}]
        self.token_count = self._count_tokens("system") + self._count_tokens(self.system_message)
