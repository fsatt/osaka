import os

import yt_dlp
from moviepy import VideoFileClip
from moviepy.video.fx import Crop
from PIL import Image

from config_loader import runtime_config


def format_path(path):
    if not path:
        return '""'

    # Normalize path separators to the OS standard
    normalized_path = os.path.normpath(path)

    # Add quotes around the path
    return f'"{normalized_path}"'


def download_video(url, output_path):
    ydl_opts = {
        "outtmpl": f"{output_path}/raw.%(ext)s",
        "format": "bestvideo+bestaudio/best",
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        ext = info.get("ext")

        return f"{output_path}/raw.{ext}"


def get_first_frame(video_path, output_path):
    try:
        clip = VideoFileClip(video_path)
        frame_array = clip.get_frame(0)
        image = Image.fromarray(frame_array)
        frame_path = f"{output_path}/first_frame.jpg"
        image.save(frame_path)
        clip.close()
        return frame_path

    except Exception as e:
        print(f"An error occurred extracting first frame: {e}")
        return None


def crop_video(video_path, output_path, x, y, width, height):
    try:
        # Ensure dimensions are even numbers (required for H.264)
        if width % 2 == 1:
            width -= 1
            print(f"Adjusted width to {width} (must be even for H.264)")
        if height % 2 == 1:
            height -= 1
            print(f"Adjusted height to {height} (must be even for H.264)")

        print(
            f"Cropping video with coordinates: X={x}, Y={y}, Width={width}, Height={height}"
        )

        if not video_path:
            print("No video path provided - cannot crop video")
            return

        # Load the video
        clip = VideoFileClip(video_path)

        # Crop the video
        crop_effect = Crop(x1=x, y1=y, x2=x + width, y2=y + height)
        cropped_clip = clip.with_effects([crop_effect])

        # Generate output filename using the same extension as the input
        _, original_ext = os.path.splitext(video_path)
        # Default to .mp4 if no extension found, since we're using H.264/AAC codecs
        ext = original_ext if original_ext else '.mp4'
        cropped_video_path = f"{output_path}/cropped{ext}"

        print(f"Saving cropped video to: {format_path(cropped_video_path)}")

        # Create temp audio file path in the same directory as output
        temp_audio_path = f"{output_path}/temp-audio.m4a"

        # Write the cropped video with Windows-compatible settings
        cropped_clip.write_videofile(
            cropped_video_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=temp_audio_path,
            remove_temp=not runtime_config.keep_temp_files,
        )

        # Clean up
        cropped_clip.close()
        clip.close()

        print(
            f"Video cropping completed! Output saved to: {format_path(cropped_video_path)}"
        )

    except ValueError:
        print("Please enter valid integer values for cropping coordinates.")
    except Exception as e:
        print(f"Error during video cropping: {e}")
