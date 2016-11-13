#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmc
import xbmcvfs
import xbmcgui
import xbmcaddon
from utils import log_msg, try_encode, KODI_VERSION, ADDON_ID, try_decode
from dialogs import DialogSelect
from xml.dom.minidom import parse
import xml.etree.ElementTree as xmltree
import sys
import os


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
        '''writes the list of all skin constants'''
        addonpath = xbmc.translatePath(os.path.join("special://skin/", 'addon.xml').encode("utf-8")).decode("utf-8")
        addon = xmltree.parse(addonpath)
        extensionpoints = addon.findall("extension")
        paths = []
        for extensionpoint in extensionpoints:
            if extensionpoint.attrib.get("point") == "xbmc.gui.skin":
                resolutions = extensionpoint.findall("res")
                for resolution in resolutions:
                    includes_file = xbmc.translatePath(
                        os.path.join(
                            "special://skin/",
                            try_decode(
                                resolution.attrib.get("folder")),
                            "script-skin_helper_service-includes.xml").encode("utf-8")).decode('utf-8')
                    tree = xmltree.ElementTree(xmltree.Element("includes"))
                    root = tree.getroot()
                    for key, value in listing.iteritems():
                        if value:
                            child = xmltree.SubElement(root, "constant")
                            child.text = value
                            child.attrib["name"] = key
                            # also write to skin strings
                            xbmc.executebuiltin("Skin.SetString(%s,%s)" % (key.encode("utf-8"), value.encode("utf-8")))
                    self.indent_xml(tree.getroot())
                    xmlstring = xmltree.tostring(tree.getroot(), encoding="utf-8")
                    f = xbmcvfs.File(includes_file, 'w')
                    f.write(xmlstring)
                    f.close()
        xbmc.executebuiltin("ReloadSkin()")

    def get_skin_constants(self):
        '''gets a list of all skin constants'''
        all_constants = {}
        addonpath = xbmc.translatePath(os.path.join("special://skin/", 'addon.xml').encode("utf-8")).decode("utf-8")
        addon = xmltree.parse(addonpath)
        extensionpoints = addon.findall("extension")
        paths = []
        for extensionpoint in extensionpoints:
            if extensionpoint.attrib.get("point") == "xbmc.gui.skin":
                resolutions = extensionpoint.findall("res")
                for resolution in resolutions:
                    includes_file = xbmc.translatePath(
                        os.path.join(
                            "special://skin/",
                            try_decode(
                                resolution.attrib.get("folder")),
                            "script-skin_helper_service-includes.xml").encode("utf-8")).decode('utf-8')
                    if xbmcvfs.exists(includes_file):
                        doc = parse(includes_file)
                        listing = doc.documentElement.getElementsByTagName('constant')
                        for item in listing:
                            name = try_decode(item.attributes['name'].nodeValue)
                            value = try_decode(item.firstChild.nodeValue)
                            all_constants[name] = value
        return all_constants

    def update_skin_constants(self, new_values):
        '''update skin constants if needed'''
        update_needed = False
        all_values = self.get_skin_constants()
        for key, value in new_values.iteritems():
            if key in all_values:
                if all_values.get(key) != value:
                    update_needed = True
                    all_values[key] = value
            else:
                update_needed = True
                all_values[key] = value
        if update_needed:
            self.write_skin_constants(all_values)

    def set_skin_constant(self, setting="", window_header="", value=""):
        '''set a skin constant'''
        cur_values = self.get_skin_constants()
        if not value:
            value, label = self.set_skin_setting(
                setting, window_header, "", cur_values.get(
                    setting, "emptyconstant"))
        result = {setting: value}
        self.update_skin_constants(result)

    def set_skin_constants(self, settings, values):
        '''set multiple constants at once'''
        result = {}
        for count, setting in enumerate(settings):
            result[setting] = values[count]
        self.update_skin_constants(result)

    def set_skin_setting(self, setting="", window_header="", sublevel="",
                         cur_value="", skip_skin_string=False, original_id=""):
        '''allows the skinner to use a select dialog to set skin settings'''
        if not cur_value:
            cur_value = xbmc.getInfoLabel("Skin.String(%s)" % setting).decode("utf-8")
        cur_value_label = xbmc.getInfoLabel("Skin.String(%s.label)" % setting).decode("utf-8")
        rich_layout = False
        select_id = 0
        itemcount = 0

        all_values = []
        settings_file = xbmc.translatePath('special://skin/extras/skinsettings.xml').decode("utf-8")
        if xbmcvfs.exists(settings_file):
            doc = parse(settings_file)
            listing = doc.documentElement.getElementsByTagName('setting')
            if sublevel:
                listitem = xbmcgui.ListItem(label="..", iconImage="DefaultFolderBack.png")
                listitem.setProperty("icon", "DefaultFolderBack.png")
                listitem.setProperty("value", "||BACK||")
                all_values.append(listitem)
            for item in listing:
                setting_id = item.attributes['id'].nodeValue
                if setting_id.startswith("$"):
                    setting_id = xbmc.getInfoLabel(setting_id).decode("utf-8")
                label = xbmc.getInfoLabel(item.attributes['label'].nodeValue).decode("utf-8")
                if ((not sublevel and setting_id.lower() == setting.lower()) or
                        (sublevel and sublevel.lower() == setting_id.lower()) or
                        (original_id and original_id.lower() == setting_id.lower())):
                    value = item.attributes['value'].nodeValue
                    if value == "||MULTISELECT||":
                        return self.multi_select(item, window_header)
                    condition = item.attributes['condition'].nodeValue
                    icon = item.attributes['icon'].nodeValue
                    description = item.attributes['description'].nodeValue
                    description = xbmc.getInfoLabel(description.encode("utf-8"))
                    if condition and not xbmc.getCondVisibility(condition):
                        continue
                    if icon:
                        rich_layout = True
                    if icon and icon.startswith("$"):
                        icon = xbmc.getInfoLabel(icon)
                    if "%" in label:
                        label = label % value
                    if cur_value and (cur_value.lower() == value.lower() or label.lower() == cur_value_label.lower()):
                        select_id = itemcount
                    listitem = xbmcgui.ListItem(label=label, iconImage=icon)
                    listitem.setProperty("value", value)
                    listitem.setProperty("icon", icon)
                    listitem.setProperty("description", description)
                    listitem.setLabel2(description)
                    # additional onselect actions
                    additionalactions = []
                    for action in item.getElementsByTagName('onselect'):
                        condition = action.attributes['condition'].nodeValue
                        if condition and not xbmc.getCondVisibility(condition):
                            continue
                        command = action.firstChild.nodeValue
                        if "$" in command:
                            command = xbmc.getInfoLabel(command)
                        additionalactions.append(command)
                    listitem.setProperty("additionalactions", " || ".join(additionalactions))
                    all_values.append(listitem)
                    itemcount += 1
            if not all_values:
                selected_item = None
            elif len(all_values) > 1:
                # only use select dialog if we have muliple values
                dialog = DialogSelect(
                    "DialogSelect.xml",
                    "",
                    listing=all_values,
                    windowtitle=window_header,
                    richlayout=rich_layout)
                if select_id >= 0 and sublevel:
                    select_id += 1
                dialog.autofocus_id = select_id
                dialog.doModal()
                selected_item = dialog.result
                del dialog
            else:
                selected_item = None
            # process the results
            if selected_item:
                value = try_decode(selected_item.getProperty("value"))
                label = try_decode(selected_item.getLabel())
                description = selected_item.getProperty("description")
                if value.startswith("||SUBLEVEL||"):
                    sublevel = value.replace("||SUBLEVEL||", "")
                    self.set_skin_setting(setting, window_header, sublevel)
                elif value == "||BACK||":
                    self.set_skin_setting(setting, window_header)
                else:
                    if value == "||BROWSEIMAGE||":
                        value = self.save_skin_image(setting, True, label)
                    if value == "||BROWSESINGLEIMAGE||":
                        value = self.save_skin_image(setting, False, label)
                    if value == "||BROWSEMULTIIMAGE||":
                        value = self.save_skin_image(setting, True, label, True)
                    if value == "||PROMPTNUMERIC||":
                        value = xbmcgui.Dialog().input(label, cur_value, 1).decode("utf-8")
                    if value == "||PROMPTSTRING||":
                        value = xbmcgui.Dialog().input(label, cur_value, 0).decode("utf-8")
                    if value == "||PROMPTSTRINGASNUMERIC||":
                        validInput = False
                        while not validInput:
                            try:
                                value = xbmcgui.Dialog().input(label, cur_value, 0).decode("utf-8")
                                valueint = int(value)
                                validInput = True
                            except Exception:
                                value = xbmcgui.Dialog().notification("Invalid input", "Please enter a number...")

                    # write skin strings
                    if not skip_skin_string and value != "||SKIPSTRING||":
                        xbmc.executebuiltin("Skin.SetString(%s,%s)" % (setting.encode("utf-8"), value.encode("utf-8")))
                        xbmc.executebuiltin(
                            "Skin.SetString(%s.label,%s)" %
                            (setting.encode("utf-8"), label.encode("utf-8")))
                    # process additional actions
                    additionalactions = selected_item.getProperty("additionalactions").split(" || ")
                    for action in additionalactions:
                        xbmc.executebuiltin(action)
                    return (value, label)
            else:
                return (None, None)

    def correct_skin_settings(self):
        '''correct any special skin settings'''
        skinconstants = {}
        settings_file = xbmc.translatePath('special://skin/extras/skinsettings.xml').decode("utf-8")
        if xbmcvfs.exists(settings_file):
            doc = parse(settings_file)
            listing = doc.documentElement.getElementsByTagName('setting')
            for item in listing:
                id = item.attributes['id'].nodeValue
                value = item.attributes['value'].nodeValue
                curvalue = xbmc.getInfoLabel("Skin.String(%s)" % id.encode("utf-8")).decode("utf-8")
                label = xbmc.getInfoLabel(item.attributes['label'].nodeValue).decode("utf-8")
                if "%" in label:
                    label = label % value
                additionalactions = item.getElementsByTagName('onselect')
                try:
                    default = item.attributes['default'].nodeValue
                except Exception:
                    default = ""
                try:
                    constantdefault = item.attributes['constantdefault'].nodeValue
                except Exception:
                    constantdefault = ""

                # skip submenu level itself, this happens when a setting id also exists as a submenu value for an item
                skip = False
                for count3, item3 in enumerate(listing):
                    if item3.attributes['value'].nodeValue == "||SUBLEVEL||" + id:
                        skip = True
                if skip:
                    continue

                # enumerate sublevel if needed
                if value.startswith("||SUBLEVEL||"):
                    sublevel = value.replace("||SUBLEVEL||", "")
                    for item2 in listing:
                        if item2.attributes['id'].nodeValue == sublevel:
                            try:
                                subdefault = item2.attributes['default'].nodeValue
                            except Exception:
                                subdefault = ""
                            try:
                                subconstantdefault = item2.attributes['constantdefault'].nodeValue
                            except Exception:
                                subconstantdefault = ""
                            # match in sublevel or default found in sublevel values
                            if (item2.attributes['value'].nodeValue.lower() == curvalue.lower()) or (
                                    not curvalue and xbmc.getCondVisibility(subdefault)):
                                label = xbmc.getInfoLabel(item2.attributes['label'].nodeValue).decode("utf-8")
                                value = item2.attributes['value'].nodeValue
                                if "%" in label:
                                    label = label % value
                                default = subdefault
                                additionalactions = item2.getElementsByTagName('onselect')
                            if ((item2.attributes['value'].nodeValue.lower() == curvalue.lower()) or
                                    xbmc.getCondVisibility(subconstantdefault)):
                                label = xbmc.getInfoLabel(item2.attributes['label'].nodeValue).decode("utf-8")
                                value = item2.attributes['value'].nodeValue
                                if "%" in label:
                                    label = label % value
                                constantdefault = subconstantdefault
                                additionalactions = item2.getElementsByTagName('onselect')
                # process any multiselects
                if value.startswith("||MULTISELECT||"):
                    options = item.getElementsByTagName('option')
                    for option in options:
                        skinsetting = option.attributes['id'].nodeValue
                        if not xbmc.getInfoLabel(
                                "Skin.String(defaultset_%s)" % skinsetting) and xbmc.getCondVisibility(
                                option.attributes['default'].nodeValue):
                            xbmc.executebuiltin("Skin.SetBool(%s)" % skinsetting)
                        # always set additional prop to define the defaults
                        xbmc.executebuiltin("Skin.SetString(defaultset_%s,defaultset)" % skinsetting)

                # only correct the label
                if value and value.lower() == curvalue.lower():
                    xbmc.executebuiltin("Skin.SetString(%s.label,%s)" % (id.encode("utf-8"), label.encode("utf-8")))
                # set the default value if current value is empty
                if not curvalue and xbmc.getCondVisibility(default):
                    xbmc.executebuiltin("Skin.SetString(%s.label,%s)" % (id.encode("utf-8"), label.encode("utf-8")))
                    xbmc.executebuiltin("Skin.SetString(%s,%s)" % (id.encode("utf-8"), value.encode("utf-8")))
                    # additional onselect actions
                    for action in additionalactions:
                        condition = action.attributes['condition'].nodeValue
                        if condition and not xbmc.getCondVisibility(condition):
                            continue
                        command = action.firstChild.nodeValue
                        if "$" in command:
                            command = xbmc.getInfoLabel(command)
                        xbmc.executebuiltin(command)
                # set the default constant value if current value is empty
                if xbmc.getCondVisibility(constantdefault) and not curvalue:
                    skinconstants[id] = value
                    # additional onselect actions
                    for action in additionalactions:
                        condition = action.attributes['condition'].nodeValue
                        if condition and not xbmc.getCondVisibility(condition):
                            continue
                        command = action.firstChild.nodeValue
                        if "$" in command:
                            command = xbmc.getInfoLabel(command)
                        xbmc.executebuiltin(command)
        if skinconstants:
            self.update_skin_constants(skinconstants)

    def save_skin_image(self, skinstring="", allow_multi=False, header="", force_multi=False):
        '''let the user select an image and save it to addon_data for easy backup'''
        if not header:
            header = xbmc.getLocalizedString(1030)
        cur_value = xbmc.getInfoLabel("Skin.String(%s)" % skinstring).decode("utf-8")
        cur_value_org = xbmc.getInfoLabel("Skin.String(%s.org)" % skinstring).decode("utf-8")

        if not force_multi and(
            not allow_multi or xbmcgui.Dialog().yesno(
                header, self.addon.getLocalizedString(32016),
                yeslabel=self.addon.getLocalizedString(32017),
                nolabel=self.addon.getLocalizedString(32018))):
            # single image (allow copy to addon_data)
            value = xbmcgui.Dialog().browse(2, header, 'files', '', True, True, cur_value_org).decode("utf-8")
            if value:
                ext = value.split(".")[-1]
                newfile = (u"special://profile/addon_data/%s/custom_images/%s.%s"
                           % (xbmc.getSkinDir(), skinstring + time.strftime("%Y%m%d%H%M%S", time.gmtime()), ext))
                if "special://profile/addon_data/%s/custom_images/" % xbmc.getSkinDir() in cur_value:
                    xbmcvfs.delete(cur_value)
                xbmcvfs.copy(value, newfile)
                xbmc.executebuiltin("Skin.SetString(%s.org,%s)" % (skinstring.encode("utf-8"), value.encode("utf-8")))
                value = newfile
        else:
            # multi image
            if not cur_value_org.startswith("$"):
                delim = "\\" if "\\" in cur_value_org else "/"
                curdir = cur_value_org.rsplit(delim, 1)[0] + delim
            else:
                curdir = ""
            value = xbmcgui.Dialog().browse(0, self.addon.getLocalizedString(32005),
                                            'files', '', True, True, curdir).decode("utf-8")
        xbmc.executebuiltin("Skin.SetString(%s,%s)" % (skinstring.encode("utf-8"), value.encode("utf-8")))
        return value

    def set_skinshortcuts_property(self, setting="", window_header="", property_name=""):
        '''allows the user to make a setting for skinshortcuts using the special skinsettings dialogs'''
        cur_value = xbmc.getInfoLabel("$INFO[Container(211).ListItem.Property(%s)]" % property_name).decode("utf-8")
        if not cur_value:
            cur_value = "None"
        if setting:
            (value, label) = self.set_skin_setting(setting, window_header, None, cur_value, True)
        else:
            value = xbmcgui.Dialog().input(window_header, cur_value, type=xbmcgui.INPUT_ALPHANUM).decode("utf-8")
        if value:
            self.wait_for_skinshortcuts_window()
            xbmc.executebuiltin("SetProperty(customProperty,%s)" % property_name.encode("utf-8"))
            xbmc.executebuiltin("SetProperty(customValue,%s)" % value.encode("utf-8"))
            xbmc.executebuiltin("SendClick(404)")
            if setting:
                xbmc.sleep(250)
                xbmc.executebuiltin("SetProperty(customProperty,%s.name)" % property_name.encode("utf-8"))
                xbmc.executebuiltin("SetProperty(customValue,%s)" % label.encode("utf-8"))
                xbmc.executebuiltin("SendClick(404)")

    @staticmethod
    def multi_select(item, window_header=""):
        '''allows the user to choose from multiple options'''
        all_options = []
        options = item.getElementsByTagName('option')
        for option in options:
            id = option.attributes['id'].nodeValue
            label = xbmc.getInfoLabel(option.attributes['label'].nodeValue).decode("utf-8")
            default = option.attributes['default'].nodeValue
            condition = option.attributes['condition'].nodeValue
            if condition and not xbmc.getCondVisibility(condition):
                continue
            listitem = xbmcgui.ListItem(label=label)
            listitem.setProperty("id", id)
            if xbmc.getCondVisibility("Skin.HasSetting(%s)" % id) or(not xbmc.getInfoLabel(
                    "Skin.String(defaultset_%s)" % id) and xbmc.getCondVisibility(default)):
                listitem.select(selected=True)
            all_options.append(listitem)
        # show select dialog
        dialog = DialogSelect("DialogSelect.xml", "", listing=all_options, windowtitle=window_header, multiselect=True)
        dialog.doModal()

        result = dialog.result
        if result:
            for item in result:
                if item.isSelected():
                    #option is enabled
                    xbmc.executebuiltin("Skin.SetBool(%s)" % skinsetting)
                else:
                    #option is disabled
                    xbmc.executebuiltin("Skin.Reset(%s)" % skinsetting)
            # always set additional prop to define the defaults
            xbmc.executebuiltin("Skin.SetString(defaultset_%s,defaultset)" % skinsetting)
        del dialog

    @staticmethod
    def wait_for_skinshortcuts_window():
        '''wait untill skinshortcuts is active window (because of any animations that may have been applied)'''
        for i in range(40):
            if not (xbmc.getCondVisibility(
                    "Window.IsActive(DialogSelect.xml) | "
                    "Window.IsActive(script-skin_helper_service-ColorPicker.xml) | "
                    "Window.IsActive(DialogKeyboard.xml)")):
                break
            else:
                xbmc.sleep(100)

    @staticmethod
    def indent_xml(elem, level=0):
        '''helper to properly indent xml strings to file'''
        text_i = "\n" + level * "\t"
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = text_i + "\t"
            if not elem.tail or not elem.tail.strip():
                elem.tail = text_i
            for elem in elem:
                indent_xml(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = text_i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = text_i
