class MessageHistory:
    def __init__(self, id, name, encoding):
        self.id = id
        self.name = name
        self.encoding = encoding
        self.messages = []
        self.attachments = []
        self.token_count = 0
        self.PLACEHOLDER_SIZE_FOR_OBJECT = 128
        self.max_return_tokens = 1024*4
        self.MAX_TOKENS = 1024*12
        self.system_message = "You are a helpful assistant in a group chat. You may receive messages from more than one username, the username is a regular string, may or may not contain numbers or emojis. You may respond to a user by addressing their username in your response but it is not necessary. Your are also able to generate images and generate text-to-speech audio files upon request."

    def _count_tokens(self, text: str):
        tokens = self.encoding.encode(text)
        return len(tokens)


    def _count_tokens_dict(self, object: dict):
        if type(object) != dict: return self.PLACEHOLDER_SIZE_FOR_OBJECT
        return sum([self._count_tokens(k) + self._count_tokens(v) for k, v in object.items()])

    
    def _exceeds_token_limit_dict(self, message: dict) -> bool:
        new_token_count = self._count_tokens_dict(message) if type(message) == dict else self.PLACEHOLDER_SIZE_FOR_OBJECT
        if self.token_count + new_token_count >= self.MAX_TOKENS - self.max_return_tokens:
            return True
        return False


    def _remove_oldest_message(self):
        message = self.messages.pop(1)  # We don't want to delete the system message so we use index 1 (since system message is at 0)
        for key, value in message.items():
            self.token_count -= self._count_tokens(key)
            self.token_count -= self._count_tokens(value)


    def _add_to_history(self, object: dict):
        while self._exceeds_token_limit_dict(object):
            self._remove_oldest_message()

        self.token_count += self._count_tokens_dict(object)

        self.messages.append(object)
    

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


    def _add_attachment(self, attachment):
        self.attachments.append(attachment)


    def _pop_attachment(self):
        return self.attachments.pop()


    def _pop_all_attachments(self):
        copy = self.attachments.copy()
        self.attachments.clear()
        return copy


    def _initialize_history(self):
        self.messages.clear()
        self.token_count = 0
        self._add_message_to_history(self.system_message, "system")


    def get_formatted_history(self) -> str:

        result = ""

        for line in self.messages:
            try:
                role, content = line["role"], line["content"]
                if role == "user":
                    role = content.split(":")[0]
            
                result += f"{role}: {content}\n\n"
            except:
                result += str(line) + "\n\n"

        return result
    

    def __str__(self):
        return '\n'.join(self.messages)
