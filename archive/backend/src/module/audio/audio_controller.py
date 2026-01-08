from fastapi import APIRouter, Depends, File, Form, UploadFile
from src.common.utils.response import Response, Status
from src.module.audio.audio_dependency import get_audio_service
from src.module.audio.audio_schema import (
    CreateVoiceResponse,
    GenerateAudioRequest,
    GenerateAudioResponse,
    GeneratedAudioDetail,
    GeneratedAudioListItem,
)
from src.module.audio.audio_service import AudioService

router = APIRouter(prefix="/audio", tags=["audio"])


@router.post("/voices", response_model=CreateVoiceResponse)
async def create_voice(
    name: str = Form(...),
    description: str = Form(...),
    files: list[UploadFile] = File(...),
    audio_service: AudioService = Depends(get_audio_service),
):
    if len(files) > 5:
        return Response.error(
            message="Maximum 5 audio files allowed",
            status_code=Status.BAD_REQUEST,
        )

    if len(files) == 0:
        return Response.error(
            message="At least one audio file is required",
            status_code=Status.BAD_REQUEST,
        )

    try:
        file_bytes_list = []
        for file in files:
            contents = await file.read()
            file_bytes_list.append(contents)

        result = await audio_service.create_voice(
            name=name, description=description, files=file_bytes_list
        )
        return Response.success(
            message="Voice created successfully",
            data=result,
            status_code=Status.CREATED,
        )
    except ValueError as e:
        return Response.error(
            message=str(e),
            status_code=Status.BAD_REQUEST,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to create voice: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.post("/generate", response_model=GenerateAudioResponse)
async def generate_audio(
    request: GenerateAudioRequest,
    audio_service: AudioService = Depends(get_audio_service),
):
    try:
        result = await audio_service.generate_audio(
            voice_id=request.voice_id, text=request.text
        )
        return Response.success(
            message="Audio generated successfully",
            data=result,
            status_code=Status.CREATED,
        )
    except ValueError as e:
        return Response.error(
            message=str(e),
            status_code=Status.BAD_REQUEST,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to generate audio: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.get("/generated", response_model=list[GeneratedAudioListItem])
async def get_generated_audios(
    audio_service: AudioService = Depends(get_audio_service),
):
    try:
        result = await audio_service.get_generated_audios()
        return Response.success(
            message="Generated audios retrieved successfully",
            data=result,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to retrieve generated audios: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )


@router.get("/generated/{audio_id}", response_model=GeneratedAudioDetail)
async def get_generated_audio(
    audio_id: str,
    audio_service: AudioService = Depends(get_audio_service),
):
    try:
        result = await audio_service.get_generated_audio_by_id(audio_id=audio_id)
        return Response.success(
            message="Generated audio retrieved successfully",
            data=result,
        )
    except ValueError as e:
        return Response.error(
            message=str(e),
            status_code=Status.NOT_FOUND,
        )
    except Exception as e:
        return Response.error(
            message=f"Failed to retrieve generated audio: {str(e)}",
            status_code=Status.INTERNAL_SERVER_ERROR,
        )
