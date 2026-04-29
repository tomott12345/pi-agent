---
name: image-reader
description: |
  Reads metadata from JPEG, PNG, GIF, and other ImageMagick-supported image files,
  returning format, dimensions, color depth, and related properties. Use when a user
  asks about the size, format, or technical details of an image file, or when you need
  to inspect image properties without opening a viewer.
license: MIT
compatibility: Linux/macOS (requires `identify` from ImageMagick)
metadata:
  author: "Thomas Ott"
  version: "1.0"
---

# Image Reader Skill

## Setup

1. **Install the prerequisite** (only needed once):

   ```bash
   # macOS (brew)  
   brew install imagemagick   # provides `identify`

   # Ubuntu/Debian  
   sudo apt-get install imagemagick
   ```

2. No additional Python packages are required.

## Usage

### 2.1 Read image details

```bash
/skill:image-reader <path-to-image>
```

*Result:* the skill prints the image's format, dimensions, color depth, and other details to STDOUT.

### 2.2 Example session

```bash
$ /skill:image-reader ./photo.jpg
Format: JPEG
Dimensions: 1920x1080
Color depth: 8-bit
```

## How it works

1. The CLI calls the skill with the image path as argument.
2. The skill’s entry script (`read_image.sh`) receives the path and runs `identify` on the file.
3. The output of `identify` is printed directly to STDOUT.
4. Errors (missing file, missing `identify`, etc.) are reported on STDERR.

## Notes & extensions

- **Supported formats** – JPEG, PNG, GIF, and other formats supported by ImageMagick.
- **Error handling** – If `identify` fails (e.g., invalid file), the script returns an error message.
- **Chunking** – Not applicable for single images, but for multiple images, the skill could process each file in sequence.