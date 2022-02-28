import json


class RequestData:
    """
    Hold request data for application. Set command type for shell command, or application command.
    Can be initated with params, or data can be added with encoded json string from recived tcp data transfer.

    @param type (string) : "shell" | "app"
    @param comand (string): command for application
    """

    # constructor
    def __init__(self, type=None, command=None) -> None:
        self.type       = type
        self.command    = command


    def parse_json(self, jsonData) -> None:
        """
        Extract data and populate fields from json string

        NOTE: Remember to decode data before using this method

        @param jsonData (string): json string
        """

        data = json.loads(jsonData)
        self.type       = data["type"]
        self.command    = data['command']
    

    def encode_data(self) -> bytes:
        """ transform object to encoded json string for tcp transfer """
        jsonData = json.dumps(self, default=lambda x: x.__dict__, sort_keys=True, indent=4)
        return jsonData.encode()