from UM.Message import Message
import requests
import sys
import json
import operator

from .AuthApiService import AuthApiService
from .http_helper import get, post
from UM.Logger import Logger
from cura.CuraApplication import CuraApplication


class DataApiService:

    def __init__(self):
        super().__init__()
        if DataApiService.__instance is not None:
            raise ValueError("Duplicate singleton creation")

        DataApiService._instance = self
        self._auth_api_service = AuthApiService.getInstance()

    def sendGcode(self, gcode, gcode_name, printerId, action = "print"):
        self.message = Message("Uploading...", 0, False, 25.0)
        self.message.show()
        headers = {"authorization": "bearer {}".format(self._auth_api_service.getToken()), 'Content-Type' : 'application/x-www-form-urlencoded'}
        # First post
        r = requests.post(self._auth_api_service.api_url + "/cura_plugging/file_policy/",
            data={
                'filename': gcode_name,
                'printer_pk': printerId
            },
            headers=headers)
        self.message.setProgress(50.0)
        if r.status_code != 200:
            if r.status_code == 403:
                self.message.hide()
                self.message = Message(r.json()["message"], 0, False, -1)
                self.message.show()
            else:
                self.show_error(r.json()['message'])
            return

        policy_data = r.json()

        # Second post
        files = {'file': (gcode_name, gcode)}
        r1 = requests.post(policy_data['url'],
                            data=policy_data['fields'],
                            files=files)
        if r1.status_code != 204:
            Logger.log("e", "ERROR: AWS Post: %s", r1.text)
            self.show_error('Something went wrong...')
            return

        # UPLOAD WORKSPACE THREAD
        r2 = requests.post(self._auth_api_service.api_url + "/cura_plugging/workspace_file_policy/",
            data={
                'filename': gcode_name,
                'printer_pk': printerId
            },
            headers=headers)
        workspace_file_policy = r2.json()

        # UPLOAD WORKSPACE THREAD
        r3 = requests.post(self._auth_api_service.api_url + "/cura_plugging/workspace_file_complete/",
            data = {
                "fileSize": sys.getsizeof(gcode),
                "file": workspace_file_policy['file_id'],
                "printer_pk": printerId,
                "aws_gcode_file_pk": policy_data["file_id"]
            },
            headers=headers)

         # Third post
        printTime, data_materials, data_lengths, data_weigths = self.getGcodeTime()
        r = requests.post(self._auth_api_service.api_url + "/cura_plugging/file_upload_complete/",
                            data={
                                'fast_print': True,
                                'printer_pk': str(printerId),
                                'time': printTime,
                                'materials': json.dumps(data_materials),
                                'length': json.dumps(data_lengths),
                                'grams': json.dumps(data_weigths),
                                'uploaded': True,
                                'fileSize': sys.getsizeof(gcode),
                                'file': policy_data['file_id'],
                                'flavor': json.dumps(self.getFlavor()),
                                'type': action
                            },
                            headers=headers)
        Logger.log("i", "UPLOAD COMPLETE: %s", r.text) 
        if r.status_code != 200:
            if r.status_code == 403:
                self.message.hide()
                self.message = Message("Permission required", 0, True, -1)
                self.message.show()
            else:
                self.show_error(r.json()['message'])
            return
        else:

            self.message.hide()
            self.message = Message("Completed", 10, True, 100)
            self.message.show()
            message = Message("The gcode has been sent to the printer successfully", title="Gcode sent")
            message.show()
            return


    def getPrinters(self):
        headers = {"authorization": "bearer {}".format(self._auth_api_service.getToken()), 'Content-Type' : 'application/x-www-form-urlencoded'}
        response = get(self._auth_api_service.api_url + "/cura_plugging/printers/", headers=headers)
        if 200 <= response.status_code < 300:
            Logger.log("i", "Printers: %s" % response.json())
            return response.json()
        else:
            reason = "No reason provided" if not hasattr(response, 'reason') else response.reason
            Logger.error("There was an error getting printers: %s" % reason)
            return []

    def getConnectedPrinter(self):
        headers = {"Authorization": "Bearer {}".format(self._auth_api_service.getToken())}
        response = get(self._auth_api_service.api_url + "/cura_plugging/printers/?status=200", headers=headers)
        if 200 <= response.status_code < 300:
            Logger.log("i", "Connected printer: %s" % response.json())
            return response.json()
        else:
            reason = "No reason provided" if not hasattr(response, 'reason') else response.reason
            Logger.error("There was an error getting connected printer: %s" % reason)
            return {}

    def show_error(self, error_msg: str) -> None:
        self.message.hide()
        self.message = Message('An error occurred:\n{}'.format(error_msg), 0, True, -1)
        self.message.show()
   
    def getFlavor(self):
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        flavor_json = {}
        if not global_container_stack:
            flavor_json['flavor'] = "UNKNOWN"

        else:
            flavor = global_container_stack.getProperty("machine_gcode_flavor", "value")
            flavor_json['flavor'] = flavor

        return flavor_json
    
    def getGcodeTime(self):
        information = CuraApplication.getInstance().getPrintInformation()
        materials = list(information.materialNames)
        lengths = list(information.materialLengths)
        weights = list(information.materialWeights)

        printTime = str(information.currentPrintTime.days * 3600 * 24 +
                        information.currentPrintTime.hours * 3600 + information.currentPrintTime.minutes * 60 + information.currentPrintTime.seconds)

        data_materials = {}
        for index, m in enumerate(materials):
            data_materials['T' + str(index)] = str(materials[index])

        data_lengths = {}
        for index, l in enumerate(lengths):
            data_lengths['T' + str(index)] = float(lengths[index])

        data_weigths = {}
        for index, w in enumerate(weights):
            data_weigths['T' + str(index)] = float(weights[index])

        # REMOVING UNNECESSARY EXTRUDER IF LENGTH IS 0
        for index, l in enumerate(lengths):
            if data_lengths["T" + str(index)] == 0:
                if len(data_lengths) > 1:
                    data_materials.pop("T" + str(index), None)
                    data_lengths.pop("T" + str(index), None)
                    data_weigths.pop("T" + str(index), None)

        print_mode = CuraApplication.getInstance().getGlobalContainerStack().getProperty("print_mode", "value")
        if print_mode == "mirror" or print_mode == "duplication":
            max_value_lengths = max(data_lengths.items(), key=operator.itemgetter(1))[0]
            max_value_weights = max(data_weigths.items(), key=operator.itemgetter(1))[0]
            for l in lengths:
                data_lengths['T' + str(lengths.index(l))] = data_lengths[max_value_lengths]
            for w in weights:
                data_weigths['T' + str(weights.index(w))] = data_weigths[max_value_weights]

        return printTime, data_materials, data_lengths, data_weigths

    @classmethod
    def getInstance(cls):
        if not DataApiService.__instance:
            DataApiService.__instance = cls()

        return DataApiService.__instance

    __instance = None
