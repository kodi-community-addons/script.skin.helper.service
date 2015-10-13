#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmc
from datetime import datetime
from random import randint
from Utils import *

class Kodi_Monitor(xbmc.Monitor):
    
    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
    
    def onSettingsChanged(self):
        setAddonsettings()
        logMsg("onNotification - Addon settings changed!")
        WINDOW.setProperty("resetPvrArtCache","reset")

    def resetMusicWidgets(self):
        #clear the cache for the music widgets
        WINDOW.clearProperty("skinhelper-recentalbums")
        WINDOW.clearProperty("skinhelper-recentplayedalbums")
        WINDOW.clearProperty("skinhelper-recentplayedsongs")
        WINDOW.clearProperty("skinhelper-recentsongs")
    
    def resetVideoWidgets(self):
        #clear the cache for the video widgets
        WINDOW.clearProperty("skinhelper-recommendedmovies")
        WINDOW.clearProperty("skinhelper-InProgressAndRecommendedMedia")
        WINDOW.clearProperty("skinhelper-InProgressMedia")
        WINDOW.clearProperty("skinhelper-RecommendedMedia")
        WINDOW.clearProperty("skinhelper-nextepisodes")
        WINDOW.clearProperty("skinhelper-similarmovies")
        WINDOW.clearProperty("skinhelper-recentmedia")
        WINDOW.clearProperty("skinhelper-favouritemedia")
    
    def onDatabaseUpdated(self,database):
        if database == "video":
            self.resetVideoWidgets()
            WINDOW.setProperty("widgetreload", datetime.now().strftime('%Y-%m-%d %H:%M:%S') + str(randint(0,9)))
            WINDOW.setProperty("resetVideoDbCache","reset")
        if database == "music" :
            self.resetMusicWidgets()
            WINDOW.setProperty("widgetreloadmusic", datetime.now().strftime('%Y-%m-%d %H:%M:%S') + str(randint(0,9)))
            WINDOW.setProperty("resetMusicArtCache","reset")
           
    def onNotification(self,sender,method,data):
        
        logMsg("Kodi_Monitor: sender %s - method: %s  - data: %s"%(sender,method,data))
               
        if method == "VideoLibrary.OnUpdate":
            #update nextup list when library has changed
            self.resetVideoWidgets()
            WINDOW.setProperty("widgetreload", datetime.now().strftime('%Y-%m-%d %H:%M:%S') + str(randint(0,9)))
            #refresh some widgets when library has changed
            WINDOW.setProperty("resetVideoDbCache","reset")
        
        elif method == "AudioLibrary.OnUpdate":
            self.resetMusicWidgets()
            WINDOW.setProperty("widgetreloadmusic", datetime.now().strftime('%Y-%m-%d %H:%M:%S') + str(randint(0,9)))
            #refresh some widgets when library has changed
            WINDOW.setProperty("resetMusicArtCache","reset")
        
        elif method == "Player.OnStop":
            WINDOW.clearProperty("Skinhelper.PlayerPlaying")
        
        elif method == "Player.OnPlay":
            
            #skip if the player is already playing
            if WINDOW.getProperty("Skinhelper.PlayerPlaying") == "playing": return
            try: secondsToDisplay = int(xbmc.getInfoLabel("Skin.String(SkinHelper.ShowInfoAtPlaybackStart)"))
            except: return
            
            logMsg("onNotification - ShowInfoAtPlaybackStart - number of seconds: " + str(secondsToDisplay))
            WINDOW.setProperty("Skinhelper.PlayerPlaying","playing")
            #Show the OSD info panel on playback start
            if secondsToDisplay != 0:
                tryCount = 0
                if WINDOW.getProperty("VideoScreensaverRunning") != "true":
                    while tryCount !=50 and xbmc.getCondVisibility("!Window.IsActive(fullscreeninfo)"):
                        xbmc.sleep(100)
                        if xbmc.getCondVisibility("!Window.IsActive(fullscreeninfo) + Window.IsActive(fullscreenvideo)"):
                            xbmc.executebuiltin('Action(info)')
                        tryCount += 1
                    
                    # close info again
                    xbmc.sleep(secondsToDisplay*1000)
                    if xbmc.getCondVisibility("Window.IsActive(fullscreeninfo)"):
                        xbmc.executebuiltin('Action(info)')