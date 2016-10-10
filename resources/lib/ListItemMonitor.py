#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading, thread
import requests
import random
from Utils import *
import ArtworkUtils as artutils
import StudioLogos as studiologos
import simplecache


class ListItemMonitor(threading.Thread):

    event = None
    exit = False
    delayedTaskInterval = 1795
    lastWeatherNotificationCheck = None
    lastNextAiredNotificationCheck = None
    widgetContainerPrefix = ""
    liPath = ""
    liFile = ""
    liLabel = ""
    liTitle = ""
    liDbId = ""
    liImdb = ""
    unwatched = 1
    contentType = ""
    widgetTaskInterval = 520
    moviesetCache = {}
    tmdbinfocache = {}
    omdbinfocache = {}
    imdb_top250 = {}
    allWindowProps = []
    allPlayerWindowProps = []
    cachePath = os.path.join(ADDON_DATA_PATH,"librarycache.json")
    ActorImagesCachePath = os.path.join(ADDON_DATA_PATH,"actorimages.json")

    def __init__(self, *args):
        logMsg("ListItemMonitor - started")
        self.event =  threading.Event()
        self.monitor = xbmc.Monitor()
        threading.Thread.__init__(self, *args)

    def stop(self):
        logMsg("ListItemMonitor - stop called")
        self.saveCacheToFile()
        self.exit = True
        self.event.set()

    def run(self):

        setAddonsettings()
        self.getCacheFromFile()
        playerTitle = ""
        playerFile = ""
        lastPlayerItem = ""
        playerItem = ""
        liPathLast = ""
        curFolder = ""
        curFolderLast = ""
        lastListItem = ""
        nextairedActive = False
        screenSaverSetting = None
        screenSaverDisableActive = False

        while (self.exit != True):

            if xbmc.getCondVisibility("Player.HasAudio"):
                #set window props for music player
                try:
                    playerTitle = xbmc.getInfoLabel("Player.Title").decode('utf-8')
                    playerFile = xbmc.getInfoLabel("Player.Filenameandpath").decode('utf-8')
                    playerItem = playerTitle + playerFile
                    #only perform actions when the listitem has actually changed
                    if playerItem and playerItem != lastPlayerItem:
                        #clear all window props first
                        self.resetPlayerWindowProps()
                        self.setMusicPlayerDetails()
                        lastPlayerItem = playerItem
                except Exception as e:
                    logMsg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)
                    logMsg("ERROR in setMusicPlayerDetails ! --> %s" %e, xbmc.LOGERROR)
            elif lastPlayerItem:
                #cleanup remaining window props
                self.resetPlayerWindowProps()
                playerItem = ""
                lastPlayerItem = ""

            #disable the screensaver if fullscreen music playback
            if xbmc.getCondVisibility("Window.IsActive(visualisation) + Skin.HasSetting(SkinHelper.DisableScreenSaverOnFullScreenMusic)") and not screenSaverDisableActive:
                screenSaverSetting = getJSON('Settings.GetSettingValue', '{"setting":"screensaver.mode"}')
                setJSON('Settings.SetSettingValue', '{"setting":"screensaver.mode", "value": ""}')
                screenSaverDisableActive = True
                logMsg("Disabled screensaver while fullscreen music playback - previous setting: %s" %screenSaverSetting)
            elif screenSaverSetting and screenSaverDisableActive:
                setJSON('Settings.SetSettingValue', '{"setting":"screensaver.mode", "value": "%s"}' %screenSaverSetting)
                screenSaverDisableActive = False
                logMsg("fullscreen music playback ended - restoring screensaver: %s" %screenSaverSetting)

            #auto close OSD after X seconds of inactivity
            if xbmc.getCondVisibility("Window.IsActive(videoosd) | Window.IsActive(musicosd)"):
                if xbmc.getCondVisibility("Window.IsActive(videoosd)"):
                    secondsToDisplay = xbmc.getInfoLabel("Skin.String(SkinHelper.AutoCloseVideoOSD)")
                    window = "videoosd"
                elif xbmc.getCondVisibility("Window.IsActive(musicosd)"):
                    secondsToDisplay = xbmc.getInfoLabel("Skin.String(SkinHelper.AutoCloseMusicOSD)")
                    window = "musicosd"
                else:
                    secondsToDisplay = ""

                if secondsToDisplay and secondsToDisplay != "0":
                    while xbmc.getCondVisibility("Window.IsActive(%s)"%window):
                        if xbmc.getCondVisibility("System.IdleTime(%s)" %secondsToDisplay):
                            if xbmc.getCondVisibility("Window.IsActive(%s)"%window):
                                xbmc.executebuiltin("Dialog.Close(%s)" %window)
                        else:
                            xbmc.sleep(500)

            #do some background stuff every 30 minutes
            if self.delayedTaskInterval >= 1800 and not self.exit:
                thread.start_new_thread(self.doBackgroundWork, ())
                self.delayedTaskInterval = 0

            #reload some widgets every 10 minutes
            if self.widgetTaskInterval >= 600 and not self.exit:
                self.resetGlobalWidgetWindowProps()
                self.widgetTaskInterval = 0

            if xbmc.getCondVisibility("System.HasModalDialog | Window.IsActive(progressdialog) | Window.IsActive(busydialog) | !IsEmpty(Window(Home).Property(TrailerPlaying))"):
                #skip when modal dialogs are opened (e.g. textviewer in musicinfo dialog)
                self.monitor.waitForAbort(1)
                self.delayedTaskInterval += 1
                self.widgetTaskInterval += 1
            elif xbmc.getCondVisibility("[Window.IsMedia | !IsEmpty(Window(Home).Property(SkinHelper.WidgetContainer))]") and not self.exit:
                try:
                    widgetContainer = WINDOW.getProperty("SkinHelper.WidgetContainer").decode('utf-8')
                    if xbmc.getCondVisibility("Window.IsActive(movieinformation)"):
                        self.widgetContainerPrefix = ""
                        curFolder = xbmc.getInfoLabel("movieinfo-$INFO[Container.FolderPath]$INFO[Container.NumItems]$INFO[Container.Content]").decode('utf-8')
                    elif widgetContainer:
                        self.widgetContainerPrefix = "Container(%s)."%widgetContainer
                        curFolder = xbmc.getInfoLabel("widget-%s-$INFO[Container(%s).NumItems]" %(widgetContainer,widgetContainer)).decode('utf-8')
                    else:
                        self.widgetContainerPrefix = ""
                        curFolder = xbmc.getInfoLabel("$INFO[Container.FolderPath]$INFO[Container.NumItems]$INFO[Container.Content]").decode('utf-8')
                    self.liTitle = xbmc.getInfoLabel("%sListItem.Title" %self.widgetContainerPrefix).decode('utf-8')
                    self.liLabel = xbmc.getInfoLabel("%sListItem.Label" %self.widgetContainerPrefix).decode('utf-8')
                except Exception as e:
                    logMsg(str(e),0)
                    curFolder = ""
                    self.liLabel = ""
                    self.liTitle = ""

                #perform actions if the container path has changed
                if (curFolder != curFolderLast):
                    self.resetWindowProps()
                    self.contentType = ""
                    curFolderLast = curFolder
                    if curFolder and self.liLabel:
                        #always wait for the contentType because plugins can be slow
                        for i in range(20):
                            self.contentType = getCurrentContentType(self.widgetContainerPrefix)
                            if self.contentType: break
                            else: xbmc.sleep(250)
                        if not self.widgetContainerPrefix and self.contentType:
                            self.setForcedView()
                            self.setContentHeader()
                        WINDOW.setProperty("contenttype",self.contentType)

                curListItem ="%s--%s--%s--%s" %(curFolder, self.liLabel, self.liTitle, self.contentType)

                #only perform actions when the listitem has actually changed
                if curListItem and curListItem != lastListItem and self.contentType:
                    #clear all window props first
                    self.resetWindowProps()
                    self.setWindowProp("curListItem",curListItem)

                    #widget properties
                    if self.widgetContainerPrefix:
                        self.setWidgetDetails()

                    #generic props
                    self.liPath = xbmc.getInfoLabel("%sListItem.Path" %self.widgetContainerPrefix).decode('utf-8')
                    if not self.liPath: self.liPath = xbmc.getInfoLabel("%sListItem.FolderPath" %self.widgetContainerPrefix).decode('utf-8')
                    self.liFile = xbmc.getInfoLabel("%sListItem.FileNameAndPath" %self.widgetContainerPrefix).decode('utf-8')
                    self.liDbId = ""
                    self.liImdb = ""

                    if not self.liLabel == "..":
                        # monitor listitem props for music content
                        if self.contentType in ["albums","artists","songs"]:
                            try:
                                thread.start_new_thread(self.setMusicDetails, (True,))
                                self.setGenre()
                            except Exception as e:
                                logMsg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)
                                logMsg("ERROR in setMusicDetails ! --> %s" %e, xbmc.LOGERROR)

                        # monitor listitem props for video content
                        elif self.contentType in ["movies","setmovies","tvshows","seasons","episodes","sets","musicvideos"]:
                            try:
                                self.liDbId = xbmc.getInfoLabel("%sListItem.DBID"%self.widgetContainerPrefix).decode('utf-8')
                                if not self.liDbId or self.liDbId == "-1": self.liDbId = xbmc.getInfoLabel("%sListItem.Property(DBID)"%self.widgetContainerPrefix).decode('utf-8')
                                if self.liDbId == "-1": self.liDbId = ""
                                self.liImdb = xbmc.getInfoLabel("%sListItem.IMDBNumber"%self.widgetContainerPrefix).decode('utf-8')
                                if not self.liImdb: self.liImdb = xbmc.getInfoLabel("%sListItem.Property(IMDBNumber)"%self.widgetContainerPrefix).decode('utf-8')
                                self.setDuration()
                                self.setStudioLogo()
                                self.setGenre()
                                self.setDirector()

                                if self.liPath.startswith("plugin://") and not ("plugin.video.emby" in self.liPath or "script.skin.helper.service" in self.liPath):
                                    #plugins only...
                                    thread.start_new_thread(self.setAddonDetails, (True,))
                                    self.setAddonName()
                                else:
                                    #library only...
                                    thread.start_new_thread(self.setTmdbInfo, (True,))
                                    thread.start_new_thread(self.setOmdbInfo, (True,))
                                    thread.start_new_thread(self.setAnimatedPoster, (True,))
                                    self.setStreamDetails()
                                    self.setMovieSetDetails()
                                    self.checkExtraFanArt()
                                #nextaired workaround for info dialog
                                if widgetContainer == "999" and xbmc.getCondVisibility("!IsEmpty(%sListItem.TvShowTitle) + System.HasAddon(script.tv.show.next.aired)" %self.widgetContainerPrefix):
                                    xbmc.executebuiltin("RunScript(script.tv.show.next.aired,tvshowtitle=%s)" %xbmc.getInfoLabel("%sListItem.TvShowTitle"%self.widgetContainerPrefix).replace("&",""))
                                    nextairedActive = True
                                elif nextairedActive:
                                    nextairedActive = False
                                    xbmc.executebuiltin("RunScript(script.tv.show.next.aired,tvshowtitle=165628787629692696)")
                            except Exception as e:
                                logMsg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)
                                logMsg("ERROR in LibraryMonitor ! --> %s" %e, xbmc.LOGERROR)

                        # monitor listitem props when PVR is active
                        elif self.contentType in ["tvchannels","tvrecordings"]:
                            try:
                                self.setDuration()
                                thread.start_new_thread(self.setPVRThumbs, (True,))
                                thread.start_new_thread(self.setPVRChannelLogo, (True,))
                                self.setGenre()
                            except Exception as e:
                                logMsg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)
                                logMsg("ERROR in LibraryMonitor ! --> %s" %e, xbmc.LOGERROR)

                    #set some globals
                    liPathLast = self.liPath
                    lastListItem = curListItem

                self.monitor.waitForAbort(0.1)
                self.delayedTaskInterval += 0.1
                self.widgetTaskInterval += 0.1
            elif lastListItem and not self.exit:
                #flush any remaining window properties
                self.resetWindowProps()
                WINDOW.clearProperty("SkinHelper.ContentHeader")
                WINDOW.clearProperty("contenttype")
                self.contentType = ""
                if nextairedActive:
                    nextairedActive = False
                    xbmc.executebuiltin("RunScript(script.tv.show.next.aired,tvshowtitle=165628787629692696)")
                lastListItem = ""
                curListItem = ""
                curFolder = ""
                curFolderLast = ""
                self.widgetContainerPrefix = ""
                self.monitor.waitForAbort(0.5)
                self.delayedTaskInterval += 0.5
                self.widgetTaskInterval += 0.5
            elif xbmc.getCondVisibility("Window.IsActive(fullscreenvideo)"):
                #fullscreen video active
                self.monitor.waitForAbort(2)
                self.delayedTaskInterval += 2
                self.widgetTaskInterval += 2
            else:
                #other window visible
                self.monitor.waitForAbort(0.5)
                self.delayedTaskInterval += 0.5
                self.widgetTaskInterval += 0.5

    def doBackgroundWork(self):
        try:
            if self.exit: return
            logMsg("Started Background worker...")
            self.genericWindowProps()
            if not self.imdb_top250: self.imdb_top250 = artutils.getImdbTop250()
            self.checkNotifications()
            self.saveCacheToFile()
            logMsg("Ended Background worker...")
        except Exception as e:
            logMsg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)
            logMsg("ERROR in ListItemMonitor.doBackgroundWork ! --> %s" %e, xbmc.LOGERROR)

    def saveCacheToFile(self):
        libraryCache = {}
        libraryCache["SetsCache"] = self.moviesetCache
        libraryCache["tmdbinfocache"] = self.tmdbinfocache
        saveDataToCacheFile(self.cachePath,libraryCache)
        actorcache = WINDOW.getProperty("SkinHelper.ActorImages").decode("utf-8")
        if actorcache:
            saveDataToCacheFile(self.ActorImagesCachePath,eval(actorcache))

    def getCacheFromFile(self):
        #library items cache
        data = getDataFromCacheFile(self.cachePath)
        if data.has_key("SetsCache"):
            self.moviesetCache = data["SetsCache"]
        if data.has_key("tmdbinfocache"):
            #we only want movies older than 2 years from the permanent tmdb cache...
            for key, value in data["tmdbinfocache"].iteritems():
                if value.get("release_year") and int(value["release_year"]) < datetime.now().year -1:
                    self.tmdbinfocache[key] = value

        #actorimagescache
        data = getDataFromCacheFile(self.ActorImagesCachePath)
        if data: WINDOW.setProperty("SkinHelper.ActorImages", repr(data))

    def checkNotifications(self):
        try:
            currentHour = time.strftime("%H")
            #weather notifications
            winw = xbmcgui.Window(12600)
            if xbmc.getCondVisibility("Skin.HasSetting(EnableWeatherNotifications) + !IsEmpty(Window(Weather).Property(Alerts.RSS)) + !IsEmpty(Window(Weather).Property(Current.Condition))") and currentHour != self.lastWeatherNotificationCheck:
                dialog = xbmcgui.Dialog()
                dialog.notification(xbmc.getLocalizedString(31294), winw.getProperty("Alerts"), xbmcgui.NOTIFICATION_WARNING, 8000)
                self.lastWeatherNotificationCheck = currentHour

            #nextaired notifications
            if (xbmc.getCondVisibility("Skin.HasSetting(EnableNextAiredNotifications) + System.HasAddon(script.tv.show.next.aired)") and currentHour != self.lastNextAiredNotificationCheck):
                if (WINDOW.getProperty("NextAired.TodayShow")):
                    dialog = xbmcgui.Dialog()
                    dialog.notification(xbmc.getLocalizedString(31295), WINDOW.getProperty("NextAired.TodayShow"), xbmcgui.NOTIFICATION_WARNING, 8000)
                    self.lastNextAiredNotificationCheck = currentHour
        except Exception as e:
            logMsg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)
            logMsg("ERROR in ListItemMonitor.checkNotifications ! --> %s" %e, xbmc.LOGERROR)

    def genericWindowProps(self):

        #GET TOTAL ADDONS COUNT
        allAddonsCount = 0
        media_array = getJSON('Addons.GetAddons','{ }')
        for item in media_array:
            allAddonsCount += 1
        WINDOW.setProperty("SkinHelper.TotalAddons",str(allAddonsCount))

        addontypes = []
        addontypes.append( ["executable", "SkinHelper.TotalProgramAddons", 0] )
        addontypes.append( ["video", "SkinHelper.TotalVideoAddons", 0] )
        addontypes.append( ["audio", "SkinHelper.TotalAudioAddons", 0] )
        addontypes.append( ["image", "SkinHelper.TotalPicturesAddons", 0] )

        for type in addontypes:
            media_array = getJSON('Addons.GetAddons','{ "content": "%s" }' %type[0])
            for item in media_array:
                type[2] += 1
            WINDOW.setProperty(type[1],str(type[2]))

        #GET FAVOURITES COUNT
        allFavouritesCount = 0
        media_array = getJSON('Favourites.GetFavourites','{ }')
        for item in media_array:
            allFavouritesCount += 1
        WINDOW.setProperty("SkinHelper.TotalFavourites",str(allFavouritesCount))

        #GET TV CHANNELS COUNT
        allTvChannelsCount = 0
        if xbmc.getCondVisibility("Pvr.HasTVChannels"):
            media_array = getJSON('PVR.GetChannels','{"channelgroupid": "alltv" }' )
            for item in media_array:
                allTvChannelsCount += 1
        WINDOW.setProperty("SkinHelper.TotalTVChannels",str(allTvChannelsCount))

        #GET MOVIE SETS COUNT
        allMovieSetsCount = 0
        allMoviesInSetCount = 0
        media_array = getJSON('VideoLibrary.GetMovieSets','{}' )
        for item in media_array:
            allMovieSetsCount += 1
            media_array2 = getJSON('VideoLibrary.GetMovieSetDetails','{"setid": %s}' %item["setid"])
            for item in media_array2:
                allMoviesInSetCount +=1
        WINDOW.setProperty("SkinHelper.TotalMovieSets",str(allMovieSetsCount))
        WINDOW.setProperty("SkinHelper.TotalMoviesInSets",str(allMoviesInSetCount))

        #GET RADIO CHANNELS COUNT
        allRadioChannelsCount = 0
        if xbmc.getCondVisibility("Pvr.HasRadioChannels"):
            media_array = getJSON('PVR.GetChannels','{"channelgroupid": "allradio" }' )
            for item in media_array:
                allRadioChannelsCount += 1
        WINDOW.setProperty("SkinHelper.TotalRadioChannels",str(allRadioChannelsCount))

    def resetWindowProps(self):
        #reset all window props set by the script...
        for prop in self.allWindowProps:
            WINDOW.clearProperty(try_encode(prop))
        self.allWindowProps = []
    
    @classmethod
    def resetGlobalWidgetWindowProps(self):
        WINDOW.setProperty("widgetreload2", time.strftime("%Y%m%d%H%M%S", time.gmtime()))

    def resetPlayerWindowProps(self):
        #reset all window props provided by the script...
        for prop in self.allPlayerWindowProps:
            WINDOW.clearProperty(try_encode(prop))
        self.allPlayerWindowProps = []

    def setWindowProp(self,key,value):
        self.allWindowProps.append(key)
        WINDOW.setProperty(try_encode(key),try_encode(value))

    def setPlayerWindowProp(self,key,value):
        self.allPlayerWindowProps.append(key)
        WINDOW.setProperty(try_encode(key),try_encode(value))

    def setMovieSetDetails(self):
        #get movie set details -- thanks to phil65 - used this idea from his skin info script
        allProperties = []
        if not self.liDbId or not self.liPath: return
        if self.exit: return
        if self.liPath.startswith("videodb://movies/sets/"):
            #try to get from cache first - use checksum compare because moviesets do not get refreshed automatically
            checksum = repr(getJSON('VideoLibrary.GetMovieSetDetails', '{"setid": %s, "properties": [ "thumbnail" ], "movies": { "properties":  [ "playcount"] }}' % self.liDbId))
            cacheStr = self.liLabel+self.liDbId
            if self.moviesetCache.get(cacheStr) and self.moviesetCache.get("checksum-" + cacheStr,"") == checksum:
                allProperties = self.moviesetCache[cacheStr]

            if self.liDbId and not allProperties:
                #get values from json api
                checksum = getJSON('VideoLibrary.GetMovieSetDetails', '{"setid": %s, "properties": [ "thumbnail" ], "movies": { "properties":  [ "playcount"] }}' % self.liDbId)
                json_response = getJSON('VideoLibrary.GetMovieSetDetails', '{"setid": %s, "properties": [ "thumbnail" ], "movies": { "properties":  [ "rating", "art", "file", "year", "director", "writer", "playcount", "genre" , "thumbnail", "runtime", "studio", "plotoutline", "plot", "country", "streamdetails"], "sort": { "order": "ascending",  "method": "year" }} }' % self.liDbId)
                if json_response:
                    count = 0
                    runtime = 0
                    unwatchedcount = 0
                    watchedcount = 0
                    runtime = 0
                    writer = []
                    director = []
                    genre = []
                    country = []
                    studio = []
                    years = []
                    plot = ""
                    title_list = ""
                    title_header = "[B]" + str(json_response['limits']['total']) + " " + xbmc.getLocalizedString(20342) + "[/B][CR]"
                    set_fanart = []
                    for item in json_response['movies']:
                        if item["playcount"] == 0:
                            unwatchedcount += 1
                        else:
                            watchedcount += 1
                        art = item['art']
                        fanart = art.get('fanart', '')
                        set_fanart.append(fanart)
                        allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.Title',item['label']) )
                        allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.Poster',art.get('poster', '')) )
                        allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.FanArt',fanart) )
                        allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.Landscape',art.get('landscape', '')) )
                        allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.DiscArt',art.get('discart', '')) )
                        allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.ClearLogo',art.get('clearlogo', '')) )
                        allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.ClearArt',art.get('clearart', '')) )
                        allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.Banner',art.get('banner', '')) )
                        allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.Rating',str(item.get('rating', ''))) )
                        allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.Plot',item['plot']) )
                        allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.Year',str(item.get('year'))) )
                        allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.DBID',str(item.get('movieid'))) )
                        allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.Duration',str(item['runtime'] / 60)) )
                        if item.get('streamdetails',''):
                            streamdetails = item["streamdetails"]
                            audiostreams = streamdetails.get('audio',[])
                            videostreams = streamdetails.get('video',[])
                            subtitles = streamdetails.get('subtitle',[])
                            if len(videostreams) > 0:
                                stream = videostreams[0]
                                height = stream.get("height","")
                                width = stream.get("width","")
                                if height and width:
                                    resolution = ""
                                    if width <= 720 and height <= 480: resolution = "480"
                                    elif width <= 768 and height <= 576: resolution = "576"
                                    elif width <= 960 and height <= 544: resolution = "540"
                                    elif width <= 1280 and height <= 720: resolution = "720"
                                    elif width <= 1920 and height <= 1080: resolution = "1080"
                                    elif width * height >= 6000000: resolution = "4K"
                                    allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.Resolution',resolution) )
                                if stream.get("codec",""):
                                    allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.Codec',str(stream["codec"]))   )
                                if stream.get("aspect",""):
                                    allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.AspectRatio',str(round(stream["aspect"], 2))) )
                            if len(audiostreams) > 0:
                                #grab details of first audio stream
                                stream = audiostreams[0]
                                allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.AudioCodec',stream.get('codec','')) )
                                allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.AudioChannels',str(stream.get('channels',''))) )
                                allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.AudioLanguage',stream.get('language','')) )
                            if len(subtitles) > 0:
                                #grab details of first subtitle
                                allProperties.append( ('SkinHelper.MovieSet.' + str(count) + '.SubTitle',subtitles[0].get('language','')) )

                        title_list += item['label'] + " (" + str(item['year']) + ")[CR]"
                        if item['plotoutline']:
                            plot += "[B]" + item['label'] + " (" + str(item['year']) + ")[/B][CR]" + item['plotoutline'] + "[CR][CR]"
                        else:
                            plot += "[B]" + item['label'] + " (" + str(item['year']) + ")[/B][CR]" + item['plot'] + "[CR][CR]"
                        runtime += item['runtime']
                        count += 1
                        if item.get("writer"):
                            writer += [w for w in item["writer"] if w and w not in writer]
                        if item.get("director"):
                            director += [d for d in item["director"] if d and d not in director]
                        if item.get("genre"):
                            genre += [g for g in item["genre"] if g and g not in genre]
                        if item.get("country"):
                            country += [c for c in item["country"] if c and c not in country]
                        if item.get("studio"):
                            studio += [s for s in item["studio"] if s and s not in studio]
                        years.append(str(item['year']))
                    allProperties.append( ('SkinHelper.MovieSet.Plot', plot) )
                    if json_response['limits']['total'] > 1:
                        allProperties.append( ('SkinHelper.MovieSet.ExtendedPlot', title_header + title_list + "[CR]" + plot) )
                    else:
                        allProperties.append( ('SkinHelper.MovieSet.ExtendedPlot', plot) )
                    allProperties.append( ('SkinHelper.MovieSet.Title', title_list) )
                    allProperties.append( ('SkinHelper.MovieSet.Runtime', str(runtime / 60)) )
                    durationString = self.getDurationString(runtime / 60)
                    if durationString:
                        allProperties.append( ('SkinHelper.MovieSet.Duration', durationString[2]) )
                        allProperties.append( ('SkinHelper.MovieSet.Duration.Hours', durationString[0]) )
                        allProperties.append( ('SkinHelper.MovieSet.Duration.Minutes', durationString[1]) )
                    allProperties.append( ('SkinHelper.MovieSet.Writer', " / ".join(writer)) )
                    allProperties.append( ('SkinHelper.MovieSet.Director', " / ".join(director)) )
                    allProperties.append( ('SkinHelper.MovieSet.Genre', " / ".join(genre)) )
                    allProperties.append( ('SkinHelper.MovieSet.Country', " / ".join(country)) )
                    for key, value in studiologos.getStudioLogo(studio).iteritems():
                        allProperties.append( (key, value) )
                    allProperties.append( ('SkinHelper.MovieSet.Studio', " / ".join(studio)) )
                    allProperties.append( ('SkinHelper.MovieSet.Years', " / ".join(years)) )
                    allProperties.append( ('SkinHelper.MovieSet.Year', years[0] + " - " + years[-1]) )
                    allProperties.append( ('SkinHelper.MovieSet.Count', str(json_response['limits']['total'])) )
                    allProperties.append( ('SkinHelper.MovieSet.WatchedCount', str(watchedcount)) )
                    allProperties.append( ('SkinHelper.MovieSet.UnWatchedCount', str(unwatchedcount)) )
                    allProperties.append( ('SkinHelper.MovieSet.Extrafanarts', repr(set_fanart)) )
                #save to cache
                self.moviesetCache[cacheStr] = allProperties
                self.moviesetCache["checksum-" + cacheStr] = repr(checksum)

            #Process properties
            for item in allProperties:
                if item[0] == "SkinHelper.MovieSet.Extrafanarts":
                    if xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnableExtraFanart)"):
                        efaProp = 'EFA_FROMWINDOWPROP_' + cacheStr
                        self.setWindowProp(efaProp, try_encode(item[1]))
                        self.setWindowProp('SkinHelper.ExtraFanArtPath', "plugin://script.skin.helper.service/?action=EXTRAFANART&path=%s" %single_urlencode(try_encode(efaProp)))
                else:
                    self.setWindowProp(item[0],try_encode(item[1]))
                    if item[0] == "SkinHelper.MovieSet.Studio":
                        self.setStudioLogo(item[1])

    def setContentHeader(self):
        WINDOW.clearProperty("SkinHelper.ContentHeader")
        itemscount = xbmc.getInfoLabel("Container.NumItems")
        if itemscount:
            if xbmc.getInfoLabel("Container.ListItemNoWrap(0).Label").startswith("*") or xbmc.getInfoLabel("Container.ListItemNoWrap(1).Label").startswith("*"):
                itemscount = int(itemscount) - 1

            headerprefix = ""
            if self.contentType == "movies":
                headerprefix = xbmc.getLocalizedString(36901)
            elif self.contentType == "tvshows":
                headerprefix = xbmc.getLocalizedString(36903)
            elif self.contentType == "seasons":
                headerprefix = xbmc.getLocalizedString(36905)
            elif self.contentType == "episodes":
                headerprefix = xbmc.getLocalizedString(36907)
            elif self.contentType == "sets":
                headerprefix = xbmc.getLocalizedString(36911)
            elif self.contentType == "albums":
                headerprefix = xbmc.getLocalizedString(36919)
            elif self.contentType == "songs":
                headerprefix = xbmc.getLocalizedString(36921)
            elif self.contentType == "artists":
                headerprefix = xbmc.getLocalizedString(36917)

            if headerprefix:
                WINDOW.setProperty("SkinHelper.ContentHeader","%s %s" %(itemscount,headerprefix) )

    def setAddonName(self):
        # set addon name as property
        if not xbmc.Player().isPlayingAudio():
            if (xbmc.getCondVisibility("Container.Content(plugins) | !IsEmpty(Container.PluginName)")):
                AddonName = xbmc.getInfoLabel('Container.PluginName').decode('utf-8')
                AddonName = xbmcaddon.Addon(AddonName).getAddonInfo('name')
                self.setWindowProp("SkinHelper.Player.AddonName", AddonName)

    def setGenre(self,genre=""):
        if not genre: genre = xbmc.getInfoLabel('%sListItem.Genre' %self.widgetContainerPrefix).decode('utf-8')
        genres = []
        if "/" in genre:
            genres = genre.split(" / ")
        else:
            genres.append(genre)
        self.setWindowProp('SkinHelper.ListItemGenres', "[CR]".join(genres))
        count = 0
        for genre in genres:
            self.setWindowProp("SkinHelper.ListItemGenre." + str(count),genre)
            count +=1

    def setDirector(self, director=""):
        if not director: director = xbmc.getInfoLabel('%sListItem.Director'%self.widgetContainerPrefix).decode('utf-8')
        directors = []
        if "/" in director:
            directors = director.split(" / ")
        else:
            directors.append(director)

        self.setWindowProp('SkinHelper.ListItemDirectors', "[CR]".join(directors))

    def setWidgetDetails(self):
        #sets all listitem properties as window prop for easy use in a widget details pane
        listOfPropsToSet = []
        cacheStr = u"SkinHelper.ListItemDetails.%s.%s.%s.%s" %(self.liLabel,self.liTitle,self.liFile,self.widgetContainerPrefix)
        cache = simplecache.get(cacheStr)
        if cache:
            listOfPropsToSet = cache
        else:
            listOfPropsToSet.append(("Label", self.liLabel))
            listOfPropsToSet.append(("Title", self.liTitle))
            listOfPropsToSet.append(("Filenameandpath", self.liFile))
            props = [
                        "Year","Genre","Filenameandpath","FileName","Label2",
                        "Art(fanart)","Art(poster)","Art(clearlogo)","Art(clearart)","Art(landscape)",
                        "FileExtension","Duration","Plot", "PlotOutline","icon","thumb",
                        "Property(FanArt)","dbtype","Property(dbtype)","Property(plot)","FolderPath"
                    ]
            if self.contentType in ["movies", "tvshows", "seasons", "episodes", "musicvideos", "setmovies"]:
                props += [
                            "imdbnumber","Art(characterart)", "studio", "TvShowTitle","Premiered", "director", "writer",
                            "firstaired", "VideoResolution","AudioCodec","AudioChannels", "VideoCodec",
                            "VideoAspect","SubtitleLanguage","AudioLanguage","MPAA", "IsStereoScopic",
                            "Property(Video3DFormat)", "tagline", "rating"
                         ]
            if self.contentType in ["episodes"]:
                props += [
                            "season","episode", "Art(tvshow.landscape)","Art(tvshow.clearlogo)","Art(tvshow.poster)"
                         ]
            if self.contentType in ["musicvideos", "artists", "albums", "songs"]:
                props += ["artist", "album", "rating"]
            if self.contentType in ["tvrecordings", "tvchannels"]:
                props += [
                            "Channel", "Property(Channel)", "Property(StartDateTime)", "DateTime", "Date", "Property(Date)",
                            "Property(DateTime)", "ChannelName", "Property(ChannelLogo)", "Property(ChannelName)",
                            "StartTime","Property(StartTime)","StartDate","Property(StartDate)","EndTime",
                            "Property(EndTime)","EndDate","Property(EndDate)"
                         ]

            for prop in props:
                propvalue = xbmc.getInfoLabel('%sListItem.%s'%(self.widgetContainerPrefix, prop)).decode('utf-8')
                if propvalue:
                    listOfPropsToSet.append( (prop, propvalue) )
                    if prop.startswith("Property"):
                        prop = prop.replace("Property(","").replace(")","")
                        listOfPropsToSet.append( (prop, propvalue) )
            if self.liTitle != xbmc.getInfoLabel('%sListItem.Title'%(self.widgetContainerPrefix)).decode('utf-8'):
                return #abort if other listitem focused
            if not self.contentType in ["systeminfos","weathers"]:
                simplecache.set(cacheStr,listOfPropsToSet,expiration=timedelta(hours=2))

        for prop in listOfPropsToSet:
            self.setWindowProp('SkinHelper.ListItem.%s' %prop[0], prop[1])

    def setPVRThumbs(self, multiThreaded=False):
        if WINDOW.getProperty("artworkcontextmenu"):
            return
        title = self.liTitle

        channel = xbmc.getInfoLabel("%sListItem.ChannelName"%self.widgetContainerPrefix).decode('utf-8')
        if xbmc.getCondVisibility("%sListItem.IsFolder"%self.widgetContainerPrefix) and not channel and not title:
            title = self.liLabel

        if not xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnablePVRThumbs)") or not title:
            return

        genre = xbmc.getInfoLabel("%sListItem.Genre"%self.widgetContainerPrefix).decode('utf-8')
        artwork = artutils.getPVRThumbs(title, channel, self.contentType, self.liPath, genre)

        #return if another listitem was focused in the meanwhile
        if multiThreaded and not (title == xbmc.getInfoLabel("ListItem.Title").decode('utf-8') or title == xbmc.getInfoLabel("%sListItem.Title"%self.widgetContainerPrefix).decode('utf-8') or title == xbmc.getInfoLabel("%sListItem.Label"%self.widgetContainerPrefix).decode('utf-8')):
            return

        #set window props
        for key, value in artwork.iteritems():
            if key != "channellogo":
                self.setWindowProp("SkinHelper.PVR." + key,value)

    def setPVRChannelLogo(self, multiThreaded=False):
        channel = xbmc.getInfoLabel("%sListItem.ChannelName"%self.widgetContainerPrefix).decode('utf-8')
        if not channel:
            return

        icon = artutils.searchChannelLogo(channel)

        #return if another listitem was focused in the meanwhile
        if multiThreaded and not (channel == xbmc.getInfoLabel("%sListItem.ChannelName"%self.widgetContainerPrefix).decode('utf-8')):
            return

        #set window prop
        if icon:
            self.setWindowProp("SkinHelper.PVR.ChannelLogo",icon)

    def setStudioLogo(self,studio=""):
        if not studio:
            studio = xbmc.getInfoLabel('%sListItem.Studio'%self.widgetContainerPrefix).decode('utf-8')
        for key, value in studiologos.getStudioLogo(studio).iteritems():
            self.setWindowProp(key,value)

    def setDuration(self,currentDuration=""):
        if xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.DisableHoursDuration)"):
            return

        if not currentDuration:
            currentDuration = xbmc.getInfoLabel("%sListItem.Duration"%self.widgetContainerPrefix)

        if ":" in currentDuration:
            durLst = currentDuration.split(":")
            if len(durLst) == 1:
                currentDuration = "0"
            elif len(durLst) == 2:
                currentDuration = durLst[0]
            elif len(durLst) == 3:
                currentDuration = str((int(durLst[0])*60) + int(durLst[1]))

        # monitor listitem to set duration
        if currentDuration:
            durationString = self.getDurationString(currentDuration)
            if durationString:
                self.setWindowProp('SkinHelper.ListItemDuration', durationString[2])
                self.setWindowProp('SkinHelper.ListItemDuration.Hours', durationString[0])
                self.setWindowProp('SkinHelper.ListItemDuration.Minutes', durationString[1])

    def getDurationString(self, duration):
        if duration == None or duration == 0:
            return None
        try:
            full_minutes = int(duration)
            minutes = str(full_minutes % 60)
            minutes = str(minutes).zfill(2)
            hours   = str(full_minutes // 60)
            durationString = hours + ':' + minutes
        except Exception as e:
            logMsg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)
            logMsg("ERROR in ListItemMonitor.getDurationString ! --> %s" %e, xbmc.LOGERROR)
            return None
        return ( hours, minutes, durationString )

    def setMusicPlayerDetails(self):
        artwork = {}
        artist = ""
        title = ""
        album = ""
        #get the playing item from the player...
        json_result = getJSON('Player.GetActivePlayers', '{}')
        for item in json_result:
            if item.get("type","") == "audio":
                json_result = getJSON('Player.GetItem', '{ "playerid": %d, "properties": [ "title","albumid","artist","album","displayartist" ] }' %item.get("playerid"))
                if json_result.get("title"):
                    if json_result.get("artist"):
                        artist = json_result.get("artist")
                        if isinstance(artist,list): artist = artist[0]
                        title = json_result.get("title")
                        album = json_result.get("album").split(" (")[0]
                    else:
                        if not artist:
                            #fix for internet streams
                            splitchar = None
                            if " - " in json_result.get("title"): splitchar = " - "
                            elif "- " in json_result.get("title"): splitchar = "- "
                            elif " -" in json_result.get("title"): splitchar = " -"
                            elif "-" in json_result.get("title"): splitchar = "-"
                            if splitchar:
                                artist = json_result.get("title").split(splitchar)[0]
                                title = json_result.get("title").split(splitchar)[1]
                    logMsg("setMusicPlayerDetails: " + repr(json_result))

        artwork = artutils.getMusicArtwork(artist,album,title)

        #merge comment from id3 tag with album info
        if artwork.get("info") and xbmc.getInfoLabel("MusicPlayer.Comment"):
            artwork["info"] = normalize_string(xbmc.getInfoLabel("MusicPlayer.Comment")).replace('\n', ' ').replace('\r', '').split(" a href")[0] + "  -  " + artwork["info"]

        #set properties
        for key, value in artwork.iteritems():
            setPlayerWindowProp(u"SkinHelper.Player.Music.%s" %key, value)

    def setMusicDetails(self,multiThreaded=False):
        artwork = {}
        if WINDOW.getProperty("artworkcontextmenu"): return
        artist = xbmc.getInfoLabel("%sListItem.Artist"%self.widgetContainerPrefix).decode('utf-8')
        album = xbmc.getInfoLabel("%sListItem.Album"%self.widgetContainerPrefix).decode('utf-8')
        title = self.liTitle
        label = self.liLabel
        artwork = artutils.getMusicArtwork(artist,album,title)

        if self.exit: return

        #return if another listitem was focused in the meanwhile
        if multiThreaded and label != xbmc.getInfoLabel("%sListItem.Label"%self.widgetContainerPrefix).decode('utf-8'):
            return

        #set properties
        for key, value in artwork.iteritems():
            self.setWindowProp("SkinHelper.Music." + key,value)

    def setStreamDetails(self):
        streamdetails = artutils.getStreamDetails(self.liDbId,self.contentType)
        #set the window properties
        for key, value in streamdetails.iteritems():
            self.setWindowProp(key,value)

    def setForcedView(self):
        currentForcedView = xbmc.getInfoLabel("Skin.String(SkinHelper.ForcedViews.%s)" %self.contentType)
        if xbmc.getCondVisibility("Control.IsVisible(%s) | IsEmpty(Container.Viewmode)" %currentForcedView):
            #skip if the view is already visible or if we're not in an actual media window
            return
        if self.contentType and currentForcedView and currentForcedView != "None" and xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.ForcedViews.Enabled)") and not "pvr://guide" in self.liPath:
            WINDOW.setProperty("SkinHelper.ForcedView",currentForcedView)
            xbmc.executebuiltin("Container.SetViewMode(%s)" %currentForcedView)
            if not xbmc.getCondVisibility("Control.HasFocus(%s)" %currentForcedView):
                xbmc.sleep(100)
                xbmc.executebuiltin("Container.SetViewMode(%s)" %currentForcedView)
                xbmc.executebuiltin("SetFocus(%s)" %currentForcedView)
        else:
            WINDOW.clearProperty("SkinHelper.ForcedView")

    def checkExtraFanArt(self):
        if xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnableExtraFanart)"):
            folderpath = self.liPath
            if "plugin.video.emby.movies" in self.liPath or "plugin.video.emby.musicvideos" in self.liPath:
                folderpath = self.liFile
            if (folderpath and (self.contentType in ["movies","seasons","episodes","tvshows","setmovies"] ) and not "videodb:" in folderpath):
                extrafanart = artutils.getExtraFanart(folderpath)
                for key, value in extrafanart.iteritems():
                    if value: self.setWindowProp(key,value)

    def setAnimatedPoster(self,multiThreaded=False,liImdb=""):
        #check animated posters
        if not liImdb: liImdb = self.liImdb
        if not liImdb: liImdb = self.liTitle
        if not xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnableAnimatedPosters)") or not liImdb:
            return
        if WINDOW.getProperty("artworkcontextmenu"): return
        if (self.contentType == "movies" or self.contentType=="setmovies"):
            for type in ["poster","fanart"]:
                image = artutils.getAnimatedArtwork(liImdb,type,self.liDbId)
                #return if another listitem was focused in the meanwhile
                if multiThreaded and not liImdb == self.liImdb:
                    return
                if image != "None":
                    self.setWindowProp("SkinHelper.Animated%s"%type,image)

    def setOmdbInfo(self,multiThreaded=False,liImdb=""):
        result = {}
        if not liImdb:
            liImdb = self.liImdb
        if not liImdb:
            liImdb = self.liTitle
        if not self.contentType in ["movies","setmovies","tvshows"]:
            return
        if self.omdbinfocache.get(liImdb):
            #get data from cache
            result = self.omdbinfocache[liImdb]
        elif not WINDOW.getProperty("SkinHelper.DisableInternetLookups"):
            #get info from OMDB
            if not liImdb.startswith("tt"):
                #get info by title and year
                year = xbmc.getInfoLabel("%sListItem.Year"%self.widgetContainerPrefix).decode('utf-8')
                title = self.liTitle
                if self.contentType == "tvshows":
                    type = "series"
                else: type = "movie"
                url = 'http://www.omdbapi.com/?t=%s&y=%s&type=%s&plot=short&tomatoes=true&r=json' %(title,year,type)
            else:
                url = 'http://www.omdbapi.com/?i=%s&plot=short&tomatoes=true&r=json' %liImdb
            res = requests.get(url)
            omdbresult = json.loads(res.content.decode('utf-8','replace'))
            if omdbresult.get("Response","") == "True":
                #convert values from omdb to our window props
                for key, value in omdbresult.iteritems():
                    if value and value != "N/A":
                        if key == "tomatoRating": result["SkinHelper.RottenTomatoesRating"] = value
                        elif key == "tomatoMeter": result["SkinHelper.RottenTomatoesMeter"] = value
                        elif key == "tomatoFresh": result["SkinHelper.RottenTomatoesFresh"] = value
                        elif key == "tomatoReviews": result["SkinHelper.RottenTomatoesReviews"] = intWithCommas(value)
                        elif key == "tomatoRotten": result["SkinHelper.RottenTomatoesRotten"] = value
                        elif key == "tomatoImage": result["SkinHelper.RottenTomatoesImage"] = value
                        elif key == "tomatoConsensus": result["SkinHelper.RottenTomatoesConsensus"] = value
                        elif key == "Awards": result["SkinHelper.RottenTomatoesAwards"] = value
                        elif key == "BoxOffice": result["SkinHelper.RottenTomatoesBoxOffice"] = value
                        elif key == "DVD": result["SkinHelper.RottenTomatoesDVDRelease"] = value
                        elif key == "tomatoUserMeter": result["SkinHelper.RottenTomatoesAudienceMeter"] = value
                        elif key == "tomatoUserRating": result["SkinHelper.RottenTomatoesAudienceRating"] = value
                        elif key == "tomatoUserReviews": result["SkinHelper.RottenTomatoesAudienceReviews"] = intWithCommas(value)
                        elif key == "Metascore": result["SkinHelper.MetaCritic.Rating"] = value
                        elif key == "imdbRating":
                            result["SkinHelper.IMDB.Rating"] = value
                            result["SkinHelper.IMDB.Rating.Percent"] = "%s" %(int(float(value) * 10))
                        elif key == "imdbVotes": result["SkinHelper.IMDB.Votes"] = value
                        elif key == "Rated": result["SkinHelper.IMDB.MPAA"] = value
                        elif key == "Runtime": result["SkinHelper.IMDB.Runtime"] = value

                #imdb top250
                result["SkinHelper.IMDB.Top250"] = self.imdb_top250.get(omdbresult["imdbID"],"")

            #store to cache
            self.omdbinfocache[liImdb] = result

            #return if another listitem was focused in the meanwhile
            if multiThreaded and not (liImdb == xbmc.getInfoLabel("%sListItem.IMDBNumber"%self.widgetContainerPrefix).decode('utf-8') or liImdb == xbmc.getInfoLabel("%sListItem.Property(IMDBNumber)"%self.widgetContainerPrefix).decode('utf-8')):
                return

        #set properties
        for key, value in result.iteritems():
            self.setWindowProp(key,value)

    def setTmdbInfo(self,multiThreaded=False,liImdb=""):
        result = {}
        if not liImdb: liImdb = self.liImdb
        if (self.contentType == "movies" or self.contentType=="setmovies") and liImdb:
            if self.tmdbinfocache.get(liImdb):
                #get data from cache
                result = self.tmdbinfocache[liImdb]
            elif not WINDOW.getProperty("SkinHelper.DisableInternetLookups"):
                logMsg("Retrieving TMDB info for ImdbId--> %s  - contentType: %s" %(liImdb,self.contentType))

                #get info from TMDB
                url = 'http://api.themoviedb.org/3/find/%s?external_source=imdb_id&api_key=%s' %(liImdb,artutils.tmdb_apiKey)
                response = requests.get(url)
                data = json.loads(response.content.decode('utf-8','replace'))
                if data and data.get("movie_results"):
                    data = data.get("movie_results")
                    if len(data) == 1:
                        url = 'http://api.themoviedb.org/3/movie/%s?api_key=%s' %(data[0].get("id"),artutils.tmdb_apiKey)
                        response = requests.get(url)
                        data = json.loads(response.content.decode('utf-8','replace'))
                        if data.get("budget") and data.get("budget") > 0:
                            result["budget"] = str(data.get("budget",""))
                            mln = float(data.get("budget")) / 1000000
                            mln = "%.1f" % mln
                            result["budget.formatted"] = "$ %s mln." %mln.replace(".0","").replace(".",",")
                            result["budget.mln"] = mln

                        if data.get("revenue","") and data.get("revenue") > 0:
                            result["revenue"] = str(data.get("revenue",""))
                            mln = float(data.get("revenue")) / 1000000
                            mln = "%.1f" % mln
                            result["revenue.formatted"] = "$ %s mln." %mln.replace(".0","").replace(".",",")
                            result["revenue.mln"] = mln

                        result["tagline"] = data.get("tagline","")
                        result["homepage"] = data.get("homepage","")
                        result["status"] = data.get("status","")
                        result["popularity"] = str(data.get("popularity",""))

                        #we only want movies older than 2 years in the permanent cache so we store the year
                        release_date = data["release_date"]
                        release_year = release_date.split("-")[0]
                        result["release_date"] = release_date
                        result["release_year"] = release_year

                #save to cache
                if result: self.tmdbinfocache[self.liImdb] = result

            #return if another listitem was focused in the meanwhile
            if multiThreaded and not (liImdb == xbmc.getInfoLabel("%sListItem.IMDBNumber"%self.widgetContainerPrefix).decode('utf-8') or liImdb == xbmc.getInfoLabel("%sListItem.Property(IMDBNumber)"%self.widgetContainerPrefix).decode('utf-8')):
                return

            #set properties
            for key, value in result.iteritems():
                self.setWindowProp("SkinHelper.TMDB." + key,value)

    def setAddonDetails(self, multiThreaded=False):
        #try to lookup additional artwork and properties for plugin content
        preftype = self.contentType
        title = self.liTitle
        year = xbmc.getInfoLabel("%sListItem.Year"%self.widgetContainerPrefix).decode('utf-8')

        if not self.contentType in ["movies", "tvshows", "seasons", "episodes", "setmovies"] or not title or not year or not xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnableAddonsLookups)"):
            return

        if xbmc.getCondVisibility("!IsEmpty(%sListItem.TvShowTitle)" %self.widgetContainerPrefix):
            preftype = "tvshows"
            title = xbmc.getInfoLabel("%sListItem.TvShowTitle"%self.widgetContainerPrefix).decode("utf8")

        artwork = artutils.getAddonArtwork(title,year,preftype)

        #return if another listitem was focused in the meanwhile
        if multiThreaded and not (title == xbmc.getInfoLabel("%sListItem.Title"%self.widgetContainerPrefix).decode('utf-8') or title == xbmc.getInfoLabel("%sListItem.TvShowTitle"%self.widgetContainerPrefix).decode("utf8")):
            return

        #set window props
        for key, value in artwork.iteritems():
            self.setWindowProp("SkinHelper.PVR." + key,value)

        #set extended movie details
        if (self.contentType == "movies" or self.contentType == "setmovies") and artwork.get("imdb_id"):
            self.setTmdbInfo(False,artwork.get("imdb_id"))
            self.setAnimatedPoster(False,artwork.get("imdb_id"))
        self.setOmdbInfo(artwork.get("imdb_id"))
