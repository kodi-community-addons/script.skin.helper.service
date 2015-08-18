#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcgui
import threading
import xbmcvfs
import random
from xml.dom.minidom import parse
import xml.etree.ElementTree as xmltree
import base64
import json
import urllib

from Utils import *

class BackgroundsUpdater(threading.Thread):
    
    event = None
    exit = False
    allBackgrounds = {}
    tempBlacklist = set()
    defBlacklist = set()
    lastPicturesPath = None
    smartShortcuts = {}
    cachePath = None
    SmartShortcutsCachePath = None
    delayedTaskInterval = 30
    refreshSmartshortcuts = False
    lastWindow = None
    
    def __init__(self, *args):
        self.lastPicturesPath = xbmc.getInfoLabel("skin.string(SkinHelper.PicturesBackgroundPath)")
        self.cachePath = os.path.join(ADDON_DATA_PATH,"backgroundscache.json")
        self.SmartShortcutsCachePath = os.path.join(ADDON_DATA_PATH,"smartshotcutscache.json")

        logMsg("BackgroundsUpdater - started")
        self.event =  threading.Event()
        threading.Thread.__init__(self, *args)    
    
    def stop(self):
        logMsg("BackgroundsUpdater - stop called",0)
        self.saveCacheToFile()
        self.exit = True
        self.event.set()

    def run(self):

        KodiMonitor = xbmc.Monitor()
            
        #first run get backgrounds immediately from filebased cache and reset the cache in memory to populate all images from scratch
        try:
            self.getCacheFromFile()
            self.UpdateBackgrounds()
        except Exception as e:
            logMsg("ERROR in BackgroundsUpdater ! --> " + str(e), 0)
        
        self.allBackgrounds = {}
        self.smartShortcuts = {}
         
        while (self.exit != True):
            
            if (not xbmc.getCondVisibility("Window.IsActive(fullscreenvideo)")):

                try:
                    backgroundDelay = int(xbmc.getInfoLabel("skin.string(SkinHelper.RandomFanartDelay)"))
                except:
                    backgroundDelay = 30
                
                # force refresh smart shortcuts when skin settings launched (so user sees any newly added smartshortcuts)
                currentWindow = xbmc.getInfoLabel("$INFO[Window.Property(xmlfile)]")
                if ("skinshortcuts.xml" in currentWindow or "SkinSettings" in currentWindow) and currentWindow != self.lastWindow and self.refreshSmartshortcuts == False:
                    self.lastWindow = currentWindow
                    self.refreshSmartshortcuts = True
                    self.UpdateBackgrounds()
                
                # Update home backgrounds every interval (default 60 seconds)
                if backgroundDelay != 0:
                    if (self.delayedTaskInterval >= backgroundDelay):
                        self.delayedTaskInterval = 0
                        try:
                            self.UpdateBackgrounds()
                        except Exception as e:
                            logMsg("ERROR in UpdateBackgrounds ! --> " + str(e), 0)
            
            xbmc.sleep(150)
            self.delayedTaskInterval += 0.15
                               
    def saveCacheToFile(self):
        #safety check: does the config directory exist?
        if not xbmcvfs.exists(ADDON_DATA_PATH + os.sep):
            xbmcvfs.mkdir(ADDON_DATA_PATH)
        
        self.allBackgrounds["blacklist"] = list(self.defBlacklist)
        json.dump(self.allBackgrounds, open(self.cachePath,'w'))
        
        json.dump(self.smartShortcuts, open(self.SmartShortcutsCachePath,'w'))
        

    def getCacheFromFile(self):
        if xbmcvfs.exists(self.cachePath):
            with open(self.cachePath) as data_file:    
                data = json.load(data_file)
                
                self.defBlacklist = set(data["blacklist"])
                self.allBackgrounds = data
        
        if xbmcvfs.exists(self.SmartShortcutsCachePath):
            with open(self.SmartShortcutsCachePath) as data_file:    
                self.smartShortcuts = json.load(data_file)    
                

    def getImageFromPath(self, libPath, fallbackImage=None):
        
        if self.exit:
            return None
            
        libPath = getContentPath(libPath)
        logMsg("getting images for path " + libPath)

        #is path in the temporary blacklist ?
        if libPath in self.tempBlacklist:
            logMsg("path blacklisted - skipping for path " + libPath)
            return fallbackImage
        
        #is path in the definitive blacklist ?
        if libPath in self.defBlacklist:
            logMsg("path blacklisted - skipping for path " + libPath)
            return fallbackImage
        
        #no blacklist so read cache and/or path
        logMsg("path is NOT blacklisted (or blacklist file error) - continuing for path " + libPath)
        images = []
               
        #cache entry exists and cache is not expired, load cache entry
        if self.allBackgrounds.has_key(libPath):
            logMsg("load random image from the cache file... " + libPath)
            image = None
            image = random.choice(self.allBackgrounds[libPath])
            if image:
                logMsg("loading done setting image from cache... " + image)
                return image
            else:
                logMsg("cache entry empty ?...skipping...")
        else:
            #no cache file so try to load images from the path
            logMsg("get images from the path or plugin... " + libPath)
            if libPath.startswith("plugin://"):
                media_type = "files"
            else:
                media_type = "video"
            media_array = None
            media_array = getJSON('Files.GetDirectory','{ "properties": ["title","art"], "directory": "' + libPath + '", "media": "' + media_type + '", "limits": {"end":150}, "sort": { "order": "ascending", "method": "random", "ignorearticle": true } }')
            if(media_array != None and media_array.has_key('files')):
                for media in media_array['files']:
                    if media.has_key('art') and not media['title'].lower() == "next page":
                        if media['art'].has_key('fanart'):
                            image = media['art']['fanart']
                            images.append(image)
                        if media['art'].has_key('tvshow.fanart'):
                            image = media['art']['tvshow.fanart']
                            images.append(image)
            else:
                logMsg("media array empty or error so add this path to blacklist..." + libPath)
                if libPath.startswith("musicdb://") or libPath.startswith("videodb://") or libPath.startswith("library://") or libPath.endswith(".xsp") or libPath.startswith("plugin://plugin.video.emby"):
                    #addpath to temporary blacklist
                    self.tempBlacklist.add(libPath)
                    return fallbackImage
                else:
                    #blacklist this path
                    self.defBlacklist.add(libPath)
                    return fallbackImage
        
        #all is fine, we have some images to randomize and return one
        image = fallbackImage
        if images != []:
            self.allBackgrounds[libPath] = images
            random.shuffle(images)
            image = images[0]
            logMsg("setting random image.... " + image)
        else:
            logMsg("image array or cache empty so skipping this path until next restart - " + libPath)
            self.tempBlacklist.add(libPath)
            
        return image

    def getPicturesBackground(self):
        logMsg("setting pictures background...")
        customPath = xbmc.getInfoLabel("skin.string(SkinHelper.CustomPicturesBackgroundPath)")
        if (self.lastPicturesPath != customPath):
            if (self.allBackgrounds.has_key("pictures")):
                logMsg("path has changed for pictures - clearing cache...")
                del self.allBackgrounds["pictures"]
            
        self.lastPicturesPath = customPath

        try:
            if (self.allBackgrounds.has_key("pictures")):
                #get random image from our global cache file
                image = None
                image = random.choice(self.allBackgrounds["pictures"])
                if image:
                    logMsg("setting random image from cache.... " + image)
                return image 
            else:
                #load the pictures from the custom path or from all picture sources
                images = []
                
                if customPath:
                    #load images from custom path
                    dirs, files = xbmcvfs.listdir(customPath)
                    #pick all images from path
                    for file in files:
                        if file.endswith(".jpg") or file.endswith(".png") or file.endswith(".JPG") or file.endswith(".PNG"):
                            image = os.path.join(customPath,file)
                            images.append(image)
                else:
                    #load picture sources
                    media_array = getJSON('Files.GetSources','{"media": "pictures"}')
                    if(media_array != None and media_array.has_key('sources')):
                        for source in media_array['sources']:
                            if source.has_key('file'):
                                if not "plugin://" in source["file"]:
                                    dirs, files = xbmcvfs.listdir(source["file"])
                                    if dirs:
                                        #pick 10 random dirs
                                        randomdirs = []
                                        randomdirs.append(os.path.join(source["file"],random.choice(dirs)))
                                        randomdirs.append(os.path.join(source["file"],random.choice(dirs)))
                                        randomdirs.append(os.path.join(source["file"],random.choice(dirs)))
                                        randomdirs.append(os.path.join(source["file"],random.choice(dirs)))
                                        randomdirs.append(os.path.join(source["file"],random.choice(dirs)))
                                        randomdirs.append(os.path.join(source["file"],random.choice(dirs)))
                                        randomdirs.append(os.path.join(source["file"],random.choice(dirs)))
                                        randomdirs.append(os.path.join(source["file"],random.choice(dirs)))
                                        randomdirs.append(os.path.join(source["file"],random.choice(dirs)))
                                        randomdirs.append(os.path.join(source["file"],random.choice(dirs)))
                                        
                                        #pick 5 images from each dir
                                        for dir in randomdirs:
                                            subdirs, files = xbmcvfs.listdir(dir)
                                            count = 0
                                            for file in files:
                                                if ((file.endswith(".jpg") or file.endswith(".png") or file.endswith(".JPG") or file.endswith(".PNG")) and count < 5):
                                                    image = os.path.join(dir,file)
                                                    images.append(image)
                                                    count += 1
                                    if files:
                                        #pick 10 images from root
                                        count = 0
                                        for file in files:
                                            if ((file.endswith(".jpg") or file.endswith(".png") or file.endswith(".JPG") or file.endswith(".PNG")) and count < 10):
                                                image = os.path.join(source["file"],file)
                                                images.append(image)
                                                count += 1
                
                #store images in the cache
                self.allBackgrounds["pictures"] = images
                
                # return a random image
                if images != []:
                    random.shuffle(images)
                    image = images[0]
                    logMsg("setting random image.... " + image)
                    return image
                else:
                    logMsg("image sources array or cache empty so skipping this path until next restart - " + libPath)
                    return None
        #if something fails, return None
        except:
            logMsg("exception occured in getPicturesBackground.... ")
            return None            
               
    def getGlobalBackground(self, fallbackImage=None):
        #just get a random image from all the images in the cache
        image = fallbackImage
        if self.allBackgrounds != {}:
            #get random image from our global cache
            images = []
            for key in self.allBackgrounds:
                randomimage = random.choice(self.allBackgrounds[key])
                if randomimage:
                    images.append(randomimage)
            
            if images:
                image = random.choice(images)

            return image 
                  
    def UpdateBackgrounds(self):
        
        allSmartShortcuts = []
        
        #get all movies  
        WINDOW.setProperty("SkinHelper.AllMoviesBackground",self.getImageFromPath("videodb://movies/titles/"))
        
        #get all tvshows  
        WINDOW.setProperty("SkinHelper.AllTvShowsBackground",self.getImageFromPath("videodb://tvshows/titles/"))
        
        #get all musicvideos  
        WINDOW.setProperty("SkinHelper.AllMusicVideosBackground",self.getImageFromPath("videodb://musicvideos/titles/"))
        
        #get all music  
        WINDOW.setProperty("SkinHelper.AllMusicBackground",self.getImageFromPath("musicdb://artists/"))
        
        #get global fanart background 
        WINDOW.setProperty("SkinHelper.GlobalFanartBackground",self.getGlobalBackground())
         
        #get in progress movies  
        WINDOW.setProperty("SkinHelper.InProgressMoviesBackground",self.getImageFromPath("special://skin/extras/widgetplaylists/inprogressmovies.xsp"))

        #get recent and unwatched movies
        WINDOW.setProperty("SkinHelper.RecentMoviesBackground",self.getImageFromPath("videodb://recentlyaddedmovies/"))
           
        #unwatched movies
        WINDOW.setProperty("SkinHelper.UnwatchedMoviesBackground",self.getImageFromPath("special://skin/extras/widgetplaylists/unwatchedmovies.xsp"))
      
        #get in progress tvshows
        WINDOW.setProperty("SkinHelper.InProgressShowsBackground",self.getImageFromPath("library://video/inprogressshows.xml"))
        
        #get recent episodes
        WINDOW.setProperty("SkinHelper.RecentEpisodesBackground",self.getImageFromPath("videodb://recentlyaddedepisodes/"))
        
        #get pictures background
        WINDOW.setProperty("SkinHelper.PicturesBackground", self.getPicturesBackground())
        
        #smart shortcuts --> emby nodes
        if xbmc.getCondVisibility("System.HasAddon(plugin.video.emby) + Skin.HasSetting(SmartShortcuts.emby)"):
            logMsg("Processing smart shortcuts for emby nodes.... ")
            
            if self.smartShortcuts.has_key("emby") and not self.refreshSmartshortcuts:
                logMsg("get emby entries from cache.... ")
                nodes = self.smartShortcuts["emby"]
                for node in nodes:
                    key = node[0]
                    label = node[1]
                    path = node[2]
                    image = self.getImageFromPath(node[2])
                    WINDOW.setProperty(key + ".image", image)
                    WINDOW.setProperty(key + ".title", label)
                    WINDOW.setProperty(key + ".path", path)
            
            elif WINDOW.getProperty("emby.nodes.total"):
                
                logMsg("no cache - Get emby entries from file.... ")            
               
                embyProperty = WINDOW.getProperty("emby.nodes.total")
                contentStrings = ["", ".recent", ".inprogress", ".unwatched", ".recentepisodes", ".inprogressepisodes", ".nextepisodes"]
                if embyProperty:
                    nodes = []
                    totalNodes = int(embyProperty)
                    for i in range(totalNodes):
                        for contentString in contentStrings:
                            key = "emby.nodes.%s%s"%(str(i),contentString)
                            path = WINDOW.getProperty("emby.nodes.%s%s.path"%(str(i),contentString))
                            label = WINDOW.getProperty("emby.nodes.%s%s.title"%(str(i),contentString))
                            if path:
                                nodes.append( (key, label, path ) )
                                image = self.getImageFromPath(path)
                                if image:
                                    WINDOW.setProperty("emby.nodes.%s%s.image"%(str(i),contentString),image)
                                if contentString == "": 
                                    allSmartShortcuts.append("emby.nodes." + str(i) )
                                
                    self.smartShortcuts["emby"] = nodes
                                        
        #smart shortcuts --> playlists
        if xbmc.getCondVisibility("Skin.HasSetting(SmartShortcuts.playlists)"):
            logMsg("Processing smart shortcuts for playlists.... ")
            try:
                if self.smartShortcuts.has_key("playlists") and not self.refreshSmartshortcuts:
                    logMsg("get playlist entries from cache.... ")
                    playlists = self.smartShortcuts["playlists"]
                    for playlist in playlists:
                        playlistCount = playlist[0]
                        WINDOW.setProperty("playlist." + str(playlistCount) + ".image", self.getImageFromPath(playlist[3]))
                        WINDOW.setProperty("playlist." + str(playlistCount) + ".label",  playlist[1])
                        WINDOW.setProperty("playlist." + str(playlistCount) + ".title",  playlist[1])
                        WINDOW.setProperty("playlist." + str(playlistCount) + ".action", playlist[2])
                        WINDOW.setProperty("playlist." + str(playlistCount) + ".path", playlist[2])
                        WINDOW.setProperty("playlist." + str(playlistCount) + ".content", playlist[3])
                        WINDOW.setProperty("playlist." + str(playlistCount) + ".type", playlist[4])
                else:
                    logMsg("no cache - Get playlist entries from file.... ")
                    playlistCount = 0
                    playlists = []                   
                    
                    paths = [['special://videoplaylists/','VideoLibrary'], ['special://musicplaylists/','MusicLibrary']]
                    for playlistpath in paths:
                        media_array = None
                        media_array = getJSON('Files.GetDirectory','{ "directory": "%s", "media": "files" }' % playlistpath[0] )
                        if media_array != None and media_array.has_key('files'):
                            for item in media_array['files']:
                                if item["file"].endswith(".xsp"):
                                    playlist = item["file"]
                                    contents = xbmcvfs.File(playlist, 'r')
                                    contents_data = contents.read().decode('utf-8')
                                    contents.close()
                                    xmldata = xmltree.fromstring(contents_data.encode('utf-8'))
                                    type = "unknown"
                                    label = item["label"]
                                    image = self.getImageFromPath(playlist)
                                    for line in xmldata.getiterator():
                                        if line.tag == "smartplaylist":
                                            type = line.attrib['type']
                                        if line.tag == "name":
                                            label = line.text
                                    path = "ActivateWindow(%s,%s,return)" %(playlistpath[1],playlist)
                                    WINDOW.setProperty("playlist." + str(playlistCount) + ".image", image)
                                    WINDOW.setProperty("playlist." + str(playlistCount) + ".label", label)
                                    WINDOW.setProperty("playlist." + str(playlistCount) + ".title", label)
                                    WINDOW.setProperty("playlist." + str(playlistCount) + ".action", path)
                                    WINDOW.setProperty("playlist." + str(playlistCount) + ".path", path)
                                    WINDOW.setProperty("playlist." + str(playlistCount) + ".content", playlist)
                                    WINDOW.setProperty("playlist." + str(playlistCount) + ".type", type)
                                    allSmartShortcuts.append("playlist." + str(playlistCount) )
                                    playlists.append( (playlistCount, label, path, playlist, type ))
                                    playlistCount += 1
                    
                    self.smartShortcuts["playlists"] = playlists
            except Exception as e:
                #something wrong so disable the smartshortcuts for this section for now
                xbmc.executebuiltin("Skin.Reset(SmartShortcuts.playlists)")
                logMsg("Error while processing smart shortcuts for playlists - set disabled.... ", 0)
                logMsg(str(e),0)
                    
        #smart shortcuts --> favorites
        if xbmc.getCondVisibility("Skin.HasSetting(SmartShortcuts.favorites)"):
            logMsg("Processing smart shortcuts for favourites.... ")
            try:
                if self.smartShortcuts.has_key("favourites") and not self.refreshSmartshortcuts:
                    logMsg("get favourites entries from cache.... ")
                    favourites = self.smartShortcuts["favourites"]
                    for favourite in favourites:
                        playlistCount = favourite[0]
                        WINDOW.setProperty("favorite." + str(playlistCount) + ".image", self.getImageFromPath(favourite[2]))
                        WINDOW.setProperty("favorite." + str(playlistCount) + ".label", favourite[1])
                        WINDOW.setProperty("favorite." + str(playlistCount) + ".title", favourite[1])
                        WINDOW.setProperty("favorite." + str(playlistCount) + ".action", favourite[2])
                        WINDOW.setProperty("favorite." + str(playlistCount) + ".path", favourite[2])
                        WINDOW.setProperty("favorite." + str(playlistCount) + ".content", favourite[3])
                else:
                    logMsg("no cache - Get favourite entries from file.... ")
                    favoritesCount = 0
                    favourites = []
                    fav_file = xbmc.translatePath( 'special://profile/favourites.xml' ).decode("utf-8")
                    if xbmcvfs.exists( fav_file ):
                        doc = parse( fav_file )
                        listing = doc.documentElement.getElementsByTagName( 'favourite' )
                        
                        for count, favourite in enumerate(listing):
                            name = favourite.attributes[ 'name' ].nodeValue
                            path = favourite.childNodes [ 0 ].nodeValue
                            content = getContentPath(path)
                            if (path.startswith("ActivateWindow(Videos") or path.startswith("ActivateWindow(10025") or path.startswith("ActivateWindow(videos") or path.startswith("ActivateWindow(Music") or path.startswith("ActivateWindow(10502")) and not "script://" in path and not "mode=9" in path and not "search" in path:
                                image = self.getImageFromPath(path)
                                if image != None:
                                    WINDOW.setProperty("favorite." + str(favoritesCount) + ".image", image)
                                    WINDOW.setProperty("favorite." + str(favoritesCount) + ".label", name)
                                    WINDOW.setProperty("favorite." + str(favoritesCount) + ".title", name)
                                    WINDOW.setProperty("favorite." + str(favoritesCount) + ".action", path)
                                    WINDOW.setProperty("favorite." + str(favoritesCount) + ".path", path)
                                    WINDOW.setProperty("favorite." + str(favoritesCount) + ".content", content)
                                    allSmartShortcuts.append("favorite." + str(favoritesCount) )
                                    favourites.append( (favoritesCount, name, path, content) )
                                    favoritesCount += 1
                                    
                    self.smartShortcuts["favourites"] = favourites
            except Exception as e:
                #something wrong so disable the smartshortcuts for this section for now
                xbmc.executebuiltin("Skin.Reset(SmartShortcuts.favorites)")
                logMsg("Error while processing smart shortcuts for favourites - set disabled.... ",0)
                logMsg(str(e),0)                
               
        #smart shortcuts --> plex nodes
        if xbmc.getCondVisibility("Skin.HasSetting(SmartShortcuts.plex)"):
            nodes = []
            logMsg("Processing smart shortcuts for plex nodes.... ")
            
            if self.smartShortcuts.has_key("plex") and not self.refreshSmartshortcuts:
                logMsg("get plex entries from cache.... ")
                nodes = self.smartShortcuts["plex"]
                for node in nodes:
                    key = node[0]
                    label = node[1]
                    path = node[2]
                    image = self.getImageFromPath(node[2])
                    WINDOW.setProperty(key + ".background", image)
                    WINDOW.setProperty(key + ".image", image)
            elif WINDOW.getProperty("plexbmc.0.title"):
                logMsg("no cache - Get plex entries from file.... ")    
                                   
                contentStrings = ["", ".ondeck", ".recent", ".unwatched"]
                if WINDOW.getProperty("plexbmc.0.title"):
                    nodes = []
                    totalNodes = 50
                    for i in range(totalNodes):
                        for contentString in contentStrings:
                            key = "plexbmc.%s%s"%(str(i),contentString)
                            path = WINDOW.getProperty("plexbmc.%s%s.content"%(str(i),contentString))
                            label = WINDOW.getProperty("plexbmc.%s%s.title"%(str(i),contentString))
                            plextype = WINDOW.getProperty("plexbmc.%s.type" %str(i))
                            if path:
                                nodes.append( (key, label, path ) )
                                image = self.getImageFromPath(path)
                                if image:
                                    WINDOW.setProperty("plexbmc.%s%s.background"%(str(i),contentString),image)
                                    WINDOW.setProperty("plexbmc.%s%s.image"%(str(i),contentString),image)
                                    if plextype == "movie":
                                        WINDOW.setProperty("plexfanartbg", image)
                                    if contentString == "":
                                        allSmartShortcuts.append("plexbmc." + str(i) )
                            else:
                                break
                
                    #channels
                    plextitle = WINDOW.getProperty("plexbmc.channels.title")
                    key = "plexbmc.channels"
                    plexcontent = WINDOW.getProperty("plexbmc.channels.path")
                    if plexcontent:
                        image = self.getImageFromPath(plexcontent)
                        nodes.append( (key, plextitle, plexcontent ) )
                        if image:
                            WINDOW.setProperty("plexbmc.channels.background", image)
                            WINDOW.setProperty("plexbmc.channels.image", image)
                            allSmartShortcuts.append("plexbmc.channels")
                            
                    
                    self.smartShortcuts["plex"] = nodes
                 
        #smart shortcuts --> netflix nodes
        if xbmc.getCondVisibility("System.HasAddon(plugin.video.netflixbmc) + Skin.HasSetting(SmartShortcuts.netflix)") and WINDOW.getProperty("netflixready") == "ready":
            
            if self.smartShortcuts.has_key("netflix") and not self.refreshSmartshortcuts:
                logMsg("get netflix entries from cache.... ")
                nodes = self.smartShortcuts["netflix"]
                for node in nodes:
                    key = node[0]
                    label = node[1]
                    content = node[2]
                    path = node[3]
                    type = node[4]
                    if len(node) == 6:
                        imagespath = node[5]
                    else:
                        imagespath = content
                    image = self.getImageFromPath(imagespath)
                    WINDOW.setProperty(key + ".title", label)
                    WINDOW.setProperty(key + ".content", content)
                    WINDOW.setProperty(key + ".path", path)
                    WINDOW.setProperty(key + ".image", image)            
            
            else:
                nodes = []
                netflixAddon = xbmcaddon.Addon('plugin.video.netflixbmc')
                logMsg("no cache - Generate netflix entries.... ")
                
                #generic netflix shortcut
                key = "netflix.generic"
                label = netflixAddon.getAddonInfo('name')
                content = "plugin://plugin.video.netflixbmc/?mode=main&widget=true&url"
                path = "ActivateWindow(Videos,%s,return)" %content.replace("&widget=true","")
                imagespath = "plugin://plugin.video.netflixbmc/?mode=listViewingActivity&thumb=&type=both&url&widget=true"
                image = self.getImageFromPath(imagespath, "special://home/addons/plugin.video.netflixbmc/fanart.jpg")
                type = "media"
                nodes.append( (key, label, content, path, type, imagespath ) )
                
                #generic netflix mylist
                key = "netflix.generic.mylist"
                label = netflixAddon.getLocalizedString(30002)
                content = "plugin://plugin.video.netflixbmc/?mode=listSliderVideos&thumb&type=both&widget=true&url=slider_38"
                path = "ActivateWindow(Videos,%s,return)" %content.replace("&widget=true","")
                image = self.getImageFromPath(content, "special://home/addons/plugin.video.netflixbmc/fanart.jpg")
                type = "movies"
                nodes.append( (key, label, content, type, path ) )
                
                #generic netflix suggestions
                key = "netflix.generic.suggestions"
                label = netflixAddon.getLocalizedString(30143)
                content = "plugin://plugin.video.netflixbmc/?mode=listSliderVideos&thumb&type=both&widget=true&url=slider_2"
                path = "ActivateWindow(Videos,%s,return)" %content.replace("&widget=true","")
                image = self.getImageFromPath(content, "special://home/addons/plugin.video.netflixbmc/fanart.jpg")
                type = "movies"
                nodes.append( (key, label, content, type, path ) )
                
                #generic netflix inprogress
                key = "netflix.generic.inprogress"
                label = netflixAddon.getLocalizedString(30121)
                content = "plugin://plugin.video.netflixbmc/?mode=listSliderVideos&thumb&type=both&widget=true&url=slider_0"
                path = "ActivateWindow(Videos,%s,return)" %content.replace("&widget=true","")
                image = self.getImageFromPath(content, "special://home/addons/plugin.video.netflixbmc/fanart.jpg")
                type = "movies"
                nodes.append( (key, label, content, type, path ) )
                
                #generic netflix recent
                key = "netflix.generic.recent"
                label = netflixAddon.getLocalizedString(30003)
                content = "plugin://plugin.video.netflixbmc/?mode=listVideos&thumb&type=both&widget=true&url=http%3a%2f%2fwww.netflix.com%2fWiRecentAdditionsGallery%3fnRR%3dreleaseDate%26nRT%3dall%26pn%3d1%26np%3d1%26actionMethod%3djson"
                path = "ActivateWindow(Videos,%s,return)" %content.replace("&widget=true","")
                image = self.getImageFromPath(content, "special://home/addons/plugin.video.netflixbmc/fanart.jpg")
                type = "movies"
                nodes.append( (key, label, content, type, path ) )

                #netflix movies
                key = "netflix.movies"
                label = netflixAddon.getAddonInfo('name') + " " + netflixAddon.getLocalizedString(30011)
                content = "plugin://plugin.video.netflixbmc/?mode=main&thumb&type=movie&url&widget=true"
                path = "ActivateWindow(Videos,%s,return)" %content.replace("&widget=true","")
                imagespath = "plugin://plugin.video.netflixbmc/?mode=listViewingActivity&thumb=&type=movie&url&widget=true"
                image = self.getImageFromPath(imagespath, "special://home/addons/plugin.video.netflixbmc/fanart.jpg")
                type = "movies"
                nodes.append( (key, label, content, path, type, imagespath ) )
                
                #netflix movies mylist
                key = "netflix.movies.mylist"
                label = netflixAddon.getLocalizedString(30011) + " - " + netflixAddon.getLocalizedString(30002)
                content = "plugin://plugin.video.netflixbmc/?mode=listVideos&thumb&type=movie&widget=true&url=http%3a%2f%2fwww.netflix.com%2fMyList%3fleid%3d595%26link%3dseeall"
                path = "ActivateWindow(Videos,%s,return)" %content.replace("&widget=true","")
                image = self.getImageFromPath(content, "special://home/addons/plugin.video.netflixbmc/fanart.jpg")
                type = "movies"
                nodes.append( (key, label, content, type, path ) )
                
                #netflix movies suggestions
                key = "netflix.movies.suggestions"
                label = netflixAddon.getLocalizedString(30011) + " - " + netflixAddon.getLocalizedString(30143)
                content = "plugin://plugin.video.netflixbmc/?mode=listSliderVideos&thumb&type=movie&widget=true&url=slider_2"
                path = "ActivateWindow(Videos,%s,return)" %content.replace("&widget=true","")
                image = self.getImageFromPath(content, "special://home/addons/plugin.video.netflixbmc/fanart.jpg")
                type = "movies"
                nodes.append( (key, label, content, type, path ) )

                #netflix movies inprogress
                key = "netflix.movies.inprogress"
                label = netflixAddon.getLocalizedString(30011) + " - " + netflixAddon.getLocalizedString(30121)
                content = "plugin://plugin.video.netflixbmc/?mode=listSliderVideos&thumb&type=movie&widget=true&url=slider_4"
                path = "ActivateWindow(Videos,%s,return)" %content.replace("&widget=true","")
                image = self.getImageFromPath(content, "special://home/addons/plugin.video.netflixbmc/fanart.jpg")
                type = "movies"
                nodes.append( (key, label, content, type, path ) )
                
                #netflix movies recent
                key = "netflix.movies.recent"
                label = netflixAddon.getLocalizedString(30011) + " - " + netflixAddon.getLocalizedString(30003)
                content = "plugin://plugin.video.netflixbmc/?mode=listVideos&thumb&type=movie&widget=true&url=http%3a%2f%2fwww.netflix.com%2fWiRecentAdditionsGallery%3fnRR%3dreleaseDate%26nRT%3dall%26pn%3d1%26np%3d1%26actionMethod%3djson"
                path = "ActivateWindow(Videos,%s,return)" %content.replace("&widget=true","")
                image = self.getImageFromPath(content, "special://home/addons/plugin.video.netflixbmc/fanart.jpg")
                type = "movies"
                nodes.append( (key, label, content, type, path ) )
                
                #netflix tvshows
                key = "netflix.tvshows"
                label = netflixAddon.getAddonInfo('name') + " " + netflixAddon.getLocalizedString(30012)
                content = "plugin://plugin.video.netflixbmc/?mode=main&thumb&type=tv&url"
                path = "ActivateWindow(Videos,%s,return)" %content.replace("&widget=true","")
                imagespath = "plugin://plugin.video.netflixbmc/?mode=listViewingActivity&thumb=&type=movie&url&widget=true"
                image = self.getImageFromPath(imagespath, "special://home/addons/plugin.video.netflixbmc/fanart.jpg")
                type = "tvshows"
                nodes.append( (key, label, content, path, type, imagespath ) )
                
                #netflix tvshows mylist
                key = "netflix.tvshows.mylist"
                label = netflixAddon.getLocalizedString(30012) + " - " + netflixAddon.getLocalizedString(30002)
                content = "plugin://plugin.video.netflixbmc/?mode=listVideos&thumb&type=tv&widget=true&url=http%3a%2f%2fwww.netflix.com%2fMyList%3fleid%3d595%26link%3dseeall"
                path = "ActivateWindow(Videos,%s,return)" %content.replace("&widget=true","")
                image = self.getImageFromPath(content, "special://home/addons/plugin.video.netflixbmc/fanart.jpg")
                type = "tvshows"
                nodes.append( (key, label, content, type, path ) )
                
                #netflix tvshows suggestions
                key = "netflix.tvshows.suggestions"
                label = netflixAddon.getLocalizedString(30012) + " - " + netflixAddon.getLocalizedString(30143)
                content = "plugin://plugin.video.netflixbmc/?mode=listSliderVideos&thumb&type=tv&widget=true&url=slider_2"
                path = "ActivateWindow(Videos,%s,return)" %content.replace("&widget=true","")
                image = self.getImageFromPath(content, "special://home/addons/plugin.video.netflixbmc/fanart.jpg")
                type = "tvshows"
                nodes.append( (key, label, content, type, path ) )

                #netflix tvshows inprogress
                key = "netflix.tvshows.inprogress"
                label = netflixAddon.getLocalizedString(30012) + " - " + netflixAddon.getLocalizedString(30121)
                content = "plugin://plugin.video.netflixbmc/?mode=listSliderVideos&thumb&type=tv&widget=true&url=slider_4"
                path = "ActivateWindow(Videos,%s,return)" %content.replace("&widget=true","")
                image = self.getImageFromPath(content, "special://home/addons/plugin.video.netflixbmc/fanart.jpg")
                type = "tvshows"
                nodes.append( (key, label, content, type, path ) )
                
                #netflix tvshows recent
                key = "netflix.tvshows.recent"
                label = netflixAddon.getLocalizedString(30012) + " - " + netflixAddon.getLocalizedString(30003)
                content = "plugin://plugin.video.netflixbmc/?mode=listVideos&thumb&type=tv&widget=true&url=http%3a%2f%2fwww.netflix.com%2fWiRecentAdditionsGallery%3fnRR%3dreleaseDate%26nRT%3dall%26pn%3d1%26np%3d1%26actionMethod%3djson"
                path = "ActivateWindow(Videos,%s,return)" %content.replace("&widget=true","")
                image = self.getImageFromPath(content, "special://home/addons/plugin.video.netflixbmc/fanart.jpg")
                type = "tvshows"
                nodes.append( (key, label, content, type, path ) )
                
                for node in nodes:
                    key = node[0]
                    label = node[1]
                    content = node[2]
                    path = node[3]
                    type = node[4]
                    if len(node) == 6:
                        imagespath = node[5]
                    else:
                        imagespath = content
                    image = self.getImageFromPath(imagespath)
                    WINDOW.setProperty(key + ".title", label)
                    WINDOW.setProperty(key + ".content", content)
                    WINDOW.setProperty(key + ".path", path)
                    WINDOW.setProperty(key + ".image", image)
                    WINDOW.setProperty(key + ".type", type) 
                    
                self.smartShortcuts["netflix"] = nodes
                allSmartShortcuts.append("netflix.generic")
                allSmartShortcuts.append("netflix.movies")
                allSmartShortcuts.append("netflix.tvshows")
                
        if allSmartShortcuts:
            self.smartShortcuts["allSmartShortcuts"] = allSmartShortcuts
            WINDOW.setProperty("allSmartShortcuts", repr(allSmartShortcuts))
        elif self.smartShortcuts.has_key("allSmartShortcuts"):
            WINDOW.setProperty("allSmartShortcuts", repr(self.smartShortcuts["allSmartShortcuts"]))
        
        self.refreshSmartshortcuts = False        
                
                
                