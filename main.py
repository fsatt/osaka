import yt_dlp
from moviepy import VideoFileClip
from PIL import Image

from gui import run_gui


def download_video(url, output_path="temp"):
    ydl_opts = {
        "outtmpl": f"{output_path}/%(title)s.%(ext)s",
        "format": "bestvideo+bestaudio/best",
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title")
        ext = info.get("ext")

        return f"{output_path}/{title}.{ext}"


def get_first_frame(video_path, output_path="temp"):
    try:
        clip = VideoFileClip(video_path)
        frame_array = clip.get_frame(0)
        image = Image.fromarray(frame_array)
        image.save(f"{output_path}/first_frame.jpg")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # DEBUG
    # video_path = download_video("https://www.instagram.com/p//")
    video_path = "temp/Video by exotic_cars_b.d.mp4"

    # first_frame = get_first_frame(video_path)
    first_frame = "temp/first_frame.jpg"

    run_gui(first_frame)
