#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcplugin
import xbmcaddon
import xbmcgui
import xbmc
import xbmcvfs
import os
import json
import re, urlparse
import requests
import sys
import urllib,urllib2,re
import base64
from traceback import print_exc

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_ICON = ADDON.getAddonInfo('icon')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_PATH = ADDON.getAddonInfo('path').decode("utf-8")
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_DATA_PATH = xbmc.translatePath("special://profile/addon_data/%s" % ADDON_ID).decode("utf-8")
KODI_VERSION  = int(xbmc.getInfoLabel( "System.BuildVersion" ).split(".")[0])
WINDOW = xbmcgui.Window(10000)
SETTING = ADDON.getSetting

fields_base = '"dateadded", "file", "lastplayed","plot", "title", "art", "playcount",'
fields_file = fields_base + '"streamdetails", "director", "resume", "runtime",'
fields_movies = fields_file + '"plotoutline", "sorttitle", "cast", "votes", "showlink", "top250", "trailer", "year", "country", "studio", "set", "genre", "mpaa", "setid", "rating", "tag", "tagline", "writer", "originaltitle", "imdbnumber"'
fields_tvshows = fields_base + '"sorttitle", "mpaa", "premiered", "year", "episode", "watchedepisodes", "votes", "rating", "studio", "season", "genre", "cast", "episodeguide", "tag", "originaltitle", "imdbnumber"'
fields_episodes = fields_file + '"cast", "productioncode", "rating", "votes", "episode", "showtitle", "tvshowid", "season", "firstaired", "writer", "originaltitle"'
fields_musicvideos = fields_file + '"genre", "artist", "tag", "album", "track", "studio", "year"'
fields_files = fields_file + fields_movies + ", " + fields_tvshows + ", " + fields_episodes
fields_songs = '"artist", "title", "rating", "fanart", "thumbnail", "duration", "playcount", "comment", "file", "album", "lastplayed"'
fields_albums = '"title", "fanart", "thumbnail", "genre", "displayartist", "artist", "genreid", "musicbrainzalbumartistid", "year", "rating", "artistid", "musicbrainzalbumid", "theme", "description", "type", "style", "playcount", "albumlabel", "mood"'
fields_pvrrecordings = '"art", "channel", "directory", "endtime", "file", "genre", "icon", "playcount", "plot", "plotoutline", "resume", "runtime", "starttime", "streamurl", "title"'

def logMsg(msg, level = 1):
    doDebugLog = False
    if doDebugLog or level == 0:
        if isinstance(msg, unicode):
            msg = msg.encode('utf-8')
        xbmc.log("Skin Helper Service --> " + msg)
        if "exception" in msg.lower() or "error" in msg.lower():
            print_exc()
            
def getContentPath(libPath):
    if "$INFO" in libPath and not "reload=" in libPath:
        libPath = libPath.replace("$INFO[Window(Home).Property(", "")
        libPath = libPath.replace(")]", "")
        libPath = WINDOW.getProperty(libPath)    
    if "Activate" in libPath:
        if "ActivateWindow(MusicLibrary," in libPath:
            libPath = libPath.replace("ActivateWindow(MusicLibrary," ,"musicdb://").lower()
            libPath = libPath.replace(",return","/")
            libPath = libPath.replace(", return","/")
        else:
            libPath = libPath.split(",",1)[1]
            libPath = libPath.replace(",return","")
            libPath = libPath.replace(", return","")
        
        libPath = libPath.replace(")","")
        libPath = libPath.replace("\"","")
        libPath = libPath.replace("musicdb://special://","special://")
        libPath = libPath.replace("videodb://special://","special://")
    if "&reload=" in libPath:
        libPath = libPath.split("&reload=")[0]
    return libPath

def getJSON(method,params):
    json_response = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method" : "%s", "params": %s, "id":1 }' %(method, try_encode(params)))
    jsonobject = json.loads(json_response.decode('utf-8','replace'))
   
    if(jsonobject.has_key('result')):
        jsonobject = jsonobject['result']
        if jsonobject.has_key('files'):
            return jsonobject['files']
        elif jsonobject.has_key('movies'):
            return jsonobject['movies']
        elif jsonobject.has_key('tvshows'):
            return jsonobject['tvshows']
        elif jsonobject.has_key('episodes'):
            return jsonobject['episodes']
        elif jsonobject.has_key('musicvideos'):
            return jsonobject['musicvideos']
        elif jsonobject.has_key('channels'):
            return jsonobject['channels']
        elif jsonobject.has_key('recordings'):
            return jsonobject['recordings']
        elif jsonobject.has_key('songs'):
            return jsonobject['songs']
        elif jsonobject.has_key('albums'):
            return jsonobject['albums']
        elif jsonobject.has_key('songdetails'):
            return jsonobject['songdetails']
        elif jsonobject.has_key('albumdetails'):
            return jsonobject['albumdetails']
        elif jsonobject.has_key('artistdetails'):
            return jsonobject['artistdetails']
        elif jsonobject.has_key('favourites'):
            if jsonobject['favourites']:
                return jsonobject['favourites']
            else:
                return {}
        elif jsonobject.has_key('tvshowdetails'):
            return jsonobject['tvshowdetails']
        elif jsonobject.has_key('episodedetails'):
            return jsonobject['episodedetails']
        elif jsonobject.has_key('moviedetails'):
            return jsonobject['moviedetails']
        elif jsonobject.has_key('setdetails'):
            return jsonobject['setdetails']
        elif jsonobject.has_key('sets'):
            return jsonobject['sets']
        elif jsonobject.has_key('video'):
            return jsonobject['video']
        elif jsonobject.has_key('artists'):
            return jsonobject['artists']
        elif jsonobject.has_key('sources'):
            if jsonobject['sources']:
                return jsonobject['sources']
            else:
                return {}
        elif jsonobject.has_key('addons'):
            return jsonobject['addons']
        else:
            logMsg("getJson - invalid result for Method %s - params: %s - response: %s" %(method,params, str(jsonobject))) 
            return {}
    else:
        logMsg("getJson - empty result for Method %s - params: %s - response: %s" %(method,params, str(jsonobject))) 
        return {}

def try_encode(text, encoding="utf-8"):
    try:
        return text.encode(encoding,"ignore")
    except:
        return text       
        
def setSkinVersion():
    skin = xbmc.getSkinDir()
    skinLabel = xbmcaddon.Addon(id=skin).getAddonInfo('name')
    skinVersion = xbmcaddon.Addon(id=skin).getAddonInfo('version')
    WINDOW.setProperty("SkinHelper.skinTitle",skinLabel + " - " + xbmc.getLocalizedString(19114) + ": " + skinVersion)
    WINDOW.setProperty("SkinHelper.skinVersion",xbmc.getLocalizedString(19114) + ": " + skinVersion)
    WINDOW.setProperty("SkinHelper.Version",ADDON_VERSION.replace(".",""))
        
def createListItem(item):

    itemtype = "Video"
    if "type" in item:
        if "artist" in item["type"] or "song" in item["type"] or "album" in item["type"]:
            itemtype = "Music"

    liz = xbmcgui.ListItem(item['title'])
    liz.setInfo( type=itemtype, infoLabels={ "Title": item['title'] })
    liz.setProperty('IsPlayable', 'true')
    season = None
    episode = None
    
    if "runtime" in item:
        liz.setInfo( type=itemtype, infoLabels={ "duration": str(item['runtime']/60) })
    
    if "file" in item:
        liz.setPath(item['file'])
        liz.setProperty("path", item['file'])
    
    if "episode" in item:
        episode = "%.2d" % float(item['episode'])
        liz.setInfo( type=itemtype, infoLabels={ "Episode": item['episode'] })
    
    if "season" in item:
        season = "%.2d" % float(item['season'])
        liz.setInfo( type=itemtype, infoLabels={ "Season": item['season'] })
        
    if season and episode:
        episodeno = "s%se%s" %(season,episode)
        liz.setProperty("episodeno", episodeno)
    
    if "episodeid" in item:
        liz.setProperty("DBID", str(item['episodeid']))
        liz.setInfo( type=itemtype, infoLabels={ "DBID": str(item['episodeid']) })
        liz.setIconImage('DefaultTVShows.png')
        
    if "songid" in item:
        liz.setProperty("DBID", str(item['songid']))
        liz.setIconImage('DefaultAudio.png')
        liz.setLabel2(item['artist'][0])
    
    if "channel" in item:
        liz.setLabel2(item['channel'])
        
    if "movieid" in item:
        liz.setProperty("DBID", str(item['movieid']))
        liz.setInfo( type=itemtype, infoLabels={ "DBID": str(item['movieid']) })
        liz.setIconImage('DefaultMovies.png')
    
    if "musicvideoid" in item:
        liz.setProperty("DBID", str(item['musicvideoid']))
        liz.setIconImage('DefaultMusicVideos.png')
    
    if "type" in item:
        liz.setProperty("type", item['type'])
    
    if "plot" in item:
        liz.setInfo( type=itemtype, infoLabels={ "Plot": item['plot'] })
    
    if "album_description" in item:
        liz.setProperty("Album_Description",item['album_description'])
    
    if "artist" in item:
        if itemtype == "Music":
            liz.setInfo( type=itemtype, infoLabels={ "Artist": " / ".join(item['artist']) })
        else:
            liz.setInfo( type=itemtype, infoLabels={ "Artist": item['artist'] })
        
    if "votes" in item:
        liz.setInfo( type=itemtype, infoLabels={ "votes": item['votes'] })
    
    if "trailer" in item:
        liz.setInfo( type=itemtype, infoLabels={ "trailer": item['trailer'] })
        liz.setProperty("trailer", item['trailer'])
        
    if "dateadded" in item:
        liz.setInfo( type=itemtype, infoLabels={ "dateadded": item['dateadded'] })
        
    if "album" in item:
        liz.setInfo( type=itemtype, infoLabels={ "album": item['album'] })
        
    if "plotoutline" in item:
        liz.setInfo( type=itemtype, infoLabels={ "plotoutline ": item['plotoutline'] })
        
    if "studio" in item:
        liz.setInfo( type=itemtype, infoLabels={ "studio": " / ".join(item['studio']) })
        
    if "playcount" in item:
        liz.setInfo( type=itemtype, infoLabels={ "playcount": item['playcount'] })
        
    if "mpaa" in item:
        liz.setInfo( type=itemtype, infoLabels={ "mpaa": item['mpaa'] })
        
    if "tagline" in item:
        liz.setInfo( type=itemtype, infoLabels={ "tagline": item['tagline'] })
    
    if "showtitle" in item:
        liz.setInfo( type=itemtype, infoLabels={ "TVshowTitle": item['showtitle'] })
    
    if "rating" in item:
        liz.setInfo( type=itemtype, infoLabels={ "Rating": str(round(float(item['rating']),1)) })
    
    if "playcount" in item:
        liz.setInfo( type=itemtype, infoLabels={ "Playcount": item['playcount'] })
    
    if "director" in item:
        liz.setInfo( type=itemtype, infoLabels={ "Director": " / ".join(item['director']) })
    
    if "writer" in item:
        liz.setInfo( type=itemtype, infoLabels={ "Writer": " / ".join(item['writer']) })
    
    if "genre" in item:
        liz.setInfo( type=itemtype, infoLabels={ "genre": " / ".join(item['genre']) })
        
    if "year" in item:
        liz.setInfo( type=itemtype, infoLabels={ "year": item['year'] })
    
    if "firstaired" in item:
        liz.setInfo( type=itemtype, infoLabels={ "premiered": item['firstaired'] })

    if "premiered" in item:
        liz.setInfo( type=itemtype, infoLabels={ "premiered": item['premiered'] })
        
    if "cast" in item:
        listCast = []
        listCastAndRole = []
        for castmember in item["cast"]:
            listCast.append( castmember["name"] )
            listCastAndRole.append( (castmember["name"], castmember["role"]) ) 
        cast = [listCast, listCastAndRole]
        liz.setInfo( type=itemtype, infoLabels={ "Cast": cast[0] })
        liz.setInfo( type=itemtype, infoLabels={ "CastAndRole": cast[1] })
    
    if "resume" in item:
        liz.setProperty("resumetime", str(item['resume']['position']))
        liz.setProperty("totaltime", str(item['resume']['total']))
    
    if "art" in item:
        art = item['art']
        liz.setThumbnailImage(item['art'].get('thumb',''))
    else:
        art = []
        if "fanart" in item:
            art.append(("fanart",item["fanart"]))
        if "thumbnail" in item:
            art.append(("thumb",item["thumbnail"]))
            liz.setThumbnailImage(item["thumbnail"])
        if "icon" in item:
            art.append(("thumb",item["icon"]))
            liz.setThumbnailImage(item["icon"])
    liz.setArt(art)
    

    if "streamdetails" in item:
        for key, value in item['streamdetails'].iteritems():
            for stream in value:
                liz.addStreamInfo( key, stream )
    
    return liz
    
def detectPluginContent(plugin,skipscan=False):
    #based on the properties in the listitem we try to detect the content
    
    #safety check: check if no library windows are active to prevent any addons setting the view
    curWindow = xbmc.getInfoLabel("$INFO[Window.Property(xmlfile)]")
    if curWindow.endswith("Nav.xml") or curWindow == "AddonBrowser.xml" or curWindow.startswith("MyPVR"):
        return None, None
    
    if not skipscan:
        media_array = getJSON('Files.GetDirectory','{ "directory": "%s", "media": "files", "properties": ["title", "file", "thumbnail", "episode", "showtitle", "season", "album", "artist", "imdbnumber", "firstaired", "mpaa", "trailer", "studio", "art"], "limits": {"end":3} }' %plugin)
        for item in media_array:
            image = None
            if item.has_key("art"):
                if item["art"].has_key("fanart"):
                    image = item["art"]["fanart"]
                elif item["art"].has_key("tvshow.fanart"):
                    image = item["art"]["tvshow.fanart"]
            if not item.has_key("showtitle") and not item.has_key("artist"):
                #these properties are only returned in the json response if we're looking at actual file content...
                # if it's missing it means this is a main directory listing and no need to scan the underlying listitems.
                return ("files", image)
            if not item.has_key("showtitle") and item.has_key("artist"):
                ##### AUDIO ITEMS ####
                if item["type"] == "artist" or item["artist"][0] == item["title"]:
                    return ("artists", image)
                elif item["type"] == "album" or item["album"] == item["title"]:
                    return ("albums", image)
                elif (item["type"] == "song" and not "play_album" in item["file"]) or (item["artist"] and item["album"]):
                    return ("songs", image)
            else:    
                ##### VIDEO ITEMS ####
                if (item["showtitle"] and not item["artist"]):
                    #this is a tvshow, episode or season...
                    if item["type"] == "season" or (item["season"] > -1 and item["episode"] == -1):
                        return ("seasons", image)
                    elif item["type"] == "episode" or item["season"] > -1 and item["episode"] > -1:
                        return ("episodes", image)
                    else:
                        return ("tvshows", image)
                elif (item["artist"]):
                    #this is a musicvideo!
                    return ("musicvideos", image)
                elif item["type"] == "movie" or item["imdbnumber"] or item["mpaa"] or item["trailer"] or item["studio"]:
                    return ("movies", image)
    
    #last resort or skipscan chosen - detect content based on the path
    if "movie" in plugin or "box" in plugin or "dvd" in plugin or "rentals" in plugin:
        type = "movies"
    elif "album" in plugin:
        type = "albums"
    elif "show" in plugin:
        type = "tvshows"
    elif "song" in plugin:
        type = "songs"
    elif "musicvideo" in plugin:
        type = "musicvideos"
    else:
        type = "unknown"
    return (type, None)

    
def getTMDBimage(title):
    apiKey = base64.b64decode("NDc2N2I0YjJiYjk0YjEwNGZhNTUxNWM1ZmY0ZTFmZWM=")
    opener = urllib2.build_opener()
    userAgent = "Mozilla/5.0 (Windows NT 5.1; rv:25.0) Gecko/20100101 Firefox/25.0"
    opener.addheaders = [('User-agent', userAgent)]
    coverUrl = ""
    fanartUrl = ""
    matchFound = False
    videoTypes = ["tv","movie"]
    
    for videoType in videoTypes:
    
        try: 
            url = 'http://api.themoviedb.org/3/search/%s?api_key=%s&language=en&query=%s' %(videoType,apiKey,try_encode(title))
            response = requests.get(url)
            data = json.loads(response.content.decode('utf-8','replace'))
            if data and data.get("results",None):
                for item in data["results"]:
                    name = item.get("name")
                    if not name: name = item.get("title")
                    if name:
                        original_name = item.get("original_name","")
                        title_alt = title.lower().replace(" ","").replace("-","").replace(":","").replace("&","").replace(",","")
                        name_alt = name.lower().replace(" ","").replace("-","").replace(":","").replace("&","").replace(",","")
                        org_name_alt = original_name.lower().replace(" ","").replace("-","").replace(":","").replace("&","").replace(",","")
                        
                        original_name = item.get("original_name")
                        if title in name == title or original_name == title:
                            matchFound = True
                        elif name.split(" (")[0] == title or title_alt == name_alt or title_alt == org_name_alt:
                            matchFound = True
                            
                        if matchFound:
                            coverUrl = item.get("poster_path","")
                            fanartUrl = item.get("backdrop_path","")
                            
                            logMsg("getTMDBimage - TMDB match found for %s !" %title)
                            
                            if coverUrl:
                                coverUrl = "http://image.tmdb.org/t/p/original"+coverUrl
                                try: opener.open(coverUrl).read()
                                except: pass
                                
                            if fanartUrl:
                                fanartUrl = "http://image.tmdb.org/t/p/original"+fanartUrl
                                try: opener.open(fanartUrl).read()
                                except: pass
                            return (coverUrl, fanartUrl)
        
        except Exception as e:
            if "getaddrinfo failed" in str(e):
                #no internet access - disable lookups for now
                WINDOW.setProperty("SkinHelper.DisableInternetLookups","disable")
                logMsg("getTMDBimage - no internet access, disabling internet lookups for now")
            else:
                logMsg("getTMDBimage - Error in getTMDBimage --> " + str(e),0)
    
    logMsg("TMDB match NOT found for %s !" %title)
    return ("", "")
    
def getPVRThumbs(persistant_cache,title,channel):
    dbID = title + channel
    cacheFound = False
    fanart = ""
    logo = ""
    poster = ""
    thumb = ""

    logMsg("getPVRThumb for %s %s--> "%(title,channel))
        
    #get the items from cache first
    cache = WINDOW.getProperty(dbID.encode('utf-8') + "SkinHelper.PVR.cache")
    if cache:
        fanart = WINDOW.getProperty(dbID.encode('utf-8') + "SkinHelper.PVR.FanArt").decode('utf-8')
        poster = WINDOW.getProperty(dbID.encode('utf-8') + "SkinHelper.PVR.Poster").decode('utf-8')
        logo = WINDOW.getProperty(channel.encode('utf-8') + "SkinHelper.PVR.ChannelLogo").decode('utf-8')
        thumb = WINDOW.getProperty(dbID.encode('utf-8') + "SkinHelper.PVR.Thumb").decode('utf-8')
        cacheFound = True
    
    if not cacheFound:
        logMsg("getPVRThumb no cache found for dbID--> " + dbID)
                
        #lookup local library
        item = None
        json_result = getJSON('VideoLibrary.GetTvShows','{ "filter": {"operator":"is", "field":"title", "value":"%s"}, "properties": [ %s ] }' %(title,fields_tvshows))
        if len(json_result) > 0:
            item = json_result[0]
        else:
            json_result = getJSON('VideoLibrary.GetMovies','{ "filter": {"operator":"is", "field":"title", "value":"%s"}, "properties": [ %s ] }' %(title,fields_movies))
            if len(json_result) > 0:
                item = json_result[0]
        if item: 
            poster = item["art"].get("poster","")
            thumb = item["art"].get("landscape","")
            fanart = item["art"].get("fanart","")
            if not thumb: thumb = fanart
            logMsg("getPVRThumb artwork found in local library for dbID--> " + dbID)
        
        #is the item in the persistant cache ?
        if not thumb and persistant_cache:
            if persistant_cache.has_key(dbID + "SkinHelper.PVR.Thumb"): 
                thumb = persistant_cache[dbID + "SkinHelper.PVR.Thumb"]
                logMsg("getPVRThumb artwork found in persistant cache for dbID--> " + dbID)
                if thumb: cacheFound = True
            if persistant_cache.has_key(dbID + "SkinHelper.PVR.FanArt"): 
                fanart = persistant_cache[dbID + "SkinHelper.PVR.FanArt"]
                if fanart: cacheFound = True
            if persistant_cache.has_key(dbID + "SkinHelper.PVR.Poster"): 
                poster = persistant_cache[dbID + "SkinHelper.PVR.Poster"]
                if poster: cacheFound = True
            if persistant_cache.has_key(dbID + "SkinHelper.PVR.ChannelLogo"): 
                logo = persistant_cache[dbID + "SkinHelper.PVR.ChannelLogo"]
                if logo: cacheFound = True
        
        #if nothing in library or persistant cache, perform the internet scraping
        if not cacheFound and not WINDOW.getProperty("SkinHelper.DisableInternetLookups"):
        
            #lookup actual recordings (for grouped recordings and actual icons provided by pvr)
            try:
                json_query = getJSON('PVR.GetRecordings', '{ "properties": [ %s ]}' %( fields_pvrrecordings))
                for item in json_query:
                    if title in item['title'] or title in item["file"]:
                        if not channel: channel = item["channel"]
                        #only some pvr's provide a thumb for recordings - assuming here that currently only mediaportal PVR does this.
                        if "mediaportal" in xbmc.getInfoLabel("Pvr.BackendName").lower() and not thumb:
                            thumb = item['icon']
                            logMsg("getPVRThumbs - title matches an existing recording: " + title)
                        break
            except Exception as e:
                logMsg("ERROR in getPVRThumbs - get thumb from recordings ! --> " + str(e))
            
            if not poster and channel:
                poster, fanart = getTMDBimage(title)
                
            if not thumb and channel:
                thumb = searchGoogleImage(title + " " + channel)           
            
            if not thumb and channel:
                #last resort: youtube search
                thumb = searchYoutubeImage(title + " " + channel)
            
            #get logo from studio logos
            if not logo and channel:
                logo = searchChannelLogo(channel)
                
        if thumb == "skip":
            thumb = ""
        else:
            #store in cache for quick access later
            WINDOW.setProperty(dbID.encode('utf-8') + "SkinHelper.PVR.cache","cached")
            WINDOW.setProperty(dbID.encode('utf-8') + "SkinHelper.PVR.FanArt",try_encode(fanart))
            WINDOW.setProperty(dbID.encode('utf-8') + "SkinHelper.PVR.Poster",try_encode(poster))
            if channel:
                WINDOW.setProperty(channel.encode('utf-8') + "SkinHelper.PVR.ChannelLogo",try_encode(logo))
            WINDOW.setProperty(dbID.encode('utf-8') + "SkinHelper.PVR.Thumb",try_encode(thumb))
    else:
        logMsg("getPVRThumb cache found for dbID--> " + dbID)
    
    return (thumb,fanart,poster,logo)

def createSmartShortcutSubmenu(windowProp,iconimage):
    try:
        if xbmcvfs.exists("special://skin/shortcuts/"):
            shortcutFile = xbmc.translatePath("special://home/addons/script.skinshortcuts/resources/shortcuts/info-window-home-property-%s-title.DATA.xml" %windowProp.replace(".","-")).decode("utf-8")
            templatefile = os.path.join(ADDON_PATH,"resources","smartshortcuts","smartshortcuts-submenu-template.xml")
            if not xbmcvfs.exists(shortcutFile):
                with open(templatefile, 'r') as f:
                    data = f.read()
                data = data.replace("WINDOWPROP",windowProp)
                data = data.replace("ICONIMAGE",iconimage)
                with open(shortcutFile, 'w') as f:
                    f.write(data)
    except Exception as e:
        logMsg("ERROR in createSmartShortcutSubmenu ! --> " + str(e), 0)

def getCurrentContentType():
    contenttype="other"
    if xbmc.getCondVisibility("Container.Content(episodes)"):
        contenttype = "episodes"
    elif xbmc.getCondVisibility("Container.Content(movies) + !substring(Container.FolderPath,setid=)"):
        contenttype = "movies"  
    elif xbmc.getCondVisibility("[Container.Content(sets) | StringCompare(Container.Folderpath,videodb://movies/sets/)] + !substring(Container.FolderPath,setid=)"):
        contenttype = "sets"
    elif xbmc.getCondVisibility("substring(Container.FolderPath,setid=)"):
        contenttype = "setmovies" 
    elif xbmc.getCondVisibility("Container.Content(tvshows)"):
        contenttype = "tvshows"
    elif xbmc.getCondVisibility("Container.Content(seasons)"):
        contenttype = "seasons"
    elif xbmc.getCondVisibility("Container.Content(musicvideos)"):
        contenttype = "musicvideos"
    elif xbmc.getCondVisibility("[Container.Content(artists) | SubString(ListItem.FolderPath,musicdb://artists)] + !SubString(ListItem.FolderPath,artistid=)"):
        contenttype = "artists"
    elif xbmc.getCondVisibility("Container.Content(albums) | SubString(ListItem.FolderPath,musicdb://albums) | SubString(ListItem.FolderPath,artistid=)"):
        contenttype = "albums"
    elif xbmc.getCondVisibility("Window.IsActive(tvchannels) | Window.IsActive(radiochannels)"):
        contenttype = "tvchannels"
    elif xbmc.getCondVisibility("Window.IsActive(tvrecordings) | Window.IsActive(radiorecordings)"):
        contenttype = "tvrecordings"
    elif xbmc.getCondVisibility("Window.IsActive(tvtimers) | Window.IsActive(radiotimers)"):
        contenttype = "tvtimers"
    elif xbmc.getCondVisibility("Window.IsActive(tvsearch) | Window.IsActive(radiosearch)"):
        contenttype = "tvsearch"
    elif xbmc.getCondVisibility("Window.IsActive(programs) | Window.IsActive(addonbrowser)"):
        contenttype = "programs"
    elif xbmc.getCondVisibility("Window.IsActive(pictures)"):
        contenttype = "pictures"
    elif xbmc.getCondVisibility("Container.Content(files)"):
        contenttype = "files"
    elif xbmc.getCondVisibility("Container.Content(songs) | Container.Content(singles) | SubString(ListItem.FolderPath,.)"):
        contenttype = "songs"
    return contenttype
        
def searchChannelLogo(searchphrase):
    #get's a thumb image for the given search phrase
    image = ""
    
    cache = WINDOW.getProperty(searchphrase.encode('utf-8') + "SkinHelper.PVR.ChannelLogo")
    if cache: return cache
    else:
    
        try:
            #lookup in channel list
            # Perform a JSON query to get all channels
            json_query = getJSON('PVR.GetChannels', '{"channelgroupid": "alltv", "properties": [ "thumbnail", "channeltype", "hidden", "locked", "channel", "lastplayed", "broadcastnow" ]}' )
            for item in json_query:
                channelname = item["label"]
                channelicon = item['thumbnail']
                if channelname == searchphrase:
                    image = getCleanImage(channelicon)
                    break

            #lookup with thelogodb
            if not image:
                url = 'http://www.thelogodb.com/api/json/v1/1/tvchannel.php?s=%s' %try_encode(searchphrase)
                response = requests.get(url)
                data = json.loads(response.content.decode('utf-8','replace'))
                if data and data.has_key('channels'):
                    results = data['channels']
                    if results:
                        for i in results: 
                            rest = i['strLogoWide']
                            if rest:
                                if ".jpg" in rest or ".png" in rest:
                                    image = rest
                                    break
                
            if not image:
                search_alt = searchphrase.replace(" HD","")
                url = 'http://www.thelogodb.com/api/json/v1/1/tvchannel.php?s=%s' %try_encode(search_alt)
                response = requests.get(url)
                data = json.loads(response.content.decode('utf-8','replace'))
                if js and js.has_key('channels'):
                    results = js['channels']
                    if results:
                        for i in results: 
                            rest = i['strLogoWide']
                            if rest:
                                if ".jpg" in rest or ".png" in rest:
                                    image = rest
                                    break
        except Exception as e:
            if "getaddrinfo failed" in str(e):
                #no internet access - disable lookups for now
                WINDOW.setProperty("SkinHelper.DisableInternetLookups","disable")
                logMsg("searchChannelLogo - no internet access, disabling internet lookups for now")
            else:
                logMsg("ERROR in searchChannelLogo ! --> " + str(e), 0)

        if image:
            if ".jpg/" in image:
                image = image.split(".jpg/")[0] + ".jpg"
        
        WINDOW.setProperty(searchphrase.encode('utf-8') + "SkinHelper.PVR.ChannelLogo",image)
        return image

def searchGoogleImage(searchphrase):
    image = ""
   
    try:
        ip_address = xbmc.getInfoLabel("Network.IPAddress")
        url = 'http://ajax.googleapis.com/ajax/services/search/images?v=1.0&safe=off&q=%s&userip=%s' %(try_encode(searchphrase),ip_address)
        response = requests.get(url)
        data = json.loads(response.content.decode('utf-8','replace'))
        if data and data.get("responseData"):
            if data['responseData'].get("results"):
                results = data['responseData']['results']
                for i in results: 
                    image = i['unescapedUrl']
                    if image:
                        if ".jpg" in image or ".png" in image:
                            logMsg("getTMDBimage - GOOGLE match found for %s !" %searchphrase)
                            return image
    except Exception as e:
        if "getaddrinfo failed" in str(e):
            #no internet access - disable lookups for now
            WINDOW.setProperty("SkinHelper.DisableInternetLookups","disable")
            logMsg("searchGoogleImage - no internet access, disabling internet lookups for now")
        else:
            logMsg("getTMDBimage - ERROR in searchGoogleImage ! --> " + str(e))
    
    logMsg("getTMDBimage - GOOGLE match NOT found for %s" %searchphrase)
    return image
 
def searchYoutubeImage(searchphrase):
    image = ""
    matchFound = False
    #safety check: prevent multiple youtube searches at once...
    waitForYouTubeCount = 0
    if WINDOW.getProperty("youtubescanrunning") == "running":
        xbmc.sleep(100)
        return "skip"
    
    WINDOW.setProperty("youtubescanrunning","running")
    libPath = "plugin://plugin.video.youtube/kodion/search/query/?q=%s" %searchphrase
    media_array = getJSON('Files.GetDirectory','{ "properties": ["title","art"], "directory": "' + libPath + '", "media": "files" }')
    for media in media_array:
        if not media["filetype"] == "directory":
            if media.has_key('art'):
                if media['art'].has_key('thumb'):
                    image = getCleanImage(media['art']['thumb'])
                    matchFound = True
                    break
    if matchFound:
        logMsg("searchYoutubeImage - YOUTUBE match found for %s" %searchphrase)
    else:
        logMsg("searchYoutubeImage - YOUTUBE match NOT found for %s" %searchphrase)
    
    WINDOW.clearProperty("youtubescanrunning")
    return image
 
def searchThumb(searchphrase, searchphrase2=""):
    #get's a thumb image for the given search phrase
    
    #is this item already in the cache?
    image = WINDOW.getProperty(searchphrase + searchphrase2 + "SkinHelper.PVR.Thumb")
    if not image and not WINDOW.getProperty("SkinHelper.DisableInternetLookups"):
        if searchphrase2:
            searchphrase = searchphrase + " " + searchphrase2
            
        WINDOW.setProperty("getthumbbusy","busy")
           
        #lookup TMDB
        if not image:
            image = getTMDBimage(searchphrase)[0]
        
        #lookup with Google images
        if not image:
            image = searchGoogleImage(searchphrase)
        
        # Do lookup with youtube addon as last resort
        if not image:
            searchYoutubeImage(searchphrase)
                
        if image:
            if ".jpg/" in image:
                image = image.split(".jpg/")[0] + ".jpg"
        WINDOW.clearProperty("getthumbbusy")
    return image
    
def getCleanImage(image):
    if "image://" in image:
        image = image.replace("image://","")
        image=urllib.unquote(image.encode("utf-8"))
        if image.endswith("/"):
            image = image[:-1]
    return image
    
def getMusicArtByDbId(dbid,itemtype):
    cdArt = None
    LogoArt = None
    BannerArt = None
    extraFanArt = None
    Info = None
    path = None
    TrackList = ""
    if itemtype == "songs":
        json_response = getJSON('AudioLibrary.GetSongDetails', '{ "songid": %s, "properties": [ "file","artistid","albumid","comment"] }'%int(dbid))  
    elif itemtype == "artists":
        json_response = getJSON('AudioLibrary.GetSongs', '{ "filter":{"artistid": %s}, "properties": [ "file","artistid","track","title","albumid" ] }'%int(dbid))
    elif itemtype == "albums":
        json_response = getJSON('AudioLibrary.GetSongs', '{ "filter":{"albumid": %s}, "properties": [ "file","artistid","track","title","albumid" ] }'%int(dbid))
    
    if json_response:
        song = {}
        if type(json_response) is list:
            #get track listing
            for item in json_response:
                if not song:
                    song = item
                    path = item["file"]
                if item["track"]:
                    TrackList += "%s - %s[CR]" %(str(item["track"]), item["title"])
                else:
                    TrackList += "%s[CR]" %(item["title"])      
        else:
            song = json_response
        path = song["file"]
        if not Info:
            json_response2 = getJSON('AudioLibrary.GetAlbumDetails','{ "albumid": %s, "properties": [ "musicbrainzalbumid","description" ] }'%song["albumid"])
            if json_response2.get("description",None):
                Info = json_response2["description"]
        if not Info and song:
            if song.has_key("artistid"):
                json_response2 = getJSON('AudioLibrary.GetArtistDetails', '{ "artistid": %s, "properties": [ "musicbrainzartistid","description" ] }'%song["artistid"][0])
                if json_response2.get("description",None):
                    Info = json_response2["description"]

    if path:
        if "\\" in path:
            delim = "\\"
        else:
            delim = "/"
                
        path = path.replace(path.split(delim)[-1],"")
                              
        #extrafanart
        imgPath = os.path.join(path,"extrafanart" + delim)
        if xbmcvfs.exists(imgPath):
            extraFanArt = imgPath
        else:
            imgPath = os.path.join(path.replace(path.split(delim)[-2]+delim,""),"extrafanart" + delim)
            if xbmcvfs.exists(imgPath):
                extraFanArt = imgPath
        
        #cdart
        if xbmcvfs.exists(os.path.join(path,"cdart.png")):
            cdArt = os.path.join(path,"cdart.png")
        else:
            imgPath = os.path.join(path.replace(path.split(delim)[-2]+delim,""),"cdart.png")
            if xbmcvfs.exists(imgPath):
                cdArt = imgPath
        
        #banner
        if xbmcvfs.exists(os.path.join(path,"banner.jpg")):
            BannerArt = os.path.join(path,"banner.jpg")
        else:
            imgPath = os.path.join(path.replace(path.split(delim)[-2]+delim,""),"banner.jpg")
            if xbmcvfs.exists(imgPath):
                BannerArt = imgPath
                
        #logo
        imgPath = os.path.join(path,"logo.png")
        if xbmcvfs.exists(imgPath):
            LogoArt = imgPath
        else:
            imgPath = os.path.join(path.replace(path.split(delim)[-2]+delim,""),"logo.png")
            if xbmcvfs.exists(imgPath):
                LogoArt = imgPath
                
    return (cdArt, LogoArt, BannerArt, extraFanArt, Info, TrackList)