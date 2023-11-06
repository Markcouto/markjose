import sys
sys.path.append("..")
from Techex import mwfunctions
from GenericCodeFunctions import misc_functions, csvfunctions


"""
Need to collect output state
Save
pause all outputs 
unpause only previously active outputs
"""


def get_output_state(edge_id, api_key, mwcore_address):
    """
    create and return a list of dictionaries for output state from a given edge
    :param edge_id: MWEdge ID to check
    :param api_key: Standard API key
    :param mwcore_address: MWCore url.
    :return:
    list of dictionaries (perfect for the csv writer which doesn't support dictionary of dictionaries.)
    Each dict for an output, used to identify if its paused, its ID and its name
    """
    BearerKey = "Bearer {}".format(api_key)
    print(edge_id)
    edge_config = mwfunctions.mwedge_get_config(edge_id, BearerKey, mwcore_address, debug=False)
    print("Got mwedge config")
    output_state = []
    configuredOutputs = edge_config.get("configuredOutputs")
    print(configuredOutputs)
    for output in configuredOutputs:
        output_state.append(
            {
            "paused": output.get("paused", False),
            "name": output.get("name", ""),
            "id": output.get("id")
            }
        )
    print(configuredOutputs)
    return output_state


def pause_edge_outputs(edge_id, api_key, mwcore_address, file=False, cron=False, debug=False):
    """
    Function to pause ALL edge outputs based on config from the Edge API
    :param edge_id: ID for the MWEdge
    :param api_key: Standard API key
    :param mwcore_address: Connected MWCore url
    :param file: File to write output state to CSV
    :param debug: Use this to enable debug printing
    :return:
    """
    BearerKey = "Bearer {}".format(api_key)
    if debug: print("starting pausing")
    output_state = get_output_state(edge_id, api_key, mwcore_address)
    if file:
        if debug: print("writing to file {}".format(file))
        csvfunctions.write_dict_to_csv(file, output_state, cron)
    else:
        if debug: print("File not provided so not writing state to file")
    for output in output_state:
        if debug: print("pausing {} - {}".format(output.get("name", ""), output["id"]))
        mwfunctions.mwedge_pause_output(edge_id, output["id"], BearerKey, mwcore_address, debug=debug)

    if debug: print("Finished pausing")
    return output_state

def un_pause_edge_outputs(edge_id, api_key, mwcore_address, file=False, debug=False):
    """
    Based on a state file unpause the given outputs that where previously not paused.
    csv should have fields:
    "paused" - True or False to match if the given output was paused
    "name" - The name of the output and "id" (optional)
    "id" - The ID of the output for the given paused state
    :param edge_id: - The ID of the MWEdge to unpause outputs on
    :param BearerKey: - Standard API Key
    :param mwcore_address: - MWCore address
    :param file: - file path to the CSV described above if not provided will unpause all (optional)
    :param debug: - Enable debug printing
    :return: n/a
    """
    BearerKey = "Bearer {}".format(api_key)
    if debug: print("starting to unpause")
    if file:
        if debug: print("File {} was provided reading file to unpause those that weren't paused".format(file))
        post_output_state = csvfunctions.read_csv_to_dict(file)
        for output in post_output_state:
            if debug: print(output)
            if output["paused"] == False:
                # Previous state was not paused so unpausing
                if debug: print("Unpausing {} - {}".format(output.get("name", ""), output["id"]))
                post_response = mwfunctions.mwedge_un_pause_output(edge_id, output["id"], BearerKey, mwcore_address, debug=debug)
                if "20" not in str(post_response.status_code):
                    print("Failed to un pause outputs {}".format(post_response))
                    return post_response
    else:
        if debug: print("No file was provided, unpausing all outputs")
        output_state = get_output_state(edge_id, BearerKey, mwcore_address)
        for output in output_state:
            if debug: print("Unpausing {} - {}".format(output.get("name", ""),output["id"]))
            post_response = mwfunctions.mwedge_un_pause_output(edge_id, output["id"], BearerKey, mwcore_address, debug=debug)
            if "20" not in str(post_response.status_code):
                print("Failed to un pause outputs {}".format(post_response))
                return post_response
    if debug: print("Finished unpausing")
    return post_response
"""
def main():
    api_key = input("please provide API key:\n")
    mwcore_address = "https://mwcore.techex.co.uk"
    edge_id = "6012db7adf764f89c9dff365"
    BearerKey = "Bearer {}".format(api_key)
    file_path = "inputdata/output_state.csv"
    pause_edge_outputs(edge_id, BearerKey, mwcore_address, file_path, debug=True)
    input("ready to unpause?")
    un_pause_edge_outputs(edge_id, BearerKey, mwcore_address, debug=True)


if __name__ == "__main__":
    main()
"""

