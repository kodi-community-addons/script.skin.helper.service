#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
import xbmcplugin
import xbmcgui

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
                paramvalue = arg.split('=')[1].upper()
                params[paramname] = paramvalue
        
        logMsg("Parameter string: " + str(params))
        return params
    
    def __init__(self):
        
        logMsg('started loading script entry',0)
        params = self.getParams()
        
        if params:
            action = params.get("ACTION",None)

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
            
            elif action == "ENABLEVIEWS":
                enableViews()
            
            elif action == "VIDEOSEARCH":
                from resources.lib.SearchDialog import SearchDialog
                searchDialog = SearchDialog("script-skin_helper_service-CustomSearch.xml", ADDON_PATH, "default", "1080i")
                searchDialog.doModal()
                del searchDialog
            
            elif action == "COLORPICKER":
                from resources.lib.ColorPicker import ColorPicker
                colorPicker = ColorPicker("script-skin_helper_service-ColorPicker.xml", ADDON_PATH, "Default", "1080i")
                colorPicker.skinString = params.get("SKINSTRING",None)
                colorPicker.doModal()
                del colorPicker
            
            elif action == "COLORTHEMES":
                from resources.lib.ColorThemes import ColorThemes
                colorThemes = ColorThemes("DialogSelect.xml", ADDON_PATH)
                colorThemes.doModal()
                del colorThemes
            
            elif action == "CREATECOLORTHEME":
                import resources.lib.ColorThemes as colorThemes
                colorThemes.createColorTheme()
            
            elif action == "RESTORECOLORTHEME":
                import resources.lib.ColorThemes as colorThemes
                colorThemes.restoreColorTheme()
            
            elif action == "COLORTHEMETEXTURE":    
                selectOverlayTexture()
            
            elif action == "BUSYTEXTURE":    
                selectBusyTexture()     
            
            elif action == "BACKUP":
                import resources.lib.BackupRestore as backup
                filter = params.get("FILTER",None)
                backup.backup(filter)
            
            elif action == "RESTORE":
                import resources.lib.BackupRestore as backup
                backup.restore()
            
            elif action == "RESET":
                import resources.lib.BackupRestore as backup
                backup.reset()


if (__name__ == "__main__"):
    Main()
logMsg('finished loading script entry')
