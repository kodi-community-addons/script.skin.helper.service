#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import log_msg
import xbmc
import time

class KodiMonitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        self.win = xbmcgui.Window(10000)
        
    def __del__(self):
        '''Cleanup Kodi Cpython instances'''
        del self.win
        log_msg("Exited")
    
    # def onDatabaseUpdated(self,database):
        # log_msg("Kodi_Monitor: onDatabaseUpdated: " + database)
        # if database == "video":
            # self.reset_video_widgets("",True)
            # artutils.preCacheAllAnimatedArt()
        # if database == "music" :
            # self.reset_music_widgets({},True)

    def onNotification(self,sender,method,data):

        log_msg("Kodi_Monitor: sender %s - method: %s  - data: %s"%(sender,method,data))

        if method == "System.OnQuit":
            self.win.setProperty("SkinHelperShutdownRequested","shutdown")

        if method == "VideoLibrary.OnUpdate":
            if not xbmc.getCondVisibility("Library.IsScanningVideo"):
                self.reset_video_widgets(data)

        if method == "AudioLibrary.OnUpdate":
            self.reset_music_widgets(data)

        if method == "Player.OnStop":
            self.win.clearProperty("Skinhelper.PlayerPlaying")
            self.win.clearProperty("TrailerPlaying")
            self.resetPlayerWindowProps()
            self.reset_video_widgets(data)
            self.reset_music_widgets(data)

        if method == "Player.OnPlay":
            #skip if the player is already playing
            if self.win.getProperty("Skinhelper.PlayerPlaying") == "playing": return
            try: secondsToDisplay = int(xbmc.getInfoLabel("Skin.String(SkinHelper.ShowInfoAtPlaybackStart)"))
            except Exception: return

            log_msg("onNotification - ShowInfoAtPlaybackStart - number of seconds: " + str(secondsToDisplay))
            self.win.setProperty("Skinhelper.PlayerPlaying","playing")
            #Show the OSD info panel on playback start
            if secondsToDisplay != 0:
                tryCount = 0
                if self.win.getProperty("VideoScreensaverRunning") != "true":
                    while tryCount !=50 and xbmc.getCondVisibility("!Player.ShowInfo"):
                        xbmc.sleep(100)
                        if xbmc.getCondVisibility("!Player.ShowInfo + Window.IsActive(fullscreenvideo)"):
                            xbmc.executebuiltin('Action(info)')
                        tryCount += 1

                    # close info again
                    self.waitForAbort(secondsToDisplay)
                    if xbmc.getCondVisibility("Player.ShowInfo"):
                        xbmc.executebuiltin('Action(info)')

    def reset_music_widgets(self,data,resetAll=False):
        #clear the cache for the music widgets
        type = "unknown"
        if data:
            data = eval(data.replace("true","True").replace("false","False"))
            type = data.get("type","")
        else:
            data = {}

        if (type in ["song","artist","album"] or resetAll and not self.win.getProperty("SkinHelperShutdownRequested")):
            #artutils.updateMusicArt(type,data.get("id"))
            if not xbmc.getCondVisibility("Library.IsScanningMusic"):
                log_msg("Music database changed - type: %s - resetAll: %s, refreshing widgets...." %(type,resetAll))
                timestr = time.strftime("%Y%m%d%H%M%S", time.gmtime())
                self.win.setProperty("widgetreloadmusic", timestr)
    
    def reset_video_widgets(self,data="",resetAll=False):
        #clear the cache for the video widgets
        type = "unknown"
        id = None
        if data:
            data = eval(data.replace("true","True").replace("false","False"))
            if data and data.get("item"):
                type = data["item"].get("type","unknown")
                id = data["item"].get("id",None)

        if (type in ["movie","tvshow","episode"] and not self.win.getProperty("skinhelper-refreshvideowidgetsbusy")) or resetAll:
            log_msg("Video database changed - type: %s - resetAll: %s, refreshing widgets...." %(type,resetAll))
            self.win.setProperty("skinhelper-refreshvideowidgetsbusy","busy")
            timestr = time.strftime("%Y%m%d%H%M%S", time.gmtime())
            #reset specific widgets, based on item that is updated
            if resetAll or type=="movie":
                self.win.setProperty("widgetreload-movies", timestr)
            if resetAll or type=="episode":
                self.win.setProperty("widgetreload-episodes", timestr)
            if resetAll or type=="tvshow":
                self.win.setProperty("widgetreload-tvshows", timestr)
            self.win.setProperty("widgetreload", timestr)
            self.win.clearProperty("skinhelper-refreshvideowidgetsbusy")
            if id:
                #refresh cache for specific item
                artutils.getStreamDetails(id,type,ignoreCache=True)

    def resetPlayerWindowProps(self):
        #reset all window props provided by the script...
        self.win.setProperty("SkinHelper.Player.Music.Banner","")
        self.win.setProperty("SkinHelper.Player.Music.ClearLogo","")
        self.win.setProperty("SkinHelper.Player.Music.DiscArt","")
        self.win.setProperty("SkinHelper.Player.Music.FanArt","")
        self.win.setProperty("SkinHelper.Player.Music.Thumb","")
        self.win.setProperty("SkinHelper.Player.Music.ArtistThumb","")
        self.win.setProperty("SkinHelper.Player.Music.AlbumThumb","")
        self.win.setProperty("SkinHelper.Player.Music.Info","")
        self.win.setProperty("SkinHelper.Player.Music.TrackList","")
        self.win.setProperty("SkinHelper.Player.Music.SongCount","")
        self.win.setProperty("SkinHelper.Player.Music.albumCount","")
        self.win.setProperty("SkinHelper.Player.Music.AlbumList","")
        self.win.setProperty("SkinHelper.Player.Music.ExtraFanArt","")