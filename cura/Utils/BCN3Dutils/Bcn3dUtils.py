from typing import Optional, Any

from UM.Application import Application
from UM.Logger import Logger
from UM.Settings.PropertyEvaluationContext import PropertyEvaluationContext
from UM.Settings.SettingFunction import SettingFunction
from typing import Any, Dict, List

##put BCN first in material list
def putBcn3dFirstInMaterials(brand_item_list : List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    position = 0
    switch = False
    for item in brand_item_list:
        if item['name'] == "BCN3D Filaments":
            switch = item
            break
        position +=1
    if switch:
        brand_item_list.pop(position)
        brand_item_list.insert(0, item)

    return brand_item_list

def checkMaterialcompatibility(active_quality_group, global_container_stack):
    checkMaterial =  Application.getInstance().getPreferences().getValue("cura/check_material_compatibility")
    if not checkMaterial:
        return active_quality_group.is_available
    materialcompatibility = {}
    materialcompatibility['PLA'] = ['PLA', 'Fillamentum PLA', 'Matterhackers PLA','Smart Materials PLA', 'Tough PLA','PVA', 'BVOH', 'TPU', 'Ultrafuse TPU 64D',]
    materialcompatibility['Tough PLA'] = ['PLA', 'Fillamentum PLA', 'Matterhackers PLA','Smart Materials PLA', 'Tough PLA','PVA', 'BVOH', 'TPU', 'Ultrafuse TPU 64D',]
    materialcompatibility['PVA'] = ['PLA', 'Fillamentum PLA', 'Matterhackers PLA','Smart Materials PLA', 'Tough PLA','PVA', 'TPU', 'Ultrafuse TPU 64D', 'PAHT CF15', 'PET CF15']
    materialcompatibility['BVOH'] = ['PLA', 'Fillamentum PLA', 'Matterhackers PLA','Smart Materials PLA', 'Tough PLA', 'BVOH', 'ABS', 'TPU','Ultrafuse TPU 64D', 'PA', 'PAHT CF15', 'PET CF15']
    materialcompatibility['ABS'] = ['BVOH', 'ABS', 'Ultrafuse PC ABS FR', 'Matterhackers ABS', 'TPU','Ultrafuse TPU 64D','PAHT CF15', 'PET CF15']
    materialcompatibility['PET-G'] = ['PET-G',  'Fillamentum PET-G','Matterhackers PET-G', 'PET CF15']
    materialcompatibility['TPU'] = ['PLA', 'Fillamentum PLA', 'Matterhackers PLA','Smart Materials PLA', 'Tough PLA', 'BVOH', 'PVA', 'ABS', 'TPU','Ultrafuse TPU 64D', 'PET CF15']
    materialcompatibility['PA'] = ['BVOH', 'PA']
    materialcompatibility['PP'] = ['PP']
    materialcompatibility['PAHT CF15'] = ['PVA', 'BVOH', 'ABS', 'Ultrafuse PC ABS FR', 'Matterhackers ABS', 'PAHT CF15']
    materialcompatibility['PP GF30'] = ['PP GF30']
    materialcompatibility['PET CF15'] = [ 'PVA', 'BVOH', 'ABS', 'Ultrafuse PC ABS FR', 'Matterhackers ABS', 'PET-G',  'Fillamentum PET-G','Matterhackers PET-G', 'TPU','Ultrafuse TPU 64D','PET CF15']
    materialcompatibility['17-4PH'] = ['17-4PH', 'Ultrafuse Support Layer']
    materialcompatibility['316L'] = ['316L', 'Ultrafuse Support Layer']
    materialcompatibility['Ultrafuse ASA'] = ['Ultrafuse ASA']
    materialcompatibility['Ultrafuse PET'] = ['Ultrafuse PET']
    materialcompatibility['Ultrafuse rPET'] = ['Ultrafuse rPET']
    materialcompatibility['Ultrafuse TPU 85A'] = ['Ultrafuse TPU 85A']
    materialcompatibility['Ultrafuse TPS 90A'] = ['Ultrafuse TPS 90A']
    materialcompatibility['Tech-X 316L HMs'] = ['Tech-X 316L HMs']
    materialcompatibility['Tech-X H13 HMs'] = ['Tech-X H13 HMs']
    materialcompatibility['Tech-X 17-4PH HMs'] = ['Tech-X 17-4PH HMs']
    materialcompatibility['Tech-X Inconel 625 HMs'] = ['Tech-X Inconel 625 HMs']
    materialcompatibility['Essentium HTN'] = ['Essentium HTN']
    materialcompatibility['Essentium PACF'] = ['Essentium PACF']
    materialcompatibility['Essentium PCTG Z'] = ['Essentium PCTG Z']
    materialcompatibility['Essentium PCTG'] = ['Essentium PCTG']
    materialcompatibility['Essentium PETCF'] = ['Essentium PETCF']
    materialcompatibility['Fillamentum NonOilen'] = ['Fillamentum NonOilen']
    materialcompatibility['Matterhackers PET-G'] = ['PET-G',  'Fillamentum PET-G','Matterhackers PET-G', 'PET CF15']
    materialcompatibility['Matterhackers PLA'] = ['PLA', 'Fillamentum PLA', 'Matterhackers PLA','Smart Materials PLA', 'Tough PLA','PVA', 'BVOH', 'TPU']
    materialcompatibility['Matterhackers Nylon'] = ['Matterhackers Nylon']
    materialcompatibility['Matterhackers ABS'] = ['BVOH', 'ABS', 'Ultrafuse PC ABS FR', 'Matterhackers ABS', 'TPU','Ultrafuse TPU 64D','PAHT CF15', 'PET CF15' 'Matterhackers ABS']
    materialcompatibility['Fillamentum PLA'] = ['PLA', 'Fillamentum PLA', 'Matterhackers PLA','Smart Materials PLA', 'Tough PLA','PVA', 'BVOH', 'TPU']
    materialcompatibility['Ultrafuse PC ABS FR'] = ['BVOH', 'ABS', 'Ultrafuse PC ABS FR', 'Matterhackers ABS', 'TPU','PAHT CF15', 'PET CF15']
    materialcompatibility['Ultrafuse TPU 64D'] = ['PLA', 'Ultrafuse TPU 64D', 'Fillamentum PLA', 'Matterhackers PLA', 'Tough PLA', 'BVOH', 'PVA', 'ABS', 'TPU', 'PET CF15', 'Smart Materials PLA']
    materialcompatibility['Ultrafuse PA6 GF30'] = ['Ultrafuse PA6 GF30']
    materialcompatibility['Fillamentum PET-G'] = ['PET-G', 'Fillamentum PET-G', 'Matterhackers PET-G', 'PET CF15']
    materialcompatibility['Fillamentum CPE'] = ['Fillamentum CPE']
    materialcompatibility['Ultrafuse Support Layer'] = ['Ultrafuse Support Layer', '316L', '17-4PH']
    materialcompatibility['Omega Proto'] = ['Omega Proto']
    materialcompatibility['Omega Resistant Nylon'] = ['Omega Resistant Nylon']
    materialcompatibility['Omega Tooling CF'] = ['Omega Tooling CF']
    materialcompatibility['Smart Materials PLA'] = ['PLA', 'Fillamentum PLA', 'Matterhackers PLA', 'Tough PLA','PVA', 'BVOH', 'TPU', 'Smart Materials PLA']


    ext0 = global_container_stack.extruderList[0]
    ext1 = global_container_stack.extruderList[1]
    if (ext0 and ext0.isEnabled ) and (ext1 and ext1.isEnabled):
        material1 = ext0.material.metaData['material']
        material2 = ext1.material.metaData['material']
        if material1 == material2:
            return True
        for material in materialcompatibility:
            if material == material1:
                for chekingMaterial in materialcompatibility[material]:
                    if chekingMaterial == material2:
                        return True
                return False
    return active_quality_group.is_available

# Gets the brand setting key (brand or material) from the given extruder position.
def getMaterialInfoInExtruder(extruder_position: int, property_key: str,
                        context: Optional["PropertyEvaluationContext"] = None) -> Any:
    
    machine_manager = Application.getInstance().getMachineManager()

    if extruder_position == -1:
        extruder_position = int(machine_manager.defaultExtruderPosition)

    global_stack = machine_manager.activeMachine
    try:
        extruder_stack = global_stack.extruderList[int(extruder_position)]
    except IndexError:
        if extruder_position != 0:
            Logger.log("w", "Value for brand of extruder %s was requested, but that extruder is not available. Returning the result from extruder 0 instead" % (extruder_position))
            return getMaterialInfoInExtruder(0, context)
        Logger.log("w", "Brand value for of extruder %s was requested, but that extruder is not available. " % (extruder_position))
        return None
    extruder_stack
    if property_key in extruder_stack.material.metaData:
        return extruder_stack.material.metaData[property_key]
    else:
        return None

# Gets the optimus value for adehsion type
def setOptimalAdhesionType(context: Optional["PropertyEvaluationContext"] = None) -> str:
        
        machine_manager = Application.getInstance().getMachineManager()
        extruder_manager = Application.getInstance().getExtruderManager()

        global_stack = machine_manager.activeMachine

        result = []
        for extruder in extruder_manager.getActiveExtruderStacks():
            if not extruder.isEnabled:
                continue
            # only include values from extruders that are "active" for the current machine instance
            if int(extruder.getMetaDataEntry("position")) >= global_stack.getProperty("machine_extruder_count", "value", context = context):
                continue

            value = extruder.getRawProperty("adhesion_type", "value", context = context)

            if value is None:
                continue

            if isinstance(value, SettingFunction):
                value = value(extruder, context = context)

            result.append(value)

        if not result:
            result.append(global_stack.getProperty("adhesion_type", "value", context = context))
        
        #Only  works with 2 active extruders machine
        if len(result) == 2:
            weight = {"none" : 0, "skirt" :1, "brim" :2, "raft" : 3}
            if weight[result[1]] > weight[result[0]]:
                return result[1]

        return result[0]

def resetDefaultQualityIfNecessary(machineType : str, resetDefault) -> None:
    if machineType == "Omega I60":
        app = Application.getInstance()
        bcn3dapiplugin = app.getPluginRegistry().getPluginObject("BCN3DApi")
        authService = bcn3dapiplugin.authService
        profile = authService.profile()
        if not profile or not profile['advanced_user']:
            resetDefault()    