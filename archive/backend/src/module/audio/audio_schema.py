from pydantic import BaseModel, Field


class GenerateAudioRequest(BaseModel):
    voice_id: str = Field(..., description="ElevenLabs voice ID")
    text: str = Field(..., description="Text to convert to speech")


class CreateVoiceResponse(BaseModel):
    voice_id: str = Field(..., description="ElevenLabs voice ID")
    name: str = Field(..., description="Voice name")
    training_audio_urls: list[str] = Field(
        ..., description="URLs of training audio files"
    )


class GenerateAudioResponse(BaseModel):
    audio_id: str = Field(..., description="Generated audio document ID")
    url: str = Field(..., description="URL of the generated audio file")


class GeneratedAudioListItem(BaseModel):
    audio_id: str = Field(..., description="Generated audio document ID")
    url: str = Field(..., description="URL of the generated audio file")
    voice_name: str = Field(..., description="Name of the voice used")
    created_at: str = Field(..., description="ISO format timestamp of creation")


class VoiceDetails(BaseModel):
    name: str = Field(..., description="Voice name")
    description: str = Field(..., description="Voice description")
    training_audio_urls: list[str] = Field(
        ..., description="URLs of training audio files"
    )


class GeneratedAudioDetail(BaseModel):
    audio_id: str = Field(..., description="Generated audio document ID")
    url: str = Field(..., description="URL of the generated audio file")
    text: str = Field(..., description="Text that was converted to speech")
    voice: VoiceDetails = Field(..., description="Details of the voice used")
