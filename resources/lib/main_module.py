#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
from simplecache import SimpleCache
from utils import log_msg, try_encode, normalize_string, get_clean_image, KODI_VERSION, process_method_on_list, log_exception, get_current_content_type, get_kodi_json
from dialogs import DialogSelectSmall, DialogSelectBig
from artutils import KodiDb, Tmdb
from datetime import timedelta
import urlparse, urllib
import sys, os


class MainModule:
    '''mainmodule provides the script methods for the skinhelper addon'''
    params = {}

    def __init__(self):
        '''Initialization'''
        self.win = xbmcgui.Window(10000)

        self.params = self.get_params()
        log_msg("script called with parameters: %s" %self.params, xbmc.LOGNOTICE)
        action = self.params.get("action","")

        #launch module for action provided by this script
        try:
            getattr(self, action)()
        except AttributeError:
            log_msg("No such action: %s"%action, xbmc.LOGWARNING)
        except Exception:
            log_exception(__name__,exc)

    def __del__(self):
        '''Cleanup Kodi Cpython instances'''
        del self.win
        log_msg("Exited")

    @classmethod
    def get_params(self):
        #extract the self.params from the called script path
        params = {}
        for arg in sys.argv:
            arg = arg.decode("utf-8")
            if arg == 'script.skin.helper.service' or arg == 'default.py':
                continue
            elif "=" in arg:
                paramname = arg.split('=')[0].lower()
                paramvalue = arg.replace(paramname+"=","")
                params[paramname] = paramvalue
        return params

    def deprecated_method(self, newaddon):
        '''
            used when one of the deprecated methods is called
            print warning in log and call the external script with the same parameters
        '''
        action = self.params.get("action")
        log_msg("Deprecated method: %s. Please call %s directly" %(action, newaddon), xbmc.LOGWARNING )
        paramstring = sys.argv[1:]
        if xbmc.getCondVisibility("System.HasAddon(%s)" %newaddon):
            xbmc.executebuiltin("RunAddon(script.skin.helper.colorpicker%s)" %paramstring)
        else:
            #trigger install of the addon
            if KODI_VERSION >= 17:
                xbmc.executebuiltin("InstallAddon(%s)" %newaddon)
            else:
                xbmc.executebuiltin("RunPlugin(plugin://%s)" %newaddon)

    @staticmethod
    def addshortcut():
        '''workaround for skinshortcuts to add new shortcut by adding empty first'''
        xbmc.executebuiltin('SendClick(301)')
        count = 0
        #wait untill the empy item is focused
        while (count != 60 and xbmc.getCondVisibility("Window.IsActive(script-skinshortcuts.xml)")):
            if not xbmc.getCondVisibility("StringCompare(Container(211).ListItem.Property(path), noop)"):
                xbmc.sleep(100)
                count += 1
            else:
                break
        if xbmc.getCondVisibility("StringCompare(Container(211).ListItem.Property(path), noop) + Window.IsActive(script-skinshortcuts.xml)"):
            xbmc.executebuiltin('SendClick(401)')

    @staticmethod
    def musicsearch():
        '''helper to go directly to music search dialog'''
        xbmc.executebuiltin( "ActivateWindow(Music)" )
        xbmc.executebuiltin( "SendClick(8)" )

    def setview(self):
        '''sets the selected viewmode for the container'''
        content_type = get_current_content_type()
        if not content_type:
            content_type = "files"
        current_view = xbmc.getInfoLabel("Container.Viewmode").decode("utf-8")
        view_id, view_label = self.selectview(content_type, current_view)
        current_forced_view = xbmc.getInfoLabel("Skin.String(SkinHelper.ForcedViews.%s)" %content_type)

        if view_id != None:
            #also store forced view
            if (content_type and current_forced_view and current_forced_view != "None"
                and xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.ForcedViews.Enabled)") ):
                xbmc.executebuiltin("Skin.SetString(SkinHelper.ForcedViews.%s,%s)" %(content_type, view_id))
                xbmc.executebuiltin("Skin.SetString(SkinHelper.ForcedViews.%s.label,%s)" %(content_type, view_label))
                self.win.setProperty("SkinHelper.ForcedView",view_id)
                if not xbmc.getCondVisibility("Control.HasFocus(%s)" %current_forced_view):
                    xbmc.sleep(100)
                    xbmc.executebuiltin("Container.SetViewMode(%s)" %view_id)
                    xbmc.executebuiltin("SetFocus(%s)" %view_id)
            else:
                self.win.clearProperty("SkinHelper.ForcedView")
            #set view
            xbmc.executebuiltin("Container.SetViewMode(%s)" %view_id)

    def selectview(self, content_type="other", current_view=None, display_none=False):
        '''reads skinfile with all views to present a dialog to choose from'''
        cur_view_select_id = None
        id = None
        label = ""
        all_views = []
        if display_none:
            listitem = xbmcgui.ListItem(label="None")
            listitem.setProperty("id","None")
            all_views.append(listitem)
        #read the special skin views file
        views_file = xbmc.translatePath( 'special://skin/extras/views.xml' ).decode("utf-8")
        if xbmcvfs.exists( views_file ):
            doc = parse( views_file )
            listing = doc.documentElement.getElementsByTagName( 'view' )
            itemcount = 0
            for view in listing:
                label = xbmc.getLocalizedString(int(view.attributes[ 'languageid' ].nodeValue))
                id = view.attributes[ 'value' ].nodeValue
                type = view.attributes[ 'type' ].nodeValue.lower().split(",")
                if label.lower() == current_view.lower() or id == current_view:
                    cur_view_select_id = itemcount
                    if display_none == True:
                        cur_view_select_id += 1
                if ( ("all" in type or content_type.lower() in type) and (not "!" + content_type.lower() in type)
                        and not xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.View.Disabled.%s)" %id) ):
                    image = "special://skin/extras/viewthumbs/%s.jpg" %id
                    listitem = xbmcgui.ListItem(label=label, iconImage=image)
                    listitem.setProperty("id",id)
                    listitem.setProperty("icon",image)
                    all_views.append(listitem)
                    itemcount +=1
        w = DialogSelectBig( "DialogSelect.xml", self.addon.getAddonInfo('path').decode("utf-8"),
            listing=all_views, windowtitle=self.addon.getLocalizedString(32054),multiselect=False )
        w.autoFocusId = cur_view_select_id
        w.doModal()
        selected_item = w.result
        del w
        if selected_item != -1:
            id = all_views[selected_item].getProperty("id")
            label = all_views[selected_item].getLabel()
            return (id,label)
        else:
            return (None,None)

    def enableviews(self):
        '''show select dialog to enable/disable views'''
        all_views = []
        views_file = xbmc.translatePath( 'special://skin/extras/views.xml' ).decode("utf-8")
        if xbmcvfs.exists( views_file ):
            doc = parse( views_file )
            listing = doc.documentElement.getElementsByTagName( 'view' )
            for view in listing:
                view_id = view.attributes[ 'value' ].nodeValue
                label = xbmc.getLocalizedString(int(view.attributes[ 'languageid' ].nodeValue))
                desc = label + " (" + str(view_id) + ")"
                listitem = xbmcgui.ListItem(label=label,label2=desc)
                listitem.setProperty("id",view_id)
                if not xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.View.Disabled.%s)" %view_id):
                    listitem.select(selected=True)
                all_views.append(listitem)

        w = DialogSelectSmall( "DialogSelect.xml", self.addon.getAddonInfo('path').decode("utf-8"), listing=all_views,
            windowtitle=self.addon.getLocalizedString(32017),multiselect=True )
        w.doModal()
        selected_items = w.result
        del w
        if selected_items != -1:
            itemcount = len(all_views) -1
            while (itemcount != -1):
                view_id = all_views[itemcount].getProperty("id")
                if itemcount in selected_items:
                    #view is enabled
                    xbmc.executebuiltin("Skin.Reset(SkinHelper.View.Disabled.%s)" %view_id)
                else:
                    #view is disabled
                    xbmc.executebuiltin("Skin.SetBool(SkinHelper.View.Disabled.%s)" %view_id)
                itemcount -= 1

    def setforcedview(self):
        '''helper that sets a forced view for a specific content type'''
        content_type = self.params.get("contenttype")
        if content_type:
            current_view = xbmc.getInfoLabel("Skin.String(SkinHelper.ForcedViews.%s)" %content_type)
            if not current_view:
                current_view = "0"
            view_id, view_label = self.selectview(content_type, current_view, True)
            if view_id:
                xbmc.executebuiltin("Skin.SetString(SkinHelper.ForcedViews.%s,%s)" %(content_type, view_id))
                xbmc.executebuiltin("Skin.SetString(SkinHelper.ForcedViews.%s.label,%s)" %(content_type, view_label))

    @staticmethod
    def get_youtube_listing(searchquery):
        lib_path = u"plugin://plugin.video.youtube/kodion/search/query/?q=%s" %searchquery
        return get_kodi_json(u'Files.GetDirectory','{ "properties": ["title","art","plot"],\
            "directory": "%s", "media": "files", "limits": {"end":25} }' %lib_path)

    def searchyoutube(self):
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        title = self.params.get("title","")
        window_header = self.params.get("header","")
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
                listitem.setProperty("path",media["file"])
                results.append(listitem)

        #finished lookup - display listing with results
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        w = DialogSelectBig( "DialogSelect.xml", "", listing=results, windowtitle=window_header, multiselect=False )
        w.doModal()
        selected_item = w.result
        del w
        if selected_item != -1:
            if xbmc.getCondVisibility("Window.IsActive(script-skin_helper_service-CustomInfo.xml) | Window.IsActive(movieinformation)"):
                xbmc.executebuiltin("Dialog.Close(movieinformation)")
                xbmc.executebuiltin("Dialog.Close(script-skin_helper_service-CustomInfo.xml)")
                xbmc.sleep(1000)
            xbmc.executebuiltin('PlayMedia("%s")' %results[selected_item].getProperty("path"))

    def setfocus(self):
        '''helper to set focus on a list or control'''
        control = self.params.get("control")
        fallback = self.params.get("FALLBACK")
        count = 0
        if control:
            while not xbmc.getCondVisibility("Control.HasFocus(%s)" %control):
                if count == 20 or (fallback and xbmc.getCondVisibility("Control.IsVisible(%s) \
                    + !IntegerGreaterThan(Container(%s).NumItems,0)" %(control,control))):
                    if fallback:
                        xbmc.executebuiltin("Control.SetFocus(%s)"%fallback)
                    break
                else:
                    xbmc.executebuiltin("Control.SetFocus(%s)"%control)
                    xbmc.sleep(50)
                    count += 1

    def setwidgetcontainer(self):
        '''helper that reports the current selected widget container/control'''
        controls = self.params.get("CONTROLS","").split("-")
        if controls:
            xbmc.sleep(150)
            for i in range(10):
                for control in controls:
                    if xbmc.getCondVisibility("Control.IsVisible(%s) + IntegerGreaterThan(Container(%s).NumItems,0)"
                        %(control,control)):
                        self.win.setProperty("SkinHelper.WidgetContainer",control)
                        return
                xbmc.sleep(50)
        self.win.clearProperty("SkinHelper.WidgetContainer")

    def saveskinimage(self):
        '''let the user select an image and save it to addon_data for easy backup'''
        skinstring = self.params.get("skinstring","")
        allow_multi = self.params.get("multi","") == "true"
        header = self.params.get("header","")
        from skinsettings import SkinSettings
        SkinSettings().save_skin_image(skinstring, allow_multi, header)

    def setskinsetting(self):
        '''allows the user to set a skin setting with a select dialog'''
        setting = self.params.get("setting","")
        org_id = self.params.get("id","")
        header = self.params.get("header","")
        from skinsettings import SkinSettings
        SkinSettings().set_skin_setting(setting=setting, window_header=header, original_id=org_id)

    def setskinconstant(self):
        '''allows the user to set a skin constant with a select dialog'''
        setting = self.params.get("setting","").split("|")
        value = self.params.get("value","").split("|")
        header = self.params.get("header","")
        from skinsettings import SkinSettings
        SkinSettings().set_skin_constant(setting, header, value)

    def setskinconstant():
        '''allows the skinner to set multiple skin constants'''
        setting = self.params.get("setting","")
        prop = self.params.get("property","")
        header = self.params.get("header","")
        from skinsettings import SkinSettings
        SkinSettings().set_skin_constant(setting, header, prop)

    def setskinshortcutsproperty(self):
        '''allows the user to make a setting for skinshortcuts using the special skinsettings dialogs'''
        setting = self.params.get("setting","")
        value = self.params.get("value","")
        header = self.params.get("header","")
        from skinsettings import SkinSettings
        SkinSettings().set_skinshortcuts_property(setting, header, value)

    def togglekodisetting(settingname):
        '''toggle kodi setting'''
        settingname = self.params.get("setting","")
        cur_value = xbmc.getCondVisibility("system.getbool(%s)"%settingname)
        if cur_value == True:
            newValue = "false"
        else:
            newValue = "true"
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.SetSettingValue","params":{"setting":"%s","value":%s}}' %(settingname,newValue))

    def setkodisetting(settingname):
        '''set kodi setting'''
        settingname = self.params.get("setting","")
        value = self.params.get("value","")
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
        elif is_int==False:
            value = '"%s"' %value
        xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.SetSettingValue",\
            "params":{"setting":"%s","value":%s}}' %(settingname,value))

    def playtrailer():
        '''auto play windowed trailer inside video listing'''
        if not xbmc.getCondVisibility("Player.HasMedia | Container.Scrolling | Container.OnNext | \
            Container.OnPrevious | !IsEmpty(Window(Home).Property(traileractionbusy))"):
            self.win.setProperty("traileractionbusy","traileractionbusy")
            widget_container = self.params.get("widgetcontainer","")
            trailer_mode = self.params.get("mode","").replace("auto_","")
            allow_youtube = self.params.get("youtube","") == "true"
            if not trailer_mode:
                trailer_mode = "windowed"
            if widget_container:
                widget_container_prefix = "Container(%s)."%widget_container
            else: widget_container_prefix = ""

            li_title = xbmc.getInfoLabel("%sListItem.Title" %widget_container_prefix).decode('utf-8')
            li_trailer = xbmc.getInfoLabel("%sListItem.Trailer" %widget_container_prefix).decode('utf-8')
            if not li_trailer and allow_youtube:
                youtube_result = self.get_youtube_listing("%s Trailer"%li_title)
                if youtube_result:
                    li_trailer = youtube_result[0].get("file")
            #always wait a bit to prevent trailer start playing when we're scrolling the list
            xbmc.Monitor().waitForAbort(3)
            if li_trailer and (li_title == xbmc.getInfoLabel("%sListItem.Title"
                %widget_container_prefix).decode('utf-8')):
                if trailer_mode == "fullscreen" and li_trailer:
                    xbmc.executebuiltin('PlayMedia("%s")' %li_trailer)
                else:
                    xbmc.executebuiltin('PlayMedia("%s",1)' %li_trailer)
                self.win.setProperty("TrailerPlaying",trailer_mode)
            self.win.clearProperty("traileractionbusy")

    def colorpicker():
        '''legacy'''
        self.deprecated_method("script.skin.helper.colorpicker")
    
    def show_splash(self):
        '''helper to show a user defined splashscreen in the skin'''
        splashfile = self.params.get("file","")
        duration = int(params.get("duration",5))
        if ( splashfile.lower().endswith("jpg") or splashfile.lower().endswith("gif") or 
            splashfile.lower().endswith("png") or splashfile.lower().endswith("tiff") ):
            #this is an image file
            self.win.setProperty("SkinHelper.SplashScreen",splashfile)
            #for images we just wait for X seconds to close the splash again
            start_time = time.time()
            while(time.time() - start_time <= duration):
                xbmc.sleep(500)
        else:
            #for video or audio we have to wait for the player to finish...
            xbmc.Player().play(splashfile,windowed=True)
            xbmc.sleep(500)
            while xbmc.getCondVisibility("Player.HasMedia"):
                xbmc.sleep(150)
        #replace startup window with home
        startupwindow = xbmc.getInfoLabel("$INFO[System.StartupWindow]")
        xbmc.executebuiltin("ReplaceWindow(%s)" %startupwindow)
        #startup playlist (if any)
        autostart_playlist = xbmc.getInfoLabel("$ESCINFO[Skin.String(autostart_playlist)]")
        if autostart_playlist: xbmc.executebuiltin("PlayMedia(%s)" %autostart_playlist)

    def videosearch(self):
        '''show the special search dialog'''
        from resources.lib.SearchDialog import SearchDialog
        search_dialog = SearchDialog("script-skin_helper_service-CustomSearch.xml", 
            self.addon.getAddonInfo('path').decode("utf-8"), "Default", "1080i")
        search_dialog.doModal()
        result = search_dialog.action
        del search_dialog
        if result:
            if "jsonrpc" in result:
                xbmc.executeJSONRPC(result)
            else:
                xbmc.executebuiltin(result)
                
    def showinfo(self):
        '''show the custom info screen'''
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        #try to figure out the params automatically if no ID provided...
        if not ( self.params.get("movieid") or self.params.get("episodeid") or self.params.get("tvshowid") ):
            widget_container = self.win.getProperty("SkinHelper.WidgetContainer").decode('utf-8')
            if widget_container: 
                widget_container_prefix = "Container(%s)."%widget_container
            else: 
                widget_container_prefix = ""
            dbid = xbmc.getInfoLabel("%sListItem.DBID"%widget_container_prefix).decode('utf-8')
            if not dbid or dbid == "-1": 
                dbid = xbmc.getInfoLabel("%sListItem.Property(DBID)"%widget_container_prefix).decode('utf-8')
            if dbid == "-1": 
                dbid = ""
            dbtype = xbmc.getInfoLabel("%sListItem.DBTYPE"%widget_container_prefix).decode('utf-8')
            log_msg("dbtype: %s - dbid: %s" %(dbtype,dbid))
            if not dbtype: 
                dbtype = xbmc.getInfoLabel("%sListItem.Property(DBTYPE)"%widget_container_prefix).decode('utf-8')
            if not dbtype:
                db_type = xbmc.getInfoLabel("%sListItem.Property(type)"%widget_container_prefix).decode('utf-8')
                if "episode" in db_type.lower() or xbmc.getLocalizedString(20360).lower() in db_type.lower(): 
                    dbtype = "episode"
                elif "movie" in db_type.lower() or xbmc.getLocalizedString(342).lower() in db_type.lower(): 
                    dbtype = "movie"
                elif "tvshow" in db_type.lower() or xbmc.getLocalizedString(36903).lower() in db_type.lower(): 
                    dbtype = "tvshow"
                elif "album" in db_type.lower() or xbmc.getLocalizedString(558).lower() in db_type.lower(): 
                    dbtype = "album"
                elif "song" in db_type.lower() or xbmc.getLocalizedString(36920).lower() in db_type.lower(): 
                    dbtype = "song"
            if dbid and dbtype: 
                self.params["%sID" %dbtype.upper()] = dbid
            self.params["lastwidgetcontainer"] = widget_container

        #open info dialog...
        from resources.lib.InfoDialog import GUI
        info_dialog = GUI( "script-skin_helper_service-CustomInfo.xml" , self.addon.getAddonInfo('path').decode("utf-8"), 
            "Default", "1080i", params=self.params )
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        if info_dialog.listitem:
            info_dialog.doModal()
            result = info_dialog.action
            if result:
                while xbmc.getCondVisibility("System.HasModalDialog | \
                    Window.IsActive(script-ExtendedInfo Script-DialogVideoInfo.xml) | \
                    Window.IsActive(script-ExtendedInfo Script-DialogInfo.xml) | \
                    Window.IsActive(script-skin_helper_service-CustomInfo.xml) | \
                    Window.IsActive(script-skin_helper_service-CustomSearch.xml)"):
                    xbmc.executebuiltin("Action(Back)")
                    xbmc.sleep(500)
                if "jsonrpc" in result:
                    xbmc.executeJSONRPC(result)
                else:
                    xbmc.executebuiltin(result)
    
    
    def init_old(self):


            if True:
                pass


            
            

            

            elif action == "COLORTHEMES":
                from resources.lib.ColorThemes import ColorThemes
                colorThemes = ColorThemes("DialogSelect.xml", self.addon.getAddonInfo('path').decode("utf-8"))
                colorThemes.daynight = self.params.get("DAYNIGHT",None)
                colorThemes.doModal()
                del colorThemes

            elif action == "CONDITIONALBACKGROUNDS":
                from resources.lib.ConditionalBackgrounds import ConditionalBackgrounds
                conditionalBackgrounds = ConditionalBackgrounds("DialogSelect.xml", self.addon.getAddonInfo('path').decode("utf-8"))
                conditionalBackgrounds.doModal()
                del conditionalBackgrounds

            elif action == "CREATECOLORTHEME":
                import resources.lib.ColorThemes as colorThemes
                colorThemes.createColorTheme()

            elif action == "RESTORECOLORTHEME":
                import resources.lib.ColorThemes as colorThemes
                colorThemes.restoreColorTheme()

            elif action == "OVERLAYTEXTURE":
                mainmodule.selectOverlayTexture()

            elif action == "BUSYTEXTURE":
                mainmodule.selectBusyTexture()

            elif action == "CACHEALLMUSICART":
                import resources.lib.Artworkutils as artworkutils
                artworkutils.preCacheAllMusicArt()

            elif action == "RESETCACHE":
                path = self.params.get("PATH")
                if path == "pvr":
                    path = self.win.getProperty("SkinHelper.pvrthumbspath").decode("utf-8")
                elif path == "music":
                    path = "special://profile/addon_data/script.skin.helper.service/musicartcache/"
                elif path == "wallbackgrounds":
                    path = "special://profile/addon_data/script.skin.helper.service/wallbackgrounds/"
                    self.win.setProperty("resetWallArtCache","reset")
                else: path = None

                if path:
                    success = True
                    ret = xbmcgui.Dialog().yesno(heading=self.addon.getLocalizedString(32089), line1=self.addon.getLocalizedString(32090)+path)
                    if ret:
                        self.win.setProperty("SkinHelper.IgnoreCache","ignore")
                        success = utils.recursiveDelete(path)
                        if success:
                            utils.checkFolders()
                            xbmcgui.Dialog().ok(heading=self.addon.getLocalizedString(32089), line1=self.addon.getLocalizedString(32091))
                        else:
                            xbmcgui.Dialog().ok(heading=self.addon.getLocalizedString(32089), line1=self.addon.getLocalizedString(32092))

            elif action == "BACKUP":
                import resources.lib.BackupRestore as backup
                filter = self.params.get("FILTER","")
                silent = self.params.get("SILENT",None)
                promptfilename = self.params.get("PROMPTFILENAME","false")
                backup.backup(filter,silent,promptfilename.lower())

            elif action == "RESTORE":
                import resources.lib.BackupRestore as backup
                silent = self.params.get("SILENT",None)
                backup.restore(silent)

            elif action == "RESET":
                import resources.lib.BackupRestore as backup
                filter = self.params.get("FILTER","")
                silent = self.params.get("SILENT","") == "true"
                backup.reset(filter,silent)
                xbmc.Monitor().waitForAbort(2)
                mainmodule.correctSkinSettings()

            elif action == "DIALOGOK":
                headerMsg = self.params.get("HEADER")
                bodyMsg = self.params.get("MESSAGE")
                if bodyMsg.startswith(" "): bodyMsg = bodyMsg[1:]
                if headerMsg.startswith(" "): headerMsg = headerMsg[1:]
                xbmcgui.Dialog().ok(heading=headerMsg, line1=bodyMsg)

            elif action == "DIALOGYESNO":
                headerMsg = self.params.get("HEADER")
                bodyMsg = self.params.get("MESSAGE")
                yesactions = self.params.get("YESACTION","").split("|")
                noactions = self.params.get("NOACTION","").split("|")
                if bodyMsg.startswith(" "): bodyMsg = bodyMsg[1:]
                if headerMsg.startswith(" "): headerMsg = headerMsg[1:]
                if xbmcgui.Dialog().yesno(heading=headerMsg, line1=bodyMsg):
                    for action in yesactions:
                        xbmc.executebuiltin(action.encode("utf-8"))
                else:
                    for action in noactions:
                        xbmc.executebuiltin(action.encode("utf-8"))

            elif action == "TEXTVIEWER":
                headerMsg = self.params.get("HEADER","")
                bodyMsg = self.params.get("MESSAGE","")
                if bodyMsg.startswith(" "): bodyMsg = bodyMsg[1:]
                if headerMsg.startswith(" "): headerMsg = headerMsg[1:]
                xbmcgui.Dialog().textviewer(headerMsg, bodyMsg)

            elif action == "FILEEXISTS":
                filename = self.params.get("FILE")
                skinstring = self.params.get("SKINSTRING")
                windowprop = self.params.get("self.winPROP")
                if xbmcvfs.exists(filename):
                    if windowprop:
                        self.win.setProperty(windowprop,"exists")
                    if skinstring:
                        xbmc.executebuiltin("Skin.SetString(%s,exists)" %skinstring)
                else:
                    if windowprop:
                        self.win.clearProperty(windowprop)
                    if skinstring:
                        xbmc.executebuiltin("Skin.Reset(%s)" %skinstring)

            elif action == "STRIPSTRING":
                splitchar = self.params.get("SPLITCHAR")
                if splitchar == "[SPACE]": splitchar = " "
                string = self.params.get("STRING")
                output = self.params.get("OUTPUT")
                index = self.params.get("INDEX",0)
                string = string.split(splitchar)[int(index)]
                self.win.setProperty(output, string)

            elif action == "GETPLAYERFILENAME":
                output = self.params.get("OUTPUT")
                filename = xbmc.getInfoLabel("Player.FileNameAndPath")
                if not filename: filename = xbmc.getInfoLabel("Player.FileName")
                if "filename=" in filename:
                    url_params = dict(urlparse.parse_qsl(filename))
                    filename = url_params.get("filename")
                self.win.setProperty(output, filename)

            elif action == "GETFILENAME":
                output = self.params.get("OUTPUT")
                filename = xbmc.getInfoLabel("ListItem.FileNameAndPath")
                if not filename: filename = xbmc.getInfoLabel("ListItem.FileName")
                if not filename: filename = xbmc.getInfoLabel("Container(999).ListItem.FileName")
                if not filename: filename = xbmc.getInfoLabel("Container(999).ListItem.FileNameAndPath")
                if "filename=" in filename:
                    url_params = dict(urlparse.parse_qsl(filename))
                    filename = url_params.get("filename")
                self.win.setProperty(output, filename)

            elif action == "CHECKRESOURCEself.addonS":
                self.addonSLIST = self.params.get("self.addonSLIST")
                mainmodule.checkResourceAddons(self.addonSLIST)

            elif action == "GETPERCENTAGE":
                total = int(params.get("TOTAL"))
                count = int(params.get("COUNT"))
                roundsteps = self.params.get("ROUNDSTEPS")
                skinstring = self.params.get("SKINSTRING")

                percentage = int(round((1.0 * count / total) * 100))
                if roundsteps:
                    roundsteps = int(roundsteps)
                    percentage = percentage + (roundsteps - percentage) % roundsteps

                xbmc.executebuiltin("Skin.SetString(%s,%s)" %(skinstring,percentage))






def selectOverlayTexture():
    overlaysList = []
    overlaysList.append("Custom Overlay Image")
    dirs, files = xbmcvfs.listdir("special://skin/extras/bgoverlays/")
    for file in files:
        if file.endswith(".png"):
            label = file.replace(".png","")
            overlaysList.append(label)

    overlaysList.append("None")

    dialog = xbmcgui.Dialog()
    ret = dialog.select(self.addon.getLocalizedString(32015), overlaysList)
    if ret == 0:
        dialog = xbmcgui.Dialog()
        custom_texture = dialog.browse( 2 , self.addon.getLocalizedString(32016), 'files')
        if custom_texture:
            xbmc.executebuiltin("Skin.SetString(BackgroundOverlayTexture,Custom)")
            xbmc.executebuiltin("Skin.SetString(CustomBackgroundOverlayTexture,%s)" % custom_texture)
    else:
        xbmc.executebuiltin("Skin.SetString(BackgroundOverlayTexture,%s)" % overlaysList[ret])
        xbmc.executebuiltin("Skin.Reset(CustomBackgroundOverlayTexture)")

def selectBusyTexture():
    spinnersList = []

    currentSpinnerTexture = xbmc.getInfoLabel("Skin.String(SkinHelper.SpinnerTexture)")

    listitem = xbmcgui.ListItem(label="None")
    listitem.setProperty("icon","None")
    spinnersList.append(listitem)

    listitem = xbmcgui.ListItem(label=self.addon.getLocalizedString(32052))
    listitem.setProperty("icon","")
    spinnersList.append(listitem)

    listitem = xbmcgui.ListItem(label=self.addon.getLocalizedString(32053))
    listitem.setProperty("icon","")
    spinnersList.append(listitem)

    path = "special://skin/extras/busy_spinners/"
    if xbmcvfs.exists(path):
        dirs, files = xbmcvfs.listdir(path)

        for dir in dirs:
            listitem = xbmcgui.ListItem(label=dir)
            listitem.setProperty("icon",path + dir)
            spinnersList.append(listitem)

        for file in files:
            if file.endswith(".gif"):
                label = file.replace(".gif","")
                listitem = xbmcgui.ListItem(label=label)
                listitem.setProperty("icon",path + file)
                spinnersList.append(listitem)

    w = dialogs.DialogSelectBig( "DialogSelect.xml", self.addon.getAddonInfo('path').decode("utf-8"), listing=spinnersList, windowtitle=self.addon.getLocalizedString(32051),multiselect=False )

    count = 0
    for li in spinnersList:
        if li.getLabel() == currentSpinnerTexture:
            w.autoFocusId = count
        count += 1

    w.doModal()
    selected_item = w.result
    del w

    if selected_item == -1:
        return

    if selected_item == 1:
        dialog = xbmcgui.Dialog()
        custom_texture = dialog.browse( 2 , self.addon.getLocalizedString(32052), 'files', mask='.gif')
        if custom_texture:
            xbmc.executebuiltin("Skin.SetString(SkinHelper.SpinnerTexture,%s)" %spinnersList[selected_item].getLabel())
            xbmc.executebuiltin("Skin.SetString(SkinHelper.SpinnerTexturePath,%s)" % custom_texture)
    elif selected_item == 2:
        dialog = xbmcgui.Dialog()
        custom_texture = dialog.browse( 0 , self.addon.getLocalizedString(32053), 'files')
        if custom_texture:
            xbmc.executebuiltin("Skin.SetString(SkinHelper.SpinnerTexture,%s)" %spinnersList[selected_item].getLabel())
            xbmc.executebuiltin("Skin.SetString(SkinHelper.SpinnerTexturePath,%s)" % custom_texture)
    else:
        xbmc.executebuiltin("Skin.SetString(SkinHelper.SpinnerTexture,%s)" %spinnersList[selected_item].getLabel())
        xbmc.executebuiltin("Skin.SetString(SkinHelper.SpinnerTexturePath,%s)" % spinnersList[selected_item].getProperty("icon"))



def multiSelect(item,window_header=""):
    allOptions = []
    options = item.getElementsByTagName( 'option' )
    for option in options:
        id = option.attributes[ 'id' ].nodeValue
        label = xbmc.getInfoLabel(option.attributes[ 'label' ].nodeValue).decode("utf-8")
        default = option.attributes[ 'default' ].nodeValue
        condition = option.attributes[ 'condition' ].nodeValue
        if condition and not xbmc.getCondVisibility(condition): continue
        listitem = xbmcgui.ListItem(label=label)
        listitem.setProperty("id",id)
        if xbmc.getCondVisibility("Skin.HasSetting(%s)" %id) or (not xbmc.getInfoLabel("Skin.String(defaultset_%s)" %id) and xbmc.getCondVisibility( default )):
            listitem.select(selected=True)
        allOptions.append(listitem)
    #show select dialog
    w = dialogs.DialogSelectSmall( "DialogSelect.xml", self.addon.getAddonInfo('path').decode("utf-8"), listing=allOptions, windowtitle=window_header,multiselect=True )
    w.doModal()

    selected_items = w.result
    if selected_items != -1:
        itemcount = len(allOptions) -1
        while (itemcount != -1):
            skinsetting = allOptions[itemcount].getProperty("id")
            if itemcount in selected_items:
                #option is enabled
                xbmc.executebuiltin("Skin.SetBool(%s)" %skinsetting)
            else:
                #option is disabled
                xbmc.executebuiltin("Skin.Reset(%s)" %skinsetting)
            #always set additional prop to define the defaults
            xbmc.executebuiltin("Skin.SetString(defaultset_%s,defaultset)" %skinsetting)
            itemcount -= 1
    del w




def checkResourceAddon(setting, addontype):
    #check for existing resource addons of this type and set first one found...
    json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Addons.GetAddons", "params": {"type": "kodi.resource.images", "properties": ["name", "thumbnail", "path"]}, "id": 1}')
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    json_response = json.loads(json_query)
    if json_response.has_key('result') and (json_response['result'] != None) and json_response['result'].has_key('addons'):
        addons = json_response['result']['addons']
        for item in addons:
            if item['addonid'].startswith(addontype):
                xbmc.executebuiltin("Skin.SetString(%s.path,resource://%s/)" %(setting,item['addonid']))
                xbmc.executebuiltin("Skin.SetString(%s.name,%s)" %(setting,item['name']))
                if ".multi" in item['addonid'] or "animated" in item['addonid']:
                    xbmc.executebuiltin("Skin.SetBool(%s.multi)" %(setting))
                return True
    return False

def checkResourceAddons(addonslist):
    addonslist = addonslist.split("|")
    for item in addonslist:
        setting = item.split(";")[0]
        addontype = item.split(";")[1]
        addontypelabel = item.split(";")[2]
        skinsetting = xbmc.getInfoLabel("Skin.String(%s.path)" %setting).decode("utf-8")
        if not skinsetting or ( skinsetting and xbmc.getCondVisibility("!System.HasAddon(%s)" %skinsetting.replace("resource://","").replace("/","")) ):
            #skin setting is empty or filled with non existing addon...
            if not checkResourceAddon(setting, addontype):
                ret = xbmcgui.Dialog().yesno(heading="%s missing!"%addontypelabel,
                line1="To get the most out of this skin, it is suggested to install a resource addon for %s. \n Please install the resource addon(s) to your preference in the next dialog. You can always change your preference later in the skin settings." %addontypelabel)
                xbmc.executebuiltin("Skin.Reset(%s.path)" %setting)
                if ret:
                    xbmc.executebuiltin("ActivateWindow(AddonBrowser, addons://repository.xbmc.org/kodi.resource.images/)")
                    #wait untill the addon is installed...
                    count = 0
                    while checkResourceAddon(setting, addontype)==False and count !=120:
                        xbmc.sleep(1000)
                        if xbmc.abortRequested: return
