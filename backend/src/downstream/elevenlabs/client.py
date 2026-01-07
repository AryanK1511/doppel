from elevenlabs.client import ElevenLabs
from src.common.config import settings


class ElevenLabsClient:
    def __init__(self):
        self.client = ElevenLabs(
            api_key=settings.ELEVENLABS_API_KEY,
        )

    def generate_audio(self, text: str, voice_id: str) -> bytes:
        return self.client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )

    def create_voice(self, name: str, files: list[bytes]) -> str:
        voice = self.client.voices.ivc.create(
            name=name,
            files=files,
        )
        return voice.voice_id
