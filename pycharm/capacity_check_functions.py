from Techex import mwfunctions
from GenericCodeFunctions import csvfunctions
import time
import argparse

class channel_object:
    """
    Creating this object to store details of the channel
    call  by doing channel = channel_object([INITILIZATION VARS])
    Functions within this class/object can be then referenced like:
    channel = channel_object([INITILIZATION VARs])
    channel.print()
    channel.check_util()
    """
    def __init__(self, name, stream_id, mwcore_address, user, password):
        """
        Initilization function for the class to set relevant variables.
        Also dynamically builds a dictionary for the stats per edge.
        :param name:
        :param stream_id:
        :param mwcore_address:
        """
        self.name = name
        self.stream_id = stream_id
        self.stats = {}
        self.outputs = {}
        self.mwcore_address = mwcore_address
        self.user = user
        self.password = password
        for edge in mw_edge_names:
            self.stats["{}-cap".format(edge)] = 0
            self.stats["{}-util".format(edge)] = 0

    def check_util(self):
        """
        Will use self.outputs to run grafana query and then parse response to calculate utilization of a channels listners
        :return:
        """
        for output_id, mwedge_name in self.outputs.items():
            print ("\nchecking grafana stats for {} on {}\n".format(self.name, mwedge_name))
            grafana_data = mwfunctions.mwcore_grafana_mwedgedata_pull(
                output_id,
                self.mwcore_address,
                self.user,
                self.password,
                0,
                minuets=1)
            #Example data:
            # {"target":"channel1:listeners","datapoints":[[9,1608051870788]]},{"target":"channel1:currentBitrate","datapoints":[[27627449,1608051870788]]}]'
            found = False
            for x in grafana_data:
                if "listeners" in x["target"]:
                    found = True
                    util = x["datapoints"][0][0]
                    #two [0]'s, first to get the first datapoint entry and then second to get value rather than the epoch timestamp

                    self.stats["{}-util".format(mwedge_name)] += util

            if not found:
                print("Something went wrong with the grafana data review, data below:\n{}".format(grafana_data))

    def print(self):
        print("{} - {}".format(self.name, self.stats))

    def export_single_dict(self):
        """
        Function to support exporting the Channel stats to a single dict rather than it being nested as a dictionary within the object.
        :return:
        """
        export = {
            "name": self.name,
            "Total_cap": 0,
            "Total_util": 0
        }

        for name, var in self.stats.items():
            export[name] = var
            if "cap" in name:
                export["Total_cap"] += var
            elif "util" in name:
                export["Total_util"] += var

        return export


def get_edge_configs(mwedge_ids, BearerKey, mwcore_address, debug=False):
    """
    For each edge provided in the "mwedge_ids" grab the config json for the relevent device
    Append this Json structure to a list so we have a list of the configs.
    :param mwedge_ids:
    :param BearerKey:
    :param mwcore_address:
    :return:
    """
    edge_configs = []

    for edge_id in mwedge_ids:
        edge_configs.append(
            mwfunctions.mwedge_get_config(edge_id, BearerKey, mwcore_address, debug=True)#TODO check and revert to debug=debug and ensure calling functions actually pass debug
        )
    find_edge_names(edge_configs)
    return edge_configs


def find_edge_names(edge_configs):
    """
    Based on the edge_configs grab the human readable names for each mwedge
    This will allow us to define capacity per edge, based on the human readbale name, rather than an edge ID
    :param edge_configs:
    :return:
    """
    global mw_edge_names
    mw_edge_names = []
    for x in edge_configs:
        mw_edge_names.append(x.get("name"))


def evaluate_edge_config(edge_config, grafana_user, grafana_pass, mwcore_address):
    """
    Pass in a single edge config json and itterate over it to form the right objects
    :param edge_config:
    :return:
    """
    edge_name = edge_config.get("name")
    configuredOutputs = edge_config.get("configuredOutputs")
    for output in configuredOutputs:
        channel_name = output.get("name")
        print (channel_name)
        if "_output" in channel_name:
            channel_name = channel_name.replace("_", "").replace("output", "")
            #Above line to remove the _output on each output object in sis mwcore
        capacity = output.get("options", {}).get("maxConnections")
        paused = output.get("paused", False)
        stream_id = output.get("stream")
        output_id = output.get("id")

        if channel_name not in channels:
            #Checking to see if the channel object has already been created or not.
            channels[channel_name] = channel_object(channel_name, stream_id, mwcore_address, grafana_user, grafana_pass)
        if not paused:
            channels[channel_name].stats["{}-cap".format(edge_name)] += capacity
            channels[channel_name].outputs[output_id] = edge_name
        else:
            print("output {} on {} is already paused so not adding capacity".format(channel_name, edge_name))


def capacity_check_function(api_key, mwcore_address, mwedge_ids, grafana_user, grafana_pass, debug=False):
    if debug: print("starting capacity check_function")
    BearerKey = "Bearer {}".format(api_key)
    if isinstance(mwedge_ids, str):
        mwedge_ids = mwedge_ids.replace(" ", "")
        mwedge_ids = mwedge_ids.split(",")

    global channels
    channels = {}

    if debug: print("trying to get configs")
    edge_configs = get_edge_configs(mwedge_ids, BearerKey, mwcore_address, debug=debug)

    if debug: print("Got configs")

    for edge in edge_configs:
        if debug: print("checking edge {}".format(edge["name"]))
        evaluate_edge_config(edge, grafana_user, grafana_pass, mwcore_address)
        if debug: print("finished checking edge {}".format(edge["name"]))

    for name, channel in channels.items():
        channel.check_util()
        time.sleep(0.5)

    list_of_dicts = []

    for name, channel in channels.items():
        channel.print()
        list_of_dicts.append(channel.export_single_dict())

    for dictionary in list_of_dicts:
        print (dictionary)

    return list_of_dicts
