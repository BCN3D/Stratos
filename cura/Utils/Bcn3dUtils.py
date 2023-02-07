from UM.Application import Application

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
    materialcompability['PLA'] = ['PLA', 'Tough PLA','PVA', 'BVOH', 'TPU']
    materialcompability['Tough PLA'] = ['PLA', 'Tough PLA','PVA', 'BVOH', 'TPU']
    materialcompability['PVA'] = ['PLA', 'Tough PLA','PVA', 'TPU', 'PAHT CF15', 'PET CF15']
    materialcompability['BVOH'] = ['PLA', 'Tough PLA', 'BVOH', 'ABS', 'TPU', 'PA', 'PAHT CF15', 'PET CF15']
    materialcompability['ABS'] = ['BVOH', 'ABS', 'TPU','PAHT CF15', 'PET CF15']
    materialcompability['PET-G'] = ['PET-G', 'PET CF15']
    materialcompability['TPU'] = ['PLA', 'Tough PLA', 'BVOH', 'PVA', 'ABS', 'TPU', 'PET CF15']
    materialcompability['PA'] = ['BVOH', 'PA']
    materialcompability['PP'] = ['PP']
    materialcompability['PAHT CF15'] = ['PVA', 'BVOH', 'ABS', 'PAHT CF15']
    materialcompability['PP GF30'] = ['PP GF30']
    materialcompability['PET CF15'] = [ 'PVA', 'BVOH', 'ABS', 'PET-G', 'TPU', 'PET CF15']

    ext0 = global_container_stack.extruderList[0]
    ext1 = global_container_stack.extruderList[1]
    if (ext0 and ext0.isEnabled ) and (ext1 and ext1.isEnabled):
        material1 = ext0.material.metaData['material']
        material2 = ext1.material.metaData['material']
        for material in materialcompability:
            if material == material1:
                for chekingMaterial in materialcompability[material]:
                    if chekingMaterial == material2:
                        return True
                return False
    return active_quality_group.is_available

