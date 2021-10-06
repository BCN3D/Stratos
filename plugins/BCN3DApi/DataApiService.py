from UM.Message import Message

from .AuthApiService import AuthApiService
from .SessionManager import SessionManager
from .http_helper import get, post


class DataApiService:
    #data_api_url = "https://api.bcn3d.com/data"
    data_api_url = "http://api.astroprint.test/v2"

    def __init__(self):
        super().__init__()
        if DataApiService.__instance is not None:
            raise ValueError("Duplicate singleton creation")

        DataApiService._instance = self
        self._auth_api_service = AuthApiService.getInstance()

    def sendGcode(self, gcode_path, gcode_name):
        headers = {"Authorization": "Bearer {}".format(self._auth_api_service.getToken())}
        files = {"file": (gcode_path, open(gcode_path, "rb"))}
        data = {"setup": "{name : %s}" % gcode_name}
        response = post(self.data_api_url + "/printfiles", data, headers, files)
        if 200 <= response.status_code < 300:
            #response_message = response.json()
            message = Message("The gcode has been sent to the cloud successfully", title="Gcode sent")
            message.show()
        else:
            message = Message("There was an error sending the gcode to the cloud", title="Gcode sent error")
            message.show()


    def getPrinters(self):
        headers = {"authorization": "bearer {}".format(self._auth_api_service.getToken()), 'Content-Type' : 'application/x-www-form-urlencoded'}
        response = get(self.data_api_url + "/devices", headers=headers)
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            return []

    def getConnectedPrinter(self, serial_number: str):
        headers = {"Authorization": "Bearer {}".format(self._auth_api_service.getToken())}
        response = get(self.data_api_url + "/devices/connected?serial_number=" + serial_number, headers=headers)
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            return {}

    @classmethod
    def getInstance(cls):
        if not DataApiService.__instance:
            DataApiService.__instance = cls()

        return DataApiService.__instance

    __instance = None
