import sys
sys.path.append("..")
import socketio
import time

from Techex import mwfunctions
from GenericCodeFunctions import misc_functions

def getListeners(token, coreUrl, edges, debug= False):
    """
    Function to setup websocket and get list of connected IP's or SRT listeners
    Note: a sleep is required after triggering this function to ensure it has time to run and get data
    This is because it will run in the background
    :param token: API Key from MWCore
    :param coreUrl: URL to form websocket to
    :param edges: Formed dictionary keyed by edgeID see start of get_stb_state() for structure
    :param debug: To enable debugging outputs - Default False
    :return:
    """
    global sio
    sio = socketio.Client(reconnection_attempts=5, request_timeout=5, engineio_logger=debug, logger=debug)
    sio.connect(url=coreUrl, transports='websocket', namespaces=[])

    @sio.on('mwedge:batch:stats')
    def batchStats(data):
        if debug:
            print("Got message")
        for edge_id, edge_dict in edges.items():
            print ("edge_dict: {}".format(edge_dict))
            for output_id, output_dict in edge_dict.items():

                if (output_id in data['outputStats']):
                    if len(output_dict["ips"]) >= 1:
                        # The List has been populated, stop re-populating it!
                        continue
                    listeners = data['outputStats'][output_id][16]
                    #print("Number of listeners ", len(listeners))
                    for listener in listeners:
                        output_dict["ips"].append(listener[1])
                    if debug:
                        print("Ips for {} - {}".format(output_id, output_dict["ips"]))
                        print("dict for edge:{} - {}".format(edge_id, edge_dict))
                    edge_dict["checked"] = True

        for edge_id, edge_dict in edges.items():
            if not edge_dict["checked"]:
                return

        sio.disconnect()

    @sio.on('connect_error')
    def error(data):
        print("Connect error", data)
    
    @sio.on('connect')
    def connect_funct():
        ips = sio.emit(event='auth',
                 data={
                     'token': token
                 },
                 callback=authCallback,
                 namespace='/')

    def authCallback(data):
        pass


def evaluate_device_state(BearerKey, core, connected_ips, debug=False):
    """
    Function to evaulate device state based on mwcore devices API response and the connected ips detail
    :param BearerKey:
    :param core:
    :param connected_ips: list of IPs concatintated with connected channel
    :param debug:
    :return:
    devices_state structure
    """
    devices = mwfunctions.mwcore_list_all_devices(BearerKey, core)
    devices_state = {}
    for device in devices:
        channel = device.get("channel", None)
        devices_state[device["_id"]] = {
            "decoding": False,
            "online": "N/A",
            "channel": "N/A",
            "external_ip": "N/A",
            "serial": device.get("serial"),
            "decoding_error": "N/A",
            "id": device.get("_id"),
            "name": device.get("name", "N/a")
        }
        if channel:
            channel_name = channel.get("name", False)
        else:
            print("device {} has no channel dict".format(device["_id"]))
            devices_state[device["_id"]]['online'] = False
            devices_state[device["_id"]]['online'] = device.get("online")
            devices_state[device["_id"]]['external_ip'] = device.get("network", {}).get("externalIp", "N/A")
            devices_state[device["_id"]]['decoding_error'] = device.get("frameDecodingError", "N/A")

            continue
            # Offline devices do "channel":Null
            # Skipping checking as if channel dict isn't populated it can't be connected/decoding
        if device.get("version") == "7.0.33":
            print("device {} is on old firmware".format(device["_id"]))

            continue
            # Skipping checking as old firmware will never be connected!

        devices_state[device["_id"]]['online'] = device.get("online")
        devices_state[device["_id"]]['channel'] = device["channel"].get("name", False)
        devices_state[device["_id"]]['external_ip'] = device.get("network", {}).get("externalIp", "N/A")
        devices_state[device["_id"]]['decoding_error'] = device.get("frameDecodingError", "N/A")

        if not devices_state[device["_id"]]['online']:
            print ("Device {} is offline".format(device["_id"]))
            continue
            # Skip checking if connected as offline!

        external_ip = device["network"]["externalIp"]
        # This is populated even for offline devices
        ip_channel = external_ip + "_" + channel_name
        # This used for cross check against connected IPs
        if ip_channel in connected_ips:
            devices_state[device["_id"]]["decoding"] = True
        else:
            print("device {} doesn't have a matching connection {}".format(device["_id"], ip_channel))
    if debug:
        for x, y in devices_state.items():
            print(x, " - ", y)
        print(len(devices_state))

    return devices_state


def form_connected_ips(edges, debug=False):
    """
    Function to use edges data structure to process and generate a list of connected IP's concatenated with channel
    :param edges: - Edges Data structure
    :param debug:
    :return:
    """
    connected_ips = []
    for edge_id, edge_dict in edges.items():
        if debug: print (edge_dict)
        for output_id, output_dict in edge_dict.items():
            if debug: print (output_dict)
            if output_id == "checked":
                continue
                #In the case of the "checked" element you will not have the ip's value.
            for x in output_dict["ips"]:
                x = x + "_" + output_dict["channel"]
                connected_ips.append(x)
    if debug:
        print(connected_ips)
        # List of "IP_CHANNELNAME"
        print("Length: ", len(connected_ips))

    return connected_ips


def get_stb_state(api_key, core, mwedge_ids, debug=False):
    """
    Function to get the STB state which are connected to given mwedge's
    will compare the connected listener ips from mwedge outputs to the /devices API response
    Devices API response will give external IP along with channel this together can help to almost uniquly identify
    All devices and if they are actually connected.
    :param api_key: - Standard plain text API key
    :param core: - URL pointing to the mwcore
    :param mwedge_ids: - list of MWEdge ID's, can be found from URL when viewing GUI
    :param debug: - Set to True when you want to enable debug mode
    :return:
    Dict showing the following state from devices_state
    devices_state{
        DEVICE_ID : {
            "decoding": False,
            "online": device.get("online"),
            "channel": device["channel"].get("name", False),
            "external_ip": device.get("network", {}).get("externalIp", "N/A"),
            "serial": device.get("serial"),
            "decoding_error": device.get("frameDecodingError", "N/A"),
            "id": device.get("_id")
        }
    }
    """
    if debug: print ("starting getting stb state")
    BearerKey = "Bearer {}".format(api_key)
    if debug: print ("trying to get edge_config")
    edge_configs = mwfunctions.mwedge_get_edge_configs(mwedge_ids, BearerKey, core, debug=False)#TODO: set this back to debug, false as it prints out a lot of shit
    """
    edges : {
        EDGEID: {
            "checked": TRUE/FALSE
            OUTPUTID: {
                "ips": [IPS]
                "channel": CHANNEL NAME
            }
        }
    }
    """

    print("Forming edges dict")
    edges = {}


    # dictionary of dictionaries for each output outputID to list of IP's
    # NEEDS TO BE GLOBAL TO SUPPORT SOCKET.IO FUNCTIONS
    for edge_id, config in edge_configs.items():
        edge_dict = {"checked": False}
        configuredOutputs = config.get("configuredOutputs")
        for output in configuredOutputs:
            channel_name = output.get("name")
            channel_name_split = channel_name.split("_")[0:-1]
            # Output name includes _output at the end get rid of this and join again in the case of lowbitrate_sis row
            channel_name = "_".join(channel_name_split)
            edge_dict[output.get("id")] = {
                "ips": [],
                "channel": channel_name
            }
        edges[config.get("_id")] = edge_dict

    if "http" not in core and "https" not in core:
        if debug: print("Core address {} doesn't have https/http in its url this is needed for the websockets!, defaulting to https".format(core))
        core = "https://{}".format(core)

    if debug: print("getting listeners using core {}, edges detail: {}".format(core, edges))

    getListeners(api_key, core, edges, debug)

    checks = 0
    #Below is to pause the python script long enough for the getListeners to run in the background
    while(checks < 20):
        allchecked = True
        for edge_id, edge_dict in edges.items():
            if not edge_dict["checked"]:
                allchecked = False
        if (allchecked): # If all edge_dicts are checked, exit the while loop
            break
        else: # Not all are checked, continue looping
            checks += 1
            time.sleep(1)
    if debug: print("Finished listening for batch stats from mwedge's")
    if not allchecked:
        if debug: print("Didn't get batch stats from every requested mwedge id")
        try:
            if debug: print("Trying to disconnect SIO to prevent always open websocket")
            sio.disconnect()
            if debug: print("Disconnnected from SIO websocket")
        except Exception as e:
            if debug: print("Couldn't disconnect SIO for exception: {}".format(e))
        return False
    if debug: print("Got Batch stats from each mwedge")
    # while(checks < 10): # Alternative using for-else pattern
    #    for edge_id, edge_dict in edges.items():
    #        if !edge_dict["checked"]:
    #            break
    #    else: # If all edge_dicts are checked, exit the while loop
    #         break
    #     checks++ # Not all are checked, continue looping
    #     time.sleep(1)

    connected_ips = form_connected_ips(edges)

    devices_state = evaluate_device_state(BearerKey, core, connected_ips, debug=False)
    return devices_state


def compare_stb_state(pre_state, post_state, debug=False, cron=False):
    state = {
        "total_stb" : len(post_state),
        "online_state_change" : 0,
        "decoding_state_change" : 0,
        "channel_state_change" : 0,
        "external_ip_state_change" : 0,
        "decoding_error_state_change" : 0,
    }
    stb_detail = ""

    """
    device_state = {
        "decoding": False,
        "online": device.get("online"),
        "channel": device["channel"].get("name", False),
        "external_ip": device.get("network", {}).get("externalIp", "N/A"),
        "serial": device.get("serial"),
        "decoding_error": device.get("frameDecodingError", "N/A"),
        "id": device.get("_id")
    }
    """
    if debug: print("\nPRE STB STATE:\n{}\n\n\n\n\n".format(pre_state))
    if debug: print("\nPOST STB STATE:\n{}\n\n\n\n\n".format(post_state))

    for device_id, device_dict in post_state.items():
        if debug: print("PRE: Device: {}, dict: {}".format(device_id, pre_state[device_id]))
        if debug: print ("POST: Device: {}, dict: {}".format(device_id, device_dict))
        if device_dict["online"] == pre_state[device_id]["online"]:
            # Good state
            pass
        else:
            if device_dict["online"]:
                # Good state as gone from offline -> Online
                pass
            else:
                # Bad state
                state["online_state_change"] += 1
                failure_text = "{} went from online to offline".format(device_id)
                print(failure_text)
                stb_detail = "{}\n{}".format(stb_detail, failure_text)

        if device_dict["decoding"] == pre_state[device_id]["decoding"]:
            # Good state
            pass
        else:
            if device_dict["decoding"]:
                # Good state as no problem with decoding now
                pass
            else:
                # Bad state as gone from True -> False
                state["decoding_state_change"] += 1
                failure_text = "{} went from Decoding to not decoding".format(device_id)
                print(failure_text)
                stb_detail = "{}\n{}".format(stb_detail, failure_text)

        if device_dict["channel"] == pre_state[device_id]["channel"]:
            # Good state
            pass
        else:
            # Bad??? as channel has changed
            state["channel_state_change"] += 1
            failure_text = "{} changed channel from {} to {}".format(device_id, pre_state[device_id]["channel"],
                                                            device_dict["channel"])
            print(failure_text)
            stb_detail = "{}\n{}".format(stb_detail, failure_text)


        if device_dict["external_ip"] == pre_state[device_id]["external_ip"]:
            # Good state
            pass
        else:
            # Bad??? as external_ip has changed
            state["external_ip_state_change"] += 1
            failure_text = "{} changed external_ip from {} to {}".format(device_id, pre_state[device_id]["external_ip"],
                                                                device_dict["external_ip"])
            print(failure_text)
            stb_detail = "{}\n{}".format(stb_detail, failure_text)
        if debug: print("checking decoding_error details now")
        if device_dict.get("decoding_error", "n/a") == pre_state[device_id].get("decoding_error", "n/a"):
            # Good state
            pass
        else:
            if not device_dict["decoding_error"]:
                #Decoding error is false
                # Good state as currently no decoding error
                pass
            elif pre_state[device_id]["decoding_error"] == True and device_dict["decoding_error"] == "N/A":
                failure_text = "post state for decode error of {} is N/a This isn't good".format(device_id)
                print(failure_text)
                state["decoding_error_state_change"] += 1
                stb_detail = "{}\n{}".format(stb_detail, failure_text)
            else:
                # Bad state as gone from True -> False
                failure_text = "{} went from no decoding error to decodingerror".format(device_id)
                state["decoding_error_state_change"] += 1
                print(failure_text)
                stb_detail = "{}\n{}".format(stb_detail, failure_text)
    if cron:
        return state, stb_detail
    else:
        return state
"""
def main():
    global edges
    api_key = input("please provide the API key:\n")
    core = 'http://sis.techex.co.uk'
    # output = 'dbfe9db8f49d4f3899833bdfbdb14ad87ce4145be2af4b45'
    mwedge_ids = "5f7dec607def3af9fffec5a6,5f7ecab712ea07ba2f0f1bbc,5f7de1627def3af9fff8a233"
    ##Bunch of code to get output ID's
    BearerKey = "Bearer {}".format(api_key)
    mwedge_ids = mwedge_ids.replace(" ", "")
    mwedge_ids = mwedge_ids.split(",")
    print("trying to get configs")


    print("getting Pre-STB state")
    pre_state = get_stb_state(api_key, core, mwedge_ids)
    print("\n\nwaiting 60s to emulate pausing outputs")
    input("Ready to post check?:")
    misc_functions.print_countdown(30)

    print("getting post-STB state")
    post_state = get_stb_state(api_key, core, mwedge_ids)
    print("\n\n\nEvaluating diff between pre and post")

    state = compare_stb_state(pre_state, post_state)
    print(state)

if __name__ == "__main__":
    main()

# Order of the stats in the listener stats list
# SRT.listenerStats = [{
#     name: 'port'
# }, {
#     name: 'addr',
#     humanName: 'Address'
# }, {
#     name: 'sent'
# }, {
#     name: 'networkLost'
# }, {
#     name: 'unrecovered'
# }, {
#     name: 'retransmitted'
# }, {
#     name: 'belated'
# }, {
#     name: 'networkLostPercentage',
#     filter: 'percent'
# }, {
#     name: 'rtt',
#     humanName: 'RTT'
# }, {
#     name: 'fecSent',
#     humanName: 'FEC Sent',
#     showWhen: [{
#         name: 'type',
#         value: 0
#     }, {
#         name: 'fecSent',
#         type: 'stat',
#         value: ">0"
#     }]
# }, {
#     name: 'fecRatio',
#     filter: 'percent',
#     humanName: 'FEC Overhead',
#     showWhen: [{
#         name: 'type',
#         value: 0
#     }, {
#         name: 'fecSent',
#         type: 'stat',
#         value: ">0"
#     }]
# }]
"""
