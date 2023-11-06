import requests
from requests.auth import HTTPBasicAuth
import json
import datetime
import argparse
from Techex.inputdata import streaminput, streamoutput
from GenericCodeFunctions import csvfunctions, misc_functions
import time
import urllib
from datetime import datetime, timedelta


def __post_call(data, url, BearerKey, debug=False):
    if debug: start = datetime.now()
    resp = requests.post(url, data=data, headers={"Authorization":BearerKey, "Content-Type": "application/json"})
    if debug:
        end = datetime.now()
        execution_time = end - start
        print("Execution time: {}".format(execution_time))
    return resp



def mwpost (url, data, BearerKey, debug=False):
    if debug:
        print("Sending post request:\nURL: {}\nData: {}".format(url, data))
    try:
        resp = __post_call(data, url, BearerKey, debug=debug)#Post message to run the URL provided.
    except:
        resp = __post_call(data, url, BearerKey, debug=debug) # Post message to run the URL provided.
    if "20" not in str(resp.status_code):
        #Done to re-try
        time.sleep(1)
        resp = __post_call(data, url, BearerKey, debug=debug)  # Post message to run the URL provided.

    if debug:
        print("{} - {} - {}".format(resp, resp.reason, resp.content))
    return resp


def __get_call(url, BearerKey, debug=False):
    if debug: start = datetime.now()
    resp = requests.get(url, headers={"Authorization": BearerKey, "Content-Type": "application/json"})
    if debug:
        end = datetime.now()
        execution_time = end - start
        print("Execution time: {}".format(execution_time))
    return resp


def mwget (url, BearerKey, debug=False):
    if debug:
        print("Sending get request:\nURL: {}".format(url))
    try:
        resp = __get_call(url, BearerKey, debug=debug)
    except:
        resp = __get_call(url, BearerKey, debug=debug)

    if "20" not in str(resp.status_code):
        #Done to re-try
        time.sleep(1)
        resp = __get_call(url, BearerKey, debug=debug)
    if debug:
        print("{} - {} - {}".format(resp, resp.reason, resp.content))
    return resp


def __put_call(data, url, BearerKey, debug=False):
    if debug: start = datetime.now()
    resp = requests.put(url, data=data, headers={"Authorization":BearerKey, "Content-Type": "application/json"})
    if debug:
        end = datetime.now()
        execution_time = end - start
        print("Execution time: {}".format(execution_time))
    return resp


def mwput (url, data, BearerKey, debug=False):
    if debug:
        print("Sending put request:\nURL: {}\nData: {}".format(url, data))
    try:
        resp = __put_call(data, url, BearerKey, debug=debug)
    except:
        resp = __put_call(data, url, BearerKey, debug=debug)
    if "20" not in str(resp.status_code):
        if debug: print(resp)
        #Done to re-try
        time.sleep(1)
        resp = __put_call(data, url, BearerKey, debug=debug)
    if debug:
        print("{} - {} - {}".format(resp, resp.reason, resp.content))
    return resp


def mwpost_basic_auth (url, data, username, password, debug=True):


    print("Sending post request:\nURL: {}\nData: {}".format(url, data))
    if debug: start = datetime.now()
    resp = requests.post(url, data=data, headers={"Content-Type": "application/json"}, auth=HTTPBasicAuth(username, password))#Post message to run the URL provided.
    if debug:
        end = datetime.now()
        execution_time = end - start
        print("Execution time: {}".format(execution_time))
    if "20" not in str(resp.status_code):
        #Do this to re-try once
        time.sleep(1)
        if debug: print("something failed in the first attempt \n{} \n- re-trying".format(resp))
        if debug: start = datetime.now()
        resp = requests.post(url, data=data, headers={"Content-Type": "application/json"}, auth=HTTPBasicAuth(username, password))  # Post message to run the URL provided.
        if debug:
            end = datetime.now()
            execution_time = end - start
            print("Execution time: {}".format(execution_time))
    print ("{} - {} - {}".format(resp, resp.reason, resp.content))
    return resp


def mwcore_grafana_mwedgedata_pull(id, mwcore_address, username, password, hours, minuets=False, debug=True):
    """
    Function to pull grafana data for an id of data either input or output ID
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
            {"target": id}
        ]

    }

    json_data = json.dumps(data)
    functional_url = "/grafana/mwedges/query"
    url = urlbuild(functional_url, mwcore_address)
    data = mwpost_basic_auth(url, json_data, username, password, debug=debug)
    if data.status_code == 500:
        print ("Server had errors with ID {}".format(id))
        return 500
    json_data = data.json()  # gets you values, epoch list of arrays e.g [[2230532,1605271971653],[2230606,1605272031652]]
    return json_data


def urlbuild(functional_url, mwcore):
    if "http" in mwcore:
        return "{mwcore_address}{URL}".format(mwcore_address=mwcore, URL=functional_url)
    else:
        return "https://{mwcore_address}{URL}".format(mwcore_address=mwcore, URL=functional_url)


def mwcore_list_all_devices(BearerKey, mwcore):
    """
    Function to list all STB's
    :param BearerKey: API key formed into a BearerKey
    :param mwcore: URL to the mwcore, should include the explicit http/s:// definition as well!
    :return: list of return data dictionaries
    """
    function_url = "/api/devices?limit=-1"
    url = urlbuild(function_url, mwcore)

    all_devices = mwget(url, BearerKey)
    return all_devices.json()["rows"]


def mwcore_list_devices_on_channel(BearerKey, mwcore, search_channel, debug=True, ids=False):
    """
    Return list of json objects for each STB that is on a given channel
    :param BearerKey:  API key formed into a BearerKey
    :param mwcore: URL to the mwcore, should include the explicit http/s:// definition as well!
    :param search_channel: string to exact matching on the channel
    :param debug: enable debug printing
    :param ids: trigger function to only return STB ID's
    :return:
    """
    print ("Running function list devices on channel")
    stbs = mwcore_list_all_devices(BearerKey, mwcore)
    matching_stbs = []
    for stb in stbs:
        try:
            stb_channel = stb.get("channel", {}).get("name", "")
            if stb_channel == search_channel:
                if debug:
                    print("Device {} - {} has channel {} matching search channel {}".format(
                        stb["name"],
                        stb["_id"],
                        stb_channel,
                        search_channel
                    ))
                matching_stbs.append(stb)
        except:
            if debug:
                print("STB {} {} doesn't have a channel assigned".format(stb["name"], stb["_id"]))
    if ids:
        stb_ids = []
        for stb in matching_stbs:
            stb_ids.append(stb["_id"])
        return stb_ids
    else:
        return matching_stbs


def mwcore_get_device_details(BearerKey, mwcore, device_id):
    """
    Function to get a box's details
    :param BearerKey:  API key formed into a BearerKey
    :param mwcore: URL to the mwcore, should include the explicit http/s:// definition as well!
    :param device_id: device_id from mwcore URL when on UI or mwcore's unique ID for the box, NOT SERIAL NUMBER!
    :return:
    """
    function_url = '/api/device/{}'.format(device_id)
    url = urlbuild(function_url, mwcore)
    device = mwget(url, BearerKey, True)
    return device.json()


def mwcore_get_device_ip(BearerKey, mwcore, device_id):
    device = mwcore_get_device_details(BearerKey, mwcore, device_id)
    return device["network"]["externalIp"]


def get_stb_geo_location(BearerKey, mwcore, device_id, public_ip=False):
    if not public_ip:
        public_ip = mwcore_get_device_ip(BearerKey, mwcore, device_id)
    details = misc_functions.geo_lookup(public_ip)
    return (details["country_code"], details["continent_code"], details["country_name"], details["continent_name"])


def grafana_stb_data_simplification(stb, stb_data, debug=False):
    """
    Function to simplify the grafana data and average it.
    :param stb dictionary to pass the data to:
    :param stb_data to evaulate and simplify:
    :return:
    """
    stb_value_datapoints = {}
    for key, dataset in stb_data.items():
        datapoints = []
        for x in dataset:
            datapoints.append(x[0])
        stb_value_datapoints[key] = datapoints

    #Could change the below two if's to a sinlge function

    if stb_value_datapoints.get("discontinuityCounter", False):
        data = misc_functions.remove_null(stb_value_datapoints["discontinuityCounter"])
        discontinuity = sum(data)
        avg_discontinuity = discontinuity/ (len(data)/60) # divide by 60 as 60 data points in an hour. avg is for an hour.
        stb["discontinuity"] = discontinuity
        stb["avg_discontinuity_hour"] = avg_discontinuity

    else:
        stb["discontinuity"] = 0
        stb["avg_discontinuity_hour"] = 0

    if stb_value_datapoints.get("unrecovered", False):
        data = misc_functions.remove_null(stb_value_datapoints["unrecovered"])
        unrecovered = sum(data)
        avg_unrecovered = unrecovered / (len(data)/60)
        stb["unrecovered"] = unrecovered
        stb["avg_unrecovered_hour"] = avg_unrecovered
    else:
        stb["unrecovered"] = 0
        stb["avg_unrecovered_hour"] = 0

    if stb_value_datapoints.get("rtt", False):
        normalized_data = misc_functions.removeOutliers(stb_value_datapoints["rtt"])
        avg_rtt = sum(normalized_data) / len(normalized_data)
        stb["rtt"] = avg_rtt
    else:
        stb["rtt"] = 0

    if stb_value_datapoints.get("Bitrate", False):
        normalized_data = misc_functions.removeOutliers(stb_value_datapoints["Bitrate"])
        avg_bw = sum(normalized_data) / len(normalized_data)
        stb["Bitrate"] = avg_bw
    else:
        stb["Bitrate"] = 0

    if debug:
        for key, value in stb.items():
            print("{} : {}".format(key, value))


def mwcore_refresh_devices(BearerKey, mwcore, device_ids):
    """
    Function to refresh boxes (reload in the API)
    :param BearerKey:  API key formed into a BearerKey
    :param mwcore: URL to the mwcore, should include the explicit http/s:// definition as well!
    :param device_ids: list of device_id's
    :return:
    """
    ids = '","'.join(device_ids)
    function_url = '/api/devices/reload/?ids=["{}"]'.format(ids)
    url = urlbuild(function_url, mwcore)
    mwget(url, BearerKey, True)


def mwcore_create_channel(BearerKey, mwcore, data):
    """
    Function to create a new channel
    :param BearerKey: API key formed into a BearerKey
    :param mwcore: URL to the mwcore, should include the explicit http/s:// definition as well!
    :param data: json data string for the new channel you want to configure
    :return:
    """
    function_url = "/api/channel"
    url = urlbuild(function_url, mwcore)
    print (json.dumps(data))
    postcode = mwpost(url, json.dumps(data), BearerKey)

    """
        Example data = {
            "name": "Python Channel",
            "number": 666,
            "category": "5ab538e9a271902162f884a4",
            "enabled": True,
            "type": 0,
            "sources": [
                {
                    "options": {
                        "srt": {
                            "encrypted": True,
                            "passphrase": "football2020"
                        }
                    },
                "protocol": 6,
                "address": "167.98.58.36:9022"
                },
            ]
        }
        """


def mwcore_add_channel_sources(BearerKey, mwcore, channel_id, data):
    """
    Function to add a source to an existing channel
    will require pulling config for the existing channel and will then append to that existing config
    Will then push the whole new config back to mwcore including the new source.
    :param BearerKey: API key formed into a BearerKey
    :param mwcore: URL to the mwcore, should include the explicit http/s:// definition as well!
    :param channel_id: the ID for the channel you're adding a source to
    :param data: json data for the new source you want to add
    :return:
    """
    #channel_id = "5f6dddfe367f2f4e7cc05178"
    function_url = "/api/channel/{channel_id}".format(channel_id=channel_id)
    url = urlbuild(function_url, mwcore)
    current_channel = mwget(url, BearerKey)
    sourceinfo = current_channel.json()['sources']
    del sourceinfo[0]["mediaInfo"]
    sourceinfo.append(data)
    data = {
        "sources": sourceinfo
    }
    print(json.dumps(data))
    postcode = mwput(url, json.dumps(data), BearerKey)

    # noinspection PyUnreachableCode
    """
        example data = {
            'options': {
                'srt': {
                    'encrypted': True,
                    'passphrase': 'football2020'
                }
            },
            'protocol': 6,
            'address': '167.98.58.38:9023'
        }
    """


def mwcore_get_channels(BearerKey, mwcore):
    function_url = "/api/channels?limit=-1"
    url = urlbuild(function_url, mwcore)
    current_channels = mwget(url, BearerKey)
    return current_channels.json()["rows"]


def mwcore_update_channel(BearerKey, mwcore, channel_id, data):
        """
        Function to update an existing channel
        :param BearerKey: API key formed into a BearerKey
        :param mwcore: URL to the mwcore, should include the explicit http/s:// definition as well!
        :param channel_id: the ID for the channel you're adding a source to
        :param data: json data for the new source you want to add
        :return:
        """
        function_url = "/api/channel/{channel_id}".format(channel_id=channel_id)
        url = urlbuild(function_url, mwcore)
        postcode = mwput(url, data, BearerKey)


def mwedge_find_edge_names(edge_configs):
    """
    Based on the edge_configs grab the human readable names for each mwedge
    This will allow us to define capacity per edge, based on the human readbale name, rather than an edge ID
    :param edge_configs:
    :return:
    """
    mw_edge_names = []
    for x in edge_configs:
        mw_edge_names.append(x.get("name"))
    return mw_edge_names


def mwedge_get_edge_configs(mwedge_ids, BearerKey, mwcore_address, debug=False):
    """
    For each edge provided in the "mwedge_ids" grab the config json for the relevent device
    Form a dictionary keyed by EdgeID with value of Json structured config.
    :param mwedge_ids:
    :param BearerKey:
    :param mwcore_address:
    :return: Dictionary keyed on mwedge_ids to json config
    """
    edge_configs = {}

    for edge_id in mwedge_ids:
        edge_configs[edge_id] = mwedge_get_config(edge_id, BearerKey, mwcore_address, debug=debug)
    return edge_configs


def mwedge_get_public_ip(mwedge_id, BearerKey, mwcore_address, debug=False):
    edge_detail = mwedge_get_config(mwedge_id, BearerKey, mwcore_address, debug=debug)
    public_ip = edge_detail.get("externalIpAddress", False)
    return public_ip


def mwedge_createstream(edge_id, name, enable_thumb, mwcore, BearerKey, failover=0, failoverMode=0):
    """
    Function to create a stream on an MWEdge
    :param name: - String representing the name of the stream
    :param edge_id: - string id of the edge as seen from web URL when accessing web UI
    :param BearerKey: - API key transformed into Bearer
    :param mwcore: - URL to the mwcore, should include the explicit http/s:// definition as well!
    :param failover: - Bool to identify if we want the stream to have failover or not, 1 to say yes
    :param failoverMode: - Used to identify the specific failover mode (string matching whats in the UI)
    :param enable_thumb: - Used to turn on/off thumbnailing for the stream
    :return: - N/a
    """

    function_url = "/api/mwedge/{edgeID}/stream/".format(edgeID=edge_id) #Format the string to replace {edgeID} with the relevent VAR
    url = urlbuild(function_url, mwcore)
    data = {"name": name}

    if enable_thumb:
        data["enableThumbnails"] =True

    if failover:
        data["options"] = {
            "failoverMode": failoverMode,
            "failoverTriggers": {
                "zeroBitrate": True,
                "TSSyncLoss": True,
                "lowBitrateThreshold": 500,
                "CCErrorsInPeriodThreshold": 10,
                "CCErrorsInPeriodTime": 10,
                "missingPacketsInPeriodThreshold": 10,
                "missingPacketsInPeriodTime": 10,
                "missingPacketsInPeriod": True,
                "CCErrorsInPeriod": True
            }
        }

    postresponse = mwpost(url, json.dumps(data), BearerKey)
    return postresponse.json()["id"]

    # noinspection PyUnreachableCode
    """
        example_data = {
          "state": [],
          "name": "Coral1_1.9_Mb",
          "enableThumbnails": true,
          "id": "c2c6f115a5005542e859f0cbee92eec683b3c0f77d402626",
          "options": {
            "failoverMode": "floating",
            "failoverTriggers": {
              "zeroBitrate": true,
              "TSSyncLoss": true,
              "CCErrorsInPeriod": true,
              "CCErrorsInPeriodThreshold": 10,
              "CCErrorsInPeriodTime": 10,
              "missingPacketsInPeriod": true,
              "missingPacketsInPeriodThreshold": 10,
              "missingPacketsInPeriodTime": 10
            }
          },
          "mwedge": "5f71aee07def3af9ffb1db6c"
        },
    """


def mwedge_add_source_to_stream(edge_id, BearerKey, data, mwcore):
    """
    Function to add a source to a stream
    :param edge_id: - string id of the edge as seen from web URL when accessing web UI
    :param BearerKey: - API key transformed into Bearer
    :param data: - Json Data string to use creating the output
    :param mwcore: - URL to the mwcore, should include the explicit http/s:// definition as well!
    :return: - N/a
    """

    function_url = "/api/mwedge/{edgeID}/source/".format(edgeID=edge_id)  # Format the string to replace {edgeID} with the relevent VAR
    url = urlbuild(function_url, mwcore)
    postresponse = mwpost(url, data, BearerKey)
    return postresponse.json()["id"]

    # noinspection PyUnreachableCode
    """
        example_data = {
          "name": "Hong Kong_2.6_Mb_input",
          "stream": "440b656214360b62381bb198184237d0cabeb54645bf7a24",
          "protocol": "2022-7",
          "priority": 0,
          "options": {
            "sourceOne": {
              "address": "93.174.216.182",
              "port": 6001,
              "protocol": "SRT",
              "enabled": true,
              "passphrase": "hB3KQBgnpzTkzCiG78TG",
              "encryption": 16
            },
            "sourceTwo": {
              "address": "93.174.216.184",
              "port": 6001,
              "protocol": "SRT",
              "enabled": true,
              "encryption": 16,
              "passphrase": "hB3KQBgnpzTkzCiG78TG"
            }
          },
          "id": "b27cb15ae3df9a7c99215f25e35e455e1de1be41d6ca38fd",
          "active": true,
          "etr290Enabled": true,
          "stopped": false,
          "exhausted": false,
          "mwedge": "5f71aee07def3af9ffb1db6c"
        }
    """


def mwedge_add_output_to_stream(edge_id, BearerKey, data, mwcore):
    """
    Function to add an output to a stream
    :param edge_id: - string id of the edge as seen from web URL when accessing web UI
    :param BearerKey: - API key transformed into Bearer
    :param data: - Json Data string to use creating the output
    :param mwcore: - URL to the mwcore, should include the explicit http/s:// definition as well!
    :return: - N/a
    """
    function_url = "/api/mwedge/{edgeID}/output/".format(edgeID=edge_id)  # Format the string to replace {edgeID} with the relevent VAR
    url = urlbuild(function_url, mwcore)
    postresponse = mwpost(url, data, BearerKey)
    """
        example_data= {
            "stream": stream_id,
            "options": {
                "type": 0,
                "maxConnections": 5,
                "maxBandwidth": 2147483647,
                "chunkSize": 1316,
                "encryption": 16,
                "port": 9025,
                "passphrase": "football2020"
            },
            "protocol": "SRT",
            "name": "first SRT",
        }
    """


def mwedge_update_output(edge_id, output_id, BearerKey, data, mwcore):
    """
        Function to update an output to a stream
        :param edge_id: - string id of the edge as seen from web URL when accessing web UI
        :param output_id: - string ID of the output as seen from the API response/json structure
        :param BearerKey: - API key transformed into Bearer
        :param data: - Json Data string to used to update the output
        :param mwcore: - URL to the mwcore, should include the explicit http/s:// definition as well!
        :return: - N/a
        """
    function_url = "/api/mwedge/{edgeID}/output/{output_id}".format(edgeID=edge_id, output_id=output_id)  # Format the string to replace {edgeID} with the relevent VAR
    url = urlbuild(function_url, mwcore)
    postresponse = mwput(url, data, BearerKey)


def mwedge_pause_output(edge_id, output_id, BearerKey, mwcore, debug=False):
    function_url = "/api/mwedge/{edgeID}/output/{output_id}".format(edgeID=edge_id,output_id=output_id)  # Format the string to replace {edgeID} with the relevent VAR
    url = urlbuild(function_url, mwcore)
    data = {"paused": True}
    if debug: print("calling mwput")
    postresponse = mwput(url, json.dumps(data), BearerKey, debug=debug)
    if debug: print (postresponse)
    return postresponse


def mwedge_un_pause_output(edge_id, output_id, BearerKey, mwcore, debug=False):
    function_url = "/api/mwedge/{edgeID}/output/{output_id}".format(edgeID=edge_id,output_id=output_id)  # Format the string to replace {edgeID} with the relevent VAR
    url = urlbuild(function_url, mwcore)
    data = {"paused": False}
    if debug: print("calling mwput")
    postresponse = mwput(url, json.dumps(data), BearerKey, debug=debug)
    if debug: print (postresponse)
    return postresponse
    #Need to return the response so we can identify if its good or bad


def mwedge_get_config(edge_id, BearerKey, mwcore, debug=False):
    """
        Function to return json structure of configured mwedge.
        :param edge_id: - string id of the edge as seen from web URL when accessing web UI
        :param BearerKey: - API key transformed into Bearer
        :param mwcore: - URL to the mwcore, should include the explicit http/s:// definition as well!
        :return: - json structure describing the given mwedge's config.
    """
    function_url = "/api/mwedge/{edgeID}".format(edgeID=edge_id)  # Format the string to replace {edgeID} with the relevent VAR
    if debug: print("formed functinonal_url: {}".format(function_url))
    url = urlbuild(function_url, mwcore)
    if debug: print("formed url: {}".format(url))
    config = mwget(url, BearerKey, debug)
    if debug: print(config)
    return config.json()


def streams_config(file):
    """
    Function to create MWEdge streams, will print the list of stream configs pushed.
    ID's from this list are really important
    :param
        file: string identifying the name of the file in the inputdata folder to read.
    :return:
        list_of_dicts - list of dictionary objects based on reading the csv file passed in but with the ID of the configured stream related to the revelent dictionary entry
    """
    list_of_dicts = csvfunctions.read_csv_to_dict(file)
    export_list_of_dicts = []
    for stream in list_of_dicts:
        action = stream.get("action", False)
        if action == "create":
            BearerKey = "Bearer {}".format(stream["api_key"])
            stream["id"] = mwedge_createstream(
                stream["mwedge"],
                stream["name"],
                stream["enable_thumb"],
                stream["mwcore_address"],
                BearerKey,
                stream["failover"],
                stream.get("failoverMode", ""))
            stream["action"] = ""
            export_list_of_dicts.append(stream)

        elif action == "delete":
            BearerKey = "Bearer {}".format(stream["api_key"])
            try:
                mwedge_deletestream(stream["mwedge"], stream["id"], stream["mwcore_address"], BearerKey)
            except:
                print("""Stream wasn't delete due to missing variables, ensure a Stream ID is available along with Edge id, mwcore address and API Key
                Stream not deleted {} - Edge ID: {} - Stream ID: {}""".format(stream.get("name", ""), stream("mwedge","NON PROVIDED"), stream("id", "NON PROVIDED")))
                export_list_of_dicts.append(stream)
        elif not action:
            export_list_of_dicts.append(stream)
        else:
            print("Action {} not supported".format(action))
            export_list_of_dicts.append(stream)


    for x in export_list_of_dicts:
        print (x)
        #List of dicts was updated with stream IDs, these are needed when configuring inputs/outputs
        #The print shows these values for later use!
    csvfunctions.write_dict_to_csv(file, export_list_of_dicts)


def form_stream_input_json(csv_dictionary):
    """
    Function to form json for inputs to a stream
    Various sections for the various protocols,
    Each section could be its own function
    e.g create_in_options_SRT()
    :param
        inout: Dictionary object from the CSV reader, should be keyed based on CSV headings
    :return:
        n/a
    """
    protocol = csv_dictionary["protocol"]
    if protocol == "SKIP":
        print("Skipping this line in the CSV")
        #Done to allow breaks in the CSV for ease of use when editing in excel
        return
    name = csv_dictionary["mwname"]
    stream_id = csv_dictionary["stream"]
    address = csv_dictionary["address"]
    port = int(csv_dictionary["port"])
    chunkSize = int(csv_dictionary["chunkSize"])

    if protocol == "RTP":
        """
        Section will create an RTP based input
        Optional options are source network interface and source address for the stream
        """
        networkInterface = csv_dictionary.get("networkInterface", False)
        sourceAddress = csv_dictionary.get("sourceAddress", False)
        preserveHeaders = csv_dictionary.get("preserveHeaders", False)
        enableCorrection = csv_dictionary.get("enableCorrection", False)
        buffer = csv_dictionary.get("buffer", False)
        options_obj = streaminput.rtp_stream_source_options(address, port, preserveHeaders, enableCorrection)
        if networkInterface:
            options_obj.networkInterface = networkInterface
        if sourceAddress:
            options_obj.sourceAddress = sourceAddress
        if buffer:
            options_obj.buffer = int(buffer)

    elif protocol == "SRT":
        """
        Section will create an SRT based input
        can provide encryption optionally
        """
        encryption = csv_dictionary.get("encryption", False)
        passphrase = csv_dictionary.get("passphrase", False)
        networkInterface = csv_dictionary.get("networkInterface", False)
        logLevel = int(csv_dictionary.get("logLevel", False))

        options_obj = streaminput.srt_stream_source_options(address, port, chunkSize)
        if encryption and passphrase:
            options_obj.encryption = int(encryption)
            options_obj.passphrase = passphrase

        if networkInterface:
            options_obj.hostAddress = networkInterface

        if logLevel:
            options_obj.logLevel = logLevel




    elif protocol == "SRT-7":
        """
        Section will create an SRT based -7 input
        Optional second input 
        Optional encryption on either input 
        """
        options_obj = streaminput.dash7_stream_source_options(address, int(port), "SRT")
        encryption = csv_dictionary.get("encryption", False)
        passphrase = csv_dictionary.get("passphrase", False)
        networkInterface = csv_dictionary.get("networkInterface", False)
        networkInterface2 = csv_dictionary.get("networkInterface2", False)
        preserveHeaders = csv_dictionary.get("preserveHeaders", False)
        buffer = csv_dictionary.get("buffer", False)
        latency = csv_dictionary.get("latency", False)
        logLevel = int(csv_dictionary.get("logLevel", False))
        logLevel2 = int(csv_dictionary.get("logLevel2", False))

        if passphrase and encryption:
            options_obj.sourceOne["passphrase"] = passphrase
            options_obj.sourceOne["encryption"] = int(encryption)

        if networkInterface:
            options_obj.sourceOne["hostAddress"] = networkInterface

        if logLevel:
            options_obj.sourceOne["logLevel"] = logLevel

        address2 = csv_dictionary.get("address2", False)
        port2 = csv_dictionary.get("port2", False)

        if address2:
            options_obj.sourceTwo = {
                "address": address2,
                "port": int(port2),
                "protocol": "SRT",
                "enabled": True,
            }

            encryption2 = csv_dictionary.get("encryption2", False)
            passphrase2 = csv_dictionary.get("passphrase2", False)

            if encryption2:
                options_obj.sourceTwo["encryption"] = int(encryption2)
                options_obj.sourceTwo["passphrase"] = passphrase2

            if networkInterface2:
                options_obj.sourceTwo["hostAddress"] = networkInterface2

            if logLevel:
                options_obj.sourceTwo["logLevel"] = logLevel2

        protocol = "2022-7"
        if preserveHeaders:
            options_obj.preserveHeaders = True

        options_obj.buffer = int(buffer)
        if buffer:
            options_obj.sourceOne["buffer"] = int(latency)
            options_obj.sourceTwo["buffer"] = int(latency)
        if latency:
            options_obj.sourceOne["latency"] = int(latency)
            options_obj.sourceTwo["latency"] = int(latency)

    elif protocol == "UDP":
        """
        Section will create a UDP source
        optional source network interface and source stream address
        """
        options_obj = streaminput.udp_stream_source_options(address, port)
        sourceAddress = csv_dictionary.get("sourceAddress", False)
        networkInterface = csv_dictionary.get("networkInterface", False)
        if sourceAddress:
            options_obj.sourceAddress = sourceAddress
        if networkInterface:
            options_obj.networkInterface = networkInterface

    else:
        print("Input protocol {} isn't supported".format(protocol))
        #last catch to ensure if the protcol isn't supported we don't try to creat an input for it, also letting the user know!
        #Return so no further action from the function
        return

    # Creating the generic input object with the given input object specific to the protocol
    input_obj = streaminput.stream_source(name, stream_id, protocol, options_obj)

    #Allowing input to be set to passive
    passive = csv_dictionary.get("passive", "")
    if passive:
        input_obj.passive = True

    input_json = input_obj.data_to_json()
    print(input_json)

    input_json = input_json.replace("\\", "") #Tidying up json
    return input_json


def form_channel_source_json(csv_dictionary):
    if csv_dictionary["protocol"] == "SRT":
        data = {
            "address": csv_dictionary["address"],
            "protocol": 6,
        }
        if csv_dictionary.get("priority"):
            data["priority"] = csv_dictionary["priority"]
        if csv_dictionary.get("encrypted", False):
            data["options"] = {
                "srt": {
                    "encrypted": True,
                    "passphrase": csv_dictionary["passphrase"]
                }
            }
        if csv_dictionary.get("chunkSize", False):
            if not data.get("options", False):
                data["options"] = {
                    "srt": {
                        "chunkSize": csv_dictionary["chunkSize"]
                    }
                }
            else:
                data["options"]["srt"]["chunkSize"] = csv_dictionary["chunkSize"]
    else:
        print("protocol {} not supported".format(csv_dictionary["protocol"]))
        data = False
    return data


def create_out(inout):
    """
    Function will trigger the creation of outputs
    Currently only working for SRT
    1 - Identifies protocol
    2 - Creates option object to store json for output options
    3 - Attempts to retrieve all optional parameters and checks for their existence
    4 - Sets all the relevant options that have been provided
    5 - Creates the overall output json and passes it to the output creation function along with key system vars
    :param
        inout:Dictionary object from the CSV reader, should be keyed based on CSV headings
    :return:
        n/a
    """
    protocol = inout["protocol"]
    if protocol == "SKIP":
        print("Skipping this line in the CSV")
        # Done to allow breaks in the CSV for ease of use when editing in excel
        return
    name = inout["mwname"]
    stream = inout["stream"]
    protocol = inout["protocol"]
    if protocol == "SRT":
        options_obj = streamoutput.srt_stream_output_options(int(inout["port"]))
        encryption = inout.get("encryption", False)
        passphase = inout.get("passphrase", False)
        maxConnections = inout.get("maxConnections", False)
        maxBandwidth = inout.get("maxBandwidth", False)
        hostAddress = inout.get("networkInterface", False)
        chunkSize = inout.get("chunkSize", 1328)
        logLevel = int(inout.get("logLevel", False))
        if encryption:
            options_obj.encryption = int(encryption)
            options_obj.passphrase = passphase
        if maxConnections:
            options_obj.maxConnections = int(maxConnections)
        if maxBandwidth:
            options_obj.maxBandwidth = int(maxBandwidth)
        if hostAddress:
            options_obj.hostAddress = hostAddress
        if chunkSize:
            options_obj.chunkSize = int(chunkSize)
        if logLevel:
            options_obj.logLevel = logLevel


    elif protocol == "UDP":
        options_obj = streamoutput.udp_stream_output_options(int(inout.get("port")), inout.get("address"))

        networkInterface = inout.get("networkInterface", False)
        encryptionType = inout.get("encryptionType", False)
        encryptionPercentage = inout.get("encryptionPercentage", False)
        encryptionKeyParity = inout.get("encryptionKeyParity", False)
        encryptionOddKey = inout.get("encryptionOddKey", False)
        encryptionEvenKey = inout.get("encryptionEvenKey", False)

        if encryptionType:
            options_obj.encryptionType = encryptionType
        if encryptionPercentage:
            options_obj.encryptionPercentage = int(encryptionPercentage)
        if encryptionKeyParity:
            options_obj.encryptionParity = encryptionKeyParity
        if encryptionOddKey:
            options_obj.encryptionOddKey = encryptionOddKey
        if encryptionEvenKey:
            options_obj.encryptionEvenKey = encryptionEvenKey
        if networkInterface:
            options_obj.networkInterface = networkInterface
    else:
        print("Output protocol {} isn't supported".format(inout["protocol"]))
        return

    output_obj = streamoutput.stream_output(name, stream, protocol, options_obj)
    output_json = output_obj.data_to_json()
    print(output_json)

    BearerKey = "Bearer {}".format(inout["api_key"])
    mwedge_add_output_to_stream(inout["mwedge"], BearerKey, output_json, inout["mwcore_address"])


def create_inouts(file):
    """
    Function will iterate through the provided CSV (semicolon delimitered)
    For each row will identify if its an input or output
    Will pass a rows data to relevant in/out function
    :param
        file: used to parse the config required
    :return
        n/a
    """
    list_of_dicts = csvfunctions.read_csv_to_dict(file)
    for inout in list_of_dicts:
        if inout["input_output"] == "input":
            form_channel_source_json(inout)
        elif inout["input_output"] == "output":
            create_out(inout)


def add_channel_sources(file):
    """
    Function to call the add channel sources function
    will parse a CSV and populate a Data dictionary (will later be converted to json) based on the details in the file
    Currently only supports SRT sources.
    Allows for optional encryption
    Allows for optional chunk size.
    :param file: CSV file to base information on
    :return:
    """
    list_of_dicts = csvfunctions.read_csv_to_dict(file)
    for line in list_of_dicts:
        BearerKey = "Bearer {}".format(line["api_key"])
        if line["protocol"] == "SRT":
            data = {
                "address": line["address"],
                "protocol": 6,
            }
            if line.get("priority"):
                data["priority"] = line["priority"]
            if line.get("encrypted", False):
                data["options"] = {
                    "srt": {
                        "encrypted": True,
                        "passphrase": line["passphrase"]
                    }
                }
            if line.get("chunkSize", False):
                if not data.get("options", False):
                    data["options"] = {
                        "srt": {
                            "chunkSize": line["chunkSize"]
                        }
                    }
                else:
                    data["options"]["srt"]["chunkSize"] = line["chunkSize"]
            mwcore_add_channel_sources(BearerKey, line["mwcore_address"], line["channel_id"], data)
        else:
            print("protocol {} not supported".format(line["protocol"]))

