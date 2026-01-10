from typing import Any, Optional

from fastapi import Response as FastAPIResponse
from fastapi import status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class StandardResponse(BaseModel):
    success: bool = Field(
        ..., description="Indicates success (true) or failure (false)"
    )
    message: Optional[str] = Field(
        None, description="A descriptive message about the response"
    )
    data: Optional[Any] = Field(
        None, description="The payload data for success responses"
    )


class Response:
    @staticmethod
    def success(
        message: str = "Success",
        data: Optional[Any] = None,
        status_code: int = status.HTTP_200_OK,
    ) -> JSONResponse:
        response = StandardResponse(success=True, message=message, data=data)
        return JSONResponse(status_code=status_code, content=response.model_dump())

    @staticmethod
    def error(
        message: str = "An error occurred",
        data: Optional[Any] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> JSONResponse:
        response = StandardResponse(success=False, message=message, data=data)
        return JSONResponse(status_code=status_code, content=response.model_dump())

    @staticmethod
    def no_content(status_code: int = status.HTTP_204_NO_CONTENT) -> FastAPIResponse:
        return FastAPIResponse(status_code=status_code)


class Status:
    OK = status.HTTP_200_OK
    CREATED = status.HTTP_201_CREATED
    ACCEPTED = status.HTTP_202_ACCEPTED
    NO_CONTENT = status.HTTP_204_NO_CONTENT
    BAD_REQUEST = status.HTTP_400_BAD_REQUEST
    UNAUTHORIZED = status.HTTP_401_UNAUTHORIZED
    FORBIDDEN = status.HTTP_403_FORBIDDEN
    NOT_FOUND = status.HTTP_404_NOT_FOUND
    CONFLICT = status.HTTP_409_CONFLICT
    UNPROCESSABLE_ENTITY = status.HTTP_422_UNPROCESSABLE_ENTITY
    TOO_MANY_REQUESTS = status.HTTP_429_TOO_MANY_REQUESTS
    INTERNAL_SERVER_ERROR = status.HTTP_500_INTERNAL_SERVER_ERROR
