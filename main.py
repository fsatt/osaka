import argparse
import gc
import os
import shutil
import sys
import time

from config_loader import config, runtime_config
from gui import run_gui
from video_utils import download_video, get_first_frame, format_path


def is_url(input_string):
    # Simple URL detection - check for common URL schemes
    url_schemes = ["http://", "https://", "ftp://", "ftps://"]
    return any(input_string.startswith(scheme) for scheme in url_schemes)


def main():
    parser = argparse.ArgumentParser(
        description="Osaka - Video Cropping Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download from URL and crop with GUI
  osaka "https://www.instagram.com/p/example/" "my_video"
  
  # Use local video file and crop with GUI  
  osaka "path/to/video.mp4" "output"
  
  # Download only, skip cropping
  osaka --nocrop "https://www.instagram.com/p/example/" "my_video"
  
  # Keep GUI open after cropping and keep temporary files
  osaka --keep-gui --keep-temp "input" "output"
        """,
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
    parser.add_argument("input", help="Video URL or local file path (auto-detected)")
    parser.add_argument("output", help="Output file name")

    args = parser.parse_args()

    # Set runtime configuration based on command line flags
    runtime_config.set_keep_temp(args.keep_temp)

    # Create temp directory if it doesn't exist
    os.makedirs(config.TEMP_DIR, exist_ok=True)
    os.makedirs(f"{config.TEMP_DIR}/{args.output}", exist_ok=True)

    # Handle input - auto-detect URL vs file path
    if is_url(args.input):
        # Download from URL
        print(f"Downloading video from: {args.input}")
        video_path = download_video(args.input, f"{config.TEMP_DIR}/{args.output}")
        if not video_path:
            print("Error: Failed to download video")
            sys.exit(1)
    else:
        # Local video file
        video_path = args.input
        if not os.path.exists(video_path):
            print(f"Error: Video file {format_path(video_path)} not found")
            sys.exit(1)
        print(f"Using local video: {format_path(video_path)}")
    path_root, ext = os.path.splitext(video_path)

    # Handle cropping vs no-crop
    if not args.nocrop:
        # Generate first frame for GUI and launch cropping interface
        print("Extracting first frame...")
        first_frame = get_first_frame(video_path, f"{config.TEMP_DIR}/{args.output}")
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

        # Cleanup GUI resources before deleting temporary files
        gui.cleanup_resources()

        finished_vid = f"{config.TEMP_DIR}/{args.output}/cropped{ext}"

        if exit_code == 0:
            print("GUI closed successfully")
        else:
            print(f"GUI closed with error code: {exit_code}")

    try:
        print(
            f"Copying video to: {format_path(f'{config.OUTPUT_DIR}/{args.output}{ext}')}"
        )
        shutil.copy2(finished_vid, f"{config.OUTPUT_DIR}/{args.output}{ext}")
        print(
            f"Video saved as: {format_path(f'{config.OUTPUT_DIR}/{args.output}{ext}')}"
        )
    except FileNotFoundError:
        print(f"No video found at {format_path(finished_vid)}, nothing to copy.")

    # Cleanup temporary files unless --keep-temp flag is used
    if not args.keep_temp:
        print("Cleaning up temporary files...")
        try:
            # Force garbage collection to ensure all file handles are released
            gc.collect()
            time.sleep(0.1)  # Small delay to ensure resources are released

            # Remove the entire temporary directory for this output
            temp_dir_path = f"{config.TEMP_DIR}/{args.output}"
            if os.path.exists(temp_dir_path):
                shutil.rmtree(temp_dir_path)
                print(f"Removed temporary directory: {format_path(temp_dir_path)}")
        except Exception as e:
            print(f"Warning: Could not cleanup some temporary files: {e}")
    else:
        print("Temporary files kept as requested")


if __name__ == "__main__":
    # Check if any command line arguments were provided
    if len(sys.argv) > 1:
        main()
    else:
        print("Oh my gah!")
        print("""
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣤⣤⣤⣤⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣠⡶⡿⢿⣿⣛⣟⣿⡿⢿⢿⣷⣦⡀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢰⣯⣷⣿⣿⣿⢟⠃⢿⣟⣿⣿⣾⣷⣽⣺⢆⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢸⣿⢿⣾⢧⣏⡴⠀⠈⢿⣘⣿⢿⣿⣿⣿⣿⡆⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢹⣿⢠⡶⠒⢶⠀⠀⣠⠒⠒⠢⡀⢿⣿⣿⣿⡇⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣿⣿⠸⣄⣠⡾⠀⠀⠻⣀⣀⡼⠁⢸⣿⣿⣿⣿⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⠀⠀⠀
⠀⠀⠀⠀⠀⢰⣿⣿⠀⠀⠀⡔⠢⠤⠔⠒⢄⠀⠀⢸⣿⣿⣿⣿⡇⠀⠀⠀
⠀⠀⠀⠀⠀⢸⣿⣿⣄⠀⠸⡀⠀⠀⠀⠀⢀⡇⠠⣸⣿⣿⣿⣿⡇⠀⠀⠀
⠀⠀⠀⠀⠀⢸⣿⣿⣿⣷⣦⣮⣉⢉⠉⠩⠄⢴⣾⣿⣿⣿⣿⡇⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢸⣿⣿⢻⣿⣟⢟⡁⠀⠀⠀⠀⢇⠻⣿⣿⣿⣿⣿⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢸⠿⣿⡈⠋⠀⠀⡇⠀⠀⠀⢰⠃⢠⣿⡟⣿⣿⢻⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠸⡆⠛⠇⢀⡀⠀⡇⠀⠀⡞⠀⠀⣸⠟⡊⠁⠚⠌⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⡍⠨⠊⣒⠴⠀⡇⡴⠋⡋⢐⠐⠅⡀⠐⢠⠕⠂⢂⠀⠀⠀
              """)
        # Play sound in background using PowerShell (fire and forget)
        try:
            import subprocess

            sound_file = os.path.abspath("assets/sound/oh-my-gah.mp3")
            # Use PowerShell's MediaPlayer to play without UI
            ps_command = f'''
            Add-Type -AssemblyName presentationCore;
            $mediaPlayer = New-Object system.windows.media.mediaplayer;
            $mediaPlayer.open([uri]"{sound_file}");
            $mediaPlayer.Play();
            Start-Sleep -Seconds 2;
            '''
            subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden", "-Command", ps_command],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception as e:
            print(f"Could not play sound: {e}")
