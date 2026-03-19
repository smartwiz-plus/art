import os
from pathlib import Path
import subprocess
import shutil
import shutil
import sys
import requests
import epd_util
from PIL import Image, ImageDraw, ImageFont
from cryptography.hazmat.primitives.serialization import load_der_private_key
from cryptography.hazmat.primitives import serialization

def get_weather_from_ha():
    """Home Assistantから天気情報を取得"""
    access_token = os.getenv("HA_ACCESS_TOKEN")
    url = "http://homeassistant.local:8123/api/states/weather.forecast_zi_zhai"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        weather_data = response.json()
        return weather_data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 display_weather_info.py <device_id>")
        sys.exit(1)

    if not shutil.which("convert"):
        print("Need install imagemagick.")
        sys.exit(1)

    try:
        weather = get_weather_from_ha()
        if weather:
            # state
            state = weather['state']

            # attributes
            # temperature, temperature_unit
            temperature = weather['attributes']['temperature']
            temperature_unit = weather['attributes']['temperature_unit']

            # humidity, humidity_unit
            humidity = weather['attributes']['humidity']

            image = Image.open("frame.png")
            draw = ImageDraw.Draw(image)

            # use NotoSansCJK-Regular.ttc font
            font = ImageFont.truetype("NotoSansCJK-Regular.ttc", 40)

            # write state, temperature, humidity on image
            draw.text((280, 250), state, fill=(240, 120, 0), font=font)
            draw.text((280, 320), f"{temperature} {temperature_unit} / {humidity} %", fill=(240, 120, 0), font=font)
            
            image.save("weather.png")
            
            input_image = Path("weather.png")
            output_image = Path("weather.s6")
            if not input_image.exists():
                print("File not found.")
                sys.exit(1)
            dither_png = input_image.with_suffix(input_image.suffix + ".dither.png")

            # dither + remap
            subprocess.run([
                "convert",
                str(input_image),
                "-colorspace", "RGB",
                "-dither", "FloydSteinberg",
                "-define", f"dither:diffusion-amount=100%",
                "-remap", "palette.png",
                str(dither_png)
            ])

            # delete weather.png
            input_image.unlink(missing_ok=True)

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

            dither_png.unlink(missing_ok=True)
            device_id = sys.argv[1]
            s6_image_file_path = output_image

            private_key_path = f"{os.getcwd()}/app_private.der"
            if not os.path.exists(private_key_path):
                print("app_private.der not found")
                sys.exit(-1)

            app_private_key = None
            with open(private_key_path, "rb") as f:
                app_private_key = load_der_private_key(f.read(), password=None)

            api_url = f"http://smartwiz-art-{device_id}.local/api/control/request"

            epd_util.initialize_request_id_file(os.getcwd(), 0)
            request_id = epd_util.get_request_id(True)
            request_utc = epd_util.get_current_request_utc()

            epd_public_key_file_path = f"{os.getcwd()}/epd_public_key.der"
            epd_public_key =None
            with open(epd_public_key_file_path, "rb") as f:
                epd_public_key_bin = f.read()

            cbc_iv = device_id[16:].encode('ascii')
            caption = ""
            orientation = 0

            # encrypt image
            x_offset = 0
            y_offset = 0
            witdh = 800
            height = 480
            epd_public_key = serialization.load_der_public_key(epd_public_key_bin)
            encrypted_image = epd_util.make_encrypted_image(0, s6_image_file_path, epd_public_key, cbc_iv, x_offset, y_offset, witdh, height, caption, orientation)

            # =====================================================
            # upload image
            # =====================================================
            epd_util.initialize_request_id_file(os.getcwd(), 0)
            request_id = epd_util.get_request_id(True)
            request_utc = epd_util.get_current_request_utc()
            response = epd_util.send_image_upload_request(api_url, request_id, request_utc, app_private_key, encrypted_image)
            json_resp = response.json()
            print(json_resp)
            file = json_resp["file"]

            # delete weather.s6
            output_image.unlink(missing_ok=True)

            # =====================================================
            # display image request
            # =====================================================
            request_id  = epd_util.get_request_id(True)
            request_utc = epd_util.get_current_request_utc()
            user_name   = "smartwizart-cli-user"
            user_comment = "user image by smartwizart-cli"
            response = epd_util.send_display_request(api_url, request_id, request_utc, app_private_key, file, user_name, user_comment)
            json_resp = response.json()
            print(json_resp)

            sys.exit(0)

        else:
            print("Failed to retrieve weather data.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    