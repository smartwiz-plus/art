import blufi
import sys
import json
import logging

# install pyBlufi
# pip install git+https://github.com/someburner/pyBlufi.git

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python3 disconnect_wifi.py <local_name>")
        sys.exit(1)

    try:
        WIFI_CREDS = {
            'ssid': "",
            'pass': ""
        }
        logging.getLogger("blufi").setLevel(logging.ERROR)

        local_name = sys.argv[1]
        client = blufi.BlufiClient()
        client.connectByName(local_name)
        client.negotiateSecurity()
        client.setPostPackageLengthLimit(256)
        client.postDeviceMode(blufi.OP_MODE_STA)
        client.postStaWifiInfo(WIFI_CREDS)
        resp_json = {"result": True, "message": ""}
        print(json.dumps(resp_json, ensure_ascii=True))
        sys.exit(0)
    except Exception as e:
        message = f"disconnect from {local_name} failed: {str(e)}"
        resp_json = {"result": False, "message": message}
        print(json.dumps(resp_json, ensure_ascii=True))
        sys.exit(-1)