import json

class stream_output(object):
    """
    Class for stream output
    """
    def __init__(self, name, stream_id, protocol, options):
        self.name = name
        self.stream = stream_id
        self.protocol = protocol
        self.options = options.__dict__

    def data_to_json(self):
        return json.dumps(self.__dict__)

class srt_stream_output_options(object):
    def __init__(self, port, srt_type=0):
        self.type = srt_type
        self.port = port


    def data_to_json(self):
        return json.dumps(self.__dict__)


class udp_stream_output_options(object):
    def __init__(self, port, address):
        self.address = address
        self.port = port



"""
    SRT_data= {
        "stream": stream_id,
        "options": {
            "type": 0,
            "maxConnections": 5,
            "maxBandwidth": 2147483647,
            "chunkSize": 1316,
            "encryption": 16,
            "port": 9025,
            "passphrase": "football2020"
        },
        "protocol": "SRT",
        "name": "first SRT",
    }
    
    UDP_data= {
      "stream": "822e35ba82dc52c4d36d6e98ae62773f1f78a522a1933271",
      "options": {
        "ttl": 5,
        "networkInterface": "195.181.164.33",
        "encryptionType": "BISS2 Mode-1",
        "address": "1.1.1.1",
        "port": 1,
        "encryptionPercentage": 10,
        "encryptionKeyParity": "odd",
        "encryptionOddKey": "00000000000000000000000000000000",
        "encryptionEvenKey": "10000000000000000000000000000000"
      },
      "name": "test",
      "protocol": "UDP",
      "id": "7b343d85963af89cb47d55c008ba5e371b85aac8a8c8d91a",
      "mwedge": "5f7de1627def3af9fff8a233"
    }
    """