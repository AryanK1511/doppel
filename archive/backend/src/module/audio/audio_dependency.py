from fastapi import Depends
from src.database.gcs.client import GCSClient
from src.downstream.elevenlabs.client import ElevenLabsClient
from src.module.audio.audio_service import AudioService


def get_elevenlabs_client() -> ElevenLabsClient:
    return ElevenLabsClient()


def get_gcs_client() -> GCSClient:
    return GCSClient()


def get_audio_service(
    elevenlabs_client: ElevenLabsClient = Depends(get_elevenlabs_client),
    gcs_client: GCSClient = Depends(get_gcs_client),
) -> AudioService:
    return AudioService(
        elevenlabs_client=elevenlabs_client,
        gcs_client=gcs_client,
    )
