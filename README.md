# Osaka

A media download and editing tool.

## Installation

```bash
git clone https://github.com/fsatt/osaka.git
cd osaka
uv sync
cp config.example.py config.py
```

## Usage

```bash
# Crop a video file
python main.py /path/to/video.mp4 output_name

# Download and crop from URL
python main.py "https://www.youtube.com/watch?v=..." output_name
```

## Requirements

- Python 3.8+
- Dependencies managed via `pyproject.toml` and `uv.lock`

## License

MIT
