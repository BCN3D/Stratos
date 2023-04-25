from typing import Optional, Any

from UM.Application import Application
from UM.Logger import Logger
from UM.Settings.PropertyEvaluationContext import PropertyEvaluationContext
from UM.Settings.SettingFunction import SettingFunction

##put BCN first in material list
def putBcn3dFirstInMaterials(brand_item_list):
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

def checkMaterialcompability(active_quality_group, global_container_stack):
    checkMaterial =  Application.getInstance().getPreferences().getValue("cura/check_material_compatibility")
    if not checkMaterial:
        return active_quality_group.is_available
    materialcompability = {}
    materialcompability['PLA'] = ['PLA', 'Fillamentum PLA', 'Matterhackers PLA', 'Tough PLA','PVA', 'BVOH', 'TPU', 'TPU 64D',]
    materialcompability['Tough PLA'] = ['PLA', 'Fillamentum PLA', 'Matterhackers PLA', 'Tough PLA','PVA', 'BVOH', 'TPU', 'TPU 64D',]
    materialcompability['PVA'] = ['PLA', 'Fillamentum PLA', 'Matterhackers PLA', 'Tough PLA','PVA', 'TPU', 'TPU 64D', 'PAHT CF15', 'PET CF15']
    materialcompability['BVOH'] = ['PLA', 'Fillamentum PLA', 'Matterhackers PLA', 'Tough PLA', 'BVOH', 'ABS', 'TPU','TPU 64D', 'PA', 'PAHT CF15', 'PET CF15']
    materialcompability['ABS'] = ['BVOH', 'ABS', 'PC ABS FR', 'TPU','TPU 64D','PAHT CF15', 'PET CF15']
    materialcompability['PET-G'] = ['PET-G',  'Fillamentum PET-G','Matterhackers PET-G', 'PET CF15']
    materialcompability['TPU'] = ['PLA', 'Fillamentum PLA', 'Matterhackers PLA', 'Tough PLA', 'BVOH', 'PVA', 'ABS', 'TPU','TPU 64D', 'PET CF15']
    materialcompability['PA'] = ['BVOH', 'PA']
    materialcompability['PP'] = ['PP']
    materialcompability['PAHT CF15'] = ['PVA', 'BVOH', 'ABS', 'PC ABS FR', 'PAHT CF15']
    materialcompability['PP GF30'] = ['PP GF30']
    materialcompability['PET CF15'] = [ 'PVA', 'BVOH', 'ABS', 'PC ABS FR', 'PET-G',  'Fillamentum PET-G','Matterhackers PET-G', 'TPU','TPU 64D','PET CF15']
    materialcompability['17-4PH'] = ['17-4PH']
    materialcompability['316L'] = ['316L']
    materialcompability['Ultrafuse ASA'] = ['Ultrafuse ASA']
    materialcompability['Ultrafuse PET'] = ['Ultrafuse PET']
    materialcompability['Ultrafuse rPET'] = ['Ultrafuse rPET']
    materialcompability['Ultrafuse TPU 85A'] = ['Ultrafuse TPU 85A']
    materialcompability['Ultrafuse TPS 90A'] = ['Ultrafuse TPS 90A']
    materialcompability['Tech-X 316L HMs'] = ['Tech-X 316L HMs']
    materialcompability['Tech-X H13 HMs'] = ['Tech-X H13 HMs']
    materialcompability['Tech-X 17-4PH HMs'] = ['Tech-X 17-4PH HMs']
    materialcompability['Tech-X Inconel 625 HMs'] = ['Tech-X Inconel 625 HMs']
    materialcompability['Essentium HTN'] = ['Essentium HTN']
    materialcompability['Essentium PACF'] = ['Essentium PACF']
    materialcompability['Essentium PCTG Z'] = ['Essentium PCTG Z']
    materialcompability['Essentium PCTG'] = ['Essentium PCTG']
    materialcompability['Essentium PETCF'] = ['Essentium PETCF']
    materialcompability['Fillamentum NonOilen'] = ['Fillamentum NonOilen']
    materialcompability['Matterhackers PET-G'] = ['PET-G',  'Fillamentum PET-G','Matterhackers PET-G', 'PET CF15']
    materialcompability['Matterhackers PLA'] = ['PLA', 'Fillamentum PLA', 'Matterhackers PLA', 'Tough PLA','PVA', 'BVOH', 'TPU']
    materialcompability['Fillamentum PLA'] = ['PLA', 'Fillamentum PLA', 'Matterhackers PLA', 'Tough PLA','PVA', 'BVOH', 'TPU']
    materialcompability['PC ABS FR'] = ['BVOH', 'ABS', 'PC ABS FR', 'TPU','PAHT CF15', 'PET CF15']
    materialcompability['TPU 64D'] = ['PLA', 'TPU 64D', 'Fillamentum PLA', 'Matterhackers PLA', 'Tough PLA', 'BVOH', 'PVA', 'ABS', 'TPU', 'PET CF15']
    materialcompability['PA6 GF30'] = ['PA6 GF30']
    materialcompability['Fillamentum PET-G'] = ['PET-G', 'Fillamentum PET-G', 'Matterhackers PET-G', 'PET CF15']
    materialcompability['Fillamentum CPE'] = ['Fillamentum CPE']

    ext0 = global_container_stack.extruderList[0]
    ext1 = global_container_stack.extruderList[1]
    if (ext0 and ext0.isEnabled ) and (ext1 and ext1.isEnabled):
        material1 = ext0.material.metaData['material']
        material2 = ext1.material.metaData['material']
        if material1 == material2:
            return True
        for material in materialcompability:
            if material == material1:
                for chekingMaterial in materialcompability[material]:
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
