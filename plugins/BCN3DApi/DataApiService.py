from UM.Message import Message

from .AuthApiService import AuthApiService
from .SessionManager import SessionManager
from .http_helper import get, post


class DataApiService:

    def __init__(self):
        super().__init__()
        if DataApiService.__instance is not None:
            raise ValueError("Duplicate singleton creation")

        DataApiService._instance = self
        self._auth_api_service = AuthApiService.getInstance()

    def sendGcode(self, gcode, gcode_name, printerId):
        headers = {"Authorization": "Bearer {}".format(self._auth_api_service.getToken())}
        files = {"file": (gcode_name, gcode)}
        response = post(self._auth_api_service.api_url + "/devices/" + printerId + "/print", [], headers, files)
        if 200 <= response.status_code < 300:
            message = Message("The gcode has been sent to the cloud successfully", title="Gcode sent")
            message.show()
        else:
            message = Message("There was an error sending the gcode to the cloud", title="Gcode sent error")
            message.show()


    def getPrinters(self):
        headers = {"authorization": "bearer {}".format(self._auth_api_service.getToken()), 'Content-Type' : 'application/x-www-form-urlencoded'}
        response = get(self._auth_api_service.api_url + "/devices", headers=headers)
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            return []

    def getConnectedPrinter(self):
        headers = {"Authorization": "Bearer {}".format(self._auth_api_service.getToken())}
        response = get(self._auth_api_service.api_url + "/devices/connected", headers=headers)
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
