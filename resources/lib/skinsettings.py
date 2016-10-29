#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmc, xbmcvfs, xbmcgui, xbmcaddon
from simplecache import SimpleCache
from utils import log_msg, try_encode, normalize_string, get_clean_image, KODI_VERSION, process_method_on_list, log_exception, ADDON_ID, try_decode
from dialogs import DialogSelectSmall, DialogSelectBig
from artutils import KodiDb, Tmdb
from datetime import timedelta
import urlparse, urllib
from xml.dom.minidom import parse
import xml.etree.ElementTree as xmltree
import sys, os

class SkinSettings:
    '''several helpers that allows skinners to have custom dialogs for their skin settings and constants'''
    params = {}

    def __init__(self):
        '''Initialization'''
        self.win = xbmcgui.Window(10000)
        self.addon = xbmcaddon.Addon(ADDON_ID)

    def __del__(self):
        '''Cleanup Kodi Cpython instances'''
        del self.win
        del self.addon

    def write_skin_constants(self, listing):
        #writes the list of all skin constants
        addonpath = xbmc.translatePath( os.path.join( "special://skin/", 'addon.xml').encode("utf-8") ).decode("utf-8")
        addon = xmltree.parse( addonpath )
        extensionpoints = addon.findall( "extension" )
        paths = []
        for extensionpoint in extensionpoints:
            if extensionpoint.attrib.get( "point" ) == "xbmc.gui.skin":
                resolutions = extensionpoint.findall( "res" )
                for resolution in resolutions:
                    includes_file = xbmc.translatePath( os.path.join("special://skin/" , try_decode( resolution.attrib.get( "folder" ) ), "script-skin_helper_service-includes.xml").encode("utf-8") ).decode('utf-8')
                    tree = xmltree.ElementTree( xmltree.Element( "includes" ) )
                    root = tree.getroot()
                    for key, value in listing.iteritems():
                        if value:
                            child = xmltree.SubElement( root, "constant" )
                            child.text = value
                            child.attrib[ "name" ] = key
                            #also write to skin strings
                            xbmc.executebuiltin("Skin.SetString(%s,%s)" %(key.encode("utf-8"),value.encode("utf-8")))
                    self.indent_xml( tree.getroot() )
                    xmlstring = xmltree.tostring(tree.getroot(), encoding="utf-8")
                    f = xbmcvfs.File(includes_file, 'w')
                    f.write(xmlstring)
                    f.close()
        xbmc.executebuiltin("ReloadSkin()")

    def get_skin_constants(self):
        #gets a list of all skin constants
        allConstants = {}
        addonpath = xbmc.translatePath( os.path.join( "special://skin/", 'addon.xml').encode("utf-8") ).decode("utf-8")
        addon = xmltree.parse( addonpath )
        extensionpoints = addon.findall( "extension" )
        paths = []
        for extensionpoint in extensionpoints:
            if extensionpoint.attrib.get( "point" ) == "xbmc.gui.skin":
                resolutions = extensionpoint.findall( "res" )
                for resolution in resolutions:
                    includes_file = xbmc.translatePath( os.path.join( "special://skin/" , try_decode( resolution.attrib.get( "folder" ) ), "script-skin_helper_service-includes.xml").encode("utf-8") ).decode('utf-8')
                    if xbmcvfs.exists( includes_file ):
                        doc = parse( includes_file )
                        listing = doc.documentElement.getElementsByTagName( 'constant' )
                        for item in listing:
                            name = try_decode(item.attributes[ 'name' ].nodeValue)
                            value = try_decode(item.firstChild.nodeValue)
                            allConstants[name] = value
        return allConstants

    def update_skin_constants(self, new_values):
        updateNeeded = False
        allValues = self.get_skin_constants()
        for key, value in new_values.iteritems():
            if allValues.has_key(key):
                if allValues.get(key) != value:
                    updateNeeded = True
                    allValues[key] = value
            else:
                updateNeeded = True
                allValues[key] = value
        if updateNeeded:
            self.write_skin_constants(allValues)

    def set_skin_constant(self, setting="", window_header="", value=""):
        allCurrentValues = self.get_skin_constants()
        if not value:
            value, label = self.set_skin_setting(setting, window_header, "", allCurrentValues.get(setting,"emptyconstant"))
        result = { setting:value }
        self.update_skin_constants(result)

    def set_skin_constants(self, settings, values):
        result = {}
        for count, setting in enumerate(settings):
            result[setting] = values[count]
        self.update_skin_constants(result)

    def set_skin_setting(self, setting="", window_header="", sublevel="", cur_value="", skip_skin_string=False, original_id=""):
        if not cur_value:
            cur_value = xbmc.getInfoLabel("Skin.String(%s)" %setting).decode("utf-8")
        cur_valueLabel = xbmc.getInfoLabel("Skin.String(%s.label)" %setting).decode("utf-8")
        useRichLayout = False
        selectId = 0
        itemcount = 0

        allValues = []
        settings_file = xbmc.translatePath( 'special://skin/extras/skinsettings.xml' ).decode("utf-8")
        if xbmcvfs.exists( settings_file ):
            doc = parse( settings_file )
            listing = doc.documentElement.getElementsByTagName( 'setting' )
            if sublevel:
                listitem = xbmcgui.ListItem(label="..", iconImage="DefaultFolderBack.png")
                listitem.setProperty("icon","DefaultFolderBack.png")
                listitem.setProperty("value","||BACK||")
                allValues.append(listitem)
            for item in listing:
                settingId = item.attributes[ 'id' ].nodeValue
                if settingId.startswith("$"): settingId = xbmc.getInfoLabel(settingId).decode("utf-8")
                label = xbmc.getInfoLabel(item.attributes[ 'label' ].nodeValue).decode("utf-8")
                if (not sublevel and settingId.lower() == setting.lower()) or (sublevel and sublevel.lower() == settingId.lower()) or (original_id and original_id.lower() == settingId.lower()):
                    value = item.attributes[ 'value' ].nodeValue
                    if value == "||MULTISELECT||": return multiSelect(item,window_header)
                    condition = item.attributes[ 'condition' ].nodeValue
                    icon = item.attributes[ 'icon' ].nodeValue
                    description = item.attributes[ 'description' ].nodeValue
                    description = xbmc.getInfoLabel(description.encode("utf-8"))
                    if condition and not xbmc.getCondVisibility(condition): continue
                    if icon: useRichLayout = True
                    if icon and icon.startswith("$"): icon = xbmc.getInfoLabel(icon)
                    if "%" in label: label = label %value
                    if cur_value and (cur_value.lower() == value.lower() or label.lower() == cur_valueLabel.lower()): selectId = itemcount
                    listitem = xbmcgui.ListItem(label=label, iconImage=icon)
                    listitem.setProperty("value",value)
                    listitem.setProperty("icon",icon)
                    listitem.setProperty("description",description)
                    listitem.setLabel2(description)
                    #additional onselect actions
                    additionalactions = []
                    for action in item.getElementsByTagName( 'onselect' ):
                        condition = action.attributes[ 'condition' ].nodeValue
                        if condition and not xbmc.getCondVisibility(condition): continue
                        command = action.firstChild.nodeValue
                        if "$" in command: command = xbmc.getInfoLabel(command)
                        additionalactions.append(command)
                    listitem.setProperty("additionalactions"," || ".join(additionalactions))
                    allValues.append(listitem)
                    itemcount +=1
            if not allValues:
                selected_item = -1
            elif len(allValues) > 1:
                #only use select dialog if we have muliple values
                if useRichLayout:
                    w = DialogSelectBig( "DialogSelect.xml", self.addon.getAddonInfo('path').decode("utf-8"), listing=allValues, windowtitle=window_header,multiselect=False )
                else:
                    w = DialogSelectSmall( "DialogSelect.xml", self.addon.getAddonInfo('path').decode("utf-8"), listing=allValues, windowtitle=window_header,multiselect=False )
                if selectId >= 0 and sublevel: selectId += 1
                w.autoFocusId = selectId
                w.doModal()
                selected_item = w.result
                del w
            else:
                selected_item = 0
            #process the results
            if selected_item != -1:
                value = try_decode( allValues[selected_item].getProperty("value") )
                label = try_decode( allValues[selected_item].getLabel() )
                description = allValues[selected_item].getProperty("description")
                if value.startswith("||SUBLEVEL||"):
                    sublevel = value.replace("||SUBLEVEL||","")
                    self.set_skin_setting(setting, window_header, sublevel)
                elif value == "||BACK||":
                    self.set_skin_setting(setting, window_header)
                else:
                    if value == "||BROWSEIMAGE||":
                        value = self.save_skin_image(setting,True,label)
                    if value == "||BROWSESINGLEIMAGE||":
                        value = self.save_skin_image(setting,False,label)
                    if value == "||BROWSEMULTIIMAGE||":
                        value = self.save_skin_image(setting,True,label,True)
                    if value == "||PROMPTNUMERIC||":
                        value = xbmcgui.Dialog().input( label,cur_value, 1).decode("utf-8")
                    if value == "||PROMPTSTRING||":
                        value = xbmcgui.Dialog().input( label,cur_value, 0).decode("utf-8")
                    if value == "||PROMPTSTRINGASNUMERIC||":
                        validInput = False
                        while not validInput:
                            try:
                                value = xbmcgui.Dialog().input( label,cur_value, 0).decode("utf-8")
                                valueint = int(value)
                                validInput = True
                            except Exception:
                                value = xbmcgui.Dialog().notification( "Invalid input", "Please enter a number...")

                    #write skin strings
                    if not skip_skin_string and value != "||SKIPSTRING||":
                        xbmc.executebuiltin("Skin.SetString(%s,%s)" %(setting.encode("utf-8"),value.encode("utf-8")))
                        xbmc.executebuiltin("Skin.SetString(%s.label,%s)" %(setting.encode("utf-8"),label.encode("utf-8")))
                    #process additional actions
                    additionalactions = allValues[selected_item].getProperty("additionalactions").split(" || ")
                    for action in additionalactions:
                        xbmc.executebuiltin(action)
                    return (value,label)
            else: return (None,None)

    def correct_skin_settings(self):
        #correct any special skin settings
        skinconstants = {}
        settings_file = xbmc.translatePath( 'special://skin/extras/skinsettings.xml' ).decode("utf-8")
        if xbmcvfs.exists( settings_file ):
            doc = parse( settings_file )
            listing = doc.documentElement.getElementsByTagName( 'setting' )
            for count, item in enumerate(listing):
                id = item.attributes[ 'id' ].nodeValue
                value = item.attributes[ 'value' ].nodeValue
                curvalue = xbmc.getInfoLabel("Skin.String(%s)" %id.encode("utf-8")).decode("utf-8")
                label = xbmc.getInfoLabel(item.attributes[ 'label' ].nodeValue).decode("utf-8")
                if "%" in label: label = label %value
                additionalactions = item.getElementsByTagName( 'onselect' )
                try: default = item.attributes[ 'default' ].nodeValue
                except Exception: default = ""
                try: constantdefault = item.attributes[ 'constantdefault' ].nodeValue
                except Exception: constantdefault = ""

                #skip submenu level itself, this happens when a setting id also exists as a submenu value for an item
                skip = False
                for count3, item3 in enumerate(listing):
                    if item3.attributes[ 'value' ].nodeValue == "||SUBLEVEL||" + id:
                        skip = True
                if skip: continue

                #enumerate sublevel if needed
                if value.startswith("||SUBLEVEL||"):
                    sublevel = value.replace("||SUBLEVEL||","")
                    for item2 in listing:
                        if item2.attributes[ 'id' ].nodeValue == sublevel:
                            try: subdefault = item2.attributes[ 'default' ].nodeValue
                            except Exception: subdefault = ""
                            try: subconstantdefault = item2.attributes[ 'constantdefault' ].nodeValue
                            except Exception: subconstantdefault = ""
                            #match in sublevel or default found in sublevel values
                            if (item2.attributes[ 'value' ].nodeValue.lower() == curvalue.lower()) or (not curvalue and xbmc.getCondVisibility( subdefault )):
                                label = xbmc.getInfoLabel(item2.attributes[ 'label' ].nodeValue).decode("utf-8")
                                value = item2.attributes[ 'value' ].nodeValue
                                if "%" in label: label = label %value
                                default = subdefault
                                additionalactions = item2.getElementsByTagName( 'onselect' )
                            if (item2.attributes[ 'value' ].nodeValue.lower() == curvalue.lower()) or xbmc.getCondVisibility( subconstantdefault ):
                                label = xbmc.getInfoLabel(item2.attributes[ 'label' ].nodeValue).decode("utf-8")
                                value = item2.attributes[ 'value' ].nodeValue
                                if "%" in label: label = label %value
                                constantdefault = subconstantdefault
                                additionalactions = item2.getElementsByTagName( 'onselect' )
                #process any multiselects
                if value.startswith("||MULTISELECT||"):
                    options = item.getElementsByTagName( 'option' )
                    for option in options:
                        skinsetting = option.attributes[ 'id' ].nodeValue
                        if not xbmc.getInfoLabel("Skin.String(defaultset_%s)" %skinsetting) and xbmc.getCondVisibility( option.attributes[ 'default' ].nodeValue ):
                            xbmc.executebuiltin("Skin.SetBool(%s)" %skinsetting)
                        #always set additional prop to define the defaults
                        xbmc.executebuiltin("Skin.SetString(defaultset_%s,defaultset)" %skinsetting)

                #only correct the label
                if value and value.lower() == curvalue.lower():
                    xbmc.executebuiltin("Skin.SetString(%s.label,%s)" %(id.encode("utf-8"),label.encode("utf-8")))
                #set the default value if current value is empty
                if not curvalue and xbmc.getCondVisibility( default ):
                    xbmc.executebuiltin("Skin.SetString(%s.label,%s)" %(id.encode("utf-8"),label.encode("utf-8")))
                    xbmc.executebuiltin("Skin.SetString(%s,%s)" %(id.encode("utf-8"),value.encode("utf-8")))
                    #additional onselect actions
                    for action in additionalactions:
                        condition = action.attributes[ 'condition' ].nodeValue
                        if condition and not xbmc.getCondVisibility(condition): continue
                        command = action.firstChild.nodeValue
                        if "$" in command: command = xbmc.getInfoLabel(command)
                        xbmc.executebuiltin(command)
                #set the default constant value if current value is empty
                if xbmc.getCondVisibility( constantdefault ) and not curvalue:
                    skinconstants[id] = value
                    #additional onselect actions
                    for action in additionalactions:
                        condition = action.attributes[ 'condition' ].nodeValue
                        if condition and not xbmc.getCondVisibility(condition): continue
                        command = action.firstChild.nodeValue
                        if "$" in command: command = xbmc.getInfoLabel(command)
                        xbmc.executebuiltin(command)
        if skinconstants:
            self.update_skin_constants(skinconstants)
        
    def save_skin_image(self, skinstring="", allow_multi=False, header="", force_multi=False):
        '''let the user select an image and save it to addon_data for easy backup'''
        if not header: 
            header = xbmc.getLocalizedString(1030)    
        cur_value = xbmc.getInfoLabel("Skin.String(%s)" %skinstring).decode("utf-8")
        cur_value_org = xbmc.getInfoLabel("Skin.String(%s.org)" %skinstring).decode("utf-8")

        if not force_multi and (not allow_multi or xbmcgui.Dialog().yesno( header, 
            self.addon.getLocalizedString(32064), 
            yeslabel=self.addon.getLocalizedString(32065), 
            nolabel=self.addon.getLocalizedString(32066) )):
            #single image (allow copy to addon_data)
            value = xbmcgui.Dialog().browse( 2 , header, 'files', '', True, True, cur_value_org).decode("utf-8")
            if value:
                ext = value.split(".")[-1]
                newfile = (u"special://profile/addon_data/%s/custom_images/%s.%s"
                    %(xbmc.getSkinDir(),skinstring + time.strftime("%Y%m%d%H%M%S", time.gmtime()),ext))
                if "special://profile/addon_data/%s/custom_images/"%xbmc.getSkinDir() in cur_value:
                    xbmcvfs.delete(cur_value)
                xbmcvfs.copy(value, newfile)
                xbmc.executebuiltin("Skin.SetString(%s.org,%s)" %(skinstring.encode("utf-8"),value.encode("utf-8")))
                value = newfile
        else:
            #multi image
            if not cur_value_org.startswith("$"):
                delim = "\\" if "\\" in cur_value_org else "/"
                curdir = cur_value_org.rsplit(delim, 1)[0] + delim
            else: 
                curdir = ""
            value = xbmcgui.Dialog().browse( 0 , self.addon.getLocalizedString(32067), 
                'files', '', True, True, curdir).decode("utf-8")
        xbmc.executebuiltin("Skin.SetString(%s,%s)" %(skinstring.encode("utf-8"),value.encode("utf-8")))
        return value

    def set_skinshortcuts_property(self, setting="",window_header="",property_name=""):
        '''allows the user to make a setting for skinshortcuts using the special skinsettings dialogs'''
        cur_value = xbmc.getInfoLabel("$INFO[Container(211).ListItem.Property(%s)]" %property_name).decode("utf-8")
        if not cur_value: 
            cur_value = "None"
        if setting:
            (value, label) = self.set_skin_setting(setting, window_header, None, cur_value, True)
        else:
            value = xbmcgui.Dialog().input(window_header, cur_value, type=xbmcgui.INPUT_ALPHANUM).decode("utf-8")
        if value:
            self.wait_for_skinshortcuts_window()
            xbmc.executebuiltin("SetProperty(customProperty,%s)" %property_name.encode("utf-8"))
            xbmc.executebuiltin("SetProperty(customValue,%s)" %value.encode("utf-8"))
            xbmc.executebuiltin("SendClick(404)")
            if setting:
                xbmc.sleep(250)
                xbmc.executebuiltin("SetProperty(customProperty,%s.name)" %property_name.encode("utf-8"))
                xbmc.executebuiltin("SetProperty(customValue,%s)" %label.encode("utf-8"))
                xbmc.executebuiltin("SendClick(404)")
                
    @staticmethod
    def wait_for_skinshortcuts_window():
        '''wait untill skinshortcuts is active window (because of any animations that may have been applied)'''
        for i in range(40):
            if not (xbmc.getCondVisibility("Window.IsActive(DialogSelect.xml) | Window.IsActive(script-skin_helper_service-ColorPicker.xml) | Window.IsActive(DialogKeyboard.xml)")):
                break
            else: xbmc.sleep(100)
            
    @staticmethod
    def indent_xml( elem, level=0 ):
        '''helper to properly indent xml strings to file'''
        i = "\n" + level*"\t"
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "\t"
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                indent_xml(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

