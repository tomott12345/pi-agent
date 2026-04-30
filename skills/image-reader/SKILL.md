---
name: image-reader
description: |
  Reads metadata from JPEG, PNG, GIF, and other ImageMagick-supported image files,
  returning format, dimensions, color depth, color space, file size, and related
  properties. Use when a user asks about the size, format, or technical details of
  an image file, or when you need to inspect image properties without opening a viewer.
license: MIT
compatibility: "macOS/Linux (requires ImageMagick — brew install imagemagick)"
metadata:
  author: "Thomas Ott"
  version: "1.1"
---

# Image Reader Skill

## Setup

Install ImageMagick (only needed once):

```bash
# macOS
brew install imagemagick

# Ubuntu/Debian
sudo apt-get install imagemagick
```

## Invocation

```
/image-reader [path-to-image]
```

Examples:
```
/image-reader ~/Downloads/photo.jpg
/image-reader /tmp/screenshot.png
/image-reader ~/Desktop/diagram.tiff
```

## Instructions for the model

### Step 1 — Run the script

```bash
bash /Users/ottt/.pi/agent/skills/image-reader/read_image.sh [path-to-image]
```

The script runs ImageMagick's `identify` command on the file and prints its raw output.

### Step 2 — Present the results

The `identify` command outputs one line per image (or one per frame for animated files).
A typical line looks like:

```
photo.jpg JPEG 1920x1080 1920x1080+0+0 8-bit sRGB 2.1MB 0.000u 0:00.000
```

Parse and report in a readable format:

| Property | Where it appears |
|---|---|
| **File name** | First token |
| **Format** | Second token (JPEG, PNG, GIF, WEBP, TIFF …) |
| **Dimensions** | `WxH` pixels |
| **Color depth** | e.g. `8-bit`, `16-bit` |
| **Color space** | e.g. `sRGB`, `CMYK`, `Gray` |
| **File size** | e.g. `2.1MB`, `450KB` |
| **Frames** | For animated GIFs, `identify` prints one line per frame — note the frame count |

### Step 3 — Note any anomalies

- If the format doesn't match the file extension, call it out
- If the image is very large (>20 MP or >50 MB), mention it
- For animated GIFs, report frame count and total size

## Error handling

| Condition | Response |
|---|---|
| File not found | Report the path; ask the user to confirm it |
| `identify` not installed | Suggest `brew install imagemagick` (macOS) or `sudo apt-get install imagemagick` |
| Unsupported format | Report the raw `identify` error |
| Permission denied | Ask the user to check file permissions |
