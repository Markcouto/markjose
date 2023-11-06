import numpy as np
import json
import requests
from requests.auth import HTTPBasicAuth

from GenericCodeFunctions import csvfunctions, misc_functions
from datetime import datetime, timedelta
import copy
from Techex import mwfunctions
import time
import sys
import argparse


def mwpost_basic_auth (url, data):
    print("Sending post request:\nURL: {}\nData: {}".format(url, data))
    resp = requests.post(url, data=data, headers={"Content-Type": "application/json"}, auth=HTTPBasicAuth("techex", "DjkbGCjnexy8rLexNEdb"))#Post message to run the URL provided.
    if "20" not in str(resp.status_code):
        #Do this to re-try once
        time.sleep(1)
        resp = requests.post(url, data=data, headers={"Content-Type": "application/json"}, auth=HTTPBasicAuth("techex","DjkbGCjnexy8rLexNEdb"))  # Post message to run the URL provided.
    print ("{} - {} - {}".format(resp, resp.reason, resp.content))
    return resp


def mwcore_grafana_stbdata_pull(stb, hours, minuets=False):
    """
    Function to pull grafana data for a STB
    Only supports historic data from now back x number of hours.
    Not moving into mwfunctions as requires the basic auth
    :param stb: - ID from STB to query
    :param hours: int for the number of hours to look back over
    :return: dictionary key'd based on [STB_ID]-DATASET e.g 5d444fa539c98f0ddfed8f24-Bitrate
    """
    now = datetime.now()
    if minuets:
        then = now - timedelta(minutes=minuets)
    else:
        then = now - timedelta(hours=hours)
    now_string = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    then_string = then.strftime("%Y-%m-%dT%H:%M:%SZ")
    data = {
        "range": {
            "from": then_string,
            "to": now_string
        },
        "targets": [
            {"target": stb}
        ]

    }
    """
    Uncomment below for static query
    data = {
        "range": {
            "from": "2020-11-20T00:00:25z",
            "to": "2020-11-26T00:00:25z"
        },
        "targets": [
            {"target": stb}
        ]

    }
    """
    json_data = json.dumps(data)
    url = "https://sis.techex.co.uk/grafana/devices/query"
    data = mwpost_basic_auth(url, json_data)
    if data.status_code == 500:
        print ("Server had errors with STB {}".format(stb))
        return 500
    json_data = data.json()  # gets you values, epoch list of arrays e.g [[2230532,1605271971653],[2230606,1605272031652]]
    stb_datapoints = {}
    for dataset in json_data:
        if "Bitrate" in dataset["target"]:
            stb_datapoints["Bitrate"] = dataset["datapoints"]
        elif "rtt" in dataset["target"]:
            stb_datapoints["rtt"] = dataset["datapoints"]
        elif "discontinuityCounter" in dataset["target"]:
            stb_datapoints["discontinuityCounter"] = dataset["datapoints"]
        elif "unrecovered" in dataset["target"]:
            stb_datapoints["unrecovered"] = dataset["datapoints"]
    return stb_datapoints


def default_value(stb, BearerKey, value=0):
    stb["discontinuity"] = value
    stb["avg_discontinuity_hour"] = value
    stb["unrecovered"] = value
    stb["avg_unrecovered_hour"] = value
    stb["rtt"] = value
    stb["Bitrate"] = value
    stb["country_code"], stb["continent_code"], stb["country"], stb["continent"] = mwfunctions.get_stb_geo_location(
        BearerKey,
        stb["mwcore_address"],
        stb["id"],
        stb["public_ip"])
    stb["sye_delay"] = value


def stb_evaluate(stb, hours, BearerKey):
    stb_data = mwcore_grafana_stbdata_pull(stb["id"], int(hours))
    if not stb_data:
        print("didn't get any data so skipping")
        default_value(stb, BearerKey, 0)
        print("\n\n")
        return

    elif stb_data == 500:
        print("Server error")
        default_value(stb, BearerKey, "error 500")
        print("\n\n")
        return

    stb["country_code"], stb["continent_code"], stb["country"], stb["continent"] = mwfunctions.get_stb_geo_location(
        BearerKey,
        stb["mwcore_address"],
        stb["id"],
        stb["public_ip"])
    if debug:
        print("Simplyfing data for {}".format(stb["id"]))
    mwfunctions.grafana_stb_data_simplification(stb, copy.deepcopy(stb_data), debug=True)



def srt_latency_update(stb, stb_detail, min_latency):
    """
    Function to update a devices SRT latency and then possibly trigger a refresh
    Will set SRT latency based on rounded up figures of RTT from previous data evaluation
    Will finish off by setting the values for update and refresh back to false to prevent doing actions more than once
    :param stb:
    :return:
    """
    BearerKey = "Bearer {}".format(stb["api_key"])
    rtt = stb.get("rtt", False)
    syelatency = stb.get("sye_delay", False)
    ping_rtt = stb.get("ping_rtt", False)
    if "unreachable" in str(ping_rtt).lower():
        ping_rtt = False
    if not rtt and not syelatency and not ping_rtt:
        print("No data to base the SRT latency setting on, we need either RTT data or previously set SYE latency!")

    if rtt:
        #Need to calculate the latency to be ~3x the rtt or a safe min of 300
        srt_latency = max(min_latency, misc_functions.round_up_10(misc_functions.round_up_10(rtt)*3))
    elif ping_rtt:
        srt_latency = max(min_latency, misc_functions.round_up_10(misc_functions.round_up_10(int(ping_rtt)) * 4))
        #Adding increased margin of error as ping results could be inaccurate so *4 instead of 3!
    elif syelatency:
        srt_latency = syelatency
    else:
        srt_latency = min_latency

    stb["srt_latency"] = srt_latency

    network = stb_detail["network"]
    network["ntpServer"] = "46.101.5.214"
    srt = stb_detail.get("srt", {})
    srt["latency"] = srt_latency
    brightsign = stb_detail.get("brightsign", {})
    brightsign["streamLatency"] = -300


    data = {
        "srt": srt,
        "network": network,
        "brightsign": brightsign
    }

    function_url = "/api/device/{}".format(stb["id"])
    url = mwfunctions.urlbuild(function_url, stb["mwcore_address"])
    mwfunctions.mwput(url, json.dumps(data), BearerKey, debug=True)
    print (stb)
    if stb.get("refresh", False) == "TRUE":
        print("Refresh was True, refreshing device {} - {}".format(stb["id"], stb["serial"]))
        mwfunctions.mwcore_refresh_devices(BearerKey, stb["mwcore_address"], [stb["id"]])

    stb["update"] = False
    stb["refresh"] = False


def parse_args():
    """
    Standard function to parse input args.
    :param:
        n/a
    :return:
        arguments - parser object where the dest vars can be referenced like .file or .streams
    """
    parser = argparse.ArgumentParser()
    file_help = "use this to define the file to use."
    time_help = "Use this argument to define how many hours back to query STB data. Default is 24hr"
    ping_help = "Use this argument ping the public ip to get an estimate for the STB's RTT"
    latency_help = "Use this argument to define the default Minimum SRT latency, default is 300"
    parser.add_argument("-f", "--file", help=file_help, dest="file", default=False, required=True)
    parser.add_argument("-t", "--time", help=time_help, dest="time", default=24)
    parser.add_argument("-p", "--ping", help=ping_help, dest="ping", default=False, action="store_true")
    parser.add_argument("-l", "--latency", help=latency_help, dest="latency", default=300)
    arguments = parser.parse_args()
    return arguments


arguments = parse_args()
stb_file = arguments.file
hours = arguments.time
debug = True

csv_data = csvfunctions.read_csv_to_dict(stb_file)

for stb in csv_data:

    BearerKey = "Bearer {}".format(stb["api_key"])
    device_details = mwfunctions.mwcore_get_device_details(BearerKey, stb["mwcore_address"], stb["id"])

    stb["online"] = device_details.get("online", False)
    stb["srt_latency"] = device_details.get("srt", {}).get("latency", 0)

    if device_details.get("sye", False):
        stb["sye_delay"] = device_details["sye"]["presentationDelay"]
    else:
        stb["sye_delay"] = 0

    stb["public_ip"] = device_details["network"]["externalIp"]
    if arguments.ping:
        stb["ping_rtt"] = misc_functions.ping_latency(stb["public_ip"])

    if not stb.get("serial", False):
        stb["serial"] = device_details["serial"]

    stb["last_check_in"] = device_details["updatedAt"]

    stb["current_stream"] = device_details.get("stream", "N/A")
    if "credentials" in stb["current_stream"]:
        stb["playing_sye"] = True
    else:
        stb["playing_sye"] = False

    current_stats = mwcore_grafana_stbdata_pull(stb["id"], 0, minuets=1)
    print("last minuet stats:{}".format(current_stats))
    if not current_stats:
        stb["playing_srt"] = False
    elif current_stats == 500:
        stb["playing_srt"] = "error 500"
    elif current_stats.get("rtt", False):
        stb["playing_srt"] = True
    else:
        stb["playing_srt"] = False

    if stb["evaluate"] == "TRUE":
        stb_evaluate(stb, hours, BearerKey)

    if stb.get("update", False) == "TRUE":
        srt_latency_update(stb, device_details, arguments.latency)

    time.sleep(1)
    #Sleep 1 sec between each box to ensure we don't crash mwcore api with calls
    print("\n\n")

csvfunctions.write_dict_to_csv(stb_file, csv_data)
