#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import log_msg as log_msg, WINDOW
import xbmc
import time

class KodiMonitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
    
    # def onDatabaseUpdated(self,database):
        # log_msg("Kodi_Monitor: onDatabaseUpdated: " + database)
        # if database == "video":
            # self.resetVideoWidgetProps("",True)
            # artutils.preCacheAllAnimatedArt()
        # if database == "music" :
            # self.resetMusicWidgetProps({},True)

    def onNotification(self,sender,method,data):

        log_msg("Kodi_Monitor: sender %s - method: %s  - data: %s"%(sender,method,data))

        if method == "System.OnQuit":
            WINDOW.setProperty("SkinHelperShutdownRequested","shutdown")

        if method == "VideoLibrary.OnUpdate":
            if not xbmc.getCondVisibility("Library.IsScanningVideo"):
                self.resetVideoWidgetProps(data)

        if method == "AudioLibrary.OnUpdate":
            self.resetMusicWidgetProps(data)

        if method == "Player.OnStop":
            WINDOW.clearProperty("Skinhelper.PlayerPlaying")
            WINDOW.clearProperty("TrailerPlaying")
            self.resetPlayerWindowProps()
            self.resetVideoWidgetProps(data)
            self.resetMusicWidgetProps(data)

        if method == "Player.OnPlay":
            #skip if the player is already playing
            if WINDOW.getProperty("Skinhelper.PlayerPlaying") == "playing": return
            try: secondsToDisplay = int(xbmc.getInfoLabel("Skin.String(SkinHelper.ShowInfoAtPlaybackStart)"))
            except Exception: return

            log_msg("onNotification - ShowInfoAtPlaybackStart - number of seconds: " + str(secondsToDisplay))
            WINDOW.setProperty("Skinhelper.PlayerPlaying","playing")
            #Show the OSD info panel on playback start
            if secondsToDisplay != 0:
                tryCount = 0
                if WINDOW.getProperty("VideoScreensaverRunning") != "true":
                    while tryCount !=50 and xbmc.getCondVisibility("!Player.ShowInfo"):
                        xbmc.sleep(100)
                        if xbmc.getCondVisibility("!Player.ShowInfo + Window.IsActive(fullscreenvideo)"):
                            xbmc.executebuiltin('Action(info)')
                        tryCount += 1

                    # close info again
                    self.waitForAbort(secondsToDisplay)
                    if xbmc.getCondVisibility("Player.ShowInfo"):
                        xbmc.executebuiltin('Action(info)')

    def resetMusicWidgetProps(self,data,resetAll=False):
        #clear the cache for the music widgets
        type = "unknown"
        if data:
            data = eval(data.replace("true","True").replace("false","False"))
            type = data.get("type","")
        else:
            data = {}

        if (type in ["song","artist","album"] or resetAll and not WINDOW.getProperty("SkinHelperShutdownRequested")):
            #artutils.updateMusicArt(type,data.get("id"))
            if not xbmc.getCondVisibility("Library.IsScanningMusic"):
                log_msg("Music database changed - type: %s - resetAll: %s, refreshing widgets...." %(type,resetAll))
                timestr = time.strftime("%Y%m%d%H%M%S", time.gmtime())
                WINDOW.setProperty("widgetreloadmusic", timestr)
    
    def resetVideoWidgetProps(self,data="",resetAll=False):
        #clear the cache for the video widgets
        type = "unknown"
        id = None
        if data:
            data = eval(data.replace("true","True").replace("false","False"))
            if data and data.get("item"):
                type = data["item"].get("type","unknown")
                id = data["item"].get("id",None)

        if (type in ["movie","tvshow","episode"] and not WINDOW.getProperty("skinhelper-refreshvideowidgetsbusy")) or resetAll:
            log_msg("Video database changed - type: %s - resetAll: %s, refreshing widgets...." %(type,resetAll))
            WINDOW.setProperty("skinhelper-refreshvideowidgetsbusy","busy")
            timestr = time.strftime("%Y%m%d%H%M%S", time.gmtime())
            #reset specific widgets, based on item that is updated
            if resetAll or type=="movie":
                WINDOW.setProperty("widgetreload-movies", timestr)
            if resetAll or type=="episode":
                WINDOW.setProperty("widgetreload-episodes", timestr)
            if resetAll or type=="tvshow":
                WINDOW.setProperty("widgetreload-tvshows", timestr)
            WINDOW.setProperty("widgetreload", timestr)
            WINDOW.clearProperty("skinhelper-refreshvideowidgetsbusy")
            if id:
                #refresh cache for specific item
                artutils.getStreamDetails(id,type,ignoreCache=True)

    def resetPlayerWindowProps(self):
        #reset all window props provided by the script...
        WINDOW.setProperty("SkinHelper.Player.Music.Banner","")
        WINDOW.setProperty("SkinHelper.Player.Music.ClearLogo","")
        WINDOW.setProperty("SkinHelper.Player.Music.DiscArt","")
        WINDOW.setProperty("SkinHelper.Player.Music.FanArt","")
        WINDOW.setProperty("SkinHelper.Player.Music.Thumb","")
        WINDOW.setProperty("SkinHelper.Player.Music.ArtistThumb","")
        WINDOW.setProperty("SkinHelper.Player.Music.AlbumThumb","")
        WINDOW.setProperty("SkinHelper.Player.Music.Info","")
        WINDOW.setProperty("SkinHelper.Player.Music.TrackList","")
        WINDOW.setProperty("SkinHelper.Player.Music.SongCount","")
        WINDOW.setProperty("SkinHelper.Player.Music.albumCount","")
        WINDOW.setProperty("SkinHelper.Player.Music.AlbumList","")
        WINDOW.setProperty("SkinHelper.Player.Music.ExtraFanArt","")