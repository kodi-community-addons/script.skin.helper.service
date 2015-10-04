#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcgui
import threading
import thread
import xbmcvfs
import random
import xml.etree.ElementTree as etree
import base64
import json
import requests
from datetime import datetime
from Utils import *

class LibraryMonitor(threading.Thread):
    
    event = None
    exit = False
    liPath = None
    liPathLast = None
    unwatched = 1
    lastEpPath = ""
    lastMusicDbId = None
    lastpvrDbId = None
    allStudioLogos = {}
    allStudioLogosColor = {}
    LastCustomStudioImagesPath = None
    delayedTaskInterval = 1800
    widgetTaskInterval = 595
    moviesetCache = {}
    extraFanartCache = {}
    musicArtCache = {}
    streamdetailsCache = {}
    pvrArtCache = {}
    rottenCache = {}
    lastFolderPath = None
    lastContentType = None
    
    def __init__(self, *args):
        
        logMsg("LibraryMonitor - started")
        self.cachePath = os.path.join(ADDON_DATA_PATH,"librarycache.json")
        self.event =  threading.Event()
        threading.Thread.__init__(self, *args)    
    
    def stop(self):
        logMsg("LibraryMonitor - stop called",0)
        self.saveCacheToFile()
        self.exit = True
        self.event.set()

    def saveCacheToFile(self):
        #safety check: does the config directory exist?
        if not xbmcvfs.exists(ADDON_DATA_PATH + os.sep):
            xbmcvfs.mkdir(ADDON_DATA_PATH)
        
        libraryCache = {}
        libraryCache["MusicArtCache"] = self.musicArtCache
        libraryCache["PVRArtCache"] = self.pvrArtCache
        libraryCache["SetsCache"] = self.moviesetCache
        libraryCache["streamdetailsCache"] = self.streamdetailsCache
        libraryCache["rottenCache"] = self.rottenCache       
        json.dump(libraryCache, open(self.cachePath,'w'))
       
    def getCacheFromFile(self):
        #TODO --> clear the cache in some conditions
        if xbmcvfs.exists(self.cachePath):
            with open(self.cachePath) as data_file:    
                data = json.load(data_file)
                if data.has_key("MusicArtCache"):
                    self.musicArtCache = data["MusicArtCache"]
                if data.has_key("SetsCache"):
                    self.moviesetCache = data["SetsCache"]
                if data.has_key("streamdetailsCache"):
                    self.streamdetailsCache = data["streamdetailsCache"]
                if data.has_key("rottenCache"):
                    self.rottenCache = data["rottenCache"]
                if data.has_key("PVRArtCache"):
                    self.pvrArtCache = data["PVRArtCache"]
                    WINDOW.setProperty("SkinHelper.pvrArtCache",repr(data["PVRArtCache"]))

    def run(self):

        lastListItemLabel = None
        self.getCacheFromFile()
        KodiMonitor = xbmc.Monitor()

        while (self.exit != True):
        
            #set forced view
            self.setForcedView()
            
            #do some background stuff every 30 minutes
            if (xbmc.getCondVisibility("!Window.IsActive(videolibrary) + !Window.IsActive(musiclibrary) + !Window.IsActive(fullscreenvideo)")):
                if (self.delayedTaskInterval >= 1800):
                    thread.start_new_thread(self.doBackgroundWork, ())
                    self.delayedTaskInterval = 0                   
            
            #reload some widgets every 10 minutes
            if (xbmc.getCondVisibility("!Window.IsActive(videolibrary) + !Window.IsActive(musiclibrary) + !Window.IsActive(fullscreenvideo)")):
                if (self.widgetTaskInterval >= 600):
                    WINDOW.setProperty("widgetreload2", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    self.widgetTaskInterval = 0

            #flush cache if videolibrary has changed
            if WINDOW.getProperty("resetVideoDbCache") == "reset":
                self.moviesetCache = {}
                self.extraFanartCache = {}
                self.streamdetailsCache = {}
                WINDOW.clearProperty("resetVideoDbCache")
                        
            # monitor listitem props when musiclibrary is active
            elif (xbmc.getCondVisibility("[Window.IsActive(musiclibrary) | Window.IsActive(MyMusicSongs.xml)] + !Container.Scrolling")):
                try:
                    if WINDOW.getProperty("resetMusicArtCache") == "reset":
                        self.lastMusicDbId = None
                        self.musicArtCache = {}
                        WINDOW.clearProperty("resetMusicArtCache")
                    liLabel = xbmc.getInfoLabel("ListItem.Label").decode('utf-8')
                    if liLabel != lastListItemLabel:
                        lastListItemLabel = liLabel
                        self.checkMusicArt()
                        self.setGenre()
                except Exception as e:
                    logMsg("ERROR in checkMusicArt ! --> " + str(e), 0)
                    
            
            # monitor listitem props when PVR is active
            elif (xbmc.getCondVisibility("[Window.IsActive(MyPVRChannels.xml) | Window.IsActive(MyPVRGuide.xml) | Window.IsActive(MyPVRTimers.xml) | Window.IsActive(MyPVRSearch.xml) | Window.IsActive(MyPVRRecordings.xml)]")):
                try:
                    self.liPath = xbmc.getInfoLabel("ListItem.Path").decode('utf-8')
                    liLabel = xbmc.getInfoLabel("ListItem.Label").decode('utf-8')
                    if ((liLabel != lastListItemLabel) and xbmc.getCondVisibility("!Container.Scrolling")):
                        self.liPathLast = self.liPath
                        lastListItemLabel = liLabel
                        # update the listitem stuff
                        self.setDuration()
                        self.setPVRThumbs()
                        self.setGenre()
                except Exception as e:
                    logMsg("ERROR in LibraryMonitor ! --> " + str(e), 0)
                        
            #monitor home widget
            elif xbmc.getCondVisibility("Window.IsActive(home)") and WINDOW.getProperty("SkinHelper.WidgetContainer"):
                try:
                    widgetContainer = WINDOW.getProperty("SkinHelper.WidgetContainer")
                    self.liPath = xbmc.getInfoLabel("Container(%s).ListItem.Path" %widgetContainer).decode('utf-8')
                    liLabel = xbmc.getInfoLabel("Container(%s).ListItem.Label"%widgetContainer).decode('utf-8')
                    if ((liLabel != lastListItemLabel) and xbmc.getCondVisibility("!Container(%s).Scrolling" %widgetContainer)):
                        self.liPathLast = self.liPath
                        lastListItemLabel = liLabel
                        self.setDuration(xbmc.getInfoLabel("Container(%s).ListItem.Duration" %widgetContainer))
                        self.setStudioLogo(xbmc.getInfoLabel("Container(%s).ListItem.Studio" %widgetContainer).decode('utf-8'))
                        self.setDirector(xbmc.getInfoLabel("Container(%s).ListItem.Director" %widgetContainer).decode('utf-8'))
                        self.checkMusicArt(xbmc.getInfoLabel("Container(%s).ListItem.Artist" %widgetContainer).decode('utf-8')+xbmc.getInfoLabel("Container(%s).ListItem.Album" %widgetContainer).decode('utf-8'))
                except Exception as e:
                    logMsg("ERROR in LibraryMonitor widgets ! --> " + str(e), 0)
                        
            # monitor listitem props when videolibrary is active
            elif (xbmc.getCondVisibility("[Window.IsActive(videolibrary) | Window.IsActive(movieinformation)] + !Window.IsActive(fullscreenvideo)")):
                try:
                    self.liPath = xbmc.getInfoLabel("ListItem.Path").decode('utf-8')
                    liLabel = xbmc.getInfoLabel("ListItem.Label").decode('utf-8')
                    if ((liLabel != lastListItemLabel) and xbmc.getCondVisibility("!Container.Scrolling")):
                        self.liPathLast = self.liPath
                        lastListItemLabel = liLabel
                        # update the listitem stuff
                        self.setDuration()
                        self.setStudioLogo()
                        self.setGenre()
                        self.setDirector()
                        self.checkExtraFanArt()
                        self.setMovieSetDetails()
                        self.setAddonName()
                        self.setStreamDetails()
                        self.setRottenRatings()
                        self.focusEpisode()
                except Exception as e:
                    logMsg("ERROR in LibraryMonitor ! --> " + str(e), 0)

            else:
                #reset window props
                WINDOW.clearProperty("SkinHelper.ListItemStudioLogo")
                WINDOW.clearProperty('SkinHelper.ListItemDuration')
                WINDOW.setProperty("SkinHelper.ExtraFanArtPath","") 
                WINDOW.clearProperty("SkinHelper.Music.BannerArt") 
                WINDOW.clearProperty("SkinHelper.Music.LogoArt") 
                WINDOW.clearProperty("SkinHelper.Music.DiscArt")
                WINDOW.clearProperty("SkinHelper.Music.Info")
                WINDOW.clearProperty('SkinHelper.RottenTomatoesRating')
                WINDOW.clearProperty('SkinHelper.RottenTomatoesAudienceRating')
                WINDOW.clearProperty('SkinHelper.RottenTomatoesConsensus')
                WINDOW.clearProperty('SkinHelper.RottenTomatoesAwards')
                WINDOW.clearProperty('SkinHelper.RottenTomatoesBoxOffice')
                WINDOW.clearProperty("SkinHelper.PVR.Thumb") 
                WINDOW.clearProperty("SkinHelper.PVR.FanArt") 
                WINDOW.clearProperty("SkinHelper.PVR.ChannelLogo")
                WINDOW.clearProperty("SkinHelper.PVR.Poster")
            xbmc.sleep(100)
            self.delayedTaskInterval += 0.10
            self.widgetTaskInterval += 0.10

    def doBackgroundWork(self):
        #background worker for any long running tasks
        try:
            self.getStudioLogos()
        except Exception as e:
            logMsg("ERROR in LibraryMonitor.doBackgroundWork ! --> " + str(e), 0)
                       
    def setMovieSetDetails(self):
        #get movie set details -- thanks to phil65 - used this idea from his skin info script
        
        WINDOW.clearProperty('SkinHelper.MovieSet.Title')
        WINDOW.clearProperty('SkinHelper.MovieSet.Runtime')
        WINDOW.clearProperty('SkinHelper.MovieSet.Duration')
        WINDOW.clearProperty('SkinHelper.MovieSet.Duration.Hours')
        WINDOW.clearProperty('SkinHelper.MovieSet.Duration.Minutes')
        WINDOW.clearProperty('SkinHelper.MovieSet.Writer')
        WINDOW.clearProperty('SkinHelper.MovieSet.Director')
        WINDOW.clearProperty('SkinHelper.MovieSet.Genre')
        WINDOW.clearProperty('SkinHelper.MovieSet.Country')
        WINDOW.clearProperty('SkinHelper.MovieSet.Studio')
        WINDOW.clearProperty('SkinHelper.MovieSet.Years')
        WINDOW.clearProperty('SkinHelper.MovieSet.Year')
        WINDOW.clearProperty('SkinHelper.MovieSet.Count')
        WINDOW.clearProperty('SkinHelper.MovieSet.Plot')
        WINDOW.clearProperty('SkinHelper.RottenTomatoesRating')
        WINDOW.clearProperty('SkinHelper.RottenTomatoesAudienceRating')
        WINDOW.clearProperty('SkinHelper.RottenTomatoesConsensus')
        WINDOW.clearProperty('SkinHelper.RottenTomatoesAwards')
        WINDOW.clearProperty('SkinHelper.RottenTomatoesBoxOffice')
        totalNodes = 50
        for i in range(totalNodes):
            if not WINDOW.getProperty('SkinHelper.MovieSet.' + str(i) + '.Title'):
                break
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.Title')
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.FanArt')
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.Landscape')
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.DiscArt')
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.ClearLogo')
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.ClearArt')
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.Banner')
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.Rating')
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.Resolution')
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.Resolution.Type')
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.AspectRatio')
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.Codec')
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.AudioCodec')
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.AudioChannels')
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.AudioLanguage')
            WINDOW.clearProperty('SkinHelper.MovieSet.' + str(i) + '.Subtitle')
        
            
        if xbmc.getCondVisibility("SubString(ListItem.Path,videodb://movies/sets/,left)"):
            dbId = xbmc.getInfoLabel("ListItem.DBID")   
            if dbId:
                #try to get from cache first
                if self.moviesetCache.has_key(dbId):
                    json_response = self.moviesetCache[dbId]
                else:
                    json_response = getJSON('VideoLibrary.GetMovieSetDetails', '{"setid": %s, "properties": [ "thumbnail" ], "movies": { "properties":  [ "rating", "art", "file", "year", "director", "writer", "playcount", "genre" , "thumbnail", "runtime", "studio", "plotoutline", "plot", "country", "streamdetails"], "sort": { "order": "ascending",  "method": "year" }} }' % dbId)
                    #save to cache
                    self.moviesetCache[dbId] = json_response
                if json_response:
                    count = 0
                    unwatchedcount = 0
                    watchedcount = 0
                    runtime = 0
                    runtime_mins = 0
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
                        set_fanart.append(art.get('fanart', ''))
                        WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.Title',item['label'])
                        WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.Poster',art.get('poster', ''))
                        WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.FanArt',art.get('fanart', ''))
                        WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.Landscape',art.get('landscape', ''))
                        WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.DiscArt',art.get('discart', ''))
                        WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.ClearLogo',art.get('clearlogo', ''))
                        WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.ClearArt',art.get('clearart', ''))
                        WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.Banner',art.get('banner', ''))
                        WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.Rating',str(item.get('rating', '')))
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
                                    WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.Resolution',resolution)
                                if stream.get("codec",""):
                                    WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.Codec',str(stream["codec"]))    
                                if stream.get("aspect",""):
                                    WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.AspectRatio',str(round(stream["aspect"], 2)))
                            if len(audiostreams) > 0:
                                #grab details of first audio stream
                                stream = audiostreams[0]
                                WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.AudioCodec',stream.get('codec',''))
                                WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.AudioChannels',str(stream.get('channels','')))
                                WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.AudioLanguage',stream.get('language',''))
                            if len(subtitles) > 0:
                                #grab details of first subtitle
                                WINDOW.setProperty('SkinHelper.MovieSet.' + str(count) + '.SubTitle',subtitles[0].get('language',''))

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
                    WINDOW.setProperty('SkinHelper.MovieSet.Plot', plot)
                    if json_response['limits']['total'] > 1:
                        WINDOW.setProperty('SkinHelper.MovieSet.ExtendedPlot', title_header + title_list + "[CR]" + plot)
                    else:
                        WINDOW.setProperty('SkinHelper.MovieSet.ExtendedPlot', plot)
                    WINDOW.setProperty('SkinHelper.MovieSet.Title', title_list)
                    WINDOW.setProperty('SkinHelper.MovieSet.Runtime', str(runtime / 60))
                    self.setDuration(str(runtime / 60))
                    durationString = self.getDurationString(runtime / 60)
                    if durationString:
                        WINDOW.setProperty('SkinHelper.MovieSet.Duration', durationString[2])
                        WINDOW.setProperty('SkinHelper.MovieSet.Duration.Hours', durationString[0])
                        WINDOW.setProperty('SkinHelper.MovieSet.Duration.Minutes', durationString[1])
                    WINDOW.setProperty('SkinHelper.MovieSet.Writer', " / ".join(writer))
                    WINDOW.setProperty('SkinHelper.MovieSet.Director', " / ".join(director))
                    self.setDirector(" / ".join(director))
                    WINDOW.setProperty('SkinHelper.MovieSet.Genre', " / ".join(genre))
                    self.setGenre(" / ".join(genre))
                    WINDOW.setProperty('SkinHelper.MovieSet.Country', " / ".join(country))
                    studioString = " / ".join(studio)
                    WINDOW.setProperty('SkinHelper.MovieSet.Studio', studioString)
                    self.setStudioLogo(studioString)
                   
                    WINDOW.setProperty('SkinHelper.MovieSet.Years', " / ".join(years))
                    WINDOW.setProperty('SkinHelper.MovieSet.Year', years[0] + " - " + years[-1])
                    WINDOW.setProperty('SkinHelper.MovieSet.Count', str(json_response['limits']['total']))
                    WINDOW.setProperty('SkinHelper.MovieSet.WatchedCount', str(watchedcount))
                    WINDOW.setProperty('SkinHelper.MovieSet.UnWatchedCount', str(unwatchedcount))
                    
                    #rotate fanart from movies in set while listitem is in focus
                    if xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnableExtraFanart)"):
                        fanartcount = 5
                        delaycount = 5
                        backgroundDelayStr = xbmc.getInfoLabel("skin.string(extrafanartdelay)")
                        if backgroundDelayStr:
                            fanartcount = int(backgroundDelayStr)
                            delaycount = int(backgroundDelayStr)
                        while dbId == xbmc.getInfoLabel("ListItem.DBID") and set_fanart != []:
                            
                            if fanartcount == delaycount:
                                random.shuffle(set_fanart)
                                WINDOW.setProperty('SkinHelper.ExtraFanArtPath', set_fanart[0])
                                fanartcount = 0
                            else:
                                xbmc.sleep(1000)
                                fanartcount += 1

    def setAddonName(self):
        # set addon name as property
        if not xbmc.Player().isPlayingAudio():
            if (xbmc.getCondVisibility("Container.Content(plugins) | !IsEmpty(Container.PluginName)")):
                AddonName = xbmc.getInfoLabel('Container.PluginName').decode('utf-8')
                AddonName = xbmcaddon.Addon(AddonName).getAddonInfo('name')
                WINDOW.setProperty("SkinHelper.Player.AddonName", AddonName)
            else:
                WINDOW.clearProperty("SkinHelper.Player.AddonName")
    
    def setGenre(self, genre=None):
        if not genre:
            genre = xbmc.getInfoLabel('ListItem.Genre').decode('utf-8')
        
        genres = []
        if "/" in genre:
            genres = genre.split(" / ")
        else:
            genres.append(genre)
        
        WINDOW.setProperty('SkinHelper.ListItemGenres', "[CR]".join(genres))
    
    def setDirector(self, director=None):
        if not director:
            director = xbmc.getInfoLabel('ListItem.Director').decode('utf-8')
        
        directors = []
        if "/" in director:
            directors = director.split(" / ")
        else:
            directors.append(director)
        
        WINDOW.setProperty('SkinHelper.ListItemDirectors', "[CR]".join(directors))
       
    def setPVRThumbs(self):
        thumb = None
        WINDOW.clearProperty("SkinHelper.PVR.Thumb") 
        WINDOW.clearProperty("SkinHelper.PVR.FanArt") 
        WINDOW.clearProperty("SkinHelper.PVR.ChannelLogo")
        WINDOW.clearProperty("SkinHelper.PVR.Poster")
        
        title = xbmc.getInfoLabel("ListItem.Title").decode('utf-8')
        channel = xbmc.getInfoLabel("ListItem.ChannelName").decode('utf-8')
        
        if xbmc.getCondVisibility("ListItem.IsFolder") and not channel and not title:
            #assume grouped recordings folderPath
            title = xbmc.getInfoLabel("ListItem.Label").decode('utf-8')

        if not xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnablePVRThumbs)") or not title:
            return
        
        dbID = title + channel
        
        if channel:
            logo = searchChannelLogo(channel)
            WINDOW.setProperty("SkinHelper.PVR.ChannelLogo",logo)
            
        logMsg("setPVRThumb dbID--> " + dbID)

        if xbmc.getInfoLabel("ListItem.Label").decode('utf-8') == "..":
            return
        
        thumb,fanart,poster,logo = getPVRThumbs(self.pvrArtCache, title, channel)
        
        if thumb:
            WINDOW.setProperty("SkinHelper.PVR.Thumb",thumb)
            self.pvrArtCache[dbID + "SkinHelper.PVR.Thumb"] = thumb
        if fanart:
            WINDOW.setProperty("SkinHelper.PVR.FanArt",fanart)
            self.pvrArtCache[dbID + "SkinHelper.PVR.FanArt"] = fanart
        if logo and channel:
            WINDOW.setProperty("SkinHelper.PVR.ChannelLogo",logo)
            self.pvrArtCache[channel + "SkinHelper.PVR.ChannelLogo"] = logo
        if poster:
            WINDOW.setProperty("SkinHelper.PVR.Poster",poster)
            self.pvrArtCache[dbID + "SkinHelper.PVR.Poster"] = poster
     
    def setStudioLogo(self, studio=None):
        
        if xbmc.getCondVisibility("Container.Content(studios)"):
            studio = xbmc.getInfoLabel('ListItem.Label').decode('utf-8')
        
        if not studio:
            studio = xbmc.getInfoLabel('ListItem.Studio').decode('utf-8')
        studiologo = None
        studiologoColor = None
        
        studios = []
        if "/" in studio:
            studios = studio.split(" / ")
            WINDOW.setProperty("SkinHelper.ListItemStudio", studios[0])
        else:
            studios.append(studio)
            WINDOW.setProperty("SkinHelper.ListItemStudio", studio)
        
        for studio in studios:
            studio = studio.lower()
            #find logo normal
            if self.allStudioLogos.has_key(studio):
                studiologo = self.allStudioLogos[studio]
            if self.allStudioLogosColor.has_key(studio):
                studiologoColor = self.allStudioLogosColor[studio]    
            
            if not studiologo and not studiologoColor:
                #find logo by substituting characters
                if " (" in studio:
                    studio = studio.split(" (")[0]
                    if self.allStudioLogos.has_key(studio):
                        studiologo = self.allStudioLogos[studio]
                    if self.allStudioLogosColor.has_key(studio):
                        studiologoColor = self.allStudioLogosColor[studio]
            
            if not studiologo and not studiologoColor:
                #find logo by substituting characters for pvr channels
                if " HD" in studio:
                    studio = studio.replace(" HD","")
                elif " " in studio:
                    studio = studio.replace(" ","")
                if self.allStudioLogos.has_key(studio):
                    studiologo = self.allStudioLogos[studio]
                if self.allStudioLogosColor.has_key(studio):
                    studiologoColor = self.allStudioLogosColor[studio]  
        
        if studiologo:
            WINDOW.setProperty("SkinHelper.ListItemStudioLogo", studiologo)
        else:
            WINDOW.clearProperty("SkinHelper.ListItemStudioLogo")
        
        if studiologoColor:
            WINDOW.setProperty("SkinHelper.ListItemStudioLogoColor", studiologo)
        else:
            WINDOW.clearProperty("SkinHelper.ListItemStudioLogoColor")
        
        #set formatted studio logo
        WINDOW.setProperty('SkinHelper.ListItemStudios', "[CR]".join(studios))
        return studiologo
                
    def getStudioLogos(self):
        #fill list with all studio logos
        allLogos = {}
        allLogosColor = {}
        allPaths = []
        allPathsColor = []

        CustomStudioImagesPath = xbmc.getInfoLabel("Skin.String(SkinHelper.CustomStudioImagesPath)").decode('utf-8')
        if CustomStudioImagesPath + xbmc.getSkinDir() != self.LastCustomStudioImagesPath:
            #only proceed if the custom path or skin has changed...
            self.LastCustomStudioImagesPath = CustomStudioImagesPath + xbmc.getSkinDir()
            
            #add the custom path to the list
            if CustomStudioImagesPath:
                path = CustomStudioImagesPath
                if not (CustomStudioImagesPath.endswith("/") or CustomStudioImagesPath.endswith("\\")):
                    CustomStudioImagesPath = CustomStudioImagesPath + os.sep()
                    allPaths.append(CustomStudioImagesPath)
            
            #add skin provided paths
            allPaths.append("special://skin/extras/flags/studios/")
            allPathsColor.append("special://skin/extras/flags/studioscolor/")
            
            #add images provided by the image resource addons
            allPaths.append("resource://resource.images.studios.white/")
            allPathsColor.append("resource://resource.images.studios.coloured/")
            allPaths.append("special://home/addons/resource.images.studios.white/")
            allPathsColor.append("special://home/addons/resource.images.studios.coloured/")
            
            #check all white logos
            for path in allPaths:               
                if xbmcvfs.exists(path):
                    dirs, files = xbmcvfs.listdir(path)
                    for file in files:
                        name = file.split(".")[0].lower()
                        if not allLogos.has_key(name):
                            allLogos[name] = path + file
                    for dir in dirs:
                        dirs2, files2 = xbmcvfs.listdir(os.path.join(path,dir))
                        for file in files2:
                            name = dir + "/" + file.split(".")[0].lower()
                            if not allLogos.has_key(name):
                                if "/" in path:
                                    sep = "/"
                                else:
                                    sep = "\\"
                                allLogos[name] = path + dir + sep + file
                    
            #check all color logos
            for path in allPathsColor:
                if xbmcvfs.exists(path):
                    dirs, files = xbmcvfs.listdir(path)
                    for file in files:
                        name = file.split(".")[0].lower()
                        if not allLogos.has_key(name):
                            allLogos[name] = path + file
                    for dir in dirs:
                        dirs2, files2 = xbmcvfs.listdir(os.path.join(path,dir))
                        for file in files2:
                            name = dir + "/" + file.split(".")[0].lower()
                            if not allLogos.has_key(name):
                                if "/" in path:
                                    sep = "/"
                                else:
                                    sep = "\\"
                                allLogos[name] = path + dir + sep + file
            
            #assign all found logos in the list
            self.allStudioLogos = allLogos
            self.allStudioLogosColor = allLogosColor
    
    def setDuration(self,currentDuration=None):
        if not currentDuration:
            currentDuration = xbmc.getInfoLabel("ListItem.Duration")
        
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
                WINDOW.setProperty('SkinHelper.ListItemDuration', durationString[2])
                WINDOW.setProperty('SkinHelper.ListItemDuration.Hours', durationString[0])
                WINDOW.setProperty('SkinHelper.ListItemDuration.Minutes', durationString[1])
            else:
                WINDOW.clearProperty('SkinHelper.ListItemDuration')
                WINDOW.clearProperty('SkinHelper.ListItemDuration.Hours')
                WINDOW.clearProperty('SkinHelper.ListItemDuration.Minutes')
        else:
            WINDOW.clearProperty('SkinHelper.ListItemDuration')
            WINDOW.clearProperty('SkinHelper.ListItemDuration.Hours')
            WINDOW.clearProperty('SkinHelper.ListItemDuration.Minutes')
        
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
            logMsg("ERROR in getDurationString ! --> " + str(e), 0)
            return None
        return ( hours, minutes, durationString )
              
    def checkMusicArt(self,widget=None):
        cacheFound = False
        cdArt = None
        LogoArt = None
        BannerArt = None
        extraFanArt = None
        Info = None
        TrackList = ""
        
        if widget:
            dbID = widget
        else:
            dbID = xbmc.getInfoLabel("ListItem.Artist").decode('utf-8') + xbmc.getInfoLabel("ListItem.Album").decode('utf-8')
        
        if dbID and self.lastMusicDbId == dbID:
            return
        
        logMsg("checkMusicArt dbID--> " + dbID)

        self.lastMusicDbId = dbID
        
        if not widget and (xbmc.getInfoLabel("ListItem.Label").decode('utf-8') == ".." or not xbmc.getInfoLabel("ListItem.FolderPath").decode('utf-8').startswith("musicdb") or not dbID):
            WINDOW.setProperty("SkinHelper.ExtraFanArtPath","") 
            WINDOW.clearProperty("SkinHelper.Music.BannerArt") 
            WINDOW.clearProperty("SkinHelper.Music.LogoArt") 
            WINDOW.clearProperty("SkinHelper.Music.DiscArt")
            WINDOW.clearProperty("SkinHelper.Music.Info")
            WINDOW.clearProperty("SkinHelper.Music.TrackList")
            return
        
        #get the items from cache first
        if self.musicArtCache.has_key(dbID + "SkinHelper.Music.DiscArt"):
            cacheFound = True
            cdArt = self.musicArtCache[dbID + "SkinHelper.Music.DiscArt"]            

        if self.musicArtCache.has_key(dbID + "SkinHelper.Music.LogoArt"):
            cacheFound = True
            LogoArt = self.musicArtCache[dbID + "SkinHelper.Music.LogoArt"]
                
        if self.musicArtCache.has_key(dbID + "SkinHelper.Music.BannerArt"):
            cacheFound = True
            BannerArt = self.musicArtCache[dbID + "SkinHelper.Music.BannerArt"]
        
        if self.musicArtCache.has_key(dbID + "extraFanArt"):
            cacheFound = True
            extraFanArt = self.musicArtCache[dbID + "extraFanArt"]
                
        if self.musicArtCache.has_key(dbID + "SkinHelper.Music.Info"):
            cacheFound = True
            Info = self.musicArtCache[dbID + "SkinHelper.Music.Info"]
        
        if self.musicArtCache.has_key(dbID + "SkinHelper.Music.TrackList"):
            cacheFound = True
            TrackList = self.musicArtCache[dbID + "SkinHelper.Music.TrackList"]

        if not cacheFound and not widget:
            logMsg("checkMusicArt no cache found for dbID--> " + dbID)
            path = None
            json_response = None
            folderPath = xbmc.getInfoLabel("ListItem.FolderPath").decode('utf-8')
            dbid = xbmc.getInfoLabel("ListItem.DBID")
            cdArt, LogoArt, BannerArt, extraFanArt, Info, TrackList = getMusicArtByDbId(dbid, getCurrentContentType())
      
            self.musicArtCache[dbID + "extraFanArt"] = extraFanArt
            self.musicArtCache[dbID + "SkinHelper.Music.DiscArt"] = cdArt
            self.musicArtCache[dbID + "SkinHelper.Music.BannerArt"] = BannerArt
            self.musicArtCache[dbID + "SkinHelper.Music.LogoArt"] = LogoArt
            self.musicArtCache[dbID + "SkinHelper.Music.TrackList"] = TrackList
            self.musicArtCache[dbID + "SkinHelper.Music.Info"] = Info

        #set properties
        WINDOW.setProperty("SkinHelper.ExtraFanArtPath",extraFanArt)
        WINDOW.setProperty("SkinHelper.Music.DiscArt",cdArt)
        WINDOW.setProperty("SkinHelper.Music.BannerArt",BannerArt)       
        WINDOW.setProperty("SkinHelper.Music.LogoArt",LogoArt)
        WINDOW.setProperty("SkinHelper.Music.TrackList",TrackList)
        WINDOW.setProperty("SkinHelper.Music.Info",Info)
              
    def setStreamDetails(self):
        streamdetails = None
        #clear props first
        WINDOW.clearProperty('SkinHelper.ListItemSubtitles')
        WINDOW.clearProperty('SkinHelper.ListItemAllAudioStreams')
        totalNodes = 50
        for i in range(totalNodes):
            if not WINDOW.getProperty('SkinHelper.ListItemAudioStreams.%d.AudioCodec' % i):
                break
            WINDOW.clearProperty('SkinHelper.ListItemAudioStreams.%d.Language' % i)
            WINDOW.clearProperty('SkinHelper.ListItemAudioStreams.%d.AudioCodec' % i)
            WINDOW.clearProperty('SkinHelper.ListItemAudioStreams.%d.AudioChannels' % i)
            WINDOW.clearProperty('SkinHelper.ListItemAudioStreams.%d'%i)
        
        contenttype = getCurrentContentType()
        dbId = xbmc.getInfoLabel("ListItem.DBID")
        if not dbId or dbId == "-1":
            return
        
        if self.streamdetailsCache.has_key(contenttype+dbId):
            #get data from cache
            streamdetails = self.streamdetailsCache[contenttype+dbId]
        else:
            streamdetails = None
            json_result = {}
            # get data from json
            if contenttype == "movies" and dbId:
                json_result = getJSON('VideoLibrary.GetMovieDetails', '{ "movieid": %d, "properties": [ "title", "streamdetails" ] }' %int(dbId))
            elif contenttype == "episodes" and dbId:
                json_result = getJSON('VideoLibrary.GetEpisodeDetails', '{ "episodeid": %d, "properties": [ "title", "streamdetails" ] }' %int(dbId))
            elif contenttype == "musicvideos" and dbId:
                json_result = getJSON('VideoLibrary.GetMusicVideoDetails', '{ "musicvideoid": %d, "properties": [ "title", "streamdetails" ] }' %int(dbId))       
            if json_result.has_key("streamdetails"): 
                streamdetails = json_result["streamdetails"]
            self.streamdetailsCache[contenttype+dbId] = streamdetails
        
        if streamdetails:
            audio = streamdetails['audio']
            subtitles = streamdetails['subtitle']
            allAudio = []
            allAudioStr = []
            allSubs = []
            count = 0
            for item in audio:
                if str(item['language']) not in allAudio:
                    allAudio.append(str(item['language']))
                    codec = item['codec']
                    channels = item['channels']
                    if "ac3" in codec: codec = "Dolby D"
                    elif "dca" in codec: codec = "DTS"
                    elif "dts-hd" in codec or "dtshd" in codec: codec = "DTS HD"
                    
                    if channels == 1: channels = "1.0"
                    elif channels == 2: channels = "2.0"
                    elif channels == 3: channels = "2.1"
                    elif channels == 4: channels = "4.0"
                    elif channels == 5: channels = "5.0"
                    elif channels == 6: channels = "5.1"
                    elif channels == 7: channels = "6.1"
                    elif channels == 8: channels = "7.1"
                    elif channels == 9: channels = "8.1"
                    elif channels == 10: channels = "9.1"
                    else: channels = str(channels)
                    language = item['language']
                    if not language: language = "?"
                    WINDOW.setProperty('SkinHelper.ListItemAudioStreams.%d.Language' % count, item['language'])
                    WINDOW.setProperty('SkinHelper.ListItemAudioStreams.%d.AudioCodec' % count, item['codec'])
                    WINDOW.setProperty('SkinHelper.ListItemAudioStreams.%d.AudioChannels' % count, str(item['channels']))
                    sep = "•".decode('utf-8')
                    audioStr = '%s %s %s %s %s' %(language,sep,codec,sep,channels)
                    WINDOW.setProperty('SkinHelper.ListItemAudioStreams.%d'%count, audioStr)
                    allAudioStr.append(audioStr)
                    count += 1
            count = 0
            for item in subtitles:
                if str(item['language']) not in allSubs:
                    allSubs.append(str(item['language']))
                    WINDOW.setProperty('SkinHelper.ListItemSubtitles.%d' % count, item['language'])
                    count += 1
            WINDOW.setProperty('SkinHelper.ListItemSubtitles', " / ".join(allSubs))
            WINDOW.setProperty('SkinHelper.ListItemAllAudioStreams', " / ".join(allAudioStr))
      
    def setForcedView(self):
        if xbmc.getCondVisibility("Window.IsMedia + Skin.HasSetting(SkinHelper.ForcedViews.Enabled)"):
            contenttype = getCurrentContentType()
            if contenttype != self.lastContentType:
                currentForcedView = xbmc.getInfoLabel("Skin.String(SkinHelper.ForcedViews.%s)" %contenttype)
                if contenttype and currentForcedView and currentForcedView != "None":
                    xbmc.executebuiltin("Container.SetViewMode(%s)" %currentForcedView)
                    WINDOW.setProperty("SkinHelper.ForcedView",currentForcedView)
                    xbmc.sleep(250)
                    xbmc.executebuiltin("Container.SetViewMode(%s)" %currentForcedView)
                    xbmc.executebuiltin("SetFocus(%s)" %currentForcedView)
                    self.lastContentType = contenttype
                    return
        else:
            WINDOW.clearProperty("SkinHelper.ForcedView")
        
    def checkExtraFanArt(self):
        
        lastPath = None
        efaPath = None
        efaFound = False
        liArt = None
        containerPath = xbmc.getInfoLabel("Container.FolderPath").decode('utf-8')
        
        if xbmc.getCondVisibility("Window.IsActive(movieinformation)"):
            return
        
        #always clear the individual fanart items first
        totalNodes = 50
        for i in range(totalNodes):
            if not WINDOW.getProperty('SkinHelper.ExtraFanArt.' + str(i)):
                break
            WINDOW.clearProperty('SkinHelper.ExtraFanArt.' + str(i))
        
        #get the item from cache first
        if self.extraFanartCache.has_key(self.liPath):
            if self.extraFanartCache[self.liPath][0] == "None":
                WINDOW.setProperty("SkinHelper.ExtraFanArtPath","")
                return
            else:
                WINDOW.setProperty("SkinHelper.ExtraFanArtPath",self.extraFanartCache[self.liPath][0])
                count = 0
                for file in self.extraFanartCache[self.liPath][1]:
                    WINDOW.setProperty("SkinHelper.ExtraFanArt." + str(count),file)
                    count +=1  
                return
        
        if not xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnableExtraFanart) + [Window.IsActive(videolibrary) | Window.IsActive(movieinformation)] + !Container.Scrolling"):
            WINDOW.setProperty("SkinHelper.ExtraFanArtPath","")
            return
        
        if (self.liPath != None and (xbmc.getCondVisibility("Container.Content(movies) | Container.Content(seasons) | Container.Content(episodes) | Container.Content(tvshows)")) and not "videodb:" in self.liPath):
                           
            if xbmc.getCondVisibility("Container.Content(episodes)"):
                liArt = xbmc.getInfoLabel("ListItem.Art(tvshow.fanart)").decode('utf-8')
            
            # do not set extra fanart for virtuals
            if (("plugin://" in self.liPath) or ("addon://" in self.liPath) or ("sources" in self.liPath) or ("plugin://" in containerPath) or ("sources://" in containerPath) or ("plugin://" in containerPath)):
                WINDOW.setProperty("SkinHelper.ExtraFanArtPath","")
                self.extraFanartCache[self.liPath] = "None"
                lastPath = None
            else:

                if xbmcvfs.exists(self.liPath + "extrafanart/"):
                    efaPath = self.liPath + "extrafanart/"
                else:
                    pPath = self.liPath.rpartition("/")[0]
                    pPath = pPath.rpartition("/")[0]
                    if xbmcvfs.exists(pPath + "/extrafanart/"):
                        efaPath = pPath + "/extrafanart/"
                        
                if xbmcvfs.exists(efaPath):
                    dirs, files = xbmcvfs.listdir(efaPath)
                    count = 0
                    extraFanArtfiles = []
                    for file in files:
                        if file.lower().endswith(".jpg"):
                            efaFound = True
                            WINDOW.setProperty("SkinHelper.ExtraFanArt." + str(count),efaPath+file)
                            extraFanArtfiles.append(efaPath+file)
                            count +=1  
       
                if (efaPath != None and efaFound == True):
                    if lastPath != efaPath:
                        WINDOW.setProperty("SkinHelper.ExtraFanArtPath",efaPath)
                        self.extraFanartCache[self.liPath] = [efaPath, extraFanArtfiles]
                        lastPath = efaPath       
                else:
                    WINDOW.setProperty("SkinHelper.ExtraFanArtPath","")
                    self.extraFanartCache[self.liPath] = ["None",[]]
                    lastPath = None
        else:
            WINDOW.setProperty("SkinHelper.ExtraFanArtPath","")
            lastPath = None

    def setRottenRatings(self):
        WINDOW.clearProperty('SkinHelper.RottenTomatoesRating')
        WINDOW.clearProperty('SkinHelper.RottenTomatoesAudienceRating')
        WINDOW.clearProperty('SkinHelper.RottenTomatoesConsensus')
        WINDOW.clearProperty('SkinHelper.RottenTomatoesAwards')
        WINDOW.clearProperty('SkinHelper.RottenTomatoesBoxOffice')
        contenttype = getCurrentContentType()
        imdbnumber = xbmc.getInfoLabel("ListItem.IMDBNumber")
        if (contenttype == "movies" or contenttype=="setmovies") and imdbnumber:
            if self.rottenCache.has_key(imdbnumber):
                #get data from cache
                result = self.rottenCache[imdbnumber]
            elif not WINDOW.getProperty("SkinHelper.DisableInternetLookups"):
                url = 'http://www.omdbapi.com/?i=%s&plot=short&tomatoes=true&r=json' %imdbnumber
                res = requests.get(url)
                result = json.loads(res.content.decode('utf-8','replace'))
                if result:
                    self.rottenCache[imdbnumber] = result
            if result:
                criticsscore = result.get('tomatoMeter',"")
                criticconsensus = result.get('tomatoConsensus',"")
                audiencescore = result.get('Metascore',"")
                awards = result.get('Awards',"")
                boxoffice = result.get('BoxOffice',"")
                if criticsscore:
                    WINDOW.setProperty("SkinHelper.RottenTomatoesRating",criticsscore)
                if audiencescore:
                    WINDOW.setProperty("SkinHelper.RottenTomatoesAudienceRating",audiencescore)
                if criticconsensus:
                    WINDOW.setProperty("SkinHelper.RottenTomatoesConsensus",criticconsensus)
                if awards:
                    WINDOW.setProperty("SkinHelper.RottenTomatoesAwards",awards)
                if boxoffice:
                    WINDOW.setProperty("SkinHelper.RottenTomatoesBoxOffice",boxoffice)

    def focusEpisode(self):
        # monitor episodes for auto focus first unwatched - Helix only as it is included in Kodi as of Isengard by default
        if xbmc.getCondVisibility("Skin.HasSetting(AutoFocusUnwatchedEpisode)"):
            
            #store unwatched episodes
            if ((xbmc.getCondVisibility("Container.Content(seasons) | Container.Content(tvshows)")) and xbmc.getCondVisibility("!IsEmpty(ListItem.Property(UnWatchedEpisodes))")):
                try:
                    self.unwatched = int(xbmc.getInfoLabel("ListItem.Property(UnWatchedEpisodes)"))
                except: pass
            
            if (xbmc.getCondVisibility("Container.Content(episodes) | Container.Content(seasons)")):
                
                if (xbmc.getInfoLabel("Container.FolderPath") != self.lastEpPath and self.unwatched != 0):
                    totalItems = 0
                    curView = xbmc.getInfoLabel("Container.Viewmode") 
                    
                    # get all views from views-file
                    viewId = None
                    skin_view_file = os.path.join(xbmc.translatePath('special://skin/extras'), "views.xml")
                    tree = etree.parse(skin_view_file)
                    root = tree.getroot()
                    for view in root.findall('view'):
                        if viewString == xbmc.getLocalizedString(int(view.attrib['languageid'])):
                            viewId=view.attrib['value']
                    
                    wid = xbmcgui.getCurrentWindowId()
                    window = xbmcgui.Window( wid )        
                    control = window.getControl(int(viewId))
                    totalItems = int(xbmc.getInfoLabel("Container.NumItems"))
                    
                    #only do a focus if we're on top of the list, else skip to prevent bouncing of the list
                    if not int(xbmc.getInfoLabel("Container.Position")) > 1:
                        if (xbmc.getCondVisibility("Container.SortDirection(ascending)")):
                            curItem = 0
                            control.selectItem(0)
                            xbmc.sleep(250)
                            while ((xbmc.getCondVisibility("Container.Content(episodes) | Container.Content(seasons)")) and totalItems >= curItem):
                                if (xbmc.getInfoLabel("Container.ListItem(" + str(curItem) + ").Overlay") != "OverlayWatched.png" and xbmc.getInfoLabel("Container.ListItem(" + str(curItem) + ").Label") != ".." and not xbmc.getInfoLabel("Container.ListItem(" + str(curItem) + ").Label").startswith("*")):
                                    if curItem != 0:
                                        control.selectItem(curItem)
                                    break
                                else:
                                    curItem += 1
                        
                        elif (xbmc.getCondVisibility("Container.SortDirection(descending)")):
                            curItem = totalItems
                            control.selectItem(totalItems)
                            xbmc.sleep(250)
                            while ((xbmc.getCondVisibility("Container.Content(episodes) | Container.Content(seasons)")) and curItem != 0):
                                
                                if (xbmc.getInfoLabel("Container.ListItem(" + str(curItem) + ").Overlay") != "OverlayWatched.png"):
                                    control.selectItem(curItem-1)
                                    break
                                else:    
                                    curItem -= 1
                                        
            self.lastEpPath = xbmc.getInfoLabel("Container.FolderPath")

                    
class Kodi_Monitor(xbmc.Monitor):
    
    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)

    def onNotification(self,sender,method,data):
    
        if method == "VideoLibrary.OnUpdate":
            #update nextup list when library has changed
            WINDOW.setProperty("widgetreload", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            #refresh some widgets when library has changed
            WINDOW.setProperty("resetVideoDbCache","reset")
        
        if method == "AudioLibrary.OnUpdate":
            WINDOW.setProperty("widgetreloadmusic", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            #refresh some widgets when library has changed
            WINDOW.setProperty("resetMusicArtCache","reset")
        
        if method == "Player.OnPlay":
            
            try:
                secondsToDisplay = int(xbmc.getInfoLabel("Skin.String(SkinHelper.ShowInfoAtPlaybackStart)"))
            except:
                secondsToDisplay = 0
            
            logMsg("onNotification - ShowInfoAtPlaybackStart - number of seconds: " + str(secondsToDisplay),0)
            
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

                                           