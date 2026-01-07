import json
from io import BytesIO

from google.cloud import storage
from google.oauth2 import service_account
from src.common.config import settings
from src.common.logger import logger


class GCSClient:
    def __init__(self):
        service_account_info = json.loads(settings.GCP_SERVICE_ACCOUNT_KEY)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info
        )
        self.client = storage.Client(
            credentials=credentials, project=credentials.project_id
        )
        self.bucket = self.client.bucket(settings.GCP_BUCKET_NAME)
        logger.info(f"Initialized GCS client for bucket: {settings.GCP_BUCKET_NAME}")

    def upload_audio(self, file_bytes: bytes, filename: str) -> str:
        blob = self.bucket.blob(filename)
        blob.upload_from_file(BytesIO(file_bytes), content_type="audio/mpeg")
        blob.make_public()
        url = blob.public_url
        logger.info(f"Uploaded audio to GCS: {filename}")
        return url
