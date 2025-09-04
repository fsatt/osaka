import os
import glob
import subprocess
from enum import Enum

import yt_dlp
from moviepy import VideoFileClip
from moviepy.video.fx import Crop
from PIL import Image

from config_loader import runtime_config, config


class MediaType(Enum):
    VIDEO = "video"
    AUDIO = "audio"
    IMAGE = "image"
    UNKNOWN = "unknown"


def get_media_type(ext):
    ext = ext.lstrip('.')  # Remove the dot
    
    # Video extensions
    video_extensions = {
        'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm', 'm4v', 
        'mpg', 'mpeg', '3gp', 'ogv', 'ts', 'mts', 'm2ts'
    }
    
    # Audio extensions
    audio_extensions = {
        'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus', 
        'aiff', 'au', 'ra', 'amr', 'ac3'
    }
    
    # Image extensions
    image_extensions = {
        'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'webp', 
        'svg', 'ico', 'psd', 'raw', 'cr2', 'nef', 'dng'
    }
    
    if ext in video_extensions:
        return MediaType.VIDEO
    elif ext in audio_extensions:
        return MediaType.AUDIO
    elif ext in image_extensions:
        return MediaType.IMAGE
    else:
        return MediaType.UNKNOWN


def is_url(input_string):
    # Simple URL detection - check for common URL schemes
    url_schemes = ["http://", "https://", "ftp://", "ftps://"]
    return any(input_string.startswith(scheme) for scheme in url_schemes)


def format_path(path):
    if not path:
        return '""'

    # Normalize path separators to the OS standard
    normalized_path = os.path.normpath(path)

    # Add quotes around the path
    return f'"{normalized_path}"'


def download_media(url, output_path):
    # First try yt-dlp
    if config.BROWSER:
        ydl_opts = {
            "outtmpl": f"{output_path}/raw.%(ext)s",
            "format": "best", 
            "noplaylist": True,
            "cookiesfrombrowser": (config.BROWSER,),
        }
    else:
        ydl_opts = {
            "outtmpl": f"{output_path}/raw.%(ext)s",
            "format": "best", 
            "noplaylist": True,
        }
    
    try:
        print("Attempting download with yt-dlp...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            ext = info.get("ext")
            downloaded_path = f"{output_path}/raw.{ext}"
            
            if os.path.exists(downloaded_path):
                print(f"Downloaded via yt-dlp: {format_path(downloaded_path)}")
                return downloaded_path
                
    except Exception:
        print(f"yt-dlp failed")
        print("Attempting download with gallery-dl...")
        
        # Fallback to gallery-dl
        try:
            # Build gallery-dl command with cookie support
            cmd = [
                "gallery-dl",
                "--dest", output_path,
                "--filename", "raw.{extension}",
            ]
            
            # Add cookie support if browser is configured
            if config.BROWSER:
                cmd.extend(["--cookies-from-browser", config.BROWSER])
                print(f"Using cookies from {config.BROWSER}")
            
            cmd.append(url)
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("gallery-dl output:", result.stdout)
            
            # Find the downloaded file
            downloaded_files = glob.glob(f"{output_path}/*/*/raw.*")
            if downloaded_files:
                downloaded_path = downloaded_files[0]
                print(f"Downloaded via gallery-dl: {format_path(downloaded_path)}")
                return downloaded_path
            else:
                print("gallery-dl completed but no file found")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"gallery-dl failed: {e}")
            print("gallery-dl stderr:", e.stderr)
            return None
        except FileNotFoundError:
            print("gallery-dl not found. Install with: pip install gallery-dl")
            return None
        except Exception as e:
            print(f"Unexpected error with gallery-dl: {e}")
            return None
    
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
        ext = original_ext if original_ext else ".mp4"
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


def crop_image(image_path, output_path, x, y, width, height):
    try:
        print(
            f"Cropping image with coordinates: X={x}, Y={y}, Width={width}, Height={height}"
        )

        if not image_path:
            print("No image path provided - cannot crop image")
            return

        # Open the image
        with Image.open(image_path) as img:
            # Define the crop box (left, top, right, bottom)
            crop_box = (x, y, x + width, y + height)
            
            # Crop the image
            cropped_img = img.crop(crop_box)
            
            # Generate output filename using the same extension as the input
            _, original_ext = os.path.splitext(image_path)
            # Default to .png if no extension found
            ext = original_ext if original_ext else ".png"
            cropped_image_path = f"{output_path}/cropped{ext}"
            
            print(f"Saving cropped image to: {format_path(cropped_image_path)}")
            
            # Save the cropped image
            cropped_img.save(cropped_image_path)
            
            print(
                f"Image cropping completed! Output saved to: {format_path(cropped_image_path)}"
            )
            
            return cropped_image_path

    except ValueError:
        print("Please enter valid integer values for cropping coordinates.")
    except Exception as e:
        print(f"Error during image cropping: {e}")
        return None
