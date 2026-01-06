# example.py
import os
from io import BytesIO

from dotenv import load_dotenv

from elevenlabs.client import ElevenLabs

load_dotenv()

elevenlabs = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
)

voice = elevenlabs.voices.ivc.create(
    name="Aryan Khurana",
    files=[
        BytesIO(
            open(
                "/Users/aryankhurana/Developer/viralens/elevenlabs/audios/train01.m4a",
                "rb",
            ).read()
        ),
        BytesIO(
            open(
                "/Users/aryankhurana/Developer/viralens/elevenlabs/audios/train02.m4a",
                "rb",
            ).read()
        ),
        BytesIO(
            open(
                "/Users/aryankhurana/Developer/viralens/elevenlabs/audios/train03.m4a",
                "rb",
            ).read()
        ),
    ],
)

print(voice.voice_id)
