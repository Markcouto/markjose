import os
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
import sys
sys.path.append("..")


import threading
import time
import argparse
from datetime import datetime, timezone
from Techex import capacity_check_functions, trafficshift_checks, edge_output_processes, stb_snapshot, mwfunctions
from GenericCodeFunctions import misc_functions, csvfunctions, linux_functions

class setInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.stopEvent = threading.Event()

    def __setInterval(self):
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime - time.time()):
            nextTime += self.interval
            self.action()

    def cancel(self):
        self.stopEvent.set()

    def start(self):
        thread = threading.Thread(target=self.__setInterval)
        thread.start()


def re_ocurring_health_check():
    print("starting re-occuring health check")
    try:
        health_check, state = trafficshift_checks.edge_health_check(global_mwedges,
                                                                   global_mwedge_ssh_user,
                                                                   global_mwedge_ssh_pass,
                                                                   global_mwcore_address,
                                                                   global_ssh_key_path,
                                                                    emails=global_emails)
        if state == "ping failure":
            print("Device was unreachable, trying once more in case of internet weather")
            time.sleep(5)
            health_check, state = trafficshift_checks.edge_health_check(global_mwedges,
                                                                        global_mwedge_ssh_user,
                                                                        global_mwedge_ssh_pass,
                                                                        global_mwcore_address,
                                                                        global_ssh_key_path,
                                                                        emails=global_emails)
        if not health_check:
            print("Health check failed for {} reason".format(state))
            global_post_failed = True
        else:
            print("Health check passed!")
    except Exception as e:
        failure_text= "Health check raised exception: {}".format(e)
        print(failure_text)
        global_post_failed = True
        subject = "!!!Warning! post checks after shifting {} - {} are throwing exceptions".format(global_edge_id_to_shift, global_mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, global_emails)
        pass
        #Not doing anything as we don't have logic to break out of this for now
        #TODO: Add this logic to break out/shift back?


def end_reoccuring_healthcheck():
    # Hit 9am UTC so leaving control for Humans to take over
    print("Time matches the cutoff time {}:{}, ending poller".format(global_cut_off_hour, global_cut_off_min))
    poller.cancel()
    success_text = "Shift away was done successfully, now ending re-occuring health checks to allow humans to do their thing, Automation is hands off, please upgrade {} - {}".format(
        global_edge_id_to_shift, global_mwcore_address)

    if global_post_failed:
        subject = "!!!Failure! Automation is hands off, please upgrade {} - {}".format(global_edge_id_to_shift,
                                                                                       global_mwcore_address)
        success_text = "Shift away was done but post checks failed, now ending re-occuring health checks to allow humans to do their thing, Automation is hands off, please upgrade {} - {}".format(
            global_edge_id_to_shift, global_mwcore_address)
    else:
        subject = "!!!Success! Automation is hands off, please upgrade {} - {}".format(
            global_edge_id_to_shift, global_mwcore_address)
    print(success_text)
    misc_functions.send_email_techexbot(success_text, subject, global_emails)
    return


def trigger_health_check():
    """
    global global_mwcore_address
    global global_ssh_key_path
    global global_edge_id_to_shift
    Function to check if the state is still good to continue checking
    :return:
    """
    #run health check, this will start to flood support@techex if there are issues
    print ("triggering re-occuring health check")
    re_ocurring_health_check()
    print ("Finished health check")
    # Check time if after x time shut down script
    now = datetime.now(tz=timezone.utc)
    print ("Time is {}".format(now))

    if now.hour >= global_cut_off_hour:
        end_reoccuring_healthcheck()
        return

    if now.minute >= global_cut_off_min and now.hour >= global_cut_off_hour: ##TODO FIX TO BE CHECKING FOR 9amUTC
        end_reoccuring_healthcheck()
        return

    print("Cut off time of {}:{} UTC hasn't been found\n waiting for interval to re-check".format(global_cut_off_hour, global_cut_off_min))


def traffic_shift(
    edge_id_to_shift, mwedge_ids, mwcore_address,
    grafana_user, grafana_pass,
    api_key, stb_state_filepath, output_state_filepath,
    mwedge_ssh_user="root", mwedge_ssh_pass="password",
    cron=False, ssh_key_path=False, emails="support@techex.co.uk"):
    # Function to carry out all checks and processes for shifting away!
    # Linux health check for all edges' - DONE
    # Capacity check - DONE
    # STB state check - DONE
    # store stb state and email to support@techex - DONE

    # output state check - DONE
    # store output state - DONE

    # pause all outputs - DONE
    # Email output state + pause success - Done

    # wait 120 seconds to allow STB's to re-connect - DONE
    # linux health check on remaining edges' - DONE
    # run stb post snapshot - DONE
    # stb snapshot compare - DONE
    # capacity check all edges - DONE
    # trigger 5 min looping edge health check!
    # end/sys.exit() at 8am UTC (8am in winter, 9am in summer time)
    # datetime.now(tz = timezone.utc)

    debug = True
    #########################################
    #Get IP's
    BearerKey = "Bearer {}".format(api_key)
    mwedges = {}
    print(mwedge_ids)
    for mwedge in mwedge_ids:
        if debug: print("Getting IP for {}".format(mwedge))
        try:
            public_ip = mwfunctions.mwedge_get_public_ip(mwedge, BearerKey, mwcore_address)
            if debug: print("Public IP found: {}".format(public_ip))
        except Exception as e:
            print ("something failed getting public IP: {}".format(e))
            return False
        mwedges[mwedge] = {"ip": public_ip}
    ##########################################
    #Health check
    for edge_id, edge_detail in mwedges.items():
        #These below functions already have try except
        if ssh_key_path:
            health_check, state = linux_functions.linux_host_health_check(edge_detail["ip"], mwedge_ssh_user, "key", key_path=ssh_key_path, debug=debug)
        else:
            health_check, state = linux_functions.linux_host_health_check(edge_detail["ip"], mwedge_ssh_user, mwedge_ssh_pass, debug=debug)
        if not health_check:
            #Something failed the pre-check so quit out
            failure_text = "An Edge {} is not healthy because {}\n failing pre-checks".format(edge_id, state)
            print(failure_text)
            subject = "Traffic shift for {} failed health check connected to {}".format(edge_id, mwcore_address)
            misc_functions.send_email_techexbot(failure_text, subject, emails)
            return

    ###########################################
    #Capacity check
    failed = False
    state = True
    exception_reason = ""
    try:
        print("getting channel capacity/util")
        channel_util = capacity_check_functions.capacity_check_function(api_key, mwcore_address, mwedge_ids, grafana_user, grafana_pass, debug=debug)
        print("got data, reviewing the capacity")
        state, reason = trafficshift_checks.capacity_review(channel_util, debug=debug)
    except Exception as e:
        failed = True
        exception_reason = e
    if failed:
        failure_text = "An exception was raised when running the capacity checker: {}".format(exception_reason)
        print (failure_text)

    else:
        if not state:
            print("something went wrong with the capacity check {}".format(reason))
            failure_text = "shifting {} failed on pre-capacity checks for '{}' reason not shifting and failing process\nSee attached channel_util output:".format(edge_id_to_shift, reason)
            for channel in channel_util:
                failure_text = "{} \n{}".format(failure_text, channel)

    if failed or not state:
        subject = "Traffic shift for {} failed pre-check connected to {}".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)
        return
    else:
        print("capacity check passed")

    #################################################################################################
    #STB state

    failed = False
    devices_state = False
    exception_reason = ""
    try:
        devices_state = stb_snapshot.get_stb_state(api_key, mwcore_address, mwedge_ids, debug=debug)
    except Exception as e:
        failed = True
        exception_reason = e

    if not devices_state or failed == True:  #Either the function returned a false or we got an exception
        failure_text = "We couldn't get all MWEdge stats\nCore: {}\nEdgeID's: {}".format(mwcore_address, mwedge_ids)
        if failed:
            failure_text = "{}\nException: {}".format(failure_text, exception_reason)
        print(failure_text)
        subject = "Traffic shift for {} connected to {} failed snapshot STBs".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)
        return

    ###############################################################################################
    #STB write/email

    devices_state_list = []
    devices_state_text = ""
    #Need the dict in list of dict format rather than dict of dict
    for id, dict in devices_state.items():
        devices_state_list.append(dict)
        devices_state_text = "{}\n{}".format(devices_state_text, dict)
    csvfunctions.write_dict_to_csv(stb_state_filepath, devices_state_list, cron)
    #Also email to ensure we have some state saved in case the file doesn't write/is lost??
    subject = "Traffic shift STB state for {} - {}".format(edge_id_to_shift, mwcore_address)
    misc_functions.send_email_techexbot(devices_state_text, subject, emails)

    ###############################################################################################
    #Output state capture

    if not cron:
        pass
    input("Pre-checks done, Are you ready to pause outputs?")


    """
    try:
        output_state = edge_output_processes.pause_edge_outputs(edge_id_to_shift, api_key, mwcore_address, file=output_state_filepath, debug=debug, cron=cron)
    except Exception as e:
        failure_text = "Something failed while trying to pause outputs, please check into this ASAP!! {}".format(e)
        print(failure_text)
        subject = "!!!FAILURE PAUSING OUTPUTS!!!! {} - {}".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)

    output_state_text = "Outputs where paused successfully! Please see the current state below and also saved at {}\n".format(output_state_filepath)
    for x in output_state:
        output_state_text = "{}\n{}".format(output_state_text, x)
    subject = "Success! Outputs paused state inside {} - {}".format(edge_id_to_shift, mwcore_address)
    misc_functions.send_email_techexbot(output_state_text, subject, emails)
    """
    ###############################################################################################
    #wait 120 seconds to allow STB's to re-connect
    pause = 10
    print ("Pausing {} seconds to allow STB's to re-connect".format(pause))
    time.sleep(pause) #TODO: set this back to 120s

    ###############################################################################################
    #linux health check on remaining edges
    post_failed = False
    failed = False
    try:
        health_check, state = trafficshift_checks.edge_health_check(mwedges, mwedge_ssh_user, mwedge_ssh_pass, mwcore_address, ssh_key_path, debug=debug, emails=emails)
        failure_text = "Something failed while trying to post check after pausing outputs, please check into this ASAP!! {}".format(state)
    except Exception as e:
        failure_text = "Something failed while trying to post check after pausing outputs, please check into this ASAP!! {}".format(e)
        failed = True
        post_failed = True


    if not health_check or failed:
        print (failure_text)
        post_failed = True
        subject = "!!!FAILURE!! MWEDGE uneahlthy at post check!!!! {} - {}".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)
        ###########
        # TODO: ADD SHIFT BACK HERE
        ###########

    ###############################################################################################
    # run stb post snapshot

    # Get active edge id's
    mwedge_ids_post_active = []
    for id in mwedge_ids:
        if edge_id_to_shift == id:
            continue
        else:
            mwedge_ids_post_active.append(id)

    failed = False
    exception_detail = ""
    try:
        devices_state_post = stb_snapshot.get_stb_state(api_key, mwcore_address, mwedge_ids_post_active, debug=debug)
    except Exception as e:
        failed = True
        post_failed = True
        exception_detail = e

    if not devices_state_post or failed == True:  # Either the function returned a false or we got an exception
        post_failed = True
        failure_text = "We couldn't get all MWEdge stats\nCore: {}\nEdgeID's: {}".format(mwcore_address, mwedge_ids_post_active)
        if failed:
            failure_text = "{}\nException: {}".format(failure_text, exception_detail)
        print(failure_text)
        subject = "!!!FAILURE!!STB post Snapshot failed! {} - {}".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)



    ###############################################################################################
    # stb snapshot compare

    devices_state_pre = devices_state
    exception_found = False
    try:
        if debug: print ("Triggering STB comparison")
        stb_state, stb_detail = stb_snapshot.compare_stb_state(devices_state_pre, devices_state_post, debug=debug, cron=cron)
        failed_state = False
        reason = ""
    except Exception as e:
        post_failed = True
        failure_text = "Something caught an exception when post checking STB State {}".format(e)
        print(failure_text)
        subject = "!!!FAILURE!!STB post Snapshot failed! {} - {}".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)
        exception_found = True

    if debug: print("finished getting STB state")
    """
        state = {
            "total_stb" : len(post_state),
            "online_state_change" : 0,
            "decoding_state_change" : 0,
            "channel_state_change" : 0,
            "external_ip_state_change" : 0,
            "decoding_error_state_change" : 0,
        }
    """
    if not exception_found:
        try:
            #TODO: .GET for all of the below lines
            if stb_state["online_state_change"] > (stb_state["total_stb"]/100)*10:  #Supporting 10% variance
                failed_state = True
                reason = "{} {} devices went offline which is higher than 10%\n".format(reason, stb_state["online_state_change"])
            if debug: print("passed online state change"
                            "")
            if stb_state["decoding_state_change"] > (stb_state["total_stb"]/100)*2:  #Supporting 2% variance
                failed_state = True
                reason = "{} {} devices went into a bad decoding state and couldn't lock onto a new SRT source\n".format(reason, stb_state["decoding_state_change"])
            if debug: print("passed decoding state change")

            if stb_state["external_ip_state_change"] > (stb_state["total_stb"]/100)*25:  #Supporting 25% variance as a few doing this isn't a major issue
                failed_state = True
                reason = "{} {} devices changed their external ip which is worrying\n".format(reason, stb_state["external_ip_state_change"])
            if debug: print("passed external IP state change")

            if stb_state["decoding_error_state_change"] > (stb_state["total_stb"]/100)*2:  #Supporting 2% variance
                failed_state = True
                reason = "{} {} devices went into a bad decoding state\n".format(reason, stb_state["decoding_error_state_change"])
            if debug: print("completed decoding error state change check")

            if failed_state:
                post_failed = True
                reason = "The STB state comparison failed for the following reasons:\n{}\nSTBs with issue:\n{}".format(reason, stb_detail)
                print(reason)
                subject = "!!!FAILURE!!! STB State comparison failed post shift away {} - {}".format(edge_id_to_shift, mwcore_address)
                misc_functions.send_email_techexbot(reason, subject, emails)
            if debug: print("completed STB state checking")
        except Exception as e:
            post_failed = True
            failure_text = "Something caught an exception when post checking STB State {}".format(e)
            print (failure_text)
            subject = "!!!FAILURE!!STB post Snapshot failed! {} - {}".format(edge_id_to_shift, mwcore_address)
            misc_functions.send_email_techexbot(failure_text, subject, emails)


    ###############################################################################################
    #capacity check all active edges

    failed = False
    state = True



    #Check util
    exception_reason = ""
    try:
        channel_util = capacity_check_functions.capacity_check_function(api_key, mwcore_address, mwedge_ids_post_active,
                                                                        grafana_user, grafana_pass)
        state, reason = trafficshift_checks.capacity_review(channel_util, post_check=True, debug=debug)
    except Exception as e:
        post_failed = True
        exception_reason = e
        failed = True

    #Review state/response
    if failed:
        post_failed = True
        failure_text = "An exception was raised when running the capacity checker: {}".format(exception_reason)
        print(failure_text)

    else:
        if not state:
            post_failed = True
            print("something went wrong with the capacity check {}".format(reason))
            failure_text = "shifting {} failed on post-capacity checks for '{}' reason not shifting and failing process\nSee attached channel_util output:".format(
                edge_id_to_shift, reason)
            for channel in channel_util:
                failure_text = "{} \n{}".format(failure_text, channel)

    #failure action
    if failed or not state:
        post_failed = True
        subject = "!!!FAILURE!! STB Capacity is in a bad state {} - {}".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)
    else:
        print("capacity check passed")

    ###############################################################################################
    # trigger 5 min looping edge health check!
    # end/sys.exit() at 8am UTC (8am in winter, 9am in summer time)
    # datetime.now(tz = timezone.utc)
    #mwedges, mwedge_ssh_user, mwedge_ssh_pass, mwcore_address, ssh_key_path

    global global_mwedges
    global global_mwedge_ssh_user
    global global_mwedge_ssh_pass
    global global_mwcore_address
    global global_ssh_key_path
    global global_edge_id_to_shift
    global global_emails
    global global_post_failed

    global_mwedges = mwedges
    global_mwedge_ssh_user = mwedge_ssh_user
    global_mwedge_ssh_pass = mwedge_ssh_pass
    global_mwcore_address = mwcore_address
    global_ssh_key_path = ssh_key_path
    global_edge_id_to_shift = edge_id_to_shift
    global_emails = emails
    global_post_failed = post_failed

    #Confirm re-occuring state checks now standard post checks passed
    if not post_failed:
        success_text = "The shift away of {} connected to {} was successful, well done now go have a cuppa and keep an eye out for any failures for the re-occuring health checks till 9am UTC" .format(edge_id_to_shift, mwcore_address)
        subject = "!!!Success!! edge {} - {} is shifted away".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(success_text, subject, emails)
    else:
        text = "The shift way of {} connected to {} was unsuccessful please investigate!!!! ".format(edge_id_to_shift, mwcore_address)
        subject = "!!!Failure!! {} MWEdge's are UNHEALTHY after traffic shift".format(mwcore_address)
        misc_functions.send_email_techexbot(text, subject, emails)

    print ("finished post checks, starting interval checks")

    interval = 3*5  #5 mins between checks
    #TODO: change this back to 5 mins (Currently 15 sec)
    global poller
    poller = setInterval(interval, trigger_health_check)
    poller.start()


def parse_args():
    """
    Standard function to parse input args.
    :param:
        n/a
    :return:
        arguments - parser object where the dest vars can be referenced like .file or .streams
    """
    parser = argparse.ArgumentParser()

    action_help = "Specify the action you want to take, 'shift_away', 'shift_back', 'health_check'"
    parser.add_argument("-a", "--action", help=action_help, dest="action", required=True)

    edge_to_target_help = "Specify the edge ID to target with the given action, found from mwcore UI when viewing the specific edge page"
    parser.add_argument("--edge_to_shift", help=edge_to_target_help, dest="edge_id_to_target", required=True)

    edge_ids_help = "Specify all edge ID's space separated which take the same function as the target, need to include the target edge ID as well as any neighbour edge's"
    parser.add_argument("--all_edge_ids", help=edge_ids_help, dest="mwedge_ids", required=True, nargs="+")

    mwcore_address_help = "specify the url for the mwcore connected to the given edge's, only 1 mwcore is supported!"
    parser.add_argument("--mwcore_address", help=mwcore_address_help, dest="mwcore_address", required=True)

    grafana_user_help = "Please provide the username for MWCORE grafana API on the mwcore, this is mandatory for pre/post health checks around capacity"
    parser.add_argument("--grafana_user", help=grafana_user_help, dest="grafana_user", required=True)

    grafana_pass_help = "Provide the grafana password for MWCORE grafana API for the given username, this is mandatory for the pre/post health checks around capacity"
    parser.add_argument("--grafana_pass", help=grafana_pass_help, dest="grafana_pass", required=True)

    stb_state_file_path_help = "provide the path to save the STB state for pre/post snapshots and comparision"
    parser.add_argument("--stb_state_file", help=stb_state_file_path_help, dest="stb_state_filepath", required=True)

    output_state_filepath_help = "provide the path to save the Output state csv to support automated shift back based on previous paused/unpaused state"
    parser.add_argument("--output_state_file", help=output_state_filepath_help, dest="output_state_filepath", required=True)

    mwedge_ssh_user_help = "Provide the username to ssh to all the edge's this must be a single username for all which supports health checking"
    parser.add_argument("--edge_ssh_user", help=mwedge_ssh_user_help, dest="mwedge_ssh_user", required=True)

    mwedge_ssh_pass_help = "Provide the password for the given username to ssh to the mwedge's alternatively provide 'key' to enable key based ssh"
    parser.add_argument("--edge_ssh_pass", help=mwedge_ssh_pass_help, dest="mwedge_ssh_pass", required=True)

    ssh_key_path_help = "provide the system path to find the ssh key if using key based ssh login"
    parser.add_argument("--ssh_key_path", help=ssh_key_path_help, dest="ssh_key_path", required=False, default=False)

    cron_help = "Use this argument if this tool is being triggered via cron or another automation method with no ability to provide dynamic cli input"
    parser.add_argument("--cron", help=cron_help, dest="cron", default=False, action="store_true")

    api_key = "provide the standard MWCore API key from the UI"
    parser.add_argument("--api_key", help=api_key, dest= "api_key", required= True)

    emails_help = "Provide space separated list of emails to provide notifications to"
    parser.add_argument("--emails", help=emails_help, dest="emails", required=False, default="support@techex.co.uk", nargs="+")

    cut_off_hour_help = "provide the hour to stop automation if shifting away"
    parser.add_argument("--cut_off_hour", help= cut_off_hour_help, dest="cut_off_hour", required=False, default=9, type=int)

    cut_off_min_help = "provide the min to stop automation if shifting away"
    parser.add_argument("--cut_off_min", help=cut_off_min_help, dest="cut_off_min", required=False, default=30, type=int)

    arguments = parser.parse_args()
    return arguments


debug = True
arguments = parse_args()
print (arguments)

action = arguments.action
#'shift_away', 'shift_back', 'health_check'
if action.lower() == "shift_away":
    if debug: print("Triggering Shift away")
    global global_cut_off_hour
    global global_cut_off_min

    global_cut_off_min = int(arguments.cut_off_min)
    global_cut_off_hour= int(arguments.cut_off_hour)

    traffic_shift(edge_id_to_shift=arguments.edge_id_to_target, mwedge_ids=arguments.mwedge_ids,
                  mwcore_address=arguments.mwcore_address,
                  grafana_user=arguments.grafana_user, grafana_pass=arguments.grafana_pass,
                  api_key=arguments.api_key,
                  stb_state_filepath=arguments.stb_state_filepath,
                  output_state_filepath=arguments.output_state_filepath,
                  mwedge_ssh_user=arguments.mwedge_ssh_user, mwedge_ssh_pass=arguments.mwedge_ssh_pass,
                  cron=True, ssh_key_path=arguments.ssh_key_path, emails=arguments.emails)

if action.lower() == "shift_back":
    if debug: print ("Triggering shift back - NOT IMPLEMENTED")
    #traffic_shift_back()

if action.lower() == "health_check":
    if debug: print("Triggering health check - NOT IMPLEMENTED")


"""
if shift:
    pass
    #Function to carry out all checks and processes for shifting away!
    #Capacity check
    #output state check
    #STB state check
    #Linux health check for all edges'
    #store stb state and email to support@techex
    #store output state + email??

    #pause all outputs

    #wait 120 seconds to allow STB's to re-connect
    #linux health check on remaining edges'
    #run stb post snapshot
    #stb snapshot compare
    #capacity check all edges - Need to ensure safe capacity and also shifted edge is at 0, email if less than 10% capacity
    #trigger 5 min looping edge health check!
    #end/sys.exit() at 8am UTC (8am in winter, 9am in summer time)
    #datetime.now(tz = timezone.utc)

elif shift_back:
    pass
    #Function to shift back manually
    #run linux health check
    #Run STB state snapshot
    #Unpause outputs
    #Check for status csv being provided, if not prompt for it or ask for confirmation to unpause all.
    #Unpause all outputs
    #Run STB state post snapshot and compare
    #run linux health check post unpause
    #Email status to support@techex.co.uk

elif health_check:
    pass
    #Function to health check remaining edge's
    #run linux health check
    #Run capacity check
else:
    print("no operation requested, ending")
    
"""
"""
Script to trigger an MWEdge Traffic shift

1- hit time and trigger
2- Pre traffic shift checks
- a - STB state (store for compare after output pause)
        - Store as file - supported
        - Send email details for this - supported
- b - Output state (Store for post checks and enabling correct outputs
        - Store details in some standard format with reference to the specific edge ID in file name
        - Stored details need to be used in shift back scripting
        - Email details as well
- c - Edge health ???
        - CPU/Load average??
        - Memory?
- d - capacity checker

3- Pause all outputs (Reference output from 2b)

4- Post traffic shift checks
- a - STB state (Compare to 2a allowing for a variance to support some boxes dropping off or coming online at the same time)
- b - capacity checker
- c - Edge health ??

5 - every 5 minuets
- a - Run capacity checker
- b - Run health checker ???

6 - Hit 9am
- a - email support@techex confirm state
- b - stop looping query

7 - Humans take over

8 - Human upgrade
        - This could be a script/ansible playbook that we trigger to trigger the upgrade, reboot, health check and unpause of outputs.

9 - Standalone server health check (2c) on upgraded server

10 - Unpause outputs based on output from pre-shift state

11 - Email to support@techex and SIS to confirm upgrade


Any failure we email support@techex, some trigger to 365 phone number??
Any failure triggers shift back/unpause
"""

