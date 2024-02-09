
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