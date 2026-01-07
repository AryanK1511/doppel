import os

from dotenv import load_dotenv
from moviepy import CompositeVideoClip, TextClip, VideoFileClip

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

words_data = []
if transcript.words:
    for word in transcript.words:
        words_data.append(
            {"text": word.text, "start": word.start / 1000, "end": word.end / 1000}
        )
        print(f"[{word.start / 1000:.2f}s - {word.end / 1000:.2f}s] {word.text}")

video_path = "/Users/aryankhurana/Developer/viralens/output_video.mp4"
video = VideoFileClip(video_path)

clips = [video]

for word_info in words_data:
    txt_clip = (
        TextClip(
            text=word_info["text"].upper(),
            font="Impact",
            font_size=70,
            size=video.size,
            color="yellow",
            stroke_color="black",
            stroke_width=3,
            method="caption",
        )
        .with_position("center")
        .with_start(word_info["start"])
        .with_duration(word_info["end"] - word_info["start"])
    )

    clips.append(txt_clip)

final_video = CompositeVideoClip(clips)

output_path = "/Users/aryankhurana/Developer/viralens/video_with_subtitles.mp4"
final_video.write_videofile(
    output_path, codec="libx264", audio_codec="aac", fps=video.fps
)

print(f"\n✅ Video with subtitles saved to: {output_path}")
