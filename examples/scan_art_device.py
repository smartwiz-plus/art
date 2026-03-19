import json
import sys
import asyncio
from bleak import BleakScanner

PREFIX="SMARTWizArt-"
devices=[]
found_devices={}
def detection_callback(device, advertisement_data):
    local_name = advertisement_data.local_name or device.name
    if local_name and local_name.startswith(PREFIX):
        if local_name not in found_devices:
            found_devices[local_name] = device.address
            devices.append({'local_name': local_name})

async def scan():
    scanner = BleakScanner(detection_callback)
    await scanner.start()
    await asyncio.sleep(3.0)
    await scanner.stop()

if __name__ == "__main__":
    try:
        asyncio.run(scan())
    except Exception as e:
        message = f"scan failed: {str(e)}"
        resp_json = {"result": False, "message": message, "devices": []}
        print(json.dumps(resp_json, ensure_ascii=True))
        sys.exit(1)

    resp_json = {"result": True, "devices": devices}
    print(json.dumps(resp_json, ensure_ascii=True))
