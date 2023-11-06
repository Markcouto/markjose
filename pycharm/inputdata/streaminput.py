"""
This file for stream sources classes so we can define srt_stream_source for example and have the right data structure

"""

import json

class stream_source(object):
    """
    Class for streams
    """
    def __init__(self, name, stream_id, protocol, options, priority=0):
        self.name = name
        self.stream = stream_id
        self.protocol = protocol
        self.priority = priority
        self.options = options.__dict__

    def data_to_json(self):
        return json.dumps(self.__dict__)


class rtp_stream_source_options (object):
    def __init__(self, address, port, preserveHeaders, enableCorrection):
        self.address = address
        self.port = port
        if preserveHeaders:
            self.preserveHeaders = True
        if enableCorrection:
            self.enableCorrection = True

    def data_to_json(self):
        return json.dumps(self.__dict__)


class srt_stream_source_options(object):
    def __init__(self, address, port, chunkSize=1328,srt_type=0):
        self.type = srt_type
        self.address = address
        self.port = port
        self.chunkSize = chunkSize

    def data_to_json(self):
        return json.dumps(self.__dict__)


class dash7_stream_source_options(object):
    def __init__(self, address, port, protocol):
        self.sourceOne = {
            "address": address,
            "port": port,
            "protocol": protocol,
            "enabled": True
        }


class udp_stream_source_options(object):
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.transmission = 1

    def data_to_json(self):
        return json.dumps(self.__dict__)

"""
Example stream source
data = {
        "name": "pythonsource",
        "protocol": "SRT",
        "stream": stream_id,
        "etr290Enabled": True,
        "priority": 0,
        "options": {
            "type": 0,
            "chunkSize": 1316,
            "latency": 1000,
            "encryption": 16,
            "fecEnabled": False,
            "passphrase": "football2020",
            "address": "1.1.1.1",
            "port": 1
      }
    }


RTPnewsource= {
      "priority": 0,
      "options": {
            "type": 0,
            "chunkSize": 1316,
            "latency": 1000,
            "encryption": 0,
            "transmission": 1,
            "sourceAddress": "2.2.2.2",
            "preserveHeaders": true,
            "enableCorrection": true,
            "buffer": 100,
            "filterSsrc": null,
            "networkInterface": "10.12.5.197",
            "address": "1.1.1.1",
            "port": 5000
      },
      "stream": stream_id,
      "protocol": "RTP",
      "name": "rtp source with source address",
      "etr290Enabled": true,
    }

UDPnewsource= {
      "priority": 0,
      "options": {
            "transmission": 1,
            "sourceAddress": "2.2.2.2",
            "networkInterface": "10.12.53.152",
            "decryptionType": null,
            "address": "1.1.1.1",
            "port": 5000
      },
      "stream": stream_id,
      "name": "udpsource",
      "protocol": "UDP",
      "etr290Enabled": true,
    }
    
    
2022-7 source:
"stream": "d4b51e83597e70a46ab5c67e638c411b3ffbd714eb6a6291",
      "priority": 0,
      "options": {
        "buffer": 100,
        "sourceOne": {
          "enabled": true,
          "protocol": "SRT",
          "transmission": 1,
          "sourceAddress": null,
          "enableCorrection": true,
          "buffer": 100,
          "filterSsrc": null,
          "networkInterface": null,
          "useFEC": false,
          "decryptionType": null,
          "type": 0,
          "latency": 1000,
          "encryption": 16,
          "fecEnabled": false,
          "address": "1.1.1.1",
          "port": 1,
          "passphrase": "football2020"
        },
        "decryptionType": null,
        "sourceTwo": {
          "enabled": true,
          "protocol": "SRT",
          "transmission": 1,
          "sourceAddress": null,
          "enableCorrection": true,
          "buffer": 100,
          "filterSsrc": null,
          "networkInterface": null,
          "useFEC": false,
          "decryptionType": null,
          "type": 0,
          "latency": 1000,
          "encryption": 16,
          "fecEnabled": false,
          "address": "2.2.2.2",
          "port": 1,
          "passphrase": "football2020"
        }
      },
      "name": "sysadmin-7",
      "protocol": "2022-7",
      "id": "c713dd2387acc2616b2dd24687e11bf5011f3a3aed51bda3",
      "active": true,
      "etr290Enabled": true,
      "stopped": false,
      "exhausted": false,
      "mwedge": "5f50f130b99e798c3d34c4c4"
    }
"""