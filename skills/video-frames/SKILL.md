---
name: video-frames
description: Extract frames or short clips from videos using ffmpeg. Use when Z wants to sample frames, create GIFs, extract thumbnails, or build datasets from video. Requires ffmpeg installed (sudo apt install ffmpeg).
---

# Video Frames Skill

Extract frames, create clips, generate GIFs — all via ffmpeg.

## Prerequisites

```bash
sudo apt install ffmpeg
```

## Extract Frames

```bash
# Extract every Nth frame to a directory
ffmpeg -i video.mp4 -vf "select='not(mod(n\,100))'" -vsync vfr frames/%03d.png

# Extract single frame at timestamp
ffmpeg -ss 00:01:30 -i video.mp4 -frames:v 1 thumbnail.jpg

# Extract every frame
ffmpeg -i video.mp4 frames/%04d.png
```

## Create Clips

```bash
# Cut 10 seconds from 00:01:00
ffmpeg -ss 00:01:00 -i video.mp4 -t 10 -c copy clip.mp4

# Cut with re-encoding (for precise cuts)
ffmpeg -ss 00:01:00 -i video.mp4 -t 10 -c:v libx264 -c:a aac clip.mp4
```

## Generate GIF

```bash
# Low-quality quick GIF
ffmpeg -ss 30 -t 5 -i video.mp4 -vf "fps=10,scale=480:-1:flags=lanczos" gif.gif

# High-quality GIF
ffmpeg -ss 30 -t 5 -i video.mp4 \
  -vf "fps=15,scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" output.gif
```

## Use Cases

- **Dataset building** — sample frames for ML training
- **Thumbnail generation** — extract key frames as previews
- **Clip sharing** — cut moments from longer videos
- **GIF creation** — social media ready short loops

## Notes

- Use `-ss` before `-i` for fast seeking (input seeking)
- `select` filter is frame-selective, not time-based
- palettegen/paletteuse gives best GIF quality but is slower
