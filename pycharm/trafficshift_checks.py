from GenericCodeFunctions import linux_functions, misc_functions, csvfunctions
from Techex import capacity_check_functions, mwfunctions, stb_snapshot, edge_output_processes

def capacity_review(channel_util, debug=False, post_check=False):
    #Channel_util will be list of dicts in this format:
    # {'name': 'Greyhound Spanish (3)', 'Total_cap': 600, 'Total_util': 120,
    # 'AMS-MWEDGE-02-cap': 200, 'AMS-MWEDGE-02-util': 24,
    # 'FRA-MWEDGE-02-cap': 200, 'FRA-MWEDGE-02-util': 41,
    # 'LON-MWEDGE-02-cap': 200, 'LON-MWEDGE-02-util': 55}
    if debug: print("Starting STB capacity review")
    for channel in channel_util:
        if not isinstance(channel, dict):
            #Ensure the data being returned is correct, should always be a full list of dicts.
            return False, "bad list of dicts"
        if debug: print("checking channel: {}".format(channel["name"]))
        total_cap = channel.get("Total_cap", False)
        total_util = channel.get("Total_util", False)
        active_edges  = 0
        print (channel)
        for key, value in channel.items():
            if "-cap" in key and value >0:
                active_edges += 1

        print ("Active edges: {}".format(active_edges))

        no_edges_post_shift = active_edges-1  # -1 to remove 1 edge for the one we will traffic shift/one that could fail
        if no_edges_post_shift <=0 and not post_check:
            print("No redundant edge's, failing capacity review")
            return False, "no redundant Edge"
        if debug: print("total_cap {}, total_util {}".format(total_cap,total_util))
        if total_util == 0:
            if debug: print("total util is 0, skipping util checks as can't devide by 0")
            continue
        if total_cap and total_util:
            if debug: print("found total util and cap")
            if post_check:
                post_shift_cap = total_cap
            else:
                post_shift_cap = (total_cap/active_edges)*no_edges_post_shift
                if debug:
                    print("running check calc ({} / {} = {} ) * {} = {}".format(
                        total_cap, active_edges, total_cap/active_edges, no_edges_post_shift, post_shift_cap
                    ))
            percent_util = total_util/post_shift_cap
            if debug: print("percent util = {}/{} = {}".format(total_util, post_shift_cap, percent_util))
            if percent_util < 0.9:
                print ("channel {} has enough capacity to lose an edge".format(channel.get("name")))
            elif percent_util >= 0.9:
                print ("Channel {} too highly utilized, failing check!".format(channel.get("name")))
                return False, "SRT_listener capacity higher than 90% when assuming one edge offline"
        else:
            return False, "no totals"

    return True, "all good"


def edge_health_check(mwedges, mwedge_ssh_user, mwedge_ssh_pass, mwcore_address, ssh_key_path, debug=False, post_check= False, emails="support@techex.co.uk"):
    for edge_id, edge_detail in mwedges.items():
        if ssh_key_path:

            health_check, state = linux_functions.linux_host_health_check(edge_detail["ip"], mwedge_ssh_user, "key", key_path=ssh_key_path, debug=debug)
        else:
            health_check, state = linux_functions.linux_host_health_check(edge_detail["ip"], mwedge_ssh_user, mwedge_ssh_pass, debug=debug)
        if not health_check:
            #Something failed the pre-check so quit out
            failure_text = "An Edge {} - {} is not healthy because {}".format(edge_id, mwcore_address, state)
            print(failure_text)
            if post_check:
                subject = "!!!FAILURE!! An edge is failing health check after peer is shifted {} - {}".format(edge_id, mwcore_address)
            else:
                subject = "Traffic shift for {} failed health check connected to {}".format(edge_id, mwcore_address)
            misc_functions.send_email_techexbot(failure_text, subject, emails)
    #No shift back here let the calling script make that decision!
    return health_check, state


def stb_state_evaluation(stb_state, stb_detail, edge_id_to_shift, mwcore_address, emails="support@techex.co.uk",  debug=False):
    if debug: print("Starting STB state evaluation")
    reason= ""
    try:
        failed_state = False
        if stb_state["online_state_change"] > (stb_state["total_stb"] / 100) * 10:  # Supporting 10% variance
            failed_state = True
            reason = "{} {} devices went offline which is higher than 10%\n".format(reason, stb_state["online_state_change"])
        if debug: print("passed online state change"
                        "")
        if stb_state["decoding_state_change"] > (stb_state["total_stb"] / 100) * 2:  # Supporting 2% variance
            failed_state = True
            reason = "{} {} devices went into a bad decoding state and couldn't lock onto a new SRT source\n".format(
                reason, stb_state["decoding_state_change"])
        if debug: print("passed decoding state change")

        if stb_state["external_ip_state_change"] > (
            stb_state["total_stb"] / 100) * 25:  # Supporting 25% variance as a few doing this isn't a major issue
            failed_state = True
            reason = "{} {} devices changed their external ip which is worrying\n".format(reason, stb_state[
                "external_ip_state_change"])
        if debug: print("passed external IP state change")

        if stb_state["decoding_error_state_change"] > (stb_state["total_stb"] / 100) * 2:  # Supporting 2% variance
            failed_state = True
            reason = "{} {} devices went into a bad decoding state\n".format(reason,
                                                                             stb_state["decoding_error_state_change"])
        if debug: print("completed decoding error state change check")

        if failed_state:
            post_failed = True
            reason = "The STB state comparison failed for the following reasons:\n{}\nSTBs with issue:\n{}".format(
                reason, stb_detail)
            print(reason)
            subject = "!!!FAILURE!!! STB State comparison failed post shift away {} - {}".format(edge_id_to_shift,
                                                                                                 mwcore_address)
            misc_functions.send_email_techexbot(reason, subject, emails)
            return False
        if debug: print("completed STB state checking")
        return True
    except Exception as e:
        post_failed = True
        failure_text = "Something caught an exception when post checking STB State {}".format(e)
        print(failure_text)
        subject = "!!!FAILURE!!STB post Snapshot failed! {} - {}".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)
        return False


def srt_capacity_check(api_key, mwcore_address, mwedge_ids,grafana_user, grafana_pass, edge_id_to_shift, emails, debug=False, post_check=False):
    failed = False
    state = True
    try:
        # DO THE CHECKS
        print("getting channel capacity/util")
        channel_util = capacity_check_functions.capacity_check_function(api_key, mwcore_address, mwedge_ids,
                                                                        grafana_user, grafana_pass, debug=debug)
        print("got data, reviewing the capacity")
        state, reason = capacity_review(channel_util, debug=debug, post_check=post_check)
    except Exception as e:
        failed = True
        failure_text = "An exception was raised when running the capacity checker: {}".format(e)
        print(failure_text)

    if not state:  # Checking the output from the capacity check review
        print("something went wrong with the capacity check {}".format(reason))
        failure_text = "shifting {} failed on pre-capacity checks for '{}' reason not shifting and failing process\nSee attached channel_util output:".format(
            edge_id_to_shift, reason)
        for channel in channel_util:
            failure_text = "{} \n{}".format(failure_text, channel)

    if failed or not state:  # Email if a failure
        if post_check:
            subject = "!!!FAILURE!! STB Capacity is in a bad state {} - {}".format(edge_id_to_shift, mwcore_address)
        else:
            subject = "Traffic shift for {} failed pre-check connected to {}".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)
        return False
    else:
        print("capacity check passed")
        return True


def get_mwedge_ips(api_key, mwedge_ids, mwcore_address, debug=False):
    #TODO Migrate this to mwfunction
    BearerKey = "Bearer {}".format(api_key)
    mwedges = {}
    print(mwedge_ids)
    for mwedge in mwedge_ids:
        if debug: print("Getting IP for {}".format(mwedge))
        try:
            public_ip = mwfunctions.mwedge_get_public_ip(mwedge, BearerKey, mwcore_address, debug=debug)
            if debug: print("Public IP found: {}".format(public_ip))
        except Exception as e:
            failure = "something failed getting public IP: {}".format(e)
            print(failure)
            return False, failure
        mwedges[mwedge] = {"ip": public_ip}
    return mwedges, "all good"


def traffic_shift_get_stb_state(api_key, mwcore_address, mwedge_ids, edge_id_to_shift, emails, debug=False, post_check=False):
    failed = False
    devices_state = False
    exception_reason = ""
    try:
        devices_state = stb_snapshot.get_stb_state(api_key, mwcore_address, mwedge_ids, debug=debug)
    except Exception as e:
        failed = True
        exception_reason = e

    if not devices_state or failed == True:  # Either the function returned a false or we got an exception
        failure_text = "We couldn't get all MWEdge stats\nCore: {}\nEdgeID's: {}".format(mwcore_address, mwedge_ids)
        if failed:
            failure_text = "{}\nException: {}".format(failure_text, exception_reason)
        print(failure_text)
        if post_check:
            subject = "!!!FAILURE!!STB post Snapshot failed! {} - {}".format(edge_id_to_shift, mwcore_address)
        else:
            subject = "Traffic shift for {} connected to {} failed snapshot STBs".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)
        return False
    return devices_state


def save_stb_state(devices_state, stb_state_filepath, edge_id_to_shift, mwcore_address, emails, cron=False):
    devices_state_list = []
    devices_state_text = ""
    # Need the dict in list of dict format rather than dict of dict
    for id, dict in devices_state.items():
        devices_state_list.append(dict)
        devices_state_text = "{}\n{}".format(devices_state_text, dict)
    csvfunctions.write_dict_to_csv(stb_state_filepath, devices_state_list, cron)
    # Also email to ensure we have some state saved in case the file doesn't write/is lost??
    subject = "Traffic shift STB state for {} - {}".format(edge_id_to_shift, mwcore_address)
    misc_functions.send_email_techexbot(devices_state_text, subject, emails)


def traffic_shift_pause_outputs(api_key, mwcore_address, mwedge_ids, edge_id_to_shift, emails, output_state_filepath, debug=False, cron=False):
    try:
        output_state = edge_output_processes.pause_edge_outputs(edge_id_to_shift, api_key, mwcore_address, file=output_state_filepath, debug=debug, cron=cron)
    except Exception as e:
        failure_text = "Something failed while trying to pause outputs, please check into this ASAP!! {}".format(e)
        print(failure_text)
        subject = "!!!FAILURE PAUSING OUTPUTS!!!! {} - {}".format(edge_id_to_shift, mwcore_address)
        misc_functions.send_email_techexbot(failure_text, subject, emails)
        return False

    output_state_text = "Outputs where paused successfully! Please see the current state below and also saved at {}\n".format(output_state_filepath)
    for x in output_state:
        output_state_text = "{}\n{}".format(output_state_text, x)
    subject = "Success! Outputs paused state inside {} - {}".format(edge_id_to_shift, mwcore_address)
    misc_functions.send_email_techexbot(output_state_text, subject, emails)
    return output_state