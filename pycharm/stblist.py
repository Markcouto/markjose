from GenericCodeFunctions import csvfunctions
import requests
import csv
from datetime import datetime
from Techex import mwfunctions
import argparse
#from Techex import mwcoreconfig #Uncomment once that code package is a libary not an executible peice of code!


def mwcore_list_all_devices(mwcore_address, BearerKey):
    functional_url = "/api/devices?limit=-1"
    url = mwfunctions.urlbuild(functional_url, mwcore_address)
    all_devices = mwget(url, BearerKey)
    return all_devices.json()["rows"]


def mwget(url, BearerKey):
    print ("Sending get request:\nURL: {}".format(url))
    resp = requests.get(url, headers={"Authorization": BearerKey, "Content-Type": "application/json"})#Post message to run the URL provided.
    #print ("{} - {} - {}".format(resp, resp.reason, resp.content))
    return resp


#mwcore_address = "sis.techex.co.uk"
#api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiI1YzU4MDU3MjQyZGRmMjAzZGE2N2ZhMTUiLCJjcmVhdGVkQXQiOiIyMDE5LTAyLTA0VDA5OjI3OjE0LjUyMFoiLCJ1cGRhdGVkQXQiOiIyMDE5LTAyLTA0VDA5OjI3OjUyLjY0NFoiLCJ1c2VybmFtZSI6InRlY2hleCIsImFkbWluIjp0cnVlLCJwcm92aWRlciI6ImxvY2FsIiwiX192IjowLCJkZXZpY2VzIjpbXSwibG9nb25MaW1pdCI6MCwibG9nb25MaW1pdGVkIjpmYWxzZSwiZGV2aWNlTGltaXQiOjAsImRldmljZUxpbWl0ZWQiOmZhbHNlLCJwZXJtaXNzaW9ucyI6eyJkZXZpY2VzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWUsInJlZnJlc2giOnRydWUsInJlYm9vdCI6dHJ1ZSwidXBncmFkZSI6dHJ1ZX0sImNoYW5uZWxzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWV9LCJtd2VkZ2VzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWV9LCJjYXRlZ29yaWVzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWV9LCJ1c2VycyI6eyJyZWFkIjp0cnVlLCJ3cml0ZSI6dHJ1ZSwiZGVsZXRlIjp0cnVlfSwicGFja2FnZXMiOnsicmVhZCI6dHJ1ZSwid3JpdGUiOnRydWUsImRlbGV0ZSI6dHJ1ZX0sInVzZXJHcm91cHMiOnsicmVhZCI6dHJ1ZSwid3JpdGUiOnRydWUsImRlbGV0ZSI6dHJ1ZX0sIm92ZXJsYXlzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWV9LCJnZW9mZW5jZXMiOnsicmVhZCI6dHJ1ZSwid3JpdGUiOnRydWUsImRlbGV0ZSI6dHJ1ZX0sInByb2dyYW1tZXMiOnsicmVhZCI6dHJ1ZSwid3JpdGUiOnRydWUsImRlbGV0ZSI6dHJ1ZX0sInRhc2tzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWV9LCJzeXN0ZW0iOnsicmVhZCI6dHJ1ZSwid3JpdGUiOnRydWV9fSwiaWF0IjoxNjAwMDg1Nzg5fQ.VNi5I3uapS5UvA5ReotMKZe9DeRdJFlYhD7Xkw1nxoI"

mwcore_address = input("Please provide the MWCore address:")
api_key = input("Please provide the API key for the related MWCore")
BearerKey = "Bearer {}".format(api_key)





rows_of_devices = mwcore_list_all_devices(mwcore_address, BearerKey)


export_devices = []
for device in rows_of_devices:
    device_dict = {
        "name": device.get("name", "")
    }

    device_dict["online"] = device.get("online", False)
    device_dict["external_ip"] = device.get("network", {}).get("externalIp", "")
    device_dict["internal_ip"] = device.get("network", {}).get("ip", "")
    try:
        device_dict["channel"] = device.get("channel", {}).get("name", "")
    except:
        device_dict["channel"] = ""
    device_dict["version"] = device["version"]
    device_dict["location"] = device.get("location", "")
    device_dict["serial"] = device["serial"]
    device_dict["last_check_in"] = device["updatedAt"]
    export_devices.append(device_dict)

now = datetime.now()
now_string = now.strftime("%H-%M-%d-%m-%Y")

with open('inputdata/stblist{}.csv'.format(now_string), 'w', newline='') as output_file:
    dict_writer = csv.DictWriter(output_file, export_devices[0].keys(), delimiter=";")
    dict_writer.writeheader()
    dict_writer.writerows(export_devices)
