def add(a: int, b: int):
    return a + b

addition_tool = {
    "type": "function",
    "function": {
        "description": "function takes two values, adds them up.",
        "name": "add",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "integer",
                    "description": "first integer to be added"
                },
                "b": {
                    "type": "integer",
                    "description": "second integer to be added"
                }
            }
        }
    }
}

def generate_speech(text: str):
    pass

text_to_speech_tool = {
    "type": "function",
    "function": {
        "description": "Function takes text and turns into to speech.",
        "name": "add",
        "parameters": {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "The text to generate audio for."
                },
                "voice": {
                    "type": "string",
                    "description": "second integer to be added"
                }
            }
        }
    }
}