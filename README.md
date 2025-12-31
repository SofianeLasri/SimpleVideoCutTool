# Simple Video Cut Tool

A simple desktop application for cutting and trimming video files using A-B markers on a timeline.

## Features

- Interactive video player with timeline visualization
- A-B marker placement for precise cutting
- Multiple cut regions support
- Hardware encoder detection (NVIDIA NVENC, Intel Quick Sync, AMD AMF)
- Real-time encoding progress
- Dark/Light theme support

## Requirements

- Python 3.x
- FFmpeg binaries (included in `ffmpeg/` directory for Windows)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python run.py
python run.py --debug  # Enable debug logging
```

## Build (Windows)

```bash
pyinstaller simple_video_cut.spec
```
