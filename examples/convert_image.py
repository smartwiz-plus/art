#!/usr/bin/env python3
import sys
import subprocess
import shutil
from pathlib import Path
import sys
import os
from PIL import Image

def run(cmd):
    subprocess.check_call(cmd)

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 conver_image.py <input_image.jpg> <output_image.s6>")
        sys.exit(1)

    input_image = Path(sys.argv[1])
    output_image = Path(sys.argv[2])
    if not input_image.exists():
        print("File not found.")
        sys.exit(1)

    if not shutil.which("convert"):
        print("Need install imagemagick.")
        sys.exit(1)

    resize_png = input_image.with_suffix(input_image.suffix + ".resize.png")
    dither_png = input_image.with_suffix(input_image.suffix + ".dither.png")

    try:
        # resize
        run([
            "convert",
            str(input_image),
            "-resize", "800x480!",
            str(resize_png)
        ])

        # dither + remap
        run([
            "convert",
            str(resize_png),
            "-colorspace", "RGB",
            "-dither", "FloydSteinberg",
            "-define", f"dither:diffusion-amount=100%",
            "-remap", "palette.png",
            str(dither_png)
        ])

        # delete resized image
        resize_png.unlink(missing_ok=True)

        img = Image.open(dither_png).convert("RGBA")
        width, height = img.size
        raw = img.tobytes("raw", "BGRA")

        cfb = bytearray((width * height) // 2)

        index = 0
        for i in range(0, len(raw), 4):
            b = raw[i + 0]
            g = raw[i + 1]
            r = raw[i + 2]
            a = raw[i + 3]

            r = (r * a) // 255
            g = (g * a) // 255
            b = (b * a) // 255

            rgb = (r << 16) | (g << 8) | b

            if rgb == 0x000000:
                color = 0      # BLACK
            elif rgb == 0xFFFF00:
                color = 2      # YELLOW
            elif rgb == 0xFF0000:
                color = 3      # RED
            elif rgb == 0x0000FF:
                color = 5      # BLUE
            elif rgb == 0x00FF00:
                color = 6      # GREEN
            else:
                color = 1      # WHITE (default)

            if index & 1:
                cfb[index >> 1] |= color
            else:
                cfb[index >> 1] |= (color << 4)

            index += 1
            if index >= width * height:
                break

        if output_image:
            with open(output_image, "wb") as f:
                f.write(cfb)
                f.flush()
                os.fsync(f.fileno())

        sys.exit(0)
    except Exception as e:
        print(f"Convert failed: {e}")
        resize_png.unlink(missing_ok=True)
        dither_png.unlink(missing_ok=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
