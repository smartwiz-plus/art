import blufi
import json
import sys
import time
import logging
# install pyBlufi
# pip install git+https://github.com/someburner/pyBlufi.git
def on_custom_data_receive(data):
    global response
    response = data.decode('utf-8')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python3 get_status.py <local_name>")
        sys.exit(1)

    local_name = sys.argv[1]
    agent = "smartwizart-cli"
    response = ""

    try:
        logging.getLogger("blufi").setLevel(logging.ERROR)
        client = blufi.BlufiClient()
        client.onCustomData = on_custom_data_receive
        client.connectByName(local_name)
        client.negotiateSecurity()

        # Cap pkt size. See README.md about MTU
        client.setPostPackageLengthLimit(256)

        request = {"command": "get_device_info_request", "args": None, "agent": agent}
        json_request = json.dumps(request, ensure_ascii=True) 
        request_bata = json_request.encode('utf-8')
        client.postCustomData(data=request_bata)
        time.sleep(1)
        if response == "":
            resp_json = {"result": False, "message": "no response"}
            print(json.dumps(resp_json, ensure_ascii=True))
            sys.exit(-1)
        print(response)
    except Exception as e:
        message = f"connect to {local_name} failed: {str(e)}"
        resp_json = {"result": False, "message": message}
        print(json.dumps(resp_json, ensure_ascii=True))
    sys.exit(0)
