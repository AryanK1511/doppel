import os

from dotenv import load_dotenv

from elevenlabs.client import ElevenLabs

load_dotenv()

elevenlabs = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

audio = elevenlabs.text_to_speech.convert(
    text="opportunities that come up all of a sudden like this is exactly why I dont do new year resolutions",
    voice_id="A6KpMxgYHip7Ydpy1qt2",
    model_id="eleven_multilingual_v2",
    output_format="mp3_44100_128",
)

with open("output.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)
