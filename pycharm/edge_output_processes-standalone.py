import sys
sys.path.append("..")
from Techex import edge_output_processes


def main():
    api_key = input("please provide API key:\n")
    mwcore_address = "https://sis.techex.co.uk"
    edge_id = "5f7dec607def3af9fffec5a6"
    BearerKey = "Bearer {}".format(api_key)
    file_path = "inputdata/output_state.csv"
    #edge_output_processes.pause_edge_outputs(edge_id, BearerKey, mwcore_address, file_path, debug=True)
    #input("ready to unpause?")
    edge_output_processes.un_pause_edge_outputs(edge_id, api_key, mwcore_address, debug=True, file=file_path)


if __name__ == "__main__":
    main()
