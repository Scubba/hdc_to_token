#!/usr/bin/python

#this takes a .hdc file and the path to a sample token directory
#reads the content.xml, replacing the xml

import sys
import shutil
import time
import os
import zipfile
import math
import xml.etree.ElementTree as ElementTree
from shutil import copyfile

ITALICS = '<i>'
ITALICS_END = '</i>'

DEBUG=1
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
        json = json + '\"' + item[0] + '\":\"' + item[1].replace('"',' in.') + '\"'

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

def add_perks(hdc_root, token_root):
    for map in token_root.findall('propertyMapCI'):
        for store in map:
            property_store = store

    #get values from hdc
    print('  Getting perks')
    for list in hdc_root.findall('PERKS'):
        count = 0
        for perk in list:

            add_token_property(
                property_store,
                'perks.perk{:02d}'.format(count),
                get_perk_json(perk))

            count = count + 1

def add_talents(hdc_root, token_root):
    for map in token_root.findall('propertyMapCI'):
        for store in map:
            property_store = store

    #get values from hdc
    print('  Getting talents')
    for list in hdc_root.findall('TALENTS'):
        count = 0
        for talent in list:

            add_token_property(
                property_store,
                'talents.talent{:02d}'.format(count),
                get_talent_json(talent))

            count = count + 1

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
                get_disad_json(disad))

            disad_count = disad_count + 1

def add_timestamp(hdc_root, token_root):
    for map in token_root.findall('propertyMapCI'):
        for store in map:
            property_store = store

    add_token_property(
        property_store,
        'convert_timestamp',
        str(int(time.time())))

def round_down(floatval):
    lower_neighbor = math.floor(floatval)
    if (floatval - lower_neighbor > 0.5):
        return lower_neighbor+1
    return lower_neighbor

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
    if (mod == "0.0"):
        return "+0"

    number_str = str(math.floor(float(mod)))
    if (float(mod)>0):
        number_str = "+"+number_str

    return number_str

def get_options_tuple(element):
    options = ""
    for sub in element.findall('ADDER'):
        alias = get_safe_attrib(sub, 'ALIAS')
        opt_alias = get_safe_attrib(sub,'OPTION_ALIAS')
        if (len(opt_alias)):
            alias = opt_alias
        if (len(options)):
            options = options +  ", "
        options = options + alias

    return ("options", options)

def get_notes_tuple(element):
    note = ""
    for sub in element.findall('NOTES'):
        note = sub.text
        if (note != None):
            return ("notes", note)
    return ()

def has_charges(element):
    modifiers = ""
    for sub in element.findall('MODIFIER'):
        xmlid = get_safe_attrib(sub, 'XMLID')
        if (xmlid == "CHARGES"):
            return 1
    return 0

# this is the advantages that apply to END
# not reduced end
def get_end_advantage(element):
    advantage = 0
    for sub in element.findall('MODIFIER'):
        levels = get_safe_attrib(sub, 'LEVELS')
        xmlid = get_safe_attrib(sub, 'XMLID')
        mod = get_safe_attrib(sub, 'BASECOST')
        mod = get_corrected_modifier(mod, xmlid, levels)

        amod = 0.0
        for adder in sub.findall('ADDER'):
            amod = float(get_safe_attrib(adder, 'BASECOST'))

        if ((float(mod)+amod) > 0 and 'REDUCEDEND' != xmlid):
            advantage = advantage + float(mod) + amod

    return advantage

def get_active_cost(element, base_cost):
    str_add = 0
    xmlid = get_safe_attrib(element, 'XMLID')
    if ('HANDTOHANDATTACK' == xmlid or
        'HKA' == xmlid):
        debug_print("could be Adding str to active cost")
        str_add = 0
    adv = get_end_advantage(element)
    debug_print("adv: "+str(adv))
    ac = (base_cost+str_add) * (1+adv)

    return ac

# check the base power
# modify by COSTEND or zero END
def power_costs_end(element):
    xmlid = get_safe_attrib(element, 'XMLID')
    costs_end = power_descriptors[xmlid][1]

    for sub in element.findall('MODIFIER'):
        xmlid = get_safe_attrib(sub, 'XMLID')
        if (xmlid == "COSTSEND"):
            debug_print("Costs END modifier")
            costs_end = True
        if (xmlid == "REDUCEDEND"):
            if (get_safe_attrib(sub,'OPTIONID')=="ZERO"):
                debug_print("0 END modifier")
                costs_end = False

    return costs_end

def get_end_multiple(element):
    end_mult = 1.0

    for sub in element.findall('MODIFIER'):
        xmlid = get_safe_attrib(sub, 'XMLID')
        optionid = get_safe_attrib(sub, 'OPTIONID')
        if (xmlid == "INCREASEDEND"):
            debug_print("Increased END modifier:" + optionid)
            if ('2X'==optionid):
                end_mult = 2.0
            elif ('3X'==optionid):
                end_mult = 3.0
            elif ('4X'==optionid):
                end_mult = 4.0
            elif ('5X'==optionid):
                end_mult = 5.0
            elif ('6X'==optionid):
                end_mult = 6.0
            elif ('7X'==optionid):
                end_mult = 7.0
            elif ('8X'==optionid):
                end_mult = 8.0
            elif ('9X'==optionid):
                end_mult = 9.0
            elif ('10X'==optionid):
                end_mult = 10.0

        if (xmlid == "REDUCEDEND"):
            debug_print("Reduced END modifier:" + optionid)
            if ('ZERO'==optionid):
                end_mult = 0.0
            else:
                end_mult = 0.5
    return end_mult

def get_end_cost(element, base_cost):
    debug_print("Getting end cost for "+get_safe_attrib(element, 'XMLID'))
    debug_print("bc:"+str(base_cost))
    ac = get_active_cost(element, base_cost)
    debug_print("ac: "+str(ac))
    # charges are always 0
    if (power_costs_end(element)==False):
        debug_print("not an end power")
        return "0"
    elif (has_charges(element)):
        debug_print("has charges (0 end)")
        return "0"
    else:
        # calculate active cost, divide by 10
        base_end = round_down(ac/10)
        debug_print("base end cost: "+str(base_end))
        # do we have reduced (increased) END?
        end_mult = get_end_multiple(element)
        end = round_down(base_end*end_mult)
        # do not round to zero
        if (end_mult > 0 and ac > 0):
            end = max(1,end)
        debug_print("final end cost: "+str(end)+" ("+str(end_mult)+")")
        return ""+str(end)

#returns nested tuples
#
# (("adders",adders),add_cost)

def get_adders(element):
    adders = ""
    add_cost = 0
    for sub in element.findall('ADDER'):
        xmlid = get_safe_attrib(sub, 'XMLID')
        mod = get_safe_attrib(sub, 'BASECOST')
        if (xmlid != "IMPROVEDNONCOMBAT"):
            add_cost = add_cost + round(float(mod))
        name = get_safe_attrib(sub, 'ALIAS')
        more = get_safe_attrib(sub, 'OPTION_ALIAS')
        comment = get_safe_attrib(sub, 'COMMENTS')

        levels = get_safe_attrib(sub, 'LEVELS')
        level_cost = get_safe_attrib(sub, 'LVLCOST')
        if (len(levels) and len(level_cost)):
            add_cost = add_cost + round(float(levels)*float(level_cost))

        if (len(adders)):
            adders = adders + ", "
        if (len(name) and len(more)):
            more = " " + more
        mod_str = get_mod_string(mod)
        if (len(comment) and len(mod_str)):
            comment = comment + " "
        if (len(comment) + len(mod_str)>0):
            comment_str = " (" + comment + mod_str + ")"
        else:
            comment_str = ""
        adders = adders + name + more + comment_str
    return (("adders", adders), add_cost)


def get_corrected_modifier(mod, xmlid, levels):
    ret_mod = mod

    # why oh why doesn't this advantage have a correct BASECOST?
    if (xmlid == 'ARMORPIERCING'):
        ret_mod = str(int(levels)*0.5)
    elif (xmlid == 'PENETRATING'):
        ret_mod = str(int(levels)*0.25)
    return ret_mod


def get_modifier_tuple(element):
    modifiers = ""
    for sub in element.findall('MODIFIER'):
        mod = get_safe_attrib(sub, 'BASECOST')
        name = get_safe_attrib(sub, 'ALIAS')
        more = get_safe_attrib(sub, 'OPTION_ALIAS')
        comment = get_safe_attrib(sub, 'COMMENTS')
        levels = get_safe_attrib(sub, 'LEVELS')
        xmlid = get_safe_attrib(sub, 'XMLID')
        mod = get_corrected_modifier(mod, xmlid, levels)

        # things like clips adding to charges
        for adder in sub.findall('ADDER'):
            more = more + " " + get_safe_attrib(adder, 'ALIAS')

        if (len(modifiers)):
            modifiers = modifiers + ", "
        if (len(name) and len(more)):
            more = " " + more
        mod_str = get_mod_string(mod)
        if (len(comment) and len(mod_str)):
            comment = comment + " "
        modifiers = modifiers + name + more + " (" + comment + mod_str + ")"
    return ("modifiers",modifiers)

def get_half_die(element):
    half_die = ""
    for sub in element.findall('ADDER'):
        if (sub.attrib['XMLID']=='PLUSONEHALFDIE'):
            half_die = " ½"
    return half_die

# Collects common power information as a list of tuples (name, value)
# this gets the powerid/name/alias/option to determine a proper presentation name
# adds ultra slot & end reserve tuples
# and also adds modifiers & adders as tuples
def get_power_name_list(element, base_cost):
    name = element.attrib['NAME']
    if (name != ''):
        name = ITALICS+name+ITALICS_END
    power_type = element.attrib['XMLID']
    alias = element.attrib['ALIAS']
    inputstr = get_safe_attrib(element,'INPUT')
    optionalias = get_safe_attrib(element,'OPTION_ALIAS')
    name_list = [("name",name),("POWER_ID",power_type),("alias",alias+" "+inputstr+optionalias)]
    name_list.append(("parent",get_parent(element)))
    if (get_safe_attrib(element,'ULTRA_SLOT')=="Yes"):
        name_list.append(("ultra","1"))
    if (get_safe_attrib(element,"USE_END_RESERVE")=="Yes"):
        name_list.append(("use_end_reserve","1"))

    name_list.append(get_modifier_tuple(element))
    adders = get_adders(element)
    name_list.append(adders[0])

#TODO: need to get max end cost for some
    name_list.append(("end",get_end_cost(element, base_cost + adders[1])))

    notes = get_notes_tuple(element)
    if (notes!=()):
        name_list.append(notes)

    return name_list

def has_plus_one_pip(element):
    for sub in element.findall('ADDER'):
        xmlid = get_safe_attrib(sub, 'XMLID')
        if (xmlid == "PLUSONEPIP"):
            return True

    return False

def get_ka_dice_power_json(element, add_dc = 0):
    levels=element.attrib['LEVELS']
    half_die = get_half_die(element)
    #TODO add STR bonus to active cost for appropriate powers
    if (add_dc > 0):
        levels = levels + 0
    name_list = get_power_name_list(element, int(levels)*15) # + (10 if len(half_die)>0 else 0) + (5 if has_plus_one_pip(element) else 0))
    name_list.append(("dice",levels+half_die))
    return get_json(get_parent(element),name_list)

#add_dc allows appropriate powers to add a STR bonus to dice
def get_std_dice_power_json(element, add_dc = 0):
    levels=element.attrib['LEVELS']
    half_die = get_half_die(element)
    name_list = get_power_name_list(element, int(levels)*5) # + (3 if len(half_die)>0 else 0))
    name_list.append(("dice",levels+half_die))
    name_list.append(("max_dice",str(int(levels)+add_dc)))
    return get_json(get_parent(element),name_list)

def get_10pt_dice_power_json(element):
    levels=element.attrib['LEVELS']
    half_die = get_half_die(element)
    name_list = get_power_name_list(element, int(levels)*10) # + (5 if len(half_die)>0 else 0))
    name_list.append(("dice",levels+half_die))
    return get_json(get_parent(element),name_list)

def get_3pt_dice_power_json(element):
    levels=element.attrib['LEVELS']
    half_die = get_half_die(element)
    name_list = get_power_name_list(element, int(levels)*3) # + (1 if len(half_die)>0 else 0))
    name_list.append(("dice",levels+half_die))
    return get_json(get_parent(element),name_list)

# Movement Powers

def get_movement_power_json(element, inch_cost):
    inches = element.attrib['LEVELS']
    name_list = get_power_name_list(element, int(inches)*inch_cost)
    name_list.append(("inches", inches))
    return get_json(get_parent(element), name_list)

def get_leaping_json(element, characteristics):
    return get_movement_power_json(element, 1)

def get_running_json(element, characteristics):
    return get_movement_power_json(element, 2)

def get_flight_json(element, characteristics):
    return get_movement_power_json(element, 2)

def get_swimming_json(element, characteristics):
    return get_movement_power_json(element, 1)

def get_teleport_json(element, characteristics):
    return get_movement_power_json(element, 2)


# General Powers

def get_absorption_json(element, characteristics):
    return get_std_dice_power_json(element)

def get_aid_json(element, characteristics):
    return get_10pt_dice_power_json(element)

def get_armor_json(element, characteristics):
    pd = element.attrib['PDLEVELS']
    ed = element.attrib['EDLEVELS']
    defense = int(pd)+int(ed)
    name_list = get_power_name_list(element, round(defense/2)*3)
    name_list.append(("pd", pd))
    name_list.append(("ed", ed))
    name_list.append(("rpd", pd))
    name_list.append(("red", ed))
    return get_json(get_parent(element),name_list)

def get_changeenvironment_json(element, characteristics):
    levels=element.attrib['LEVELS']
    name_list = get_power_name_list(element, 5 * int(levels))
    return get_json(get_parent(element),name_list)

def get_clinging_json(element, characteristics):
    levels=element.attrib['LEVELS']
    name_list = get_power_name_list(element, 10+int(levels))
    name_list.append(("str_add",str(3*int(levels))))
    return get_json(get_parent(element),name_list)

def get_damage_reduction_json(element, characteristics):
    bc = get_safe_attrib(element, 'BASECOST')
    name_list = get_power_name_list(element, round(float(bc)))
    opt=element.attrib['OPTION']
    name_list.append(("damagereduction_opt",opt))
    return get_json(get_parent(element),name_list)

def get_darkness_json(element, characteristics):
    radius = element.attrib['LEVELS']
    name_list = get_power_name_list(element, 10*int(radius))
    name_list.append(("radius",radius))
    return get_json(get_parent(element),name_list)

def get_dispel_json(element, characteristics):
    return get_3pt_dice_power_json(element)

def get_drain_json(element, characteristics):
    return get_10pt_dice_power_json(element)

def get_damage_resistance_json(element, characteristics):
    rpd = element.attrib['PDLEVELS']
    red = element.attrib['EDLEVELS']
    name_list = get_power_name_list(element, round((int(rpd)+int(red))/2))
    name_list.append(("rpd", rpd))
    name_list.append(("red", red))
    md = element.attrib['MDLEVELS']
    powd = element.attrib['POWDLEVELS']
    if (int(md)>0):
        name_list.append(("rmentaldef", md))
    if (int(powd)>0):
        name_list.append(("rpowerdef", powd))
    return get_json(get_parent(element),name_list)

def get_ego_attack_json(element, characteristics):
    return get_10pt_dice_power_json(element)

def get_endurancereserve_json(element, characteristics):
    name_list = get_power_name_list(element, 0)

    #REC is stored in a POWER CHILD
    for sub in element.findall('POWER'):
        id = get_safe_attrib(sub, "XMLID")
        if ("ENDURANCERESERVEREC" == id):
            name_list.append(("rec",sub.attrib['LEVELS']))

    name_list.append(("end",element.attrib['LEVELS']))
    return get_json(get_parent(element),name_list)

def get_energyblast_json(element, characteristics):
    return get_std_dice_power_json(element)

def get_entangle_json(element, characteristics):
    #TODO:  is additional def/body handled correctly by adders/modifiers?
    return get_10pt_dice_power_json(element)

def get_extralimbs_json(element, characteristics):
    limbs = element.attrib['LEVELS']
    name_list = get_power_name_list(element, 5*int(limbs))
    name_list.append(("limbs",limbs))
    return get_json(get_parent(element),name_list)

def get_findweakness_json(element, characteristics):
    bc = round(float(get_safe_attrib(element, 'BASECOST')))
    levels = int(element.attrib['LEVELS'])
    name_list = get_power_name_list(element, bc + 5*levels)
    name_list.append(("roll",str(11+levels)))
    return get_json(get_parent(element),name_list)

def get_flash_json(element, characteristics):
    return get_std_dice_power_json(element)

def get_flashdefense_json(element, characteristics):
    defense = element.attrib['LEVELS']
    name_list = get_power_name_list(element, int(defense))
    name_list.append(("flashdef", defense))
    return get_json(get_parent(element),name_list)

def get_forcefield_json(element, characteristics):
    pd = element.attrib['PDLEVELS']
    ed = element.attrib['EDLEVELS']
    name_list = get_power_name_list(element, int(pd)+int(ed))
    name_list.append(("pd", pd))
    name_list.append(("ed", ed))
    name_list.append(("rpd", pd))
    name_list.append(("red", ed))
    md = element.attrib['MDLEVELS']
    powd = element.attrib['POWDLEVELS']
    if (int(md)>0):
        name_list.append(("mentaldef", md))
    if (int(powd)>0):
        name_list.append(("powerdef", powd))
    return get_json(get_parent(element),name_list)

def get_forcewall_json(element, characteristics):
    pd = element.attrib['PDLEVELS']
    ed = element.attrib['EDLEVELS']
    length = element.attrib['LENGTHLEVELS']
    name_list = get_power_name_list(element, 5*round_down((int(pd)+int(ed))/2)+2*int(length))
    name_list.append(("pd", pd))
    name_list.append(("ed", ed))
    name_list.append(("length", length))
    return get_json(get_parent(element),name_list)

def get_hka_json(element, characteristics):
    #TODO: determine how many DCs we can add (no more than original, allowing for advantages)
    return get_ka_dice_power_json(element)

def get_hth_attack_json(element, characteristics):
    str_add = round(int(characteristics['STR']) / 5)
    return get_std_dice_power_json(element, str_add)

def get_images_json(element, characteristics):
    return get_std_dice_power_json(element)

def get_invisibility_json(element, characteristics):
    bc = get_safe_attrib(element, 'BASECOST')
    name_list = get_power_name_list(element, round(float(bc)))
    return get_json(get_parent(element),name_list)

def get_kb_resistance_json(element, characteristics):
    kbres = element.attrib['LEVELS']
    name_list = get_power_name_list(element, round(int(kbres)/2))
    name_list.append(("inches", kbres))
    return get_json(get_parent(element),name_list)

def get_lack_of_weakness_json(element, characteristics):
    lack = element.attrib['LEVELS']
    name_list = get_power_name_list(element, int(lack))
    return get_json(get_parent(element),name_list)

def get_lifesupport_json(element, characteristics):
    name_list = get_power_name_list(element, 0) #all adders
    return get_json(get_parent(element),name_list)

def get_luck_json(element, characteristics):
    luck = element.attrib['LEVELS']
    name_list = get_power_name_list(element, 5*int(luck))
    name_list.append(("luck", luck))
    return get_json(get_parent(element),name_list)

def get_mentaldefense_json(element, characteristics):
    defense = element.attrib['LEVELS']
    name_list = get_power_name_list(element, int(defense))
    name_list.append(("mentaldef", defense))
    return get_json(get_parent(element),name_list)

def get_mentalillusions_json(element, characteristics):
    return get_std_dice_power_json(element)

def get_mindcontrol_json(element, characteristics):
    return get_std_dice_power_json(element)

def get_mind_link_json(element, characteristics):
    bc = get_safe_attrib(element,'BASECOST')
    name_list = get_power_name_list(element, round(float(bc)))
    return get_json(get_parent(element),name_list)

def get_missile_deflection_json(element, characteristics):
    bc = get_safe_attrib(element,'BASECOST')
    name_list = get_power_name_list(element, round(float(bc)))
    return get_json(get_parent(element),name_list)

def get_powerdefense_json(element, characteristics):
    defense = element.attrib['LEVELS']
    name_list = get_power_name_list(element, int(defense))
    name_list.append(("powerdef", defense))
    return get_json(get_parent(element),name_list)

def get_rka_json(element, characteristics):
    return get_ka_dice_power_json(element)

def get_stretching_json(element, characteristics):
    levels=element.attrib['LEVELS']
    name_list = get_power_name_list(element, 5*round(float(levels)))
    name_list.append(("reach",levels))
    return get_json(get_parent(element),name_list)

def get_telekinesis_json(element, characteristics):
    str = element.attrib['LEVELS']
    name_list = get_power_name_list(element, 3*round(int(str)/2))
    name_list.append(("strength", str))
    return get_json(get_parent(element),name_list)

def get_telepathy_json(element, characteristics):
    return get_std_dice_power_json(element)


# Enhanced Senses

def get_activesonar_json(element, characteristics):
    bc = get_safe_attrib(element,'BASECOST')
    name_list = get_power_name_list(element, round(float(bc)))
    return get_json(get_parent(element),name_list)

def get_detect_json(element, characteristics):
    bc = get_safe_attrib(element,'BASECOST')
    levels = get_safe_attrib(element,'LEVELS')
    name_list = get_power_name_list(element, round(float(bc))+int(levels))
    return get_json(get_parent(element),name_list)

def get_enhanced_perception_json(element, characteristics):
    bc = get_safe_attrib(element,'BASECOST')
    name_list = get_power_name_list(element, round(float(bc)))
    return get_json(get_parent(element),name_list)

def get_infrared_json(element, characteristics):
    bc = get_safe_attrib(element,'BASECOST')
    name_list = get_power_name_list(element, round(float(bc)))
    return get_json(get_parent(element),name_list)

def get_mental_awareness_json(element, characteristics):
    bc = get_safe_attrib(element,'BASECOST')
    name_list = get_power_name_list(element, round(float(bc)))
    return get_json(get_parent(element),name_list)

def get_nightvision_json(element, characteristics):
    bc = get_safe_attrib(element,'BASECOST')
    name_list = get_power_name_list(element, round(float(bc)))
    return get_json(get_parent(element),name_list)

def get_nray_perception_json(element, characteristics):
    bc = get_safe_attrib(element,'BASECOST')
    name_list = get_power_name_list(element, round(float(bc)))
    return get_json(get_parent(element),name_list)

def get_radar_json(element, characteristics):
    bc = get_safe_attrib(element,'BASECOST')
    name_list = get_power_name_list(element, round(float(bc)))
    return get_json(get_parent(element),name_list)

def get_radio_json(element, characteristics):
    bc = get_safe_attrib(element,'BASECOST')
    name_list = get_power_name_list(element, round(float(bc)))
    return get_json(get_parent(element),name_list)

def get_spatial_awareness_json(element, characteristics):
    bc = get_safe_attrib(element,'BASECOST')
    name_list = get_power_name_list(element, round(float(bc)))
    return get_json(get_parent(element),name_list)

def get_ultraviolet_json(element, characteristics):
    bc = get_safe_attrib(element,'BASECOST')
    name_list = get_power_name_list(element, round(float(bc)))
    return get_json(get_parent(element),name_list)

def get_ultrasonic_json(element, characteristics):
    bc = get_safe_attrib(element,'BASECOST')
    name_list = get_power_name_list(element, round(float(bc)))
    return get_json(get_parent(element),name_list)

# Characteristic Powers

def get_characteristic_power(name, element):
    name_list = get_power_name_list(element, 0)
    levels=element.attrib['LEVELS']
    name_list.append((name,levels))
    return get_json(get_parent(element),name_list)

def get_body_power_json(element, characteristics):
    return get_characteristic_power("body",element)

def get_rec_power_json(element, characteristics):
    return get_characteristic_power("recovery",element)

def get_con_power_json(element, characteristics):
    return get_characteristic_power("constitution",element)

def get_dex_power_json(element, characteristics):
    return get_characteristic_power("dexterity",element)

def get_end_power_json(element, characteristics):
    return get_characteristic_power("endurance",element)

def get_int_power_json(element, characteristics):
    return get_characteristic_power("intelligence",element)

def get_pre_power_json(element, characteristics):
    return get_characteristic_power("presence",element)

def get_ed_power_json(element, characteristics):
    return get_characteristic_power("ed",element)

def get_pd_power_json(element, characteristics):
    return get_characteristic_power("pd",element)

def get_spd_power_json(element, characteristics):
    return get_characteristic_power("speed",element)

def get_str_power_json(element, characteristics):
    return get_characteristic_power("strength",element)

def get_framework_json(element, characteristics):
    pool = element.attrib['BASECOST']
    title = ITALICS+element.attrib['NAME']+ITALICS_END
    name_list = [("name",title),("POWER_ID", element.attrib['XMLID'])]
    name_list.append(("id",element.attrib['ID']))
    alias_attrib = element.attrib['ALIAS']
    alias = alias_attrib
    if (pool != '0.0'):
        alias = alias+", "+str(math.floor(float(pool)))+"-point"
        if (alias_attrib == 'Multipower'):
            alias = alias + " reserve"
        if (alias_attrib == 'Elemental Control'):
            alias = alias + " powers"
    name_list.append(("alias",alias))
    name_list.append(get_modifier_tuple(element))
    return get_json(get_parent(element),name_list)

def missing_power_json(element):
    return element.attrib['NAME'] + ": " + element.attrib['XMLID'] + " UNSUPPORTED"

# Skills

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

    title = language+' ('+alias+'; '+literacy+')'
    if (name != ''):
        title = ITALICS+name+ITALICS_END+': '+ title

    return get_json(get_parent(element),[("name",title)])

def get_csl_json(element):
    levels = element.attrib['LEVELS']
    name = element.attrib['NAME']
    alias = element.attrib['OPTION_ALIAS']
    tuples = [("name",name),("alias",alias),("levels",str(levels))]
    notes = get_notes_tuple(element)
    if (notes!=()):
        tuples.append(notes)
    if (name != ""):
        name = ITALICS+name+ITALICS_END
    return get_json(get_parent(element),tuples)

def get_skill_level_json(element):
    levels = element.attrib['LEVELS']
    name = element.attrib['NAME']
    alias = element.attrib['OPTION_ALIAS']
    tuples = [("name",name),("alias",alias),("levels",str(levels))]
    notes = get_notes_tuple(element)
    if (notes!=()):
        tuples.append(notes)
    if (name != ""):
        name = ITALICS+name+ITALICS_END
    return get_json(get_parent(element),tuples)

def get_penalty_skill_level_json(element):
    levels = element.attrib['LEVELS']
    name = element.attrib['NAME']
    alias = element.attrib['OPTION_ALIAS']
    inputstr = element.attrib['INPUT']
    if (name != ""):
        name = ITALICS+name+ITALICS_END
    return get_json(get_parent(element),[("name",name),("alias","vs. "+inputstr+" with "+alias),("levels",str(levels))])

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
    elif (skill_type == 'PENALTY_SKILL_LEVELS'):
        return get_penalty_skill_level_json(element)

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
        tuples = [("name",name),("alias",element.attrib['ALIAS']+input_val)]
    else:
        tuples = [("name",name),("alias",element.attrib['ALIAS']+input_val),("roll",str(value))]

    notes = get_notes_tuple(element)
    if (notes!=()):
        tuples.append(notes)
    return get_json(get_parent(element),tuples)


power_descriptors = {
    #xmlid : (get_json_func, bCostsEnd)
    "ABSORPTION" : (get_absorption_json, False),
    "ACTIVESONAR" : (get_activesonar_json, False),
    "AID" : (get_aid_json, False),
    "ARMOR" : (get_armor_json, False),
    "CHANGEENVIRONMENT" : (get_changeenvironment_json, True),
    "CLINGING" : (get_clinging_json, False),
    "COMBAT_LEVELS" : (get_csl_json, False),
    "DAMAGEREDUCTION" : (get_damage_reduction_json, False),
    "DAMAGERESISTANCE" : (get_damage_resistance_json, False),
    "DARKNESS" : (get_darkness_json, True),
    "DISPEL" : (get_dispel_json, False),
    "DRAIN" : (get_drain_json, False),
    "EGOATTACK" : (get_ego_attack_json, True),
    "ENDURANCERESERVE" : (get_endurancereserve_json, False),
    "ENERGYBLAST" : (get_energyblast_json, True),

    # Enhanced Senses
    "DETECT" : (get_detect_json, False),
    "ENHANCEDPERCEPTION" : (get_enhanced_perception_json, False),
    "INFRAREDPERCEPTION" : (get_infrared_json, False),
    "NIGHTVISION" : (get_nightvision_json, False),
    "NRAYPERCEPTION" : (get_nray_perception_json, False),
    "RADAR" : (get_radar_json, False),
    "RADIOPERCEIVETRANSMIT" : (get_radio_json, False),
    "SPATIALAWARENESS" : (get_spatial_awareness_json, False),
    "ULTRASONICPERCEPTION" : (get_ultrasonic_json, False),
    "ULTRAVIOLETPERCEPTION" : (get_ultraviolet_json, False),

    "ENTANGLE" : (get_entangle_json, True),
    "EXTRALIMBS" : (get_extralimbs_json, False),
    "FINDWEAKNESS" : (get_findweakness_json, False),
    "FLASH" : (get_flash_json, True),
    "FLASHDEFENSE" : (get_flashdefense_json, False),
    "FLIGHT" : (get_flight_json, True),
    "FORCEFIELD" : (get_forcefield_json, True),
    "FORCEWALL" : (get_forcewall_json, True),
    "GENERIC_OBJECT" : (get_framework_json, False),
    "GLIDING" : (get_leaping_json, True),
    "HANDTOHANDATTACK" : (get_hth_attack_json, True),
    "HKA" : (get_hka_json, True),
    "IMAGES" : (get_images_json, True),
    "INVISIBILITY" : (get_invisibility_json, True),
    "KBRESISTANCE" : (get_kb_resistance_json, False),
    "LACKOFWEAKNESS" : (get_lack_of_weakness_json, False),
    "LEAPING" : (get_leaping_json, True),
    "LIFESUPPORT" : (get_lifesupport_json, False),
    "LUCK" : (get_luck_json, False),
    "MENTALAWARENESS" : (get_mental_awareness_json, False),
    "MENTALDEFENSE" : (get_mentaldefense_json, False),
    "MENTALILLUSIONS" : (get_mentalillusions_json, True),
    "MINDCONTROL" : (get_mindcontrol_json, True),
    "MINDLINK" : (get_mind_link_json, False),
    "MISSILEDEFLECTION" : (get_missile_deflection_json, False),
    "POWERDEFENSE" : (get_powerdefense_json, False),
    "RKA" : (get_rka_json, True),
    "RUNNING" : (get_running_json, True),
    "STRETCHING" : (get_stretching_json, True),
    "SWIMMING" : (get_swimming_json, True),
    "TELEPORTATION" : (get_teleport_json, True),
    "TELEKINESIS": (get_telekinesis_json, True),
    "TELEPATHY" : (get_telepathy_json, True),

    #characterstics as powers
    "BODY"  : (get_body_power_json, False),
    "CON" : (get_con_power_json, False),
    "DEX" : (get_dex_power_json, False),
    "END" : (get_end_power_json, False),
    "ED" : (get_ed_power_json, False),
    "PD" : (get_pd_power_json, False),
    "INT" : (get_int_power_json, False),
    "PRE" : (get_pre_power_json, False),
    "REC" : (get_rec_power_json, False),
    "SPD" : (get_spd_power_json, False),
    "STR" : (get_str_power_json, True)
}

def get_power_json(element, characteristics):
    power_type = element.attrib['XMLID']
    return power_descriptors[power_type][0](element, characteristics)

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

def add_powers(hdc_root, token_root, characteristics):
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
    name = get_safe_attrib(element,'DISPLAY')
    alias = get_safe_attrib(element,'ALIAS')
    if (name==""):
        name = alias

    return get_json(get_parent(element),[("name",name)])

def get_perk_json(element):
    # <i>NAME</i>: ALIAS: INPUT (OPTION_ALIAS)
    name = element.attrib['NAME']
    alias = element.attrib['ALIAS']
    option_alias = get_safe_attrib(element,'OPTION_ALIAS')
    input_txt = get_safe_attrib(element,'INPUT')

    title = (ITALICS + name + ITALICS_END) if len(name) else ""
    title = (title + ': '+ alias) if len(title) else alias
    title = (title + ': '+ input_txt) if len(input_txt) else title
    title = (title + ': ('+ option_alias + ')') if len(option_alias) else title

    tuples = [("name",title)]

    # get NOTES item
    notes = get_notes_tuple(element)
    if (notes!=()):
        tuples.append(notes)
    # get all ADDER items
    tuples.append(get_options_tuple(element))
    return get_json(get_parent(element),tuples)

def get_combat_luck_tuples(element):
    levels = get_safe_attrib(element,'LEVELS')
    defense = 3 * levels
    return [("pd", defense),
            ("ed", defense),
            ("rpd", defense),
            ("red", defense)]

talent_descriptors = {
    "COMBAT_LUCK" : get_combat_luck_tuples
}


def get_talent_json(element):
    name = element.attrib['NAME']
    title = element.attrib['ALIAS']
    if (name != ""):
        title = ITALICS+name + ITALICS_END+': '+title

    if (element.attrib.get('OPTION_ALIAS')!=None):
        title = title + ' ('+element.attrib['OPTION_ALIAS']+')'

    tuples = [("name",title)]

    talent_type = element.attrib['XMLID']
    if (talent_type in talent_descriptors):
        tuples = tuples + talent_descriptors[talent_type](element)

    # get NOTES item
    notes = get_notes_tuple(element)
    if (notes!=()):
        tuples.append(notes)
    # get all ADDER items
    tuples.append(get_options_tuple(element))
    return get_json(get_parent(element),tuples)

def get_disad_json(element):
    name = element.attrib['ALIAS']
    if (element.attrib.get('INPUT')!=None):
        name = name + ': '+element.attrib['INPUT']
    tuples = [("name",name)]
    # get NOTES item
    notes = get_notes_tuple(element)
    if (notes!=()):
        tuples.append(notes)
    # get all ADDER items
    tuples.append(get_options_tuple(element))
    return get_json(get_parent(element),tuples)

def add_martial_arts(hdc_root, token_root, characteristics):

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

def pd_stat(found_characteristics, value):
    return round_down((int(found_characteristics['STR'])+10)/5)+int(value)
def ed_stat(found_characteristics, value):
    return round_down((int(found_characteristics['CON'])+10)/5)+int(value)
def spd_stat(found_characteristics, value):
    return 1+math.floor((int(found_characteristics['DEX'])+10)/10)+int(value)
def rec_stat(found_characteristics, value):
    return round_down((int(found_characteristics['STR'])+10)/5) + round_down((int(found_characteristics['CON'])+10)/5)+int(value)
def end_stat(found_characteristics, value):
    return (int(found_characteristics['CON'])+10)*2+int(value)
def stun_stat(found_characteristics, value):
    return (int(found_characteristics['BODY'])+10) + round_down((int(found_characteristics['STR'])+10)/2) + round_down((int(found_characteristics['CON'])+10)/2) +int(value)

def running_stat(found_characteristics, value):
    return 6+int(value)
def swimming_stat(found_characteristics, value):
    return 2+int(value)
def leaping_stat(found_characteristics, value):
    return round_down((int(found_characteristics['STR'])+10)/5)+int(value)

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
        'stun_base':('STUN',stun_stat),
        'running_base':('RUNNING',running_stat),
        'swimming_base':('SWIMMING',swimming_stat),
        'leaping_base':('LEAPING',leaping_stat)
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

def main():
    print('hdc_to_token v0.1')
    debug_print('Number of arguments:'+ str(len(sys.argv)) + ' arguments.')
    debug_print('Argument List:' + str(sys.argv))

    for n in range(1, len(sys.argv)):
        hdc_name = sys.argv[n]
        debug_print('Name:' + hdc_name)
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
        add_martial_arts(hdc_root, token_root, characteristics)
        add_perks(hdc_root, token_root)
        add_talents(hdc_root, token_root)
        add_powers(hdc_root, token_root, characteristics)
        add_disads(hdc_root, token_root)
        add_timestamp(hdc_root, token_root)

        update_zip(new_token_filename,'content.xml',ElementTree.tostring(token_root))
        print("Done.")

###############################################################################
# script start
if __name__=="__main__":
   main()