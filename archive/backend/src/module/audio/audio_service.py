from datetime import datetime
from typing import Any

from bson import ObjectId
from src.common.logger import logger
from src.database.gcs.client import GCSClient
from src.database.mongodb.mongodb_client import mongodb_client
from src.downstream.elevenlabs.client import ElevenLabsClient


class AudioService:
    def __init__(
        self,
        elevenlabs_client: ElevenLabsClient,
        gcs_client: GCSClient,
    ):
        self.elevenlabs_client = elevenlabs_client
        self.gcs_client = gcs_client

    async def create_voice(
        self, name: str, description: str, files: list[bytes]
    ) -> dict[str, Any]:
        if len(files) > 5:
            raise ValueError("Maximum 5 audio files allowed")

        training_audio_urls = []
        for idx, file_bytes in enumerate(files):
            filename = f"training/{name.replace(' ', '_')}_{idx}_{datetime.now().timestamp()}.mp3"
            url = self.gcs_client.upload_audio(file_bytes, filename)
            training_audio_urls.append(url)

            audio_doc = {
                "type": "trained",
                "url": url,
                "created_at": datetime.utcnow(),
            }
            await mongodb_client.audios.insert_one(audio_doc)

        voice_id = self.elevenlabs_client.create_voice(name=name, files=files)

        voice_doc = {
            "voice_id": voice_id,
            "name": name,
            "description": description,
            "training_audio_urls": training_audio_urls,
            "created_at": datetime.utcnow(),
        }
        result = await mongodb_client.voices.insert_one(voice_doc)
        voice_doc["_id"] = result.inserted_id

        logger.info(f"Created voice: {name} with voice_id: {voice_id}")

        return {
            "voice_id": voice_id,
            "name": name,
            "training_audio_urls": training_audio_urls,
        }

    async def generate_audio(self, voice_id: str, text: str) -> dict[str, Any]:
        audio_bytes = self.elevenlabs_client.generate_audio(
            text=text, voice_id=voice_id
        )

        filename = f"generated/{voice_id}_{datetime.now().timestamp()}.mp3"
        url = self.gcs_client.upload_audio(audio_bytes, filename)

        audio_doc = {
            "type": "generated",
            "url": url,
            "voice_id": voice_id,
            "text": text,
            "created_at": datetime.utcnow(),
        }
        result = await mongodb_client.audios.insert_one(audio_doc)
        audio_doc["_id"] = result.inserted_id

        logger.info(f"Generated audio for voice_id: {voice_id}")

        return {
            "audio_id": str(audio_doc["_id"]),
            "url": url,
        }

    async def get_generated_audios(self) -> list[dict[str, Any]]:
        cursor = mongodb_client.audios.find({"type": "generated"}).sort(
            "created_at", -1
        )
        audios = await cursor.to_list(length=None)

        result = []
        for audio in audios:
            voice = await mongodb_client.voices.find_one(
                {"voice_id": audio["voice_id"]}
            )
            voice_name = voice["name"] if voice else "Unknown"

            result.append(
                {
                    "audio_id": str(audio["_id"]),
                    "url": audio["url"],
                    "voice_name": voice_name,
                    "created_at": audio["created_at"].isoformat(),
                }
            )

        return result

    async def get_generated_audio_by_id(self, audio_id: str) -> dict[str, Any]:
        audio = await mongodb_client.audios.find_one({"_id": ObjectId(audio_id)})

        if not audio:
            raise ValueError(f"Audio with id {audio_id} not found")

        if audio["type"] != "generated":
            raise ValueError(f"Audio with id {audio_id} is not a generated audio")

        voice = await mongodb_client.voices.find_one({"voice_id": audio["voice_id"]})

        if not voice:
            raise ValueError(f"Voice with voice_id {audio['voice_id']} not found")

        return {
            "audio_id": str(audio["_id"]),
            "url": audio["url"],
            "text": audio["text"],
            "voice": {
                "name": voice["name"],
                "description": voice["description"],
                "training_audio_urls": voice["training_audio_urls"],
            },
        }
