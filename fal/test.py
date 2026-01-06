from pathlib import Path

import fal_client
import requests
from dotenv import load_dotenv

load_dotenv()


def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs:
            print(log["message"])


result = fal_client.subscribe(
    "veed/fabric-1.0/fast",
    arguments={
        "image_url": "https://nojdwshibrejmzwdoptq.supabase.co/storage/v1/object/public/monkeybun-public/IMG_4503.JPG",
        "audio_url": "https://nojdwshibrejmzwdoptq.supabase.co/storage/v1/object/public/monkeybun-public/output.mp3",
        "resolution": "720p",
    },
    with_logs=True,
    on_queue_update=on_queue_update,
)
print(result)

video_url = result.get("video", {}).get("url") or result.get("video_url")
if not video_url:
    video_url = result.get("url")

if video_url:
    print(f"Downloading video from: {video_url}")
    response = requests.get(video_url)
    response.raise_for_status()

    output_path = Path("output_video.mp4")
    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"Video saved to: {output_path.absolute()}")
else:
    print("No video URL found in result")
    print(f"Result structure: {result}")
