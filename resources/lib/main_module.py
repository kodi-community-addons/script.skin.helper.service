#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmc
import xbmcvfs
import xbmcgui
import xbmcaddon
from simplecache import SimpleCache, use_cache
from utils import log_msg, KODI_VERSION, json, kodi_json
from utils import log_exception, get_current_content_type, ADDON_ID, recursive_delete_dir
from dialogs import DialogSelect
from xml.dom.minidom import parse
from artutils import KodiDb, Tmdb, process_method_on_list, extend_dict
from datetime import timedelta
import urlparse
import urllib
import urllib2
import re
import sys
import os


class MainModule:
    '''mainmodule provides the script methods for the skinhelper addon'''
    params = {}

    def __init__(self):
        '''Initialization and main code run'''
        self.win = xbmcgui.Window(10000)
        self.addon = xbmcaddon.Addon(ADDON_ID)
        self.kodidb = KodiDb()
        self.cache = SimpleCache()

        self.params = self.get_params()
        log_msg("MainModule called with parameters: %s" % self.params)
        action = self.params.get("action", "")
        xbmc.executebuiltin("dialog.Close(busydialog)")
        # launch module for action provided by this script
        try:
            getattr(self, action)()
        except AttributeError:
            log_exception(__name__, "No such action: %s" % action)
        except Exception as exc:
            log_exception(__name__, exc)
        finally:
            xbmc.executebuiltin("dialog.Close(busydialog)")

        # do cleanup
        self.close()

    def close(self):
        '''Cleanup Kodi Cpython instances on exit'''
        self.cache.close()
        del self.win
        del self.addon
        del self.kodidb
        log_msg("MainModule exited")

    @classmethod
    def get_params(self):
        # extract the params from the called script path
        params = {}
        for arg in sys.argv[1:]:
            paramname = arg.split('=')[0]
            paramvalue = arg.replace(paramname + "=", "")
            paramname = paramname.lower()
            if paramname == "action":
                paramvalue = paramvalue.lower()
            params[paramname] = paramvalue
        return params

    def deprecated_method(self, newaddon):
        '''
            used when one of the deprecated methods is called
            print warning in log and call the external script with the same parameters
        '''
        action = self.params.get("action")
        log_msg("Deprecated method: %s. Please call %s directly" % (action, newaddon), xbmc.LOGWARNING)
        paramstring = ""
        for key, value in self.params.iteritems():
            paramstring += ",%s=%s" % (key, value)
        if xbmc.getCondVisibility("System.HasAddon(%s)" % newaddon):
            xbmc.executebuiltin("RunAddon(%s%s)" % (newaddon, paramstring))
        else:
            # trigger install of the addon
            if KODI_VERSION >= 17:
                xbmc.executebuiltin("InstallAddon(%s)" % newaddon)
            else:
                xbmc.executebuiltin("RunPlugin(plugin://%s)" % newaddon)

    @staticmethod
    def addshortcut():
        '''workaround for skinshortcuts to add new shortcut by adding empty first'''
        xbmc.executebuiltin('SendClick(301)')
        count = 0
        # wait untill the empy item is focused
        while (count != 60 and xbmc.getCondVisibility("Windodialog.IsActive(script-skinshortcuts.xml)")):
            if not xbmc.getCondVisibility("StringCompare(Container(211).ListItem.Property(path), noop)"):
                xbmc.sleep(100)
                count += 1
            else:
                break
        if xbmc.getCondVisibility(
                "StringCompare(Container(211).ListItem.Property(path), noop) + "
                "Windodialog.IsActive(script-skinshortcuts.xml)"):
            xbmc.executebuiltin('SendClick(401)')

    @staticmethod
    def musicsearch():
        '''helper to go directly to music search dialog'''
        xbmc.executebuiltin("ActivateWindow(Music)")
        xbmc.executebuiltin("SendClick(8)")

    def setview(self):
        '''sets the selected viewmode for the container'''
        content_type = get_current_content_type()
        if not content_type:
            content_type = "files"
        current_view = xbmc.getInfoLabel("Container.Viewmode").decode("utf-8")
        view_id, view_label = self.selectview(content_type, current_view)
        current_forced_view = xbmc.getInfoLabel("Skin.String(SkinHelper.ForcedViews.%s)" % content_type)

        if view_id is not None:
            # also store forced view
            if (content_type and current_forced_view and current_forced_view != "None" and
                    xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.ForcedViews.Enabled)")):
                xbmc.executebuiltin("Skin.SetString(SkinHelper.ForcedViews.%s,%s)" % (content_type, view_id))
                xbmc.executebuiltin("Skin.SetString(SkinHelper.ForcedViews.%s.label,%s)" % (content_type, view_label))
                self.win.setProperty("SkinHelper.ForcedView", view_id)
                if not xbmc.getCondVisibility("Control.HasFocus(%s)" % current_forced_view):
                    xbmc.sleep(100)
                    xbmc.executebuiltin("Container.SetViewMode(%s)" % view_id)
                    xbmc.executebuiltin("SetFocus(%s)" % view_id)
            else:
                self.win.clearProperty("SkinHelper.ForcedView")
            # set view
            xbmc.executebuiltin("Container.SetViewMode(%s)" % view_id)

    def selectview(self, content_type="other", current_view=None, display_none=False):
        '''reads skinfile with all views to present a dialog to choose from'''
        cur_view_select_id = None
        id = None
        label = ""
        all_views = []
        if display_none:
            listitem = xbmcgui.ListItem(label="None")
            listitem.setProperty("id", "None")
            all_views.append(listitem)
        # read the special skin views file
        views_file = xbmc.translatePath('special://skin/extras/views.xml').decode("utf-8")
        if xbmcvfs.exists(views_file):
            doc = parse(views_file)
            listing = doc.documentElement.getElementsByTagName('view')
            itemcount = 0
            for view in listing:
                label = xbmc.getLocalizedString(int(view.attributes['languageid'].nodeValue))
                id = view.attributes['value'].nodeValue
                type = view.attributes['type'].nodeValue.lower().split(",")
                if label.lower() == current_view.lower() or id == current_view:
                    cur_view_select_id = itemcount
                    if display_none:
                        cur_view_select_id += 1
                if (("all" in type or content_type.lower() in type) and (not "!" + content_type.lower() in type) and not
                        xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.view.Disabled.%s)" % id)):
                    image = "special://skin/extras/viewthumbs/%s.jpg" % id
                    listitem = xbmcgui.ListItem(label=label, iconImage=image)
                    listitem.setProperty("id", id)
                    listitem.setProperty("icon", image)
                    all_views.append(listitem)
                    itemcount += 1
        dialog = DialogSelect(
            "DialogSelect.xml",
            "",
            listing=all_views,
            windowtitle=self.addon.getLocalizedString(32012),
            richlayout=True)
        dialog.autofocus_id = cur_view_select_id
        dialog.doModal()
        result = dialog.result
        del dialog
        if result:
            id = result.getProperty("id")
            label = result.getLabel()
            return (id, label)
        else:
            return (None, None)

    def enableviews(self):
        '''show select dialog to enable/disable views'''
        all_views = []
        views_file = xbmc.translatePath('special://skin/extras/views.xml').decode("utf-8")
        if xbmcvfs.exists(views_file):
            doc = parse(views_file)
            listing = doc.documentElement.getElementsByTagName('view')
            for view in listing:
                view_id = view.attributes['value'].nodeValue
                label = xbmc.getLocalizedString(int(view.attributes['languageid'].nodeValue))
                desc = label + " (" + str(view_id) + ")"
                listitem = xbmcgui.ListItem(label=label, label2=desc)
                listitem.setProperty("id", view_id)
                if not xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.view.Disabled.%s)" % view_id):
                    listitem.select(selected=True)
                all_views.append(listitem)

        dialog = DialogSelect(
            "DialogSelect.xml",
            "",
            listing=all_views,
            windowtitle=self.addon.getLocalizedString(32013),
            multiselect=True)
        dialog.doModal()
        result = dialog.result
        del dialog
        if result:
            for item in result:
                view_id = item.getProperty("id")
                if item.isSelected():
                    # view is enabled
                    xbmc.executebuiltin("Skin.Reset(SkinHelper.view.Disabled.%s)" % view_id)
                else:
                    # view is disabled
                    xbmc.executebuiltin("Skin.SetBool(SkinHelper.view.Disabled.%s)" % view_id)

    def setforcedview(self):
        '''helper that sets a forced view for a specific content type'''
        content_type = self.params.get("contenttype")
        if content_type:
            current_view = xbmc.getInfoLabel("Skin.String(SkinHelper.ForcedViews.%s)" % content_type)
            if not current_view:
                current_view = "0"
            view_id, view_label = self.selectview(content_type, current_view, True)
            if view_id:
                xbmc.executebuiltin("Skin.SetString(SkinHelper.ForcedViews.%s,%s)" % (content_type, view_id))
                xbmc.executebuiltin("Skin.SetString(SkinHelper.ForcedViews.%s.label,%s)" % (content_type, view_label))

    @staticmethod
    def get_youtube_listing(searchquery):
        '''get items from youtube plugin by query'''
        lib_path = u"plugin://plugin.video.youtube/kodion/search/query/?q=%s" % searchquery
        return KodiDb().files(lib_path)

    def searchyoutube(self):
        '''helper to search youtube for the given title'''
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        title = self.params.get("title", "")
        window_header = self.params.get("header", "")
        results = []
        for media in self.get_youtube_listing(title):
            if not media["filetype"] == "directory":
                label = media["label"]
                label2 = media["plot"]
                image = ""
                if media.get('art'):
                    if media['art'].get('thumb'):
                        image = (media['art']['thumb'])
                listitem = xbmcgui.ListItem(label=label, label2=label2, iconImage=image)
                listitem.setProperty("path", media["file"])
                results.append(listitem)

        # finished lookup - display listing with results
        xbmc.executebuiltin("dialog.Close(busydialog)")
        dialog = DialogSelect("DialogSelect.xml", "", listing=results, windowtitle=window_header, multiselect=False)
        dialog.doModal()
        result = dialog.result
        del dialog
        if result:
            if xbmc.getCondVisibility(
                    "Windodialog.IsActive(script-skin_helper_service-CustomInfo.xml) | Windodialog.IsActive(movieinformation)"):
                xbmc.executebuiltin("dialog.Close(movieinformation)")
                xbmc.executebuiltin("dialog.Close(script-skin_helper_service-CustomInfo.xml)")
                xbmc.sleep(1000)
            xbmc.executebuiltin('PlayMedia("%s")' % result.getProperty("path"))
            del result

    def getcastmedia(self):
        '''helper to show a dialog with all media for a specific actor'''
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        name = self.params.get("name", "")
        window_header = self.params.get("name", "")
        results = []
        items = self.kodidb.castmedia(name)
        items = process_method_on_list(self.kodidb.prepare_listitem, items)
        for item in items:
            if item["file"].startswith("videodb://"):
                item["file"] = "ActivateWindow(Videos,%s,return)" % item["file"]
            else:
                item["file"] = 'PlayMedia("%s")' % item["file"]
            results.append(self.kodidb.create_listitem(item, False))
        # finished lookup - display listing with results
        xbmc.executebuiltin("dialog.Close(busydialog)")
        dialog = DialogSelect("DialogSelect.xml", "", listing=results, windowtitle=window_header, richlayout=True)
        dialog.doModal()
        result = dialog.result
        del dialog
        if result:
            while xbmc.getCondVisibility("System.HasModalDialog"):
                xbmc.executebuiltin("Action(Back)")
                xbmc.sleep(300)
            xbmc.executebuiltin(result.getfilename())
            del result

    def setfocus(self):
        '''helper to set focus on a list or control'''
        control = self.params.get("control")
        fallback = self.params.get("fallback")
        count = 0
        if control:
            xbmc.sleep(200)
            while not xbmc.getCondVisibility("Control.HasFocus(%s)" % control):
                if count == 20 or(
                    fallback and xbmc.getCondVisibility(
                        "Control.IsVisible(%s)"
                        "+ !IntegerGreaterThan(Container(%s).NumItems,0)" % (control, control))):
                    if fallback:
                        xbmc.executebuiltin("Control.SetFocus(%s)" % fallback)
                    break
                else:
                    xbmc.executebuiltin("Control.SetFocus(%s)" % control)
                    xbmc.sleep(50)
                    count += 1

    def setwidgetcontainer(self):
        '''helper that reports the current selected widget container/control'''
        controls = self.params.get("controls", "").split("-")
        if controls:
            xbmc.sleep(50)
            for i in range(10):
                for control in controls:
                    if xbmc.getCondVisibility("Control.IsVisible(%s) + IntegerGreaterThan(Container(%s).NumItems,0)"
                                              % (control, control)):
                        self.win.setProperty("SkinHelper.WidgetContainer", control)
                        return
                xbmc.sleep(50)
        self.win.clearProperty("SkinHelper.WidgetContainer")

    def saveskinimage(self):
        '''let the user select an image and save it to addon_data for easy backup'''
        skinstring = self.params.get("skinstring", "")
        allow_multi = self.params.get("multi", "") == "true"
        header = self.params.get("header", "")
        from skinsettings import SkinSettings
        SkinSettings().save_skin_image(skinstring, allow_multi, header)

    def setskinsetting(self):
        '''allows the user to set a skin setting with a select dialog'''
        setting = self.params.get("setting", "")
        org_id = self.params.get("id", "")
        header = self.params.get("header", "")
        from skinsettings import SkinSettings
        SkinSettings().set_skin_setting(setting=setting, window_header=header, original_id=org_id)

    def setskinconstant(self):
        '''allows the user to set a skin constant with a select dialog'''
        setting = self.params.get("setting", "").split("|")
        value = self.params.get("value", "").split("|")
        header = self.params.get("header", "")
        from skinsettings import SkinSettings
        SkinSettings().set_skin_constant(setting, header, value)

    def setskinconstants(self):
        '''allows the skinner to set multiple skin constants'''
        settings = self.params.get("settings", "")
        values = self.params.get("values", "")
        from skinsettings import SkinSettings
        SkinSettings().set_skin_constants(settings, values)

    def setskinshortcutsproperty(self):
        '''allows the user to make a setting for skinshortcuts using the special skinsettings dialogs'''
        setting = self.params.get("setting", "")
        value = self.params.get("value", "")
        header = self.params.get("header", "")
        from skinsettings import SkinSettings
        SkinSettings().set_skinshortcuts_property(setting, header, value)

    def togglekodisetting(self, settingname):
        '''toggle kodi setting'''
        settingname = self.params.get("setting", "")
        cur_value = xbmc.getCondVisibility("system.getbool(%s)" % settingname)
        if cur_value:
            new_value = "false"
        else:
            new_value = "true"
        xbmc.executeJSONRPC(
            '{"jsonrpc":"2.0", "id":1, "method":"Settings.SetSettingValue","params":{"setting":"%s","value":%s}}' %
            (settingname, new_value))

    def setkodisetting(self, settingname):
        '''set kodi setting'''
        settingname = self.params.get("setting", "")
        value = self.params.get("value", "")
        is_int = False
        try:
            valueint = int(value)
            is_int = True
        except Exception:
            pass
        if value.lower() == "true":
            value = 'true'
        elif value.lower() == "false":
            value = 'false'
        elif is_int:
            value = '"%s"' % value
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.SetSettingValue",\
            "params":{"setting":"%s","value":%s}}' % (settingname, value))

    def playtrailer(self):
        '''auto play windowed trailer inside video listing'''
        if not xbmc.getCondVisibility("Player.HasMedia | Container.Scrolling | Container.OnNext | "
                                      "Container.OnPrevious | !IsEmpty(Window(Home).Property(traileractionbusy))"):
            self.win.setProperty("traileractionbusy", "traileractionbusy")
            widget_container = self.params.get("widgetcontainer", "")
            trailer_mode = self.params.get("mode", "").replace("auto_", "")
            allow_youtube = self.params.get("youtube", "") == "true"
            if not trailer_mode:
                trailer_mode = "windowed"
            if widget_container:
                widget_container_prefix = "Container(%s)." % widget_container
            else:
                widget_container_prefix = ""

            li_title = xbmc.getInfoLabel("%sListItem.Title" % widget_container_prefix).decode('utf-8')
            li_trailer = xbmc.getInfoLabel("%sListItem.Trailer" % widget_container_prefix).decode('utf-8')
            if not li_trailer and allow_youtube:
                youtube_result = self.get_youtube_listing("%s Trailer" % li_title)
                if youtube_result:
                    li_trailer = youtube_result[0].get("file")
            # always wait a bit to prevent trailer start playing when we're scrolling the list
            xbmc.Monitor().waitForAbort(3)
            if li_trailer and (li_title == xbmc.getInfoLabel("%sListItem.Title"
                                                             % widget_container_prefix).decode('utf-8')):
                if trailer_mode == "fullscreen" and li_trailer:
                    xbmc.executebuiltin('PlayMedia("%s")' % li_trailer)
                else:
                    xbmc.executebuiltin('PlayMedia("%s",1)' % li_trailer)
                self.win.setProperty("TrailerPlaying", trailer_mode)
            self.win.clearProperty("traileractionbusy")

    def colorpicker(self):
        '''legacy'''
        self.deprecated_method("script.skin.helper.colorpicker")

    def conditionalbackgrounds(self):
        '''legacy'''
        self.deprecated_method("script.skin.helper.backgrounds")

    def show_splash(self):
        '''helper to show a user defined splashscreen in the skin'''
        splashfile = self.params.get("file", "")
        duration = int(params.get("duration", 5))
        if (splashfile.lower().endswith("jpg") or splashfile.lower().endswith("gif") or
                splashfile.lower().endswith("png") or splashfile.lower().endswith("tiff")):
            # this is an image file
            self.win.setProperty("SkinHelper.SplashScreen", splashfile)
            # for images we just wait for X seconds to close the splash again
            start_time = time.time()
            while(time.time() - start_time <= duration):
                xbmc.sleep(500)
        else:
            # for video or audio we have to wait for the player to finish...
            xbmc.Player().play(splashfile, windowed=True)
            xbmc.sleep(500)
            while xbmc.getCondVisibility("Player.HasMedia"):
                xbmc.sleep(150)
        # replace startup window with home
        startupwindow = xbmc.getInfoLabel("$INFO[System.StartupWindow]")
        xbmc.executebuiltin("ReplaceWindow(%s)" % startupwindow)
        # startup playlist (if any)
        autostart_playlist = xbmc.getInfoLabel("$ESCINFO[Skin.String(autostart_playlist)]")
        if autostart_playlist:
            xbmc.executebuiltin("PlayMedia(%s)" % autostart_playlist)

    def videosearch(self):
        '''show the special search dialog'''
        from resources.lib.searchdialog import SearchDialog
        search_dialog = SearchDialog("script-skin_helper_service-CustomSearch.xml",
                                     self.addon.getAddonInfo('path').decode("utf-8"), "Default", "1080i")
        search_dialog.doModal()
        del search_dialog

    def showinfo(self):
        '''shows our special videoinfo dialog'''
        dbid = self.params.get("dbid", "")
        dbtype = self.params.get("dbtype", "")
        from infodialog import show_infodialog
        show_infodialog(dbid, dbtype)

    def deletedir(self):
        '''helper to delete a directory, input can be normal filesystem path or vfs'''
        del_path = self.params.get("path")
        if del_path:
            ret = xbmcgui.Dialog().yesno(heading=xbmc.getLocalizedString(122),
                                         line1=u"%s[CR]%s" % (xbmc.getLocalizedString(125), del_path))
            if ret:
                success = recursive_delete_dir(del_path)
                if success:
                    xbmcgui.Dialog().ok(heading=xbmc.getLocalizedString(19179),
                                        line1=self.addon.getLocalizedString(32014))
                else:
                    xbmcgui.Dialog().ok(heading=xbmc.getLocalizedString(16205),
                                        line1=xbmc.getLocalizedString(32015))

    def overlaytexture(self):
        '''helper to let the user choose a background overlay from a skin defined folder'''
        overlays = []
        overlays.append(self.addon.getLocalizedString(32000))  # Custom image
        dirs, files = xbmcvfs.listdir("special://skin/extras/bgoverlays/")
        for file in files:
            if file.endswith(".png"):
                label = file.replace(".png", "")
                overlays.append(label)
        overlays.append(self.addon.getLocalizedString(32001))  # None
        dialog = xbmcgui.Dialog()
        ret = dialog.select(self.addon.getLocalizedString(32002), overlays)
        del dialog
        if ret == 0:
            dialog = xbmcgui.Dialog()
            custom_texture = dialog.browse(2, self.addon.getLocalizedString(32003), 'files')
            if custom_texture:
                xbmc.executebuiltin("Skin.SetString(BackgroundOverlayTexture,Custom)")
                xbmc.executebuiltin("Skin.SetString(CustomBackgroundOverlayTexture,%s)" % custom_texture)
        elif ret > 0:
            xbmc.executebuiltin("Skin.SetString(BackgroundOverlayTexture,%s)" % overlays[ret])
            xbmc.executebuiltin("Skin.Reset(CustomBackgroundOverlayTexture)")

    def busytexture(self):
        '''helper which lets the user select a busy spinner from predefined spinners in the skin'''
        spinners = []

        current_spinner = xbmc.getInfoLabel("Skin.String(SkinHelper.SpinnerTexture)")
        # none option
        listitem = xbmcgui.ListItem(label=self.addon.getLocalizedString(32001), iconImage="DefaultAddonNone.png")
        listitem.setProperty("icon", "DefaultAddonNone.png")
        listitem.setProperty("id", "none")
        spinners.append(listitem)
        # custom single
        listitem = xbmcgui.ListItem(label=self.addon.getLocalizedString(32004), iconImage="DefaultAddonPicture.png")
        listitem.setProperty("icon", "DefaultAddonPicture.png")
        listitem.setProperty("id", "customsingle")
        spinners.append(listitem)
        # custom multi
        listitem = xbmcgui.ListItem(label=self.addon.getLocalizedString(32005), iconImage="DefaultFolder.png")
        listitem.setProperty("icon", "DefaultFolder.png")
        listitem.setProperty("id", "custommulti")
        spinners.append(listitem)
        # enumerate skin folder with busy spinners
        spinners_path = "special://skin/extras/busy_spinners/"
        if xbmcvfs.exists(spinners_path):
            dirs, files = xbmcvfs.listdir(spinners_path)
            for item in dirs:
                icon = "DefaultFolder.png"
                listitem = xbmcgui.ListItem(label=item, iconImage=icon)
                listitem.setProperty("icon", icon)
                listitem.setPath(spinners_path + item)
                spinners.append(listitem)
            for file in files:
                if file.endswith(".gif"):
                    label = file.replace(".gif", "")
                    icon = spinners_path + file
                    listitem = xbmcgui.ListItem(label=label, iconImage=icon)
                    listitem.setProperty("icon", icon)
                    listitem.setPath(icon)
                    spinners.append(listitem)

        # show select dialog with choices
        dialog = DialogSelect("DialogSelect.xml", "", listing=spinners,
                              windowtitle=self.addon.getLocalizedString(32006), richlayout=True)
        for count, li in enumerate(spinners):
            if li.getLabel() == current_spinner:
                dialog.autofocus_id = count
        dialog.doModal()
        result = dialog.result
        del dialog
        if result:
            id = result.getLabel()
            if result.getProperty("id") == "customsingle":
                dialog = xbmcgui.Dialog()
                custom_texture = dialog.browse(2, self.addon.getLocalizedString(32004), 'files', mask='.gif')
                if custom_texture:
                    result.setPath(custom_texture)
            elif result.getProperty("id") == "custommulti":
                dialog = xbmcgui.Dialog()
                custom_texture = dialog.browse(0, self.addon.getLocalizedString(32005), 'files')
                if custom_texture:
                    result.setPath(custom_texture)
            # write the values to skin strings
            xbmc.executebuiltin("Skin.SetString(SkinHelper.SpinnerTexture,%s)" % result.getLabel())
            xbmc.executebuiltin("Skin.SetString(SkinHelper.SpinnerTexturePath,%s)" % result.getfilename())
            del result

    def dialogok(self):
        '''helper to show an OK dialog with a message'''
        headertxt = self.params.get("header")
        bodytxt = self.params.get("message")
        if bodytxt.startswith(" "):
            bodytxt = bodytxt[1:]
        if headertxt.startswith(" "):
            headertxt = headertxt[1:]
        dialog = xbmcgui.Dialog()
        dialog.ok(heading=headertxt, line1=bodytxt)
        del dialog

    def dialogyesno(self):
        '''helper to show a YES/NO dialog with a message'''
        headertxt = self.params.get("header")
        bodytxt = self.params.get("message")
        yesactions = self.params.get("yesaction", "").split("|")
        noactions = self.params.get("noaction", "").split("|")
        if bodytxt.startswith(" "):
            bodytxt = bodytxt[1:]
        if headertxt.startswith(" "):
            headertxt = headertxt[1:]
        if xbmcgui.Dialog().yesno(heading=headertxt, line1=bodytxt):
            for action in yesactions:
                xbmc.executebuiltin(action.encode("utf-8"))
        else:
            for action in noactions:
                xbmc.executebuiltin(action.encode("utf-8"))

    def textviewer(self):
        '''helper to show a textviewer dialog with a message'''
        headertxt = self.params.get("header", "")
        bodytxt = self.params.get("message", "")
        if bodytxt.startswith(" "):
            bodytxt = bodytxt[1:]
        if headertxt.startswith(" "):
            headertxt = headertxt[1:]
        xbmcgui.Dialog().textviewer(headertxt, bodytxt)

    def fileexists(self):
        '''helper to let the skinner check if a file exists
        and write the outcome to a window prop or skinstring'''
        filename = self.params.get("file")
        skinstring = self.params.get("skinstring")
        windowprop = self.params.get("winprop")
        if xbmcvfs.exists(filename):
            if windowprop:
                self.win.setProperty(windowprop, "exists")
            if skinstring:
                xbmc.executebuiltin("Skin.SetString(%s,exists)" % skinstring)
        else:
            if windowprop:
                self.win.clearProperty(windowprop)
            if skinstring:
                xbmc.executebuiltin("Skin.Reset(%s)" % skinstring)

    def stripstring(self):
        '''helper to allow the skinner to strip a string and write results to a skin string'''
        splitchar = self.params.get("splitchar")
        if splitchar.upper() == "[SPACE]":
            splitchar = " "
        skinstring = self.params.get("string")
        if not skinstring:
            skinstring = self.params.get("skinstring")
        output = self.params.get("output")
        index = self.params.get("index", 0)
        skinstring = skinstring.split(splitchar)[int(index)]
        self.win.setProperty(output, skinstring)

    def getfilename(self, filename=""):
        '''helper to display a sanitized filename in the vidoeinfo dialog'''
        output = self.params.get("output")
        if not filename:
            filename = xbmc.getInfoLabel("ListItem.FileNameAndPath")
        if not filename:
            filename = xbmc.getInfoLabel("ListItem.FileName")
        if "filename=" in filename:
            url_params = dict(urlparse.parse_qsl(filename))
            filename = url_params.get("filename")
        self.win.setProperty(output, filename)

    def getplayerfilename(self):
        '''helper to parse the filename from a plugin (e.g. emby) filename'''
        filename = xbmc.getInfoLabel("Player.FileNameAndPath")
        if not filename:
            filename = xbmc.getInfoLabel("Player.FileName")
        self.getfilename(filename)

    def getpercentage(self):
        '''helper to calculate the percentage of 2 numbers and write results to a skinstring'''
        total = int(params.get("total"))
        count = int(params.get("count"))
        roundsteps = self.params.get("roundsteps")
        skinstring = self.params.get("skinstring")
        percentage = int(round((1.0 * count / total) * 100))
        if roundsteps:
            roundsteps = int(roundsteps)
            percentage = percentage + (roundsteps - percentage) % roundsteps
        xbmc.executebuiltin("Skin.SetString(%s,%s)" % (skinstring, percentage))

    def setresourceaddon(self):
        '''helper to let the user choose a resource addon and set that as skin string'''
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        addontype = self.params.get("addontype")
        skinstring = self.params.get("skinstring")
        listing = []

        # none option
        listitem = xbmcgui.ListItem(label=self.addon.getLocalizedString(32001), iconImage="DefaultAddonNone.png")
        listitem.setProperty("addonid", "none")
        listing.append(listitem)

        # custom path
        listitem = xbmcgui.ListItem(label=self.addon.getLocalizedString(32009), iconImage="DefaultFolder.png")
        listitem.setProperty("addonid", "custom")
        listing.append(listitem)

        # installed addons
        installed_addons = []
        for item in self.get_resourceaddons(addontype):
            installed_addons.append(item["addonid"])
            label2 = "%s: %s" % (xbmc.getLocalizedString(21863), item["author"])
            listitem = xbmcgui.ListItem(label=item["name"], label2=label2, iconImage=item["thumbnail"])
            listitem.setPath("resource://%s/" % item["addonid"])
            listitem.setProperty("addonid", item["addonid"])
            listing.append(listitem)

        # repo adons
        for item in self.get_repo_resourceaddons(addontype):
            if not item["addonid"] in installed_addons:
                label2 = "%s: %s" % (xbmc.getLocalizedString(21863), item["author"])
                label2 = "%s - %s" % (label2, self.addon.getLocalizedString(32011))
                listitem = xbmcgui.ListItem(label=item["name"],
                                            label2=label2, iconImage=item["thumbnail"])
                listitem.setPath("resource://%s/" % item["addonid"])
                listitem.setProperty("addonid", item["addonid"])
                listing.append(listitem)

        # special skinhelper paths
        if addontype == "resource.images.moviegenrefanart":
            label = self.addon.getLocalizedString(32019)
            listitem = xbmcgui.ListItem(
                label=label, label2="Skin Helper Service",
                iconImage="special://home/addons/script.skin.helper.service/icon.png")
            listitem.setPath("plugin://script.skin.helper.service/?action=moviegenrebackground&genre=")
            listitem.setProperty("addonid", "skinhelper.forgenre")
            installed_addons.append("skinhelper.forgenre")
            listing.append(listitem)

        # show select dialog with choices
        dialog = DialogSelect("DialogSelect.xml", "", listing=listing,
                              windowtitle=self.addon.getLocalizedString(32010), richlayout=True)
        dialog.doModal()
        result = dialog.result
        del dialog

        # process selection...
        if result:
            addon_id = result.getProperty("addonid")
            addon_name = result.getLabel()
            if addon_id == "none":
                # None
                xbmc.executebuiltin('Skin.Reset(%s)' % skinstring)
                xbmc.executebuiltin('Skin.Reset(%s.ext)' % skinstring)
                xbmc.executebuiltin('Skin.SetString(%s.name,%s)' % (skinstring, addon_name))
                xbmc.executebuiltin('Skin.Reset(%s.path)' % skinstring)
                xbmc.executebuiltin('Skin.Reset(%s.multi)' % skinstring)
            else:
                if addon_id == "custom":
                    # custom path
                    dialog = xbmcgui.Dialog()
                    custom_path = dialog.browse(0, self.addon.getLocalizedString(32005), 'files')
                    del dialog
                    result.setPath(custom_path)
                elif addon_id not in installed_addons:
                    # trigger install...
                    if KODI_VERSION >= 17:
                        xbmc.executebuiltin("InstallAddon(%s)" % addon_id)
                    else:
                        xbmc.executebuiltin("RunPlugin(plugin://%s)" % addon_id)
                    count = 0
                    # wait (max 2 minutes) untill install is completed
                    install_succes = False
                    while not install_succes and count < 240:
                        install_succes = xbmc.getCondVisibility("System.HasAddon(%s)" % addon_id)
                        xbmc.sleep(500)
                    if not install_succes:
                        return

                addonpath = result.getfilename()
                if addonpath:
                    is_multi, extension = self.get_multi_extension(addonpath)
                    xbmc.executebuiltin('Skin.SetString(%s,%s)' % (skinstring, addonpath))
                    xbmc.executebuiltin('Skin.SetString(%s.path,%s)' % (skinstring, addonpath))
                    xbmc.executebuiltin('Skin.SetString(%s.name,%s)' % (skinstring, addon_name))
                    xbmc.executebuiltin('Skin.SetString(%s.ext,.%s)' % (skinstring, extension))
                    if is_multi:
                        xbmc.executebuiltin('Skin.SetBool(%s.multi)' % skinstring)
                    else:
                        xbmc.executebuiltin('Skin.Reset(%s.multi)' % skinstring)

    def checkresourceaddons(self, addonslist):
        '''allow the skinner to perform a basic check if some required resource addons are available'''
        addonslist = self.params.get("addonslist", "")
        addonslist = addonslist.split("|")
        for item in addonslist:
            setting = item.split(";")[0]
            addontype = item.split(";")[1]
            addontypelabel = item.split(";")[2]
            skinsetting = xbmc.getInfoLabel("Skin.String(%s.path)" % setting).decode("utf-8")
            if not skinsetting or (skinsetting and
                                   xbmc.getCondVisibility("!System.HasAddon(%s)" %
                                                          skinsetting.replace("resource://", "").replace("/", ""))):
                # skin setting is empty or filled with non existing addon...
                if not checkresourceaddon(setting, addontype):
                    ret = xbmcgui.Dialog().yesno(
                        heading=self.addon.getLocalizedString(32007) % addontypelabel,
                        line1=self.addon.getLocalizedString(32008) % addontypelabel)
                    xbmc.executebuiltin("Skin.Reset(%s.path)" % setting)
                    if ret:
                        xbmc.executebuiltin(
                            "ActivateWindow(AddonBrowser, addons://repository.xbmc.org/kodi.resource.images/)")
                        # wait untill the addon is installed...
                        count = 0
                        while not checkresourceaddon(setting, addontype) and count < 120:
                            xbmc.sleep(1000)
                            if self.win.getProperty("SkinHelperShutdownRequested"):
                                return

    def checkresourceaddon(self, skinstring="", addontype=""):
        ''' check for existing resource addons of specified type and set first one found'''
        if not addontype:
            addontype = self.params.get("addontype")
        if not skinstring:
            skinstring = self.params.get("skinstring")
        if addontype and skinstring:
            for item in self.get_resourceaddons(addontype):
                xbmc.executebuiltin("Skin.SetString(%s.path,resource://%s/)" % (skinstring, item['addonid']))
                xbmc.executebuiltin("Skin.SetString(%s.name,%s)" % (skinstring, item['name']))
                if item["isMulti"]:
                    xbmc.executebuiltin("Skin.SetBool(%s.multi)" % (skinstring))
                return True
        return False

    def get_resourceaddons(self, filter=""):
        '''helper to retrieve all installed resource addons'''
        result = []
        params = {"type": "kodi.resource.images",
                  "properties": ["name", "thumbnail", "path", "author"]}
        for item in kodi_json("Addons.GetAddons", params, "addons"):
            if not filter or item['addonid'].lower().startswith(filter.lower()):
                result.append(item)

        return result

    @staticmethod
    def get_multi_extension(filepath):
        '''check if resource addon or custom path has subfolders (multiimage)'''
        is_multi = False
        extension = ""
        dirs, files = xbmcvfs.listdir(filepath)
        for dir in dirs:
            is_multi = True
        if not is_multi:
            for item in files:
                extension = item.split(".")[-1]
                break
        return (is_multi, extension)

    @use_cache(2)
    def get_repo_resourceaddons(self, filter=""):
        '''helper to retrieve all available resource addons on the kodi repo'''
        result = []
        for item in xbmcvfs.listdir("addons://all/kodi.resource.images/")[1]:
            if not filter or item.lower().startswith(filter.lower()):
                addoninfo = self.get_repo_addoninfo(item)
                if not addoninfo.get("name"):
                    addoninfo = {"addonid": item, "name": item}
                    addon["thumbnail"] = "http://mirrors.kodi.tv/addons/krypton/%s/icon.png" % item
                result.append(addoninfo)
        return result

    def get_repo_addoninfo(self, addonid):
        '''tries to grab info about the addon from kodi repo addons listing'''
        cachestr = "SkinHelper.repoaddoninfo.%s" % addonid
        cache = self.cache.get(cachestr)
        if cache:
            return cache
        info = {"addonid": addonid, "name": "", "thumbnail": "", "author": ""}
        mirrorurl = "http://addons.kodi.tv/show/%s/" % addonid
        try:
            req = urllib2.Request(mirrorurl)
            req.add_header('User-Agent',
                           'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
            response = urllib2.urlopen(req)
            body = response.read()
            response.close()
            body = body.replace('\r', '').replace('\n', '').replace('\t', '')
            for addondetail in re.compile('<div id="addonDetail">(.*?)</div>').findall(body):
                for h2_item in re.compile('<h2>(.*?)</h2>').findall(addondetail):
                    info["name"] = h2_item
                    break
                for thumbnail in re.compile('src="(.*?)"').findall(addondetail):
                    icon = "http://addons.kodi.tv/%s" % thumbnail
                    info["thumbnail"] = icon
                    break
                authors = []
                for addonmetadata in re.compile('<div id="addonMetaData">(.*?)</div>').findall(body):
                    for author in re.compile('<a href="(.*?)">(.*?)</a>').findall(addonmetadata):
                        authors.append(author[1])
                info["author"] = ",".join(authors)
                break

        except Exception as exc:
            log_exception(__name__, exc)

        self.cache.set(cachestr, info)
        return info
