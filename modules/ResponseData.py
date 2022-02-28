import imp


import json

class ResponseData:

    def __init__(self, out = None, err = None, cwd = None) -> None:
        self.out = out
        self.err = err
        self.cwd = cwd


    def parse_json(self, jsonData) -> None:
        """
        Extract data and populate fields from json string

        NOTE: Remember to decode data before using this method

        @param jsonData (string): json string
        """
        
        data = json.loads(jsonData)

        self.out        = data["out"]
        self.err        = data["err"]
        self.cwd        = data["cwd"]


    def encode_data(self) -> bytes:
        """ transform object to encoded json string for tcp transfer """

        jsonData = json.dumps(self, default=lambda x: x.__dict__, sort_keys=True, indent=4)
        return jsonData.encode()

