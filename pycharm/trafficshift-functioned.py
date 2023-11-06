import os
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
import sys
sys.path.append("..")

import threading
import time
import argparse
import traceback
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
        failure_text= "Health check raised exception: {} - {}".format(e, traceback.format_exc())
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
    periodic_health_check_poller.cancel()
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

    if now.hour > global_cut_off_hour:
        #Done to support the case where cut min is 30 and cut hour is 9 but time is 10:00 or later.
        end_reoccuring_healthcheck()
        return

    if now.minute >= global_cut_off_min and now.hour >= global_cut_off_hour:
        end_reoccuring_healthcheck()
        return

    print("Cut off time of {}:{} UTC hasn't been found\n waiting for interval to re-check".format(global_cut_off_hour, global_cut_off_min))


def tshift_pre_checks(
    api_key, mwedge_ids, mwcore_address, edge_id_to_shift, mwedge_ssh_user, mwedge_ssh_pass, ssh_key_path,
    grafana_user, grafana_pass, stb_state_filepath, emails="support@techex.co.uk", debug=False, cron=False):
    """
    Funcionalizing all pre-checks so they can be called separately
    :param api_key: Standard API key
    :param mwedge_ids: - List of neighbour edge ID's including the edge ID for the edge we want to shift
    :param mwcore_address: - Standard http/https url for the MWCore
    :param edge_id_to_shift: - Specific Edge ID to shift.
    :param mwedge_ssh_user: - SSH username when logging into hosts
    :param mwedge_ssh_pass: - SSH password for logging into hosts, provide "key" to login via Keys
    :param ssh_key_path: - SSH Key path for the local key file on the host
    :param grafana_user: - Login for MWCore Grafana API, not the login for the grafana ui
    :param grafana_pass: - Password for above login
    :param stb_state_filepath: - Where to save STB state CSV
    :param emails: - list of emails to send status emails to
    :param debug: - True/False for if we debug or not
    :param cron: - True/False if we are running via cron, if cron we stop any script blocking CLI input
    :return:
    """
    debug = True
    #########################################
    # Get IP's
    mwedges, failure = trafficshift_checks.get_mwedge_ips(api_key, mwedge_ids, mwcore_address, debug=debug)
    if not mwedges:
        failure_text = "Can't seem to get IP detail: {} \n failing pre-checks".format(failure)
        print(failure_text)
        subject = "Traffic shift for {} failed health check connected to {}".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)
        return False, False, False
    ##########################################
    # Health check
    health_check, state  = trafficshift_checks.edge_health_check(mwedges, mwedge_ssh_user, mwedge_ssh_pass, mwcore_address,
                                                  ssh_key_path, debug=debug, emails=emails)
    if not health_check:
        # Health check function has email function for failure no need to do it here
        return False, False, False

    ###########################################
    # Capacity check
    state = trafficshift_checks.srt_capacity_check(api_key, mwcore_address, mwedge_ids, grafana_user, grafana_pass,
                                                   edge_id_to_shift, emails, debug=debug, post_check=False)
    if not state:
        # Capacity check includes the email functions
        return False, False, False
    #################################################################################################
    # STB state
    devices_state = trafficshift_checks.traffic_shift_get_stb_state(api_key, mwcore_address, mwedge_ids,
                                                                    edge_id_to_shift, emails, debug=debug)
    if not devices_state:
        # Email in the function already.
        return False, False, False
    ###############################################################################################
    # STB write/email
    try:
        trafficshift_checks.save_stb_state(devices_state, stb_state_filepath, edge_id_to_shift, mwcore_address, emails,
                                           cron=cron)
    except Exception as e:
        print("Something went wrong either writing to CSV or emailing stb state\nException:{} - {}".format(e, traceback.format_exc()))

    print("Pre-Traffic shift checks completed successfully")
    return True, devices_state, mwedges


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

    state, devices_state, mwedges = tshift_pre_checks(api_key, mwedge_ids, mwcore_address, edge_id_to_shift, mwedge_ssh_user, mwedge_ssh_pass,
                      ssh_key_path, grafana_user, grafana_pass, stb_state_filepath, emails=emails,
                      debug=debug, cron=False)

    if not state:
        print("Pre-checks failed, stopping traffic shift")
        return False
    ###############################################################################################
    #Output state capture/Pause

    if not cron:
        pass
    input("Pre-checks done, Are you ready to pause outputs?")

    output_state = trafficshift_checks.traffic_shift_pause_outputs(api_key, mwcore_address, mwedge_ids, edge_id_to_shift, emails, output_state_filepath, debug=debug, cron=False)

    ###############################################################################################
    #wait 120 seconds to allow STB's to re-connect
    pause = 10 #TODO: set this back to 120s
    print ("Pausing {} seconds to allow STB's to re-connect".format(pause))
    time.sleep(pause)

    ###############################################################################################
    #linux health check on remaining edges
    post_failed = False
    try:
        health_check, state = trafficshift_checks.edge_health_check(mwedges, mwedge_ssh_user, mwedge_ssh_pass, mwcore_address, ssh_key_path, debug=debug, post_check=True, emails=emails)
        if not health_check:
            post_failed = True
            #Set var to track post check state
    except Exception as e:
        failure_text = "Something failed while trying to post check after pausing outputs, please check into this ASAP!! {} - {}".format(e, traceback.format_exc())
        post_failed = True
        print (failure_text)
        #Only need to email in the case that we find exception, function called already emails in case of failure
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

    devices_state_post = trafficshift_checks.traffic_shift_get_stb_state(api_key, mwcore_address, mwedge_ids_post_active, edge_id_to_shift, emails, debug=debug, post_check=True)
    if not devices_state_post:
        post_failed = True
        #Emailed in the function
        #Try except in the function

    if devices_state:
        # STB write/email
        stb_state_filepath_split = stb_state_filepath.split(".")
        #Split filename from .csv
        stb_state_filepath_post = stb_state_filepath_split[0] + "_post_state." + stb_state_filepath_split[1]
        #Form the post state file path adding back on the .csv .split() removes the delimiter so need to include that.
        try:
            trafficshift_checks.save_stb_state(devices_state, stb_state_filepath_post, edge_id_to_shift, mwcore_address,
                                               emails,
                                               cron=cron)
        except Exception as e:
            print("Something went wrong either writing to CSV or emailing stb state\nException:{} - {}".format(e, traceback.format_exc()))

    ###############################################################################################
    # stb snapshot compare

    devices_state_pre = devices_state
    stb_state = False
    try:
        if debug: print("Triggering STB comparison")
        stb_state, stb_detail = stb_snapshot.compare_stb_state(devices_state_pre, devices_state_post, debug=debug, cron=cron)
        #STB state is the stats for each failure reason, external_ip_state_change for example
        #STB detail is the formed string showing what each STB failed for
        if debug: print("Completed STB comparison without exceptions")
    except Exception as e:
        post_failed = True
        failure_text = "Something caught an exception when post checking STB State {} - {}".format(e, traceback.format_exc())
        print(failure_text)
        subject = "!!!FAILURE!!STB post Snapshot failed! {} - {}".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)

    if debug: print("finished getting STB state")
    """
        stb_state = {
            "total_stb" : len(post_state),
            "online_state_change" : 0,
            "decoding_state_change" : 0,
            "channel_state_change" : 0,
            "external_ip_state_change" : 0,
            "decoding_error_state_change" : 0,
        }
    """
    if not stb_state:
        if debug: print("Can't run stb_state_evaluation as we don't have stb_state/detail as function failed to run correctly")
    else:
        state = trafficshift_checks.stb_state_evaluation(stb_state, stb_detail, edge_id_to_shift, mwcore_address, emails=emails,  debug=debug)
    if not state:
        if debug: print("Failed to run STB state evaluation successfully")
        post_failed = True

    #try except in function, emails in function if failed

    ###############################################################################################
    #capacity check all active edges

    state = trafficshift_checks.srt_capacity_check(api_key, mwcore_address, mwedge_ids,grafana_user, grafana_pass, edge_id_to_shift, emails, debug=debug, post_check=True)
    if not state:
        post_failed = True
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

    interval = 60*2  #2 mins between checks
    #TODO: Review and decide on the correct interval (Currently 2 mins maybe 5 Mins? or longer?)
    global periodic_health_check_poller
    periodic_health_check_poller = setInterval(interval, trigger_health_check)
    periodic_health_check_poller.start()

###################################################


def traffic_shift_back(edge_id_to_shift, mwedge_ids, mwcore_address, api_key, output_state_filepath, grafana_user, grafana_pass,
    stb_state_filepath,
    mwedge_ssh_user="root", mwedge_ssh_pass="password", ssh_key_path=False, emails="support@techex.co.uk"):

    #####
    #Pre checks
    ##Linux health
    #####
    mwedges, failure = trafficshift_checks.get_mwedge_ips(api_key, mwedge_ids, mwcore_address, debug=debug)
    if not mwedges:
        failure_text = "Can't seem to get IP detail: {} \n failing pre-checks".format(failure)
        print(failure_text)
        subject = "Traffic shift for {} failed health check connected to {}".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)
        return False, False

    ##########################################
    # Health check
    state = trafficshift_checks.edge_health_check(mwedges, mwedge_ssh_user, mwedge_ssh_pass, mwcore_address,
                                                  ssh_key_path, debug=debug, emails=emails)
    if not state:
        # Health check function has email function for failure no need to do it here
        return False, False

    #####
    #Unpause outputs
    unpause_failure = False
    try:
        post_response = edge_output_processes.un_pause_edge_outputs(edge_id_to_shift, api_key, mwcore_address, debug=debug, file=output_state_filepath)
        # If the above call fails it'll return the failing post response for us to print on.
        # If it passes we will get back the last post response which would have a code 200
        if "20" not in str(post_response.status_code):
            failure_text = "Failed to un pause outputs {}".format(post_response)
            print(failure_text)
            unpause_failure = True

    except Exception as e:
        failure_text ="Something failed while trying to unpause the edge outputs {}, {}".format(e, traceback.format_exc())
        print(failure_text)
        unpause_failure = True

    if unpause_failure:
        subject = "Traffic shift back for {} failed to unpause outputs connected to {}".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)

        #No return as we want to do post checks to make sure everything is healthy!

    print("Sleeping for 30 seconds")
    time.sleep(30)

    ####
    #Post checks
        #Linux health
        #capacity???
        #STB state
            #get state
            #load old post pause state
                # stb_state_filepath_split = stb_state_filepath.split(".")
                # Split filename from .csv
                # stb_state_filepath_post = stb_state_filepath_split[0] + "_post_state." + stb_state_filepath_split[1]
            #compare

    ##########################################
    # Health check
    state = trafficshift_checks.edge_health_check(mwedges, mwedge_ssh_user, mwedge_ssh_pass, mwcore_address,
                                                  ssh_key_path, debug=debug, emails=emails)
    #No need to state check just email which is in the function above

    ###########################################
    # SRT capacity review
    state = trafficshift_checks.srt_capacity_check(api_key, mwcore_address, mwedge_ids, grafana_user, grafana_pass,
                                                   edge_id_to_shift, emails, debug=debug, post_check=unpause_failure)
    #Post check using pause failure var. If we failed to pause then that will be True and hence we need to capacity check based on a edge being shifted
    #If we didn't fail the unpause then do a standard capacity check!
    #No need to review the state email and try/except already handled in the function

    ###############################################################################################
    # run stb post snapshot

    # Get active edge id's
    mwedge_ids_post_active = []
    for id in mwedge_ids:
        if edge_id_to_shift == id and unpause_failure:
            #Only skip adding this if the unpause failed for some reason!
            continue
        else:
            mwedge_ids_post_active.append(id)

    devices_state_post_unpause = trafficshift_checks.traffic_shift_get_stb_state(api_key, mwcore_address,
                                                                         mwedge_ids_post_active, edge_id_to_shift,
                                                                         emails, debug=debug, post_check=True)


    try:
        stb_state_filepath_split = stb_state_filepath.split(".")
        #Split filename from .csv
        stb_state_filepath_post = stb_state_filepath_split[0] + "_post_state." + stb_state_filepath_split[1]
        devices_state_post_pause_list = csvfunctions.read_csv_to_dict(stb_state_filepath_post)
        #Above is list of dicts we need to re-format to dict of dict

        devices_state_post_pause = {}
        for x in devices_state_post_pause_list:
            # will be the dict to represent the line in the csv and hence the device state
            devices_state_post_pause[x["id"]] = x

        stb_state = False
        try:
            if debug: print("Triggering STB comparison")
            stb_state, stb_detail = stb_snapshot.compare_stb_state(devices_state_post_unpause, devices_state_post_pause, debug=debug,
                                                                   cron=True)
            # STB state is the stats for each failure reason, external_ip_state_change for example
            # STB detail is the formed string showing what each STB failed for
            if debug: print("Completed STB comparison without exceptions")
        except Exception as e:
            post_failed = True
            failure_text = "Something caught an exception when post checking STB State {} - {}".format(e, traceback.format_exc())
            print(failure_text)
            subject = "!!!FAILURE!!STB post Snapshot failed! {} - {}".format(edge_id_to_shift, mwcore_address)
            misc_functions.send_email_techexbot(failure_text, subject, emails)

        if debug: print("finished getting STB state")
        """
            stb_state = {
                "total_stb" : len(post_state),
                "online_state_change" : 0,
                "decoding_state_change" : 0,
                "channel_state_change" : 0,
                "external_ip_state_change" : 0,
                "decoding_error_state_change" : 0,
            }
        """
        if not stb_state:
            if debug: print(
                "Can't run stb_state_evaluation as we don't have stb_state/detail as function failed to run correctly")
        else:
            state = trafficshift_checks.stb_state_evaluation(stb_state, stb_detail, edge_id_to_shift, mwcore_address,
                                                             emails=emails, debug=debug)
        if not state:
            if debug: print("Failed to run STB state evaluation successfully, either hit exception or the checks failed ")
            unpause_failure = True
    except Exception as e:
        unpause_failure = True
        failure_text = "An exception was found trying to check post paused against post unpaused STB state for exception: {} - {}".format(e, traceback.format_exc())
        print(failure_text)
        subject = "!!!FAILURE!!STB post Snapshot failed! {} - {}".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)

    text = "{} has been shifted back successfully, all capacity and host health checks have been completed.".format(edge_id_to_shift)
    print(text)
    subject = "!!!Success!!Edge {} has been shifted back into service {}".format(edge_id_to_shift, mwcore_address)
    misc_functions.send_email_techexbot(text, subject, emails)

def parse_args():
    """
    Standard function to parse input args.
    :param:
        n/a
    :return:
        arguments - parser object where the dest vars can be referenced like .file or .streams
    """
    parser = argparse.ArgumentParser()

    action_help = "Specify the action you want to take, 'shift_away', 'shift_back', 'pre_health_check'"
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
    parser.add_argument("--edge_ssh_user", help=mwedge_ssh_user_help, dest="mwedge_ssh_user", required=False, default="root")

    mwedge_ssh_pass_help = "Provide the password for the given username to ssh to the mwedge's alternatively provide 'key' to enable key based ssh"
    parser.add_argument("--edge_ssh_pass", help=mwedge_ssh_pass_help, dest="mwedge_ssh_pass", required=False, default="key")

    ssh_key_path_help = "provide the system path to find the ssh key if using key based ssh login"
    parser.add_argument("--ssh_key_path", help=ssh_key_path_help, dest="ssh_key_path", required=False)

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
                  cron=arguments.cron, ssh_key_path=arguments.ssh_key_path, emails=arguments.emails)

if action.lower() == "shift_back":
    if debug: print ("Triggering shift back - NOT IMPLEMENTED")
    traffic_shift_back(arguments.edge_id_to_target, arguments.mwedge_ids, arguments.mwcore_address, arguments.api_key,
                       arguments.output_state_filepath, arguments.grafana_user, arguments.grafana_pass,
                       arguments.stb_state_filepath, mwedge_ssh_user=arguments.mwedge_ssh_user, mwedge_ssh_pass=arguments.mwedge_ssh_pass,
                       ssh_key_path=arguments.ssh_key_path, emails=arguments.emails)


if action.lower() == "pre_health_check":
    if debug: print("Triggering health check")
    state, devices_state, mwedges = tshift_pre_checks(arguments.api_key, arguments.mwedge_ids, arguments.mwcore_address, arguments.edge_id_to_target,
                                                      arguments.mwedge_ssh_user, arguments.mwedge_ssh_pass,
                                                      arguments.ssh_key_path, arguments.grafana_user, arguments.grafana_pass, arguments.stb_state_filepath,
                                                      emails=arguments.emails,
                                                      debug=debug, cron=arguments.cron)

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

