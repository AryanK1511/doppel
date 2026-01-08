from pydantic import BaseModel


class ContentStrategistAgent(BaseModel):
    async def invoke(self) -> str:
        return "Here is a content strategy for your blog post: [content strategy]"
