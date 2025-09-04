import argparse
import gc
import os
import shutil
import sys
import time

from config_loader import config, runtime_config
from gui import run_gui
from utils import download_media, format_path, is_url, get_media_type, MediaType


def main():
    parser = argparse.ArgumentParser(
        description="Osaka - Media Download and Editing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download from URL and crop with GUI
  osaka "https://www.instagram.com/p/example/" "my_media"
  
  # Use local media file and crop with GUI  
  osaka "path/to/media.mp4" "output"
  
  # Download only, skip cropping
  osaka --no-edit "https://www.instagram.com/p/example/" "my_media"
  
  # Keep GUI open after cropping and keep temporary files
  osaka --keep-gui --keep-temp "input" "output"
        """,
    )

    # No crop flag - skip GUI and just download/copy
    parser.add_argument(
        "--no-edit",
        "-n",
        action="store_true",
        help="Skip cropping, just download the media",
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
    parser.add_argument("input", help="Media URL or local file path (auto-detected)")
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
        print(f"Downloading media from: {args.input}")
        media_path = download_media(args.input, f"{config.TEMP_DIR}/{args.output}")
        if not media_path:
            print("Error: Failed to download media")
            sys.exit(1)
    else:
        # Local media file
        media_path = args.input
        if not os.path.exists(media_path):
            print(f"Error: File {format_path(media_path)} not found")
            sys.exit(1)
        print(f"Using local file: {format_path(media_path)}")
    
    path_root, ext = os.path.splitext(media_path)
    
    # Handle unsupported media types
    media_type = get_media_type(ext)
    if media_type == MediaType.UNKNOWN:
        print(f"Error: Unsupported media type: {ext}")
        sys.exit(1)
    if media_type == MediaType.AUDIO:
        print("No support for Audio files yet :)")
        sys.exit(1)
    print(f"Detected media type: {media_type.value}")

    # Handle edit vs no-edit
    if not args.no_edit:
        # Launch GUI for editing
        print("Launching GUI for editing...")
        exit_code, gui = run_gui(
            media_path=media_path,
            media_type=media_type,
            output_path=f"{config.TEMP_DIR}/{args.output}",
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

        result = f"{config.TEMP_DIR}/{args.output}/cropped{ext}"

        if exit_code == 0:
            print("GUI closed successfully")
        else:
            print(f"GUI closed with error code: {exit_code}")

    try:
        print(
            f"Copying {media_type.value.lower()} to: {format_path(f'{config.OUTPUT_DIR}/{args.output}{ext}')}"
        )
        shutil.copy2(result, f"{config.OUTPUT_DIR}/{args.output}{ext}")
        print(
            f"{media_type.value.capitalize()} saved as: {format_path(f'{config.OUTPUT_DIR}/{args.output}{ext}')}"
        )
    except FileNotFoundError:
        print(f"No {media_type.value.lower()} found at {format_path(result)}, nothing to copy.")

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
