# -*- coding: utf-8 -*-
from utils import *
from artutils import ArtUtils

#Kodi contextmenu item to configure the artwork
if __name__ == '__main__':

    ##### PVR Artwork ########
    artwork = {}
    
    artutils = ArtUtils()
    
    log_msg("Context menu artwork settings for PVR artwork")
    WINDOW.setProperty("artworkcontextmenu", "busy")
    xbmc.executebuiltin("ActivateWindow(busydialog)")
    options=[]
    options.append(ADDON.getLocalizedString(32144)) #Refresh item (auto lookup)
    options.append(ADDON.getLocalizedString(32145)) #Refresh item (manual lookup)
    options.append(xbmc.getLocalizedString(13511)) #Choose art
    options.append(ADDON.getLocalizedString(32149)) #Add channel to ignore list
    options.append(ADDON.getLocalizedString(32150)) #Add title to ignore list
    options.append(ADDON.getLocalizedString(32148)) #Open addon settings
    header = ADDON.getLocalizedString(32143) + " - " + ADDON.getLocalizedString(32120)
    title = xbmc.getInfoLabel("ListItem.Title").decode('utf-8')
    if not title: title = xbmc.getInfoLabel("ListItem.Label").decode('utf-8')
    channel = xbmc.getInfoLabel("ListItem.ChannelName").decode('utf-8')
    genre = xbmc.getInfoLabel("ListItem.Genre").decode('utf-8')
    ret = xbmcgui.Dialog().select(header, options)
    if ret == 0:
        #Refresh item (auto lookup)
        artutils.get_pvr_artwork(title=title,channel=channel,genre=genre,ignore_cache=True, manual_select=False)
    elif ret == 1:
        #Refresh item (manual lookup)
        artutils.get_pvr_artwork(title=title,channel=channel,genre=genre,ignore_cache=True, manual_select=True)
    elif ret == 2:
        #Choose art
        artutils.pvrart.manual_set_pvr_artwork(title,channel,genre)

    elif ret == 3:
        #Add channel to ignore list
        ignorechannels = WINDOW.getProperty("SkinHelper.ignorechannels").decode("utf-8")
        if ignorechannels: ignorechannels += ";"
        ignorechannels += channel
        ADDON.setSetting("ignorechannels",ignorechannels)
        WINDOW.setProperty("SkinHelper.ignorechannels",ignorechannels)
        artwork = pvrart.get_pvr_artwork(title,channel,genre,ignore_cache=True, manual_select=False)
    elif ret == 4:
        #Add title to ignore list
        ignoretitles = WINDOW.getProperty("SkinHelper.ignoretitles").decode("utf-8")
        if ignoretitles: ignoretitles += ";"
        ignoretitles += title
        ADDON.setSetting("ignoretitles",ignoretitles)
        WINDOW.setProperty("SkinHelper.ignoretitles",ignoretitles)
        artwork = pvrart.get_pvr_artwork(title,channel,genre,ignore_cache=True, manual_select=False)
    elif ret == 5:
        #Open addon settings
        xbmc.executebuiltin("Addon.OpenSettings(script.skin.helper.service)")

    xbmc.executebuiltin("Dialog.Close(busydialog)")
    xbmc.sleep(500)
    xbmc.executebuiltin("Container.Refresh")
    xbmc.sleep(500)
    WINDOW.clearProperty("artworkcontextmenu")
