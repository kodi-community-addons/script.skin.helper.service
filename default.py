#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcplugin
import xbmcgui
import shutil

from resources.lib.Utils import *
from resources.lib.MainModule import *

class Main:
    
    def getParams(self):
        #extract the params from the called script path
        params = {}
        for arg in sys.argv:
            if arg == 'script.skin.helper.service' or arg == 'default.py':
                continue
            arg = arg.replace('"', '').replace("'", " ").replace("?", "")
            if "=" in arg:
                paramname = arg.split('=')[0].upper()
                paramvalue = arg.split('=')[1]
                params[paramname] = paramvalue
        
        logMsg("Parameter string: " + str(params))
        return params
    
    def __init__(self):
        
        logMsg('started loading script entry')
        params = self.getParams()
        
        if params:
            action = params.get("ACTION","").upper()

            if action =="ADDSHORTCUT":
                addShortcutWorkAround()
            
            elif action == "MUSICSEARCH":
                musicSearch()
            
            elif action == "SETVIEW":
                setView()
            
            elif action == "SEARCHYOUTUBE":
                title = params.get("TITLE",None)
                windowHeader = params.get("HEADER","")
                searchYouTube(title,windowHeader)
            
            elif action == "SETFORCEDVIEW":
                contenttype = params.get("CONTENTTYPE",None)
                setForcedView(contenttype)
            
            elif action == "TOGGLEKODISETTING":
                kodisetting = params.get("SETTING")
                toggleKodiSetting(kodisetting)
            
            elif action == "ENABLEVIEWS":
                enableViews()
            
            elif action == "VIDEOSEARCH":
                from resources.lib.SearchDialog import SearchDialog
                searchDialog = SearchDialog("script-skin_helper_service-CustomSearch.xml", ADDON_PATH, "Default", "1080i")
                searchDialog.doModal()
                del searchDialog
            
            elif action == "COLORPICKER":
                from resources.lib.ColorPicker import ColorPicker
                colorPicker = ColorPicker("script-skin_helper_service-ColorPicker.xml", ADDON_PATH, "Default", "1080i")
                colorPicker.skinString = params.get("SKINSTRING",None)
                colorPicker.winProperty = params.get("WINPROPERTY",None)
                colorPicker.shortcutProperty = params.get("SHORTCUTPROPERTY",None)
                colorPicker.doModal()
                propname = params.get("SHORTCUTPROPERTY",None)
                if propname:
                    wid = xbmcgui.getCurrentWindowDialogId()
                    currentWindow = xbmcgui.Window( xbmcgui.getCurrentWindowDialogId() )
                    currentWindow.setProperty("customProperty",propname)
                    currentWindow.setProperty("customValue",colorPicker.result[0])
                    xbmc.executebuiltin("SendClick(404)")
                    xbmc.sleep(250)
                    currentWindow.setProperty("customProperty",propname+".name")
                    currentWindow.setProperty("customValue",colorPicker.result[1])
                    xbmc.executebuiltin("SendClick(404)")
                del colorPicker
            
            elif action == "COLORTHEMES":
                from resources.lib.ColorThemes import ColorThemes
                colorThemes = ColorThemes("DialogSelect.xml", ADDON_PATH)
                colorThemes.daynight = params.get("DAYNIGHT",None)
                colorThemes.doModal()
                del colorThemes
            
            elif action == "CONDITIONALBACKGROUNDS":
                from resources.lib.ConditionalBackgrounds import ConditionalBackgrounds
                conditionalBackgrounds = ConditionalBackgrounds("DialogSelect.xml", ADDON_PATH)
                conditionalBackgrounds.doModal()
                del conditionalBackgrounds
            
            elif action == "CREATECOLORTHEME":
                import resources.lib.ColorThemes as colorThemes
                colorThemes.createColorTheme()
            
            elif action == "RESTORECOLORTHEME":
                import resources.lib.ColorThemes as colorThemes
                colorThemes.restoreColorTheme()
            
            elif action == "OVERLAYTEXTURE":    
                selectOverlayTexture()
            
            elif action == "BUSYTEXTURE":    
                selectBusyTexture()

            elif action == "RESETPVRTHUMBS":
                path = WINDOW.getProperty("pvrthumbspath").decode("utf-8")
                WINDOW.setProperty("resetPvrArtCache","reset")
                success = True
                ret = xbmcgui.Dialog().yesno(heading=ADDON.getLocalizedString(32089), line1=ADDON.getLocalizedString(32090)+path)
                if ret:
                    dirs, files = xbmcvfs.listdir(path)
                    for file in files:
                        success = xbmcvfs.delete(os.path.join(path,file))
                    for dir in dirs:
                        dirs2, files2 = xbmcvfs.listdir(os.path.join(path,dir))
                        for file in files2:
                            success = xbmcvfs.delete(os.path.join(path,dir,file))
                        success = xbmcvfs.rmdir(os.path.join(path,dir))
                    if success:
                        xbmcgui.Dialog().ok(heading=ADDON.getLocalizedString(32089), line1=ADDON.getLocalizedString(32091))
                    else:
                        xbmcgui.Dialog().ok(heading=ADDON.getLocalizedString(32089), line1=ADDON.getLocalizedString(32092))
                    
            
            elif action == "BACKUP":
                import resources.lib.BackupRestore as backup
                filter = params.get("FILTER","")
                silent = params.get("SILENT",None)
                promptfilename = params.get("PROMPTFILENAME","false")
                backup.backup(filter,silent,promptfilename.lower())
            
            elif action == "RESTORE":
                import resources.lib.BackupRestore as backup
                silent = params.get("SILENT",None)
                backup.restore(silent)
            
            elif action == "RESET":
                import resources.lib.BackupRestore as backup
                backup.reset()


if (__name__ == "__main__"):
    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
    Main()
    
logMsg('finished loading script entry')
