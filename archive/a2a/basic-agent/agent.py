from pydantic import BaseModel


class BasicAgent(BaseModel):
    async def invoke(self) -> str:
        return "Hello, World!"
