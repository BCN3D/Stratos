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

    def sendGcode(self, gcode_path, gcode_name, serial_number):
        headers = {"Authorization": "Bearer {}".format(self._auth_api_service.getToken())}
        files = {"file": (gcode_path, open(gcode_path, "rb"))}
        data = {"serialNumber": serial_number, "fileName": gcode_name}
        response = post(self.data_api_url + "/gcodes", data, headers)
        if 200 <= response.status_code < 300:
            response_message = response.json()
            presigned_url = response_message["url"]
            fields = response_message["fields"]
            response2 = post(presigned_url, fields, files=files)
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
        print("DataApiService getPrinters")
        headers = {"authorization": "bearer {}".format(self._auth_api_service.getToken()), 'Content-Type' : 'application/x-www-form-urlencoded'}
        print(headers)
        response = get(self.data_api_url + "/devices", headers=headers)
        print(response.status_code)
        print(response.json())
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            return []

    def getPrinter(self, serial_number: str):
        headers = {"Authorization": "Bearer {}".format(self._auth_api_service.getToken())}
        response = get(self.data_api_url + "/devices/" + serial_number, headers=headers)
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
