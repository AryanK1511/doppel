from src.database.mongodb.mongodb_client import MongoDBClient, mongodb_client


def get_mongodb_client() -> MongoDBClient:
    return mongodb_client
