from motor.motor_asyncio import AsyncIOMotorClient
from src.common.config import settings
from src.common.logger import logger


class MongoDBClient:
    def __init__(self):
        self.client: AsyncIOMotorClient | None = None
        self.db = None

    async def connect(self):
        if self.client is None:
            self.client = AsyncIOMotorClient(settings.MONGODB_URI)
            self.db = self.client.get_default_database()
            logger.info("Connected to MongoDB")

    async def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("Disconnected from MongoDB")

    @property
    def agents(self):
        if self.db is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self.db.agents

    @property
    def conversations(self):
        if self.db is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self.db.conversations

    @property
    def matches(self):
        if self.db is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        return self.db.matches


mongodb_client = MongoDBClient()
