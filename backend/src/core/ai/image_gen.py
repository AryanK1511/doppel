from google import genai
from src.common.config import settings
from src.common.logger import logger


def generate_image(prompt: str) -> bytes:
    logger.info(f"Generating image with prompt: {prompt}")
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=prompt,
    )

    for part in response.parts:
        if part.inline_data:
            return part.inline_data.data


# if __name__ == "__main__":
#     image = generate_image(
#         "Create a picture of a futuristic banana with neon lights in a cyberpunk city."
#     )
#     logger.info(f"Generated image: {image}")
#     with open("image.png", "wb") as f:
#         f.write(image)
