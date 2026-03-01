import os
from PIL import Image
import sys

src_dir = r"d:\Cavin Real\HackBA\Images"
# Next.js public directory
dest_dir = r"d:\Cavin Real\HackBA\wpdev\public\frames"

try:
    os.makedirs(dest_dir, exist_ok=True)
except Exception as e:
    print(f"Error creating directory: {e}")
    sys.exit(1)

# Get files and sort to ensure sequential frames
files = sorted([f for f in os.listdir(src_dir) if f.endswith('.png')])

if not files:
    print("No PNG files found in Images directory!")
    sys.exit(1)

print(f"Found {len(files)} PNGs. Converting first 120 frames to WEBP...")

count = 0
for i, file in enumerate(files[:120]):
    img_path = os.path.join(src_dir, file)
    try:
        with Image.open(img_path) as img:
            dest_filename = f"frame_{i}_delay-0.04s.webp"
            dest_path = os.path.join(dest_dir, dest_filename)
            img.save(dest_path, "WEBP", quality=85)
            count += 1
    except Exception as e:
        print(f"Error converting {file}: {e}")

print(f"Converted {count} images to WEBP successfully.")
