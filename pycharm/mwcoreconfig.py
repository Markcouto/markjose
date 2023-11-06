import requests
import json
import datetime
import argparse
from Techex.inputdata import streaminput, streamoutput
from Techex import mwfunctions
from GenericCodeFunctions import csvfunctions
import time

def mwpost (url, data, BearerKey):
    print("Sending post request:\nURL: {}\nData: {}".format(url, data))
    resp = requests.post(url, data=data, headers={"Authorization":BearerKey, "Content-Type": "application/json"})#Post message to run the URL provided.
    print ("{} - {} - {}".format(resp, resp.reason, resp.content))
    return resp

def mwget (url, BearerKey):
    print ("Sending get request:\nURL: {}".format(url))
    resp = requests.get(url, headers={"Authorization":BearerKey, "Content-Type": "application/json"})#Post message to run the URL provided.
    print ("{} - {} - {}".format(resp, resp.reason, resp.content))
    return resp

def mwput (url, data, BearerKey):
    print ("Sending put request:\nURL: {}\nData: {}".format(url, data))
    resp = requests.put(url, data=data, headers={"Authorization":BearerKey, "Content-Type": "application/json"})#Post message to run the URL provided.
    print ("{} - {} - {}".format(resp, resp.reason, resp.content))
    return resp


def mwdelete (url, BearerKey):
    print("Sending get request:\nURL: {}".format(url))
    resp = requests.delete(url, headers={"Authorization": BearerKey,"Content-Type": "application/json"})  # Post message to run the URL provided.
    print("{} - {} - {}".format(resp, resp.reason, resp.content))
    return resp

#####STATIC DETAILS########
#apikey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwZXJtaXNzaW9ucyI6eyJkZXZpY2VzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWUsInJlZnJlc2giOnRydWUsInJlYm9vdCI6dHJ1ZSwidXBncmFkZSI6dHJ1ZX0sImNoYW5uZWxzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWV9LCJtd2VkZ2VzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWV9LCJjYXRlZ29yaWVzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWV9LCJ1c2VycyI6eyJyZWFkIjp0cnVlLCJ3cml0ZSI6dHJ1ZSwiZGVsZXRlIjp0cnVlfSwicGFja2FnZXMiOnsicmVhZCI6dHJ1ZSwid3JpdGUiOnRydWUsImRlbGV0ZSI6dHJ1ZX0sInVzZXJHcm91cHMiOnsicmVhZCI6dHJ1ZSwid3JpdGUiOnRydWUsImRlbGV0ZSI6dHJ1ZX0sIm92ZXJsYXlzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWV9LCJnZW9mZW5jZXMiOnsicmVhZCI6dHJ1ZSwid3JpdGUiOnRydWUsImRlbGV0ZSI6dHJ1ZX0sInByb2dyYW1tZXMiOnsicmVhZCI6dHJ1ZSwid3JpdGUiOnRydWUsImRlbGV0ZSI6dHJ1ZX0sInRhc2tzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWV9LCJzeXN0ZW0iOnsicmVhZCI6dHJ1ZSwid3JpdGUiOnRydWV9fSwiZGV2aWNlTGltaXRlZCI6ZmFsc2UsImRldmljZUxpbWl0IjowLCJsb2dvbkxpbWl0ZWQiOmZhbHNlLCJsb2dvbkxpbWl0IjowLCJkZXZpY2VzIjpbIjVkODBhNGEzMTZkNGY0Mzc2NzNhNWI2ZCIsIjViNTZmMTY2MjU1NGJlMjc5NTcwZTZlMyIsIjVlYjk0MzY2M2VhZDRkNDI0M2NhM2M2MSIsIjVmMDgzMmQzNzE3N2RlNWIwZWYxMTZhMyJdLCJfaWQiOiI1NTE5MjYxYWNkYjZjYjFiMWRkNjk4ZTYiLCJfX3YiOjAsImFkbWluIjp0cnVlLCJjcmVhdGVkQXQiOiIyMDE1LTAzLTMwVDEwOjMxOjU0LjA4NFoiLCJwcm92aWRlciI6ImxvY2FsIiwidXBkYXRlZEF0IjoiMjAxNS0wOS0zMFQxMzo1NToyOC44NDBaIiwidXNlcm5hbWUiOiJhZG1pbiIsImlhdCI6MTU5NTk0NTcxMn0.ttK-nmSnAmOoPfPvLu4j045slQy-RmFiU1fFdG8QxRk"
#BearerKey = "Bearer {}".format(apikey) #add the var API key in the first {} of the string this will be static across MWCORE and its associated MWEDGE's
#edge_id = "5f50f130b99e798c3d34c4c4" #Found using the https://middleware/api/mwedges call or in the URL in GUI currently the Amsterdam edge, in static for now while testing
#mwcore_address = "mwcore.techex.co.uk"
###########################


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
    if len(sourceinfo) != 0:
        if sourceinfo[0].get("mediaInfo", False):
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


def mwedge_deletestream(edge_id, stream_id, mwcore, BearerKey):
    function_url = "/api/mwedge/{edgeID}/stream/{stream_id}".format(edgeID=edge_id, stream_id=stream_id)  # Format the string to replace {edgeID} with the relevent VAR
    url = urlbuild(function_url, mwcore)
    postresponse = mwdelete(url, BearerKey)


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


def mwedge_update_source_to_stream(edge_id, BearerKey, data, mwcore, source_id):
    """
    Function to update a source to a stream
    :param edge_id: - string id of the edge as seen from web URL when accessing web UI
    :param BearerKey: - API key transformed into Bearer
    :param data: - Json Data string to use creating the output
    :param mwcore: - URL to the mwcore, should include the explicit http/s:// definition as well!
    :return: - N/a
    """

    function_url = "/api/mwedge/{edgeID}/source/{sourceID}".format(edgeID=edge_id, sourceID=source_id)  # Format the string to replace {edgeID} with the relevent VAR
    url = urlbuild(function_url, mwcore)
    postresponse = mwput(url, data, BearerKey)
    return


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
            print(stream)
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
    csvfunctions.write_dict_to_csv(file, export_list_of_dicts)


def create_in(inout):
    """
    Function to create inputs for a stream
    Various sections for the various protocols,
    Each section could be its own function
    e.g create_in_options_SRT()
    :param
        inout: Dictionary object from the CSV reader, should be keyed based on CSV headings
    :return:
        n/a

    TODO output to CSV the sourceid for future updates
    """
    input_json = mwfunctions.form_stream_input_json(inout)
    BearerKey = "Bearer {}".format(inout["api_key"])

    mwedge_add_source_to_stream(inout["mwedge"], BearerKey, input_json, inout["mwcore_address"])


def search_sourceids(inout):
    """
    Return list of sourceID's for a given stream and source name
    :param inout:
    :return: list of source id's
    """
    stream_id = inout["stream"]
    name = inout["mwname"]

    sourceids = []
    BearerKey = "Bearer {}".format(inout["api_key"])
    edge_conifg= mwfunctions.mwedge_get_config(inout["mwedge"], BearerKey, inout["mwcore_address"])
    for source in edge_conifg["configuredSources"]:
        if source["stream"] == stream_id and source["name"] == name:
            sourceids.append(source["id"])

    for source in sourceids:
        print(source)
    return sourceids


def update_input(inout):
    """
    Function to update an input
    Requires searching for the sourceID first? or do in the function.
    :param inout:
    :return:
    """
    if not inout.get("source_id", False):
        inout["source_id"] = search_sourceids(inout)
        if inout["source_id"] == []:
            print ("Failed to find the sources specifified {}".format(inout))
            return

    input_json = mwfunctions.form_stream_input_json(inout)
    BearerKey = "Bearer {}".format(inout["api_key"])
    if isinstance(inout["source_id"], list):
        for source_id in inout["source_id"]:
            print (source_id)
            mwedge_update_source_to_stream(inout["mwedge"], BearerKey, input_json, inout["mwcore_address"], source_id)
    elif "['" in inout["source_id"]:
        print(inout["source_id"][2:-2])
        mwedge_update_source_to_stream(inout["mwedge"], BearerKey, input_json, inout["mwcore_address"], inout["source_id"][2:-2])
    else:
        mwedge_update_source_to_stream(inout["mwedge"], BearerKey, input_json, inout["mwcore_address"], inout["source_id"])


def inouts_config(file, debug=False):
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
    export_list_of_dicts = []
    for inout in list_of_dicts:
        action = inout.get("action", False)
        if action:
            if action == "create":
                if inout["input_output"] == "input":
                    create_in(inout)
                elif inout["input_output"] == "output":
                    mwfunctions.create_out(inout)
                inout["action"] = ""
            elif action == "update":
                if inout["input_output"] == "input":
                    update_input(inout)
                    inout["action"] = ""
                elif debug:
                    print("update outs not supported right now")
            elif action == "delete":
                if debug:
                    print("delete In/outs not supported right now")
            else:
                print("Action: {} not supported only create, update, delete in lower case please.".format(action))
                print("sleeping for 15 seconds")
                time.sleep(10)
            export_list_of_dicts.append(inout)
        else:
            if debug:
                print("No action give for line, skipping")
            export_list_of_dicts.append(inout)
    csvfunctions.write_dict_to_csv(file, export_list_of_dicts)

def channel_sources_config(file, debug=True):
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
    export_list_of_dicts = []
    for line in list_of_dicts:
        action = line.get("action", False)
        if action:
            BearerKey = "Bearer {}".format(line["api_key"])
            if action == "create":
                data = mwfunctions.form_channel_source_json(line)
                if data:
                    mwcore_add_channel_sources(BearerKey, line["mwcore_address"], line["channel_id"], data)
                    line["action"] = ""
                    export_list_of_dicts.append(line)
            elif action == "update":
                print ("update is not currently supported for channel sources! UI only for this action")
                export_list_of_dicts.append(line)
                """
                This would be difficult need to identify the correct element and then update the relevent fields
                """

            elif action == "delete":
                print ("delete is not currently supported for channel sources! UI only for this action")
                export_list_of_dicts.append(line)
                """
                To support this we would have to add some logic to match exactly the source on address, priority and all other vars
                then remove this from the json structure and then 
                """
            else:
                print ("Action '{}' is not supported, only create, update or delete in lower case".format(action))
        else:
            export_list_of_dicts.append(line)
            if debug:
                print("no action column/data provided skipping this line")

    csvfunctions.write_dict_to_csv(file, export_list_of_dicts)


def parse_args():
    """
    Standard function to parse input args.
    :param:
        n/a
    :return:
        arguments - parser object where the dest vars can be referenced like .file or .streams
    """
    parser = argparse.ArgumentParser()
    streams_help = "Use this agrument to define creating the overal streams"
    file_help = "use this to define the file to use."
    inouts_help = "Use this argument to define creating inouts for previously created streams"
    channelsourceadd_help = "Use this argument to trigger the channel source addition function"
    parser.add_argument("-s", "--streams", help=streams_help, dest="streams", default=False, action="store_true")
    parser.add_argument("-f", "--file", help=file_help, dest="file", default=False)
    parser.add_argument("-io", "--inouts", help=inouts_help, dest="inouts", default=False, action="store_true")
    parser.add_argument("-csa", "--channelsourceadd", help=channelsourceadd_help, dest="csa", default=False, action="store_true")
    arguments = parser.parse_args()
    return arguments



arguments = parse_args()
if not arguments.file:
    print("Please provide a file to reference!")
elif arguments.streams and arguments.inouts:
    print("You can not create streams and inouts at the same time with the same file name!")
elif arguments.streams:
    streams_config(arguments.file) #TESTED TO WORK
elif arguments.inouts:
    inouts_config(arguments.file) #TESTED TO WORK
elif arguments.csa:
    channel_sources_config(arguments.file)
else:
    print ("Please use with --streams or --inouts to create either of these.")




date_time = datetime.datetime.now()
print (date_time)

