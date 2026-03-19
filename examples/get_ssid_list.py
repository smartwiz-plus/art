import blufi
import json
import os
import sys
import time
import logging

# install pyBlufi
# pip install git+https://github.com/someburner/pyBlufi.git

def on_custom_data_receive(data):
    global response
    response = data.decode('utf-8')

if __name__ == "__main__":
    global response

    if len(sys.argv) != 2:
        print(f"Usage: python3 get_ssid_list.py <local_name>")
        sys.exit(1)

    try:
        agent = "smartwizart-cli"
        local_name = sys.argv[1]
        response = ""

        logging.getLogger("blufi").setLevel(logging.ERROR)
        client = blufi.BlufiClient()
        client.onCustomData = on_custom_data_receive
        client.connectByName(local_name)
        client.negotiateSecurity()

        # Cap pkt size. See README.md about MTU
        client.setPostPackageLengthLimit(256)

        request = {"command": "get_ssid_list_request", "args": None, "agent": agent}
        json_request = json.dumps(request, ensure_ascii=True) 
        request_bata = json_request.encode('utf-8')
        client.postCustomData(data=request_bata)
        time.sleep(5)
        if response == "":
            print(f"Error: response is empty", file=sys.stderr)
            sys.exit(-1)

        print(response)
        sys.exit(0)
    except Exception as e:
        message = f"connect to {local_name} failed: {str(e)}"
        resp_json = {"result": False, "message": message}
        print(json.dumps(resp_json, ensure_ascii=True))
        sys.exit(-1)
