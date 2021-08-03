#!/usr/bin/python

#this takes a .hdc file and the path to a sample token directory
#reads the content.xml, replacing the xml

#TODO
# - emit existing powers as JSON
# - emit missing powers

import sys
import shutil
import os
import zipfile
import math
import xml.etree.ElementTree as ElementTree
from shutil import copyfile

ITALICS = '<i>'
ITALICS_END = '</i>'

DEBUG=0
SHOW_MISSING_PROPERTIES=0

def debug_print(string):
    if (DEBUG):
        print(string)

# Replace specific file within zip archive with data provided
def update_zip(zipname, filename, data):
    # generate a temp file
    tmpname = zipname+".temp"
    if (os.path.exists(tmpname)):
        os.remove(tmpname)
    shutil.copyfile(zipname, tmpname)

    # create a temp copy of the archive without filename
    with zipfile.ZipFile(zipname, 'r') as zin:
        with zipfile.ZipFile(tmpname, 'w') as zout:
            zout.comment = zin.comment # preserve the comment
            for item in zin.infolist():
                if item.filename != filename:
                    zout.writestr(item, zin.read(item.filename))

    # replace with the temp archive
    os.remove(zipname)
    os.rename(tmpname, zipname)

    # now add filename with its new data
    with zipfile.ZipFile(zipname, mode='a', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(filename, data)

def get_json(parent, list_of_tuples):
    json = "{"
    if (parent != None):
        json = json + '\"parent\":\"'+parent+'\"'

    for item in list_of_tuples:
        if (len(json) > 1):
            json = json + ","
        json = json + '\"' + item[0] + '\":\"' + item[1] + '\"'

    json = json + "}"
    return json

def get_safe_attrib(element, key):
    attrib = ""
    try:
        attrib = element.attrib[key]
    except (Exception):
        if (SHOW_MISSING_PROPERTIES):
            print("Can't find "+key)
    return attrib

def get_parent(element):
    return get_safe_attrib(element, 'PARENTID')

def add_disads(hdc_root, token_root):
    for map in token_root.findall('propertyMapCI'):
        for store in map:
            property_store = store

    #get values from hdc
    print('  Getting disads')
    for ma_list in hdc_root.findall('DISADVANTAGES'):
        disad_count = 0
        for disad in ma_list:

            add_token_property(
                property_store,
                'disadvantages.disad{:02d}'.format(disad_count),
                get_disad_json(disad, characteristics))

            disad_count = disad_count + 1

def get_mod_string(mod):
    if (mod == "0.25"):
        return "+¼"
    if (mod == "0.5"):
        return "+½"
    if (mod == "-0.5"):
        return "-½"
    if (mod == "-0.25"):
        return "-¼"
    if (mod == "0.75"):
        return "+¾"
    if (mod == "-0.75"):
        return "-¾"
    return mod

def get_modifier_tuple(element):
    modifiers = ""
    for sub in element.findall('MODIFIER'):
        mod = get_safe_attrib(sub, 'BASECOST')
        name = get_safe_attrib(sub, 'ALIAS')
        more = get_safe_attrib(sub, 'OPTION_ALIAS')
        comment = get_safe_attrib(sub, 'COMMENTS')
        if (len(modifiers)):
            modifiers = modifiers + ", "
        if (len(name) and len(more)):
            more = " " + more
        mod_str = get_mod_string(mod)
        if (len(comment) and len(mod_str)):
            comment = comment + " "
        modifiers = modifiers + name + more + " (" + comment + mod_str + ")"
    return ("modifiers",modifiers)

def get_power_name_list(element):
    name = element.attrib['NAME']
    power_type = element.attrib['XMLID']
    alias = element.attrib['ALIAS']
    name_list = [("name",ITALICS+name+ITALICS_END),("POWER_ID",power_type),("alias",alias)]
    name_list.append(("parent",get_parent(element)))
    if (get_safe_attrib(element,'ULTRA_SLOT')=="Yes"):
        name_list.append(("ultra","1"))

    name_list.append(get_modifier_tuple(element))

    return name_list

def get_extralimbs_json(element):
    name_list = get_power_name_list(element)
    levels=element.attrib['LEVELS']
    name_list.append(("limbs",levels))
    return get_json(get_parent(element),name_list)

def get_std_dice_power_json(element):
    name_list = get_power_name_list(element)
    levels=element.attrib['LEVELS']
    name_list.append(("dice",levels))
    return get_json(get_parent(element),name_list)

def get_leaping_json(element):
    name_list = get_power_name_list(element)
    levels=element.attrib['LEVELS']
    name_list.append(("inches",levels))
    return get_json(get_parent(element),name_list)

def get_running_json(element):
    name_list = get_power_name_list(element)
    name_list.append(("inches",str(6+int(element.attrib['LEVELS']))))
    return get_json(get_parent(element),name_list)

def get_swimming_json(element):
    name_list = get_power_name_list(element)
    name_list.append(("inches",str(6+int(element.attrib['LEVELS']))))
    return get_json(get_parent(element),name_list)

def get_armor_json(element):
    name_list = get_power_name_list(element)
    name_list.append(("pd", element.attrib['PDLEVELS']))
    name_list.append(("ed",element.attrib['EDLEVELS']))
    name_list.append(("rpd", element.attrib['PDLEVELS']))
    name_list.append(("red",element.attrib['EDLEVELS']))
    return get_json(get_parent(element),name_list)

def get_hth_attack_json(element):
    #TODO add actual HTH dice?
    return get_std_dice_power_json(element)

def get_ego_attack_json(element):
    return get_std_dice_power_json(element)

def get_telepathy_json(element):
    return get_std_dice_power_json(element)

def get_flash_json(element):
    return get_std_dice_power_json(element)

def get_drain_json(element):
    return get_std_dice_power_json(element)

def get_dispel_json(element):
    return get_std_dice_power_json(element)

def get_hka_json(element):
    return get_std_dice_power_json(element)

def get_aid_json(element):
    return get_std_dice_power_json(element)

def get_rka_json(element):
    return get_std_dice_power_json(element)

def get_entangle_json(element):
    return get_std_dice_power_json(element)

def get_infrared_json(element):
    name_list = get_power_name_list(element)
    return get_json(get_parent(element),name_list)

def get_ultrasonic_json(element):
    name_list = get_power_name_list(element)
    return get_json(get_parent(element),name_list)

def get_images_json(element):
    return get_std_dice_power_json(element)

def get_energyblast_json(element):
    return get_std_dice_power_json(element)

def get_telekinesis_json(element):
    name_list = get_power_name_list(element)
    #TODO:  get the value
    return get_json(get_parent(element),name_list)


def get_invisibility_json(element):
    name_list = get_power_name_list(element)
    #TODO:  get the value
    return get_json(get_parent(element),name_list)

def get_mindcontrol_json(element):
    name_list = get_power_name_list(element)
    #TODO:  get the value
    return get_json(get_parent(element),name_list)

def get_teleport_json(element):
    name_list = get_power_name_list(element)
    #TODO:  get the value
    return get_json(get_parent(element),name_list)

def get_lifesupport_json(element):
    name_list = get_power_name_list(element)
    #TODO:  get the value
    return get_json(get_parent(element),name_list)

def get_forcewall_json(element):
    name_list = get_power_name_list(element)
    #TODO:  get the value
    return get_json(get_parent(element),name_list)

def get_mentaldefense_json(element):
    name_list = get_power_name_list(element)
    name_list.append(("mentaldef", element.attrib['LEVELS']))
    return get_json(get_parent(element),name_list)

def get_luck_json(element):
    name_list = get_power_name_list(element)
    name_list.append(("luck", element.attrib['LEVELS']))
    return get_json(get_parent(element),name_list)

def get_dr_json(element):
    name_list = get_power_name_list(element)
    #TODO:  conditionally do MDLEVELS and POWDLEVELS
    name_list.append(("rpd", element.attrib['PDLEVELS']))
    name_list.append(("red",element.attrib['EDLEVELS']))
    return get_json(get_parent(element),name_list)

def get_forcefield_json(element):
    name_list = get_power_name_list(element)
    #TODO:  conditionally do MDLEVELS and POWDLEVELS
    name_list.append(("pd", element.attrib['PDLEVELS']))
    name_list.append(("ed",element.attrib['EDLEVELS']))
    name_list.append(("rpd", element.attrib['PDLEVELS']))
    name_list.append(("red",element.attrib['EDLEVELS']))
    return get_json(get_parent(element),name_list)

def get_missile_deflection_json(element):
    name_list = get_power_name_list(element)
    return get_json(get_parent(element),name_list)

def get_clinging_json(element):
    name_list = get_power_name_list(element)
    levels=element.attrib['LEVELS']
    name_list.append(("str_add",levels))
    return get_json(get_parent(element),name_list)

def get_characteristic_power(name, element):
    name_list = get_power_name_list(element)
    levels=element.attrib['LEVELS']
    name_list.append((name,levels))
    return get_json(get_parent(element),name_list)

def get_con_power_json(element):
    return get_characteristic_power("constitution",element)

def get_dex_power_json(element):
    return get_characteristic_power("dexterity",element)

def get_ed_power_json(element):
    return get_characteristic_power("ed",element)

def get_pd_power_json(element):
    return get_characteristic_power("pd",element)

def get_spd_power_json(element):
    return get_characteristic_power("speed",element)

def get_str_power_json(element):
    return get_characteristic_power("strength",element)

def get_framework_json(element):
    name_list = [("name",ITALICS+element.attrib['NAME']+ITALICS_END),("POWER_ID", element.attrib['XMLID'])]
    name_list.append(("id",element.attrib['ID']))
    name_list.append(("alias",element.attrib['ALIAS']))
    name_list.append(get_modifier_tuple(element))
    return get_json(get_parent(element),name_list)

def missing_power_json(element):
    return element.attrib['NAME'] + ": " + element.attrib['XMLID'] + " UNSUPPORTED"

def get_skill_bonus(characteristic, characteristics):
    if (characteristic=='GENERAL' or characteristic==''):
        return 0
    return round(int(characteristics[characteristic])/5)

def get_language_json(element):
    language = get_safe_attrib(element,'INPUT')
    name = element.attrib['NAME']
    alias = element.attrib['OPTION_ALIAS']
    lit_element = element.find('ADDER')
    debug_print(lit_element)

    if (lit_element and lit_element.attrib['XMLID']=='LITERACY'):
        literacy = "literate"
    else:
        literacy = "not literate"

    return get_json(get_parent(element),[("name",ITALICS+name+ITALICS_END+': '+language+' ('+alias+'; '+literacy+')')])

def get_csl_json(element):
    levels = element.attrib['LEVELS']
    name = element.attrib['NAME']
    alias = element.attrib['OPTION_ALIAS']
    return get_json(get_parent(element),[("name",ITALICS+name+ITALICS_END),("alias",alias),("levels",str(levels))])

def get_skill_level_json(element):
    levels = element.attrib['LEVELS']
    name = element.attrib['NAME']
    alias = element.attrib['OPTION_ALIAS']
    return get_json(get_parent(element),[("name",ITALICS+name+ITALICS_END),("alias",alias),("levels",str(levels))])

def get_separator_json(element):
    alias = element.attrib['ALIAS']
    return get_json(get_parent(element),[("name",alias)])

# recursive search for ADDERs with a BASECOST != "0.0"
def get_transport_familiarities(element):
    fams = ""
    if (element.tag == 'ADDER'):
        if (element.attrib['BASECOST']!='0.0'):
            substr = element.attrib['ALIAS']
            if (len(fams)):
                fams = fams + ", "
            fams = fams + substr

    for sub in element.findall("ADDER"):
        substr = get_transport_familiarities(sub)
        if (len(fams)):
            fams = fams + ", "
        fams = fams + substr
    return fams

def get_skill_json(element, characteristics):
    skill_type = element.attrib['XMLID']
    debug_print(skill_type)
    if (skill_type == 'COMBAT_LEVELS'):
        return get_csl_json(element)
    elif (skill_type == 'SKILL_LEVELS'):
        return get_skill_level_json(element)
    elif (skill_type == 'GENERIC_OBJECT'):
        return get_separator_json(element)
    elif (skill_type == 'LANGUAGES'):
        return get_language_json(element)

    characteristic = get_safe_attrib(element,'CHARACTERISTIC')
    value = 11 + get_skill_bonus(characteristic, characteristics)
    levels = element.attrib['LEVELS']
    value = value + int(levels)
    if (get_safe_attrib(element,'FAMILIARITY')=='Yes'):
        value = 8
    name = element.attrib['NAME']
    if (name):
        name = ITALICS+name+ITALICS_END+": "

    input_val = get_safe_attrib(element, 'INPUT')
    input_val = input_val + get_transport_familiarities(element)
    if (len(input_val)):
        input_val = ": "+input_val

    if (characteristic == ''):
        return get_json(get_parent(element),[("name",name),("alias",element.attrib['ALIAS']+input_val)])
    else:
        return get_json(get_parent(element),[("name",name),("alias",element.attrib['ALIAS']+input_val),("roll",str(value))])

power_descriptors = {
    "AID" : get_aid_json,
    "ARMOR" : get_armor_json,
    "CLINGING" : get_clinging_json,
    "COMBAT_LEVELS" : get_csl_json,
    "DAMAGERESISTANCE" : get_dr_json,
    "DISPEL" : get_dispel_json,
    "DRAIN" : get_drain_json,
    "EGOATTACK" : get_ego_attack_json,
    "ENERGYBLAST" : get_energyblast_json,
    "ENTANGLE" : get_entangle_json,
    "EXTRALIMBS" : get_extralimbs_json,
    "FLASH": get_flash_json,
    "FORCEFIELD" : get_forcefield_json,
    "FORCEWALL" : get_forcewall_json,
    "GENERIC_OBJECT" : get_framework_json,
    "GLIDING" : get_leaping_json,
    "HANDTOHANDATTACK" : get_hth_attack_json,
    "HKA" : get_hka_json,
    "RKA" : get_rka_json,
    "IMAGES": get_images_json,
    "INVISIBILITY": get_invisibility_json,
    "INFRAREDPERCEPTION": get_infrared_json,
    "LEAPING" : get_leaping_json,
    "LIFESUPPORT" : get_lifesupport_json,
    "LUCK" : get_luck_json,
    "MENTALDEFENSE" : get_mentaldefense_json,
    "MINDCONTROL" : get_mindcontrol_json,
    "MISSILEDEFLECTION" : get_missile_deflection_json,
    "TELEKINESIS": get_telekinesis_json,
    "TELEPATHY" : get_telepathy_json,
    "ULTRASONICPERCEPTION" : get_ultrasonic_json,
    "RUNNING" : get_running_json,
    "SWIMMING" : get_swimming_json,
    "TELEPORTATION" : get_teleport_json,
    "CON" : get_con_power_json,
    "DEX" : get_dex_power_json,
    "ED" : get_ed_power_json,
    "PD" : get_pd_power_json,
    "SPD" : get_spd_power_json,
    "STR" : get_str_power_json
}

def get_power_json(element, characteristics):
    power_type = element.attrib['XMLID']
    return power_descriptors[power_type](element)

# Example
#      <entry>
#        <string>skills.skill1</string>
#        <net.rptools.CaseInsensitiveHashMap_-KeyValue>
#          <key>skills.skill1</key>
#          <value class="string">Climbing 11-</value>
#          <outer-class reference="../../../.."/>
#        </net.rptools.CaseInsensitiveHashMap_-KeyValue>
#      </entry>
def add_token_property(property_store, text, description):
    entry = ElementTree.SubElement(property_store,'entry')
    string = ElementTree.SubElement(entry,'string')
    string.text = text
    key_value = ElementTree.SubElement(entry,'net.rptools.CaseInsensitiveHashMap_-KeyValue')
    key = ElementTree.SubElement(key_value,'key')
    key.text = string.text
    value = ElementTree.SubElement(key_value,'value',{'class':'string'})
    value.text = description
    debug_print('property: '+description)
    ElementTree.SubElement(key_value,'outer-class',{'reference':'../../../..'})

def add_powers(hdc_root, token_root):
    for map in token_root.findall('propertyMapCI'):
        for store in map:
            property_store = store

    #get values from hdc
    print('  Getting powers')
    for power in hdc_root.findall('POWERS'):
        power_count = 0
        for child in power:
            #add_modifiers(child)
            add_token_property(
                property_store,
                'powers.power{:02d}'.format(power_count),
                get_power_json(child, characteristics))

            power_count = power_count + 1

def get_maneuver_json(element, characteristics):
    name = element.attrib['DISPLAY']

    return get_json(get_parent(element),[("name",name)])

def get_disad_json(element, characteristics):
    name = element.attrib['ALIAS']
    if (element.attrib.get('INPUT')!=None):
        name = name + ': '+element.attrib['INPUT']

    #todo get NOTES item
    #todo get all ADDER items
    return get_json(get_parent(element),[("name",name)])

def add_martial_arts(hdc_root, token_root):

    for map in token_root.findall('propertyMapCI'):
        for store in map:
            property_store = store

    #get values from hdc
    print('  Getting martial arts')
    for ma_list in hdc_root.findall('MARTIALARTS'):
        skill_count = 0
        for maneuver in ma_list:

            add_token_property(
                property_store,
                'martialarts.maneuver{:02d}'.format(skill_count),
                get_maneuver_json(maneuver, characteristics))

            skill_count = skill_count + 1

def add_skills(hdc_root, token_root, characteristics):

    for map in token_root.findall('propertyMapCI'):
        for store in map:
            property_store = store

    #get values from hdc
    print('  Getting skills')
    for skill_list in hdc_root.findall('SKILLS'):
        skill_count = 0
        for skill in skill_list:

            add_token_property(
                property_store,
                'skills.skill{:02d}'.format(skill_count),
                get_skill_json(skill, characteristics))

            skill_count = skill_count + 1

def update_character_info(hdc_root, token_root):
    print ('  Updating character info')
    info = hdc_root.find('CHARACTER_INFO')
    name = info.attrib['CHARACTER_NAME']
    debug_print("Name: "+name)

    tok_name = token_root.find('name')
    tok_name.text = name

def myround(floatval):
    lower_neighbor = math.floor(floatval)
    if (floatval - lower_neighbor >= 0.5):
        return lower_neighbor+1
    return lower_neighbor

def pd_stat(found_characteristics, value):
    return myround((int(found_characteristics['STR'])+10)/5)+int(value)
def ed_stat(found_characteristics, value):
    return myround((int(found_characteristics['CON'])+10)/5)+int(value)
def spd_stat(found_characteristics, value):
    return 1+math.floor((int(found_characteristics['DEX'])+10)/10)+int(value)
def rec_stat(found_characteristics, value):
    return myround((int(found_characteristics['STR'])+10)/5) + myround((int(found_characteristics['CON'])+10)/5)+int(value)
def end_stat(found_characteristics, value):
    return (int(found_characteristics['CON'])+10)*2+int(value)
def stun_stat(found_characteristics, value):
    return (int(found_characteristics['BODY'])+10) + myround((int(found_characteristics['STR'])+10)/2) + myround((int(found_characteristics['CON'])+10)/2) +int(value)

def primary_stat(found_characteristics, value):
    return 10+int(value)

def update_characteristics(hdc_root, token_root):
    found_characteristics = {}

    #get values from hdc
    for characteristic in hdc_root.findall('CHARACTERISTICS'):
        for child in characteristic:
            #print(child.attrib["XMLID"],child.attrib["LEVELS"])
            found_characteristics[child.attrib['XMLID']]=child.attrib['LEVELS']

    debug_print ('Found characteristics in hdc')
    debug_print (found_characteristics)

    #update token values
    char_name_mapping = {
        'strength_base':('STR',primary_stat),
        'dexterity_base':('DEX',primary_stat),
        'constitution_base':('CON',primary_stat),
        'body_base':('BODY',primary_stat),
        'intelligence_base':('INT',primary_stat),
        'ego_base':('EGO',primary_stat),
        'presence_base':('PRE',primary_stat),
        'comeliness_base':('COM',primary_stat),
        'pd_base':('PD',pd_stat),
        'ed_base':('ED',ed_stat),
        'speed_base':('SPD',spd_stat),
        'recovery_base':('REC',rec_stat),
        'endurance_base':('END',end_stat),
        'stun_base':('STUN',stun_stat)
    }

    for map in token_root.findall('propertyMapCI'):
        for store in map:
            for entry in store:
                string_elem = entry.find('string')
                if (string_elem.text in char_name_mapping.keys()):
                    new_value = int(found_characteristics[char_name_mapping[string_elem.text][0]])
                    new_value = char_name_mapping[string_elem.text][1](found_characteristics, new_value)
                    key_val = entry.find('net.rptools.CaseInsensitiveHashMap_-KeyValue')
                    value = key_val.find('value')
                    value.text=str(new_value)
                else:
                    debug_print("Couldn't map "+string_elem.text)

    #TODO figured characteristics

    return found_characteristics

def get_sample_token_content_xml(filename):
    with zipfile.ZipFile(filename) as myzip:
        with myzip.open('content.xml') as myfile:
            tree = ElementTree.parse(myfile)
            root = tree.getroot()

    return root

def read_hdc(filename):
    print('Reading ',filename)
    tree = ElementTree.parse(filename)
    root = tree.getroot()

    return root


###############################################################################
# script start
print('hdc_to_token v0.1')
#print('Number of arguments:', len(sys.argv), 'arguments.')
#print('Argument List:', str(sys.argv))
#print('Name:', sys.argv[1])

for n in range(1, len(sys.argv)):
    hdc_name = sys.argv[n]
    hdc_root = read_hdc(hdc_name)

    new_token_filename = hdc_name+".rptok"

    if (os.path.exists(new_token_filename)):
        os.remove(new_token_filename)

    sample_token_filename = 'sample.rptok'
    shutil.copyfile(sample_token_filename, new_token_filename)

    token_root = get_sample_token_content_xml(new_token_filename)

    update_character_info(hdc_root, token_root)
    characteristics = update_characteristics(hdc_root, token_root)
    add_skills(hdc_root, token_root, characteristics)
    add_martial_arts(hdc_root, token_root)
    add_powers(hdc_root, token_root)
    add_disads(hdc_root, token_root)

    update_zip(new_token_filename,'content.xml',ElementTree.tostring(token_root))
    print("Done.")