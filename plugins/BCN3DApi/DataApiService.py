from UM.Message import Message

from .AuthApiService import AuthApiService
from .http_helper import get, post
from UM.Logger import Logger


class DataApiService:

    def __init__(self):
        super().__init__()
        if DataApiService.__instance is not None:
            raise ValueError("Duplicate singleton creation")

        DataApiService._instance = self
        self._auth_api_service = AuthApiService.getInstance()

    def sendGcode(self, gcode, gcode_name, printerId, save = False):
        headers = {"Authorization": "Bearer {}".format(self._auth_api_service.getToken())}
        files = {"file": (gcode_name, gcode)}
        if save:
            data = {"setup": "{name : %s}" % gcode_name}
            response = post(self._auth_api_service.api_url + "/printfiles", data, headers, files)
            if 200 <= response.status_code < 300:
                response_message = response.json()
                print_file_id = response_message[0]["print_file_id"]
                data = {"print_file_id" : print_file_id }
                headers = {"Authorization": "Bearer {}".format(self._auth_api_service.getToken())}
                response2 = post(self._auth_api_service.api_url + "/devices/" + printerId + "/print", data, headers)
                if 200 <= response2.status_code < 300:
                    message = Message("The gcode has been sent to the cloud and the printer successfully", title="Gcode sent")
                    message.show()
                else:
                    message = Message("The gcode has been sent to the cloud successfully but there was an error sending the gcode to the printer", title="Gcode sent error")
                    Logger.error("There was an error sending gcode to the printer: %s".format(response2.reason))
                    message.show()
            else:
                message = Message("There was an error sending the gcode to the cloud", title="Gcode sent error")
                reason = "No reason provided" if not hasattr(response, 'reason') else response.reason
                Logger.error("There was an error sending gcode to cloud: %s" % reason)
                message.show()
        else :
            response = post(self._auth_api_service.api_url + "/devices/" + printerId + "/print", [], headers, files)
            if 200 <= response.status_code < 300:
                message = Message("The gcode has been sent to the printer successfully", title="Gcode sent")
                message.show()
            else:
                message = Message("There was an error sending the gcode to the printer", title="Gcode sent error")
                message.show()


    def getPrinters(self):
        headers = {"authorization": "bearer {}".format(self._auth_api_service.getToken()), 'Content-Type' : 'application/x-www-form-urlencoded'}
        response = get(self._auth_api_service.api_url + "/devices", headers=headers)
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            reason = "No reason provided" if not hasattr(response, 'reason') else response.reason
            Logger.error("There was an error getting printers: %s" % reason)
            return []

    def getConnectedPrinter(self):
        headers = {"Authorization": "Bearer {}".format(self._auth_api_service.getToken())}
        response = get(self._auth_api_service.api_url + "/devices/connected", headers=headers)
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            reason = "No reason provided" if not hasattr(response, 'reason') else response.reason
            Logger.error("There was an error getting connected printer: %s" % reason)
            return {}

    @classmethod
    def getInstance(cls):
        if not DataApiService.__instance:
            DataApiService.__instance = cls()

        return DataApiService.__instance

    __instance = None
