from GenericCodeFunctions import csvfunctions
import argparse
import sys

maxConnections_default = 50 #Defined here as its not a CLI input depends on the stream, can't be global
no_stream_listener_processes = 2 #Defined here as will depend on the input as to how many to duplicate


def duplicate(list_of_dicts, st_port, max):
    """
    Function to create the correct lists of dictionaries for outputs on a stream.
    :param list_of_dicts: Input list of dicts read from a CSV
    :param st_port: Starting port for SRT port number Default is 7000 from argparse
    :return:list of dicts to represent the config for SRT outputs
    """
    outputs = []
    port = st_port
    for input_stream in list_of_dicts:
        if input_stream["action"] == "NEXT SERVER":
            port = st_port
        else:
            name = input_stream["Name"]
            stream = input_stream["stream"]
            #print (input_stream)
            #print ("{} {}".format(input_stream.get("no_srtout_processes", no_stream_listener_processes), type(input_stream.get("no_srtout_processes", no_stream_listener_processes))))
            no_processes = int(input_stream.get("no_srtout_processes", no_stream_listener_processes))
            if no_processes > max:
                print ("****WARNING****\n Max ports reserved {} breaks number of processes {}\nQuitting for saftey please use --max {} or a greater number\n***************".format(max, no_processes, no_processes))
                sys.exit()
            start_reserved_port = port
            maxConnections = int(input_stream.get("maxConnections", maxConnections_default))
            for x in range(no_processes):
                output = {
                    "stream": stream,
                    "input_output": "output",
                    "Name": name,
                    "mwname": "{}_output".format(name),
                    "protocol": "SRT",
                    "port": port,
                    "encryption": input_stream.get("encryption", 0),
                    "passphrase": input_stream.get("passphrase", ""),
                    "maxConnections": maxConnections,
                    "mwcore_address": input_stream["mwcore_address"],
                    "mwedge": input_stream["mwedge"],
                    "api_key": input_stream["api_key"],
                    "action": ""
                }

                if input_stream["origin_protocol"] == "UDP":
                    output["chunkSize"] = 1316
                else:
                    output["chunkSize"] = 1328
                outputs.append(output)
                port += 1
            port = start_reserved_port + max #itterate to account for max port reservation
    return outputs


def parse_args():
    """
    Standard function to parse input args.
    :param:
        n/a
    :return:
        arguments - parser object where the dest vars can be referenced like .file or .streams
    """
    parser = argparse.ArgumentParser()
    file_help_in = "use this to define the input file to use. this should be a list of inputs you want duplicate outputs for, will look in the inputdata/ folder in techex for the provided filepath"
    file_help_out = "use this to define the output file to use, this will be populated with relevant output config"
    st_port_help = "use this to define the starting port to use for the duplicator"
    max_help = "Use this to define the range of ports to reserve for each channel for expansion later"
    parser.add_argument("-if", "--infile", help=file_help_in, dest="infile", required=True)
    parser.add_argument("-of", "--outfile", help=file_help_out, dest="outfile", required=True)
    parser.add_argument("-p", "--st_port", help=st_port_help, dest="st_port", required=False, default=7000)
    parser.add_argument("-m", "--max", help=max_help, dest="max", required=False, default=10)
    arguments = parser.parse_args()
    return arguments


arguments = parse_args()
list_of_dicts = csvfunctions.read_csv_to_dict(arguments.infile)
outputs = duplicate(list_of_dicts, arguments.st_port, int(arguments.max))
csvfunctions.write_dict_to_csv(arguments.outfile, outputs)