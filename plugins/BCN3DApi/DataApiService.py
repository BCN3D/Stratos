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

    def sendGcode(self, gcode_path, gcode_name, printerId):
        headers = {"Authorization": "Bearer {}".format(self._auth_api_service.getToken())}
        files = {"file": (gcode_path, open(gcode_path, "rb"))}
        data = {"setup": "{name : %s}" % gcode_name}
        response = post(self._auth_api_service.api_url + "/printfiles", data, headers, files)
        if 200 <= response.status_code < 300:
            response_message = response.json()
            print_file_id = response_message[0]["print_file_id"]
            data = {"print_file_id" : print_file_id }
            headers = {"Authorization": "Bearer {}".format(self._auth_api_service.getToken())}
            response2 = post(self._auth_api_service.api_url + "/devices/" + printerId + "/print", data, headers)
            if 200 <= response2.status_code < 300:
                message = Message("The gcode has been sent to the cloud successfully", title="Gcode sent")
                message.show()
            else:
                message = Message("There was an error sending the gcode to the cloud", title="Gcode sent error")
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
