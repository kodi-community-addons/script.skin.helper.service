# -*- coding: utf-8 -*-
from Utils import *
import ArtworkUtils as artworkutils

#Kodi contextmenu item to configure the artwork 
if __name__ == '__main__':
    
    #### Animated artwork #######
    logMsg("Context menu artwork settings for Animated artwork",0)
    options=[]
    options.append(ADDON.getLocalizedString(32173)) #animated poster
    options.append(ADDON.getLocalizedString(32174)) #animated fanart
    header = ADDON.getLocalizedString(32143)
    ret = xbmcgui.Dialog().select(header, options)
    if ret == 0 or ret == 1:
        if ret == 0: type = "poster"
        if ret == 1: type = "fanart"
    
    liImdb = xbmc.getInfoLabel("ListItem.IMDBNumber")
    liDbId = xbmc.getInfoLabel("ListItem.DBID")
    if liImdb and WINDOW.getProperty("contenttype") in ["movies","setmovies"]:
        image = artworkutils.getAnimatedArtwork(liImdb,type,liDbId,options[ret])
        WINDOW.setProperty("SkinHelper.Animated%s"%type,"DefaultMovieTitle.png")
        xbmc.sleep(150)
        WINDOW.setProperty("SkinHelper.Animated%s"%type,image)
    WINDOW.setProperty("resetExtendedInfoCache", "reset")
    xbmc.executebuiltin("Container.Refresh")
    xbmcgui.Dialog().notification('Needs restart', 'Kodi restart might be needed to apply these changes', xbmcgui.NOTIFICATION_INFO, 5000)
        