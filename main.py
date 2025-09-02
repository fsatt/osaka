import argparse
import shutil
import sys
import os

import yt_dlp
from moviepy import VideoFileClip
from PIL import Image

from config_loader import config
from gui import run_gui


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


def main():
    parser = argparse.ArgumentParser(
        description="Osaka - Video Cropping Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download from URL and crop with GUI (default)
  osaka "https://www.instagram.com/p/example/" "my_video"
  
  # Use local video file and crop with GUI  
  osaka --video "path/to/video.mp4" "output"
  
  # Download only, skip cropping
  osaka --nocrop "https://www.instagram.com/p/example/" "my_video"
  
  # Keep GUI open after cropping and keep temporary files
  osaka --keep-gui --keep-temp "url" "output"
        """,
    )

    # Video source option
    parser.add_argument(
        "--video", "-v", action="store_true", help="Use local video file instead of URL"
    )

    # No crop flag - skip GUI and just download/copy
    parser.add_argument(
        "--nocrop",
        "-n",
        action="store_true",
        help="Skip cropping, just download the video",
    )

    # Keep GUI open after cropping
    parser.add_argument(
        "--keep-gui",
        "-k",
        action="store_true",
        help="Keep GUI open after crop button is clicked",
    )

    # Keep temporary files
    parser.add_argument(
        "--keep-temp",
        "-t",
        action="store_true",
        help="Keep temporary files (don't cleanup at end)",
    )

    # Positional arguments
    parser.add_argument(
        "input", help="Video URL or file path (use --video for file path)"
    )
    parser.add_argument("output", help="Output file name")

    args = parser.parse_args()

    # Create temp directory if it doesn't exist
    os.makedirs(config.TEMP_DIR, exist_ok=True)
    os.makedirs(f"{config.TEMP_DIR}/{args.output}", exist_ok=True)

    # Handle input
    if args.video:
        # Local video file
        video_path = args.input
        if not os.path.exists(video_path):
            print(f"Error: Video file '{video_path}' not found")
            sys.exit(1)
        print(f"Using local video: {video_path}")
    else:
        # Download from URL
        print(f"Downloading video from: {args.input}")
        video_path = download_video(
            args.input, args.output, f"{config.TEMP_DIR}/{args.output}"
        )
        if not video_path:
            print("Error: Failed to download video")
            sys.exit(1)
    path_root, ext = os.path.splitext(video_path)

    # Handle cropping vs no-crop
    if not args.nocrop:
        # Generate first frame for GUI and launch cropping interface
        print("Extracting first frame...")
        first_frame = get_first_frame(
            video_path, args.output, f"{config.TEMP_DIR}/{args.output}"
        )
        if not first_frame:
            print("Error: Could not extract first frame")
            sys.exit(1)

        # Launch GUI for cropping
        print("Launching GUI for cropping...")
        exit_code, gui = run_gui(
            first_frame,
            video_path,
            f"{config.TEMP_DIR}/{args.output}",
            keep_open=args.keep_gui,
        )

        # Wait for crop thread to complete if it exists
        crop_thread = gui.get_crop_thread()
        if crop_thread:
            print("Waiting for crop process to complete...")
            crop_thread.join()  # Wait for the thread to finish
            print("Crop process completed!")

        video_path = f"{path_root}_cropped{ext}"

        if exit_code == 0:
            print("GUI closed successfully")
        else:
            print(f"GUI closed with error code: {exit_code}")

    try:
        print(f"Copying video to: {args.output}{ext}")
        shutil.copy2(video_path, f"{config.OUTPUT_DIR}/{args.output}{ext}")
        print(f"Video saved as: {args.output}{ext}")
    except FileNotFoundError:
        print(f"No video found at {video_path}, nothing to copy.")

    # Cleanup temporary files unless --keep-temp flag is used
    if not args.keep_temp:
        print("Cleaning up temporary files...")
        try:
            # Remove the entire temporary directory for this output
            temp_dir_path = f"{config.TEMP_DIR}/{args.output}"
            if os.path.exists(temp_dir_path):
                shutil.rmtree(temp_dir_path)
                print(f"Removed temporary directory: {temp_dir_path}")
        except Exception as e:
            print(f"Warning: Could not cleanup some temporary files: {e}")
    else:
        print("Temporary files kept as requested")


if __name__ == "__main__":
    # Check if any command line arguments were provided
    if len(sys.argv) > 1:
        main()
    else:
        print("Oh mai gah")
