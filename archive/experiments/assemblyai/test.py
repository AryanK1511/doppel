import os

from dotenv import load_dotenv

import assemblyai as aai

load_dotenv()

api_key = os.getenv("ASSEMBLYAI_API_KEY")
if not api_key:
    raise ValueError("ASSEMBLYAI_API_KEY not found in environment variables")

aai.settings.api_key = api_key

audio_url = "https://nojdwshibrejmzwdoptq.supabase.co/storage/v1/object/public/monkeybun-public/output.mp3"

transcript = aai.Transcriber().transcribe(audio_url)

if transcript.status == "error":
    raise RuntimeError(f"Transcription failed: {transcript.error}")

if transcript.words:
    for word in transcript.words:
        start_time = word.start / 1000
        end_time = word.end / 1000
        print(f"[{start_time:.2f}s - {end_time:.2f}s] {word.text}")
else:
    print(transcript.text)
