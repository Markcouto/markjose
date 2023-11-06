from Techex import capacity_check_functions

import argparse



def parse_args():
    """
    Standard function to parse input args.
    :param:
        n/a
    :return:
        arguments - parser object where the dest vars can be referenced like .file or .streams
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    #Above helps with formatting the help test when displayed.
    file_help = "use this to define the file to use for export. \n "
    mwcore_help = "Use this to define the mwcore address of the core e.g: https://mwcore.techex.co.uk \n "
    api_help = "Use this to define the mwcore API key, this is a long string so add it at the end of your CLI call \n "
    mwedge_help = "USe this to define the comma separated list of mwedge ID's e.g ABC123,DEF456,GHI789 \n "
    grafana_user_help = "Grafana username"
    grafana_pass_help = "Grafana password"
    parser.add_argument("-f", "--file", help=file_help, dest="file", default=False, required=True)
    parser.add_argument("-m", "--mwcore", help=mwcore_help, dest="mwcore_address", default=False)
    parser.add_argument("-a", "--api", help=api_help, dest="api_key", default=False)
    parser.add_argument("-e", "--mwedge", help=mwedge_help, dest="mwedge_ids", default=False, nargs='+')
    parser.add_argument("--grafana_pass", help=grafana_pass_help, dest="grafana_pass", required=True)
    parser.add_argument("--grafana_user", help=grafana_user_help, dest="grafana_user", required=True)
    arguments = parser.parse_args()
    return arguments


def main():
    arguments = parse_args()
    print("Got arguments")
    mwcore_address = arguments.mwcore_address
    api_key = arguments.api_key
    dirty_mwedge_ids = arguments.mwedge_ids
    BearerKey = "Bearer {}".format(api_key)
    print(dirty_mwedge_ids)
    mwedge_ids = []
    for x in dirty_mwedge_ids:
        x = x.replace(" ", "")
        x = x.replace(",", "")
        mwedge_ids.append(x)
    print(mwedge_ids)

    capacity_check_functions.capacity_check_function(api_key, mwcore_address, mwedge_ids, arguments.grafana_user, arguments.grafana_pass, debug=False)



main()
