from Techex import mwfunctions
import json


def mwedge_srt_output_passphrase_update(BearerKey, mwcore, row, edge_config):
    #EDGE update:
    for edge_id in row["edges"].split(","):
        config = edge_config[edge_id]
        for output in config["configuredOutputs"]:
            output_search = row.get("outputName", row["channel"])
            if output_search == output["name"]:
                encryption_type = row.get("encryption", 16) #default to 16
                data = {
                    "options": {
                        "passphrase": row["passphrase"],
                        "encryption": 16
                    }
                }
                mwfunctions.mwedge_update_output(edge_id, output["id"], BearerKey, json.dumps(data), mwcore)


def mwcore_channel_passphrase_update(BearerKey, mwcore, row, channel_config):
    #Channel update:
    for mwchannel in channel_config:
        print ("mwchannel name: {}, row channel:{}".format(mwchannel["name"], row["channel"]))
        if row["channel"] == mwchannel["name"]:
            print ("found channel now updating")
            mwchannel_to_update = mwchannel.copy()
            for source in mwchannel_to_update["sources"]:

                if source["protocol"] == 7:
                    print("Skipping SYE channels")
                if source["protocol"] == 6: #looking for srt channels
                    options = source.get("options", False)
                    if options:
                        source["options"]["srt"]["passphrase"] = row["passphrase"]
                        source["options"]["srt"]["encrypted"] = True
                    else:
                        source["options"] = {
                            "srt": {
                                "encrypted": True,
                                "passphrase": row["passphrase"]
                            }
                        }

                else:
                    print ("Source isn't SRT skipping")
            print(mwchannel_to_update)
            mwfunctions.mwcore_update_channel(BearerKey, mwcore, mwchannel_to_update["_id"], json.dumps(mwchannel_to_update))
