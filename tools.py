from io import BytesIO
import requests
import openai
import discord


def download_image(image_url: str) -> BytesIO:
    response = requests.get(image_url)
    
    if response.ok:
        return  BytesIO(response.content)
         
    else:
        raise Exception("Error in downloading image from URL")

def generate_image(prompt: str, quality="standard"):
    response = openai.images.generate(
        prompt=prompt,
        n=1,
        size="1024x1024",
        quality=quality,
        style="vivid",
        response_format="url"
    )

    image = download_image(response.data[0].url)
    return "image file will be added as an attachment to the message.", discord.File(fp=image, filename=f"{prompt[:64]}.png")

generate_image_tool = {
    "type": "function",
    "function": {
        "description": "Function takes text and turns into an image when asked to.",
        "name": "generate_image",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The text to generate image of."
                },
                "quality": {
                    "type": "string",
                    "description": "Optional field, specify quality of the image, defaults to 'standard'",
                    "enum": ["hd", "standard"]
                }
            }
        }
    }
}

def generate_speech(input: str, voice: str = "echo", speed: float = 1.0):
    print(f"Called with {input} and {voice}")
    response = openai.audio.speech.create(
        model="tts-1-hd",
        voice=voice,
        input=input,
        speed=speed,
        response_format="mp3"
    )

    buffer = BytesIO()
    for chunk in response.iter_bytes(chunk_size=4096):
        buffer.write(chunk)
    buffer.seek(0)

    return "audio file will be added as an attachment to the message.", discord.File(fp=buffer, filename=f"{input[:16]}.mp3")

text_to_speech_tool = {
    "type": "function",
    "function": {
        "description": "Function takes text and turns into to speech.",
        "name": "tts",
        "parameters": {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "The text to generate audio for."
                },
                "voice": {
                    "type": "string",
                    "description": "Optional field, type of voice to use, defaults to 'echo'",
                    "enum": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
                },
                "speed": {
                    "type": "number",
                    "description": "The speed of the generated audio. Select a value from 0.25 to 4.0. 1.0 is the default."
                }
            }
        }
    }
}