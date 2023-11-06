from Techex import mwfunctions, passphraseupdate
from GenericCodeFunctions import misc_functions, csvfunctions
import argparse
import json
import sys

"""
provide CSV of channels to update, optional key otherwise random string generated within python (If done will print this out at the end, can also do CSV output)

- Check CSV for channel names and related mwedge's to update (comma separated list of id's)
- expose all edge's to review
- for each edge pull once http://mwcore/docs/#api-MWEdge-GetMWEdge
- store output in dictionary (will be a json object itself)
- pull http://mwcore/docs/#api-Channels-GetChannels
- itterating over CSV lines for each channel
    - For each edge
        - get channel name wanted to change
        - itterate through and search for an output name that has the name highlighted in the CSV in it
            - e.g csv says "channel bob" but output is "channel bob 2" or "channel bob" this will match otherwise not
            - when finding a match, trigger an output update only updating the options{passphrase} with the passphrase identified in csv or auto generated
            - Push using http://mwcore/docs/#api-MWEdge-UpdateMWEdgeOutput
    - using the channel output itterate/search for matching channel similar to the output name search
        - once found copy sources field, itterate through sources
            - when source is SRT update passphrase field
            - push http://mwcore/docs/#api-Channel-UpdateChannel json with the updated sources json
"""
"""
edges =["5eb96181bc710537721320a6", "5ea2b4cef4ec229de7dd2a25"]
mwcore = "https://mwcore.techex.co.uk"
apikey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwZXJtaXNzaW9ucyI6eyJkZXZpY2VzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWUsInJlZnJlc2giOnRydWUsInJlYm9vdCI6dHJ1ZSwidXBncmFkZSI6dHJ1ZX0sImNoYW5uZWxzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWV9LCJtd2VkZ2VzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWV9LCJjYXRlZ29yaWVzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWV9LCJ1c2VycyI6eyJyZWFkIjp0cnVlLCJ3cml0ZSI6dHJ1ZSwiZGVsZXRlIjp0cnVlfSwicGFja2FnZXMiOnsicmVhZCI6dHJ1ZSwid3JpdGUiOnRydWUsImRlbGV0ZSI6dHJ1ZX0sInVzZXJHcm91cHMiOnsicmVhZCI6dHJ1ZSwid3JpdGUiOnRydWUsImRlbGV0ZSI6dHJ1ZX0sIm92ZXJsYXlzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWV9LCJnZW9mZW5jZXMiOnsicmVhZCI6dHJ1ZSwid3JpdGUiOnRydWUsImRlbGV0ZSI6dHJ1ZX0sInByb2dyYW1tZXMiOnsicmVhZCI6dHJ1ZSwid3JpdGUiOnRydWUsImRlbGV0ZSI6dHJ1ZX0sInRhc2tzIjp7InJlYWQiOnRydWUsIndyaXRlIjp0cnVlLCJkZWxldGUiOnRydWV9LCJzeXN0ZW0iOnsicmVhZCI6dHJ1ZSwid3JpdGUiOnRydWV9fSwiZGV2aWNlTGltaXRlZCI6ZmFsc2UsImRldmljZUxpbWl0IjowLCJsb2dvbkxpbWl0ZWQiOmZhbHNlLCJsb2dvbkxpbWl0IjowLCJkZXZpY2VzIjpbIjVkODBhNGEzMTZkNGY0Mzc2NzNhNWI2ZCIsIjViNTZmMTY2MjU1NGJlMjc5NTcwZTZlMyIsIjVlYjk0MzY2M2VhZDRkNDI0M2NhM2M2MSIsIjVmMDgzMmQzNzE3N2RlNWIwZWYxMTZhMyJdLCJfaWQiOiI1NTE5MjYxYWNkYjZjYjFiMWRkNjk4ZTYiLCJfX3YiOjAsImFkbWluIjp0cnVlLCJjcmVhdGVkQXQiOiIyMDE1LTAzLTMwVDEwOjMxOjU0LjA4NFoiLCJwcm92aWRlciI6ImxvY2FsIiwidXBkYXRlZEF0IjoiMjAxNS0wOS0zMFQxMzo1NToyOC44NDBaIiwidXNlcm5hbWUiOiJhZG1pbiIsImlhdCI6MTYwMTI5Njc1Nn0.jJOnYuqrWXoyAJh1ITtD0CtONE1OHRrVY1XQ4k7x0UI"
csv_emulate = [{"channel": "BBC One HD", "edges": "5eb96181bc710537721320a6", "passphrase": "examplekey", "refresh": True},
               {"channel": "python test 123", "edges": "5eb96181bc710537721320a6", "refresh": 1},
               {"channel": "python test 456", "edges": "5eb96181bc710537721320a6,5ea2b4cef4ec229de7dd2a25" }]
BearerKey = "Bearer {}".format(apikey)
"""


def list_all_edges(csv):
    edges = []
    for row in csv:
        edge = row.get("edges", False)
        if edge:
            edges_to_add = edge.split(",")
            for e in edges_to_add:
                if e not in edges:
                    edges.append(e)
    return edges


def update_passphrases(csv, file_name):

    mwcore = csv[0]["mwcore"]
    BearerKey = "Bearer {}".format(csv[0]["apiKey"])


    debug = False
    stbs = mwfunctions.mwcore_list_all_devices(BearerKey, mwcore)

    # Identify all edge's
    edges = list_all_edges(csv)

    # Get Edge config
    edge_config = {}
    for edge in edges:
        edge_config[edge] = mwfunctions.mwedge_get_config(edge, BearerKey, mwcore)

    # Get MWCore Channels
    channel_config = mwfunctions.mwcore_get_channels(BearerKey, mwcore)

    for row in csv:
        mwcore = row["mwcore"]
        BearerKey = "Bearer {}".format(row["apiKey"])
        # Identify STB's to refresh later(search for STB's on a channel)
        if row.get("refresh", False):
            stb_ids = mwfunctions.mwcore_list_devices_on_channel(BearerKey, mwcore, row["channel"], ids=True)
            #print (stb_ids)
        # Get the key from CSV or generate one
        new_passphrase = row.get("passphrase", False)
        if not new_passphrase:
            row["passphrase"] = str(misc_functions.random_key())
            print("{}\nNew key for {}: {}\n{}".format("*" * 60, row["channel"], row["passphrase"], "*" * 60))

        passphraseupdate.mwedge_srt_output_passphrase_update(BearerKey, mwcore, row, edge_config)

        passphraseupdate.mwcore_channel_passphrase_update(BearerKey, mwcore, row, channel_config)

        # STB refresh:
        if row.get("refresh", False):
            if len(stb_ids)>0:
                answer = input("Are you 100% sure you want to refresh boxes? This could cause impact to customer screens\nY/N:")
                if answer == "Y":
                    mwfunctions.mwcore_refresh_devices(BearerKey, mwcore, stb_ids)
                else:
                    print ("You provided either a wrong format (Not 'Y') or provided 'n', skipping STB Refresh for saftey")
    csvfunctions.write_dict_to_csv(file_name[:-4] + "_keys.csv", csv)

def passphrase_documentation_update(csv, outputsfile, channelsourcesfile):
    outputs_dict = csvfunctions.read_csv_to_dict(outputsfile)
    channelsources_dict = csvfunctions.read_csv_to_dict(channelsourcesfile)
    for row in csv:
        channel = row["channel"]
        outputname = row["outputName"]
        edges = row["edges"].split(",")
        passphrase = row["passphrase"]
        for output in outputs_dict:
            if output["mwname"] == outputname and output["mwedge"] in edges:
                output["passphrase"] = passphrase
        for channelsource in channelsources_dict:
            if channelsource["Name"] == channel:
                channelsource["passphrase"] = passphrase
    csvfunctions.write_dict_to_csv(outputsfile, outputs_dict)
    csvfunctions.write_dict_to_csv(channelsourcesfile, channelsources_dict)

def parse_args():
    """
    Standard function to parse input args.
    :param:
        n/a
    :return:
        arguments - parser object where the dest vars can be referenced like .file or .streams
    """
    parser = argparse.ArgumentParser()
    file_help = "use this to define the CSV to use."
    option_help = """ Use this to define the function you want to run
        *'passphrase' - Use this to update SRT passphrases on mwedge outputs, and mwcore related channels
        *'passphrasedocs' - Use this to trigger an update of documents with the new passphrases"""
    outputsfile_help = "Use this with the passphrasedocs option to define the CSV where stream outputs config is for update"
    channelsourcesfile_help = "Use this with the passphrasedocs option to define the CSV where channel sources config is for update"
    parser.add_argument("-f", "--file", help=file_help, dest="file", default=False, required=True)
    parser.add_argument("-o", "--option", help=option_help, dest="option", required=True)
    parser.add_argument("-of", "--outputsfile", help=outputsfile_help, dest="outputsfile")
    parser.add_argument("-csf", "--channelsourcesfile", help=channelsourcesfile_help, dest="channelsourcesfile")
    arguments = parser.parse_args()
    return arguments




arguments = parse_args()
csv = csvfunctions.read_csv_to_dict(arguments.file)
if arguments.option == "passphrase":
    update_passphrases(csv, arguments.file)
if arguments.option == "passphrasedocs":
    passphrase_documentation_update(csv, arguments.outputsfile, arguments.channelsourcesfile)

