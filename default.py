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
        
        logMsg("Parameter string: " + str(params),0)
        return params
    
    def __init__(self):
        
        logMsg('started loading script entry',0)
        params = self.getParams()
        
        if params:
            action = params.get("ACTION",None)

            elif action =="ADDSHORTCUT":
                addShortcutWorkAround()
            
            elif action == "SHOWINFO":
                ## TODO --> MOVE TO SERVICE !
                pass
            
            elif action == "MUSICSEARCH":
                musicSearch()
            
            elif action == "SETVIEW":
                setView()
            
            elif action == "SEARCHTRAILER":
                title = params.get("TITLE",None)
                searchTrailer(title)
            
            elif action == "SETFORCEDVIEW":
                contenttype = params.get("CONTENTTYPE",None)
                setForcedView(contenttype)    
            
            elif action == "ENABLEVIEWS":
                enableViews()
            
            elif action == "VIDEOSEARCH":
                from resources.lib.SearchDialog import SearchDialog
                searchDialog = SearchDialog("script-skin_helper_service-CustomSearch.xml", __cwd__, "default", "1080i")
                searchDialog.doModal()
                del searchDialog
            
            elif action == "COLORPICKER":
                from resources.lib.ColorPicker import ColorPicker
                colorPicker = ColorPicker("script-skin_helper_service-ColorPicker.xml", __cwd__, "default", "1080i")
                colorPicker.skinStringName = params.get("SKINSTRINGNAME",None)
                colorPicker.skinStringValue = params.get("SKINSTRINGVALUE",None)
                colorPicker.doModal()
                del colorPicker
            
            elif action == "COLORTHEMES":
                from resources.lib.ColorThemes import ColorThemes
                colorThemes = ColorThemes("script-skin_helper_service-ColorThemes.xml", __cwd__, "default", "1080i")
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
                import resources.lib.BackupRestore
                BackupRestore.backup()
            
            elif action == "RESTORE":
                import resources.lib.BackupRestore
                BackupRestore.restore()
            
            elif action == "RESET":
                import resources.lib.BackupRestore
                BackupRestore.reset()


if (__name__ == "__main__"):
    Main()
logMsg('finished loading script entry',0)
