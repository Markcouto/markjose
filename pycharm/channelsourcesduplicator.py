#from GenericCodeFunctions import test

#from Techex.inputdata import test

from GenericCodeFunctions import csvfunctions
import argparse

def parse_args():
    """
    Standard function to parse input args.
    :param:
        n/a
    :return:
        arguments - parser object where the dest vars can be referenced like .file or .streams
    """
    parser = argparse.ArgumentParser()
    file_help_in = "use this to define the input file to use. this should be a list of outputs you want duplicate channel sources for, will look in the inputdata/ folder in techex for the provided filepath"
    file_help_out = "use this to define the output file to use, this will be populated with relevant channel sources config for API interaction"
    servers_help = "Use this to define a list of server addresses to duplicate the channel sources based on, will itterate priority from 1 and up to len of servers list"

    priority_help = "define an int for the starting priority, if the 'highpri' flag is set in the CSV this will be the value used for that channel source! Default to 1"
    parser.add_argument("-if", "--infile", help=file_help_in, dest="infile", required=True)
    parser.add_argument("-of", "--outfile", help=file_help_out, dest="outfile", required=True)
    parser.add_argument("-s", "--servers", help=servers_help, dest="servers", required=True, nargs='+')
    parser.add_argument("-p", "--priority", help=priority_help, dest="priority", required=False, default=1)
    arguments = parser.parse_args()
    return arguments

def duplicate (list_of_dicts, servers, initialprivalue):
    """
    This code will do the actual duplication
    Will take in the list of outputs and create a channel source for each server provided in the --servers CLI argument
    Will create address and server_address fields in the CSV, address will take the port field and append to the end of the server address
    Server address added to CSV for documentation purposes

    Priorities for channel sources from the same server have the same priority.
    e.g If you have 5 outputs from server 1 they all show the same priority so outputs from server one for channel X have X priority
    channel x+1 outputs (all 5 of them for example) have priority X+1
    When the priority goes above the number of servers we are load balencing against the priority number loops back to initial value
    Use "highpri" flag in CSV to trigger channel sources to share the same priority value (Initialprivalue)

    :param list_of_dicts:
    :param servers:
    :param initialprivalue:
    :return:
    """
    export_list = []
    for x in range(len(servers)):
        print (x)
        address = servers[x]
        priority = x +1
        last_name = list_of_dicts[0]["Name"] #Initialize to the first name so the first time doesn't increment priority
        for line in list_of_dicts:
            dictionary_line = line.copy()
            #print(address)
            dictionary_line["server_address"] = address
            dictionary_line["address"] = "{}:{}".format(address, dictionary_line["port"])

            if dictionary_line.get("encryption", False):
                dictionary_line["encrypted"] = True

            if dictionary_line.get("highpri", False):
                dictionary_line["priority"] = initialprivalue
            else:
                if dictionary_line["Name"] != last_name:
                    priority += 1
                    # If previous channel name was different move onto new priority value.
                if priority > len(servers):
                    priority = 1
                dictionary_line["priority"] = priority

            last_name = dictionary_line["Name"]
            export_list.append(dictionary_line)
        #print ("Done with {} server, export things looks like: \n{}".format(address, export_things))

    for x in export_list:
        print(x)
    return export_list

"""
This code should take in code from an ouput CSV. Only addition required is a channel mapping from the output csv created.
As part of a CLI input you need to provide the list of server ip's for the source duplication to take place
Can use a field called highpri to flag an output that is high prioriry so duplicated sources will share the same priority of 1
"""
"""
thing = [{"name": "bob1", "port": "51", "highpri": True},
         {"name": "bob2", "port": "52"},
         {"name": "bob3", "port": "53"},
         {"name": "bob4", "port": "54"},
         {"name": "bob5", "port": "55"},
         {"name": "bob6", "port": "56"},
         {"name": "bob7", "port": "57"},
         {"name": "bob8", "port": "58"},
         {"name": "bob9", "port": "59"},
         {"name": "bob10", "port": "60"}
         ]
servers =["1.1.1.1", "2.2.2.2", "3.3.3.3", "4", "5", "6", "7", "8", "9", "10"]
"""

arguments = parse_args()

list_of_dicts = csvfunctions.read_csv_to_dict(arguments.infile)
outputs = duplicate(list_of_dicts, arguments.servers, arguments.priority)
csvfunctions.write_dict_to_csv(arguments.outfile, outputs)




