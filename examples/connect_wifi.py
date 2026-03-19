import blufi
import sys
import json
import logging

# install pyBlufi
# pip install git+https://github.com/someburner/pyBlufi.git

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"Usage: python3 connect_wifi.py <local_name> <ssid> <password>")
        sys.exit(1)

    local_name = sys.argv[1]
    WIFI_CREDS = {
        'ssid': sys.argv[2],
        'pass': sys.argv[3]
    }

    try:
        logging.getLogger("blufi").setLevel(logging.ERROR)
        client = blufi.BlufiClient()
        client.connectByName(local_name)
        client.negotiateSecurity()
        client.postDeviceMode(blufi.OP_MODE_STA)
        client.postStaWifiInfo(WIFI_CREDS)
        resp_json = {"result": True, "message": ""}
        print(json.dumps(resp_json, ensure_ascii=True))
        sys.exit(0)
    except Exception as e:
        message = f"connect to {local_name} failed: {str(e)}"
        resp_json = {"result": False, "message": message}
        print(json.dumps(resp_json, ensure_ascii=True))
        sys.exit(-1)

