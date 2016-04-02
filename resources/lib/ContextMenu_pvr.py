# -*- coding: utf-8 -*-
from Utils import *
import ArtworkUtils as artworkutils

#Kodi contextmenu item to configure the artwork 
if __name__ == '__main__':
    
    ##### PVR Artwork ########
    artwork = {}
    logMsg("Context menu artwork settings for PVR artwork",0)
    WINDOW.setProperty("artworkcontextmenu", "busy")
    options=[]
    options.append(ADDON.getLocalizedString(32144)) #Refresh item (auto lookup)
    options.append(ADDON.getLocalizedString(32145)) #Refresh item (manual lookup)
    options.append(ADDON.getLocalizedString(32149)) #Add channel to ignore list
    options.append(ADDON.getLocalizedString(32150)) #Add title to ignore list
    options.append(ADDON.getLocalizedString(32148)) #Open addon settings
    header = ADDON.getLocalizedString(32143) + " - " + ADDON.getLocalizedString(32120)
    title = xbmc.getInfoLabel("ListItem.Title").decode('utf-8')
    if not title: title = xbmc.getInfoLabel("ListItem.Label").decode('utf-8')
    channel = xbmc.getInfoLabel("ListItem.ChannelName").decode('utf-8')
    path = xbmc.getInfoLabel("ListItem.FileNameAndPath").decode('utf-8')
    genre = xbmc.getInfoLabel("ListItem.Genre").decode('utf-8')
    year = xbmc.getInfoLabel("ListItem.Year").decode('utf-8')
    ret = xbmcgui.Dialog().select(header, options)
    if ret == 0:
        #Refresh item (auto lookup)
        artwork = artworkutils.getPVRThumbs(title,channel,type,path,genre,year,ignoreCache=True, manualLookup=False)
    elif ret == 1:
        #Refresh item (manual lookup)
        artwork = artworkutils.getPVRThumbs(title,channel,type,path,genre,year,ignoreCache=True, manualLookup=True)
    elif ret == 2:
        #Add channel to ignore list
        ignorechannels = WINDOW.getProperty("SkinHelper.ignorechannels").decode("utf-8")
        if ignorechannels: ignorechannels += ";"
        ignorechannels += channel
        ADDON.setSetting("ignorechannels",ignorechannels)
        WINDOW.setProperty("SkinHelper.ignorechannels",ignorechannels)
        artwork = artworkutils.getPVRThumbs(title,channel,type,path,genre,year,ignoreCache=True, manualLookup=False)
    elif ret == 3:
        #Add title to ignore list
        ignoretitles = WINDOW.getProperty("SkinHelper.ignoretitles").decode("utf-8")
        if ignoretitles: ignoretitles += ";"
        ignoretitles += title
        ADDON.setSetting("ignoretitles",ignoretitles)
        WINDOW.setProperty("SkinHelper.ignoretitles",ignoretitles)
        artwork = artworkutils.getPVRThumbs(title,channel,type,path,genre,year,ignoreCache=True, manualLookup=False)
    elif ret == 4:
        #Open addon settings
        xbmc.executebuiltin("Addon.OpenSettings(script.skin.helper.service)")
        
    #flush properties and set new ones (if any)
    if artwork or ret==2 or ret==3:
        xbmc.sleep(150)
        WINDOW.setProperty("resetPvrArtCache","reset")
        WINDOW.clearProperty("SkinHelper.PVR.Thumb") 
        WINDOW.clearProperty("SkinHelper.PVR.FanArt") 
        WINDOW.clearProperty("SkinHelper.PVR.ChannelLogo")
        WINDOW.clearProperty("SkinHelper.PVR.Poster")
        WINDOW.clearProperty("SkinHelper.PVR.Landscape")
        WINDOW.clearProperty("SkinHelper.PVR.ClearArt")
        WINDOW.clearProperty("SkinHelper.PVR.CharacterArt") 
        WINDOW.clearProperty("SkinHelper.PVR.ClearLogo")
        WINDOW.clearProperty("SkinHelper.PVR.Banner")
        WINDOW.clearProperty("SkinHelper.PVR.DiscArt")
        WINDOW.clearProperty("SkinHelper.PVR.Plot")
        WINDOW.clearProperty("SkinHelper.PVR.Channel")
        WINDOW.clearProperty("SkinHelper.PVR.Genre")
        WINDOW.clearProperty("SkinHelper.PVR.ExtraFanArt")
        #set new properties
        for key, value in artwork.iteritems():
            WINDOW.setProperty("SkinHelper.PVR." + key,value)
    WINDOW.clearProperty("artworkcontextmenu")
