#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcplugin
import xbmcaddon
import xbmcgui
import xbmc
import xbmcvfs
import os
import json
import urlparse
import sys
import urllib,urllib2,re
import base64

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
fields_pvrrecordings = '"art", "channel", "directory", "endtime", "file", "genre", "icon", "playcount", "plot", "plotoutline", "resume", "runtime", "starttime", "streamurl", "title"'

def logMsg(msg, level = 1):
    doDebugLog = False
    if doDebugLog == True or level == 0:
        xbmc.log("Skin Helper Service --> " + msg)
        
def getContentPath(libPath):
    if "$INFO" in libPath and not "reload=" in libPath:
        win = xbmcgui.Window( 10000 )
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
            logMsg("invalid result " + str(jsonobject))
            logMsg('{ "jsonrpc" : "2.0" , "method" : "' + method + '" , "params" : ' + params + ' , "id":1 }')
            return {}
    else:
        logMsg("no result " + str(jsonobject))
        logMsg('{ "jsonrpc" : "2.0" , "method" : "' + method + '" , "params" : ' + params + ' , "id":1 }')
        return {}

def try_encode(text, encoding="utf-8"):
    try:
        return text.encode(encoding)
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
       
    liz = xbmcgui.ListItem(item['title'])
    liz.setInfo( type="Video", infoLabels={ "Title": item['title'] })
    liz.setProperty('IsPlayable', 'true')
    season = None
    episode = None
    
    if "runtime" in item:
        liz.setInfo( type="Video", infoLabels={ "duration": str(item['runtime']/60) })
    
    if "file" in item:
        liz.setPath(item['file'])
        liz.setProperty("path", item['file'])
    
    if "episode" in item:
        episode = "%.2d" % float(item['episode'])
        liz.setInfo( type="Video", infoLabels={ "Episode": item['episode'] })
    
    if "season" in item:
        season = "%.2d" % float(item['season'])
        liz.setInfo( type="Video", infoLabels={ "Season": item['season'] })
        
    if season and episode:
        episodeno = "s%se%s" %(season,episode)
        liz.setProperty("episodeno", episodeno)
    
    if "episodeid" in item:
        liz.setProperty("DBID", str(item['episodeid']))
        liz.setInfo( type="Video", infoLabels={ "DBID": str(item['episodeid']) })
        liz.setIconImage('DefaultTVShows.png')
        
    if "songid" in item:
        liz.setProperty("DBID", str(item['songid']))
        liz.setIconImage('DefaultAudio.png')
        liz.setLabel2(item['artist'][0])
    
    if "channel" in item:
        liz.setLabel2(item['channel'])
        
    if "movieid" in item:
        liz.setProperty("DBID", str(item['movieid']))
        liz.setInfo( type="Video", infoLabels={ "DBID": str(item['movieid']) })
        liz.setIconImage('DefaultMovies.png')
    
    if "musicvideoid" in item:
        liz.setProperty("DBID", str(item['musicvideoid']))
        liz.setIconImage('DefaultMusicVideos.png')
    
    
    if "plot" in item:
        plot = item['plot']
    elif "comment" in item:
        plot = item['comment']
    else:
        plot = None
    
    liz.setInfo( type="Video", infoLabels={ "Plot": plot })
    
    if "artist" in item:
        liz.setInfo( type="Video", infoLabels={ "Artist": item['artist'] })
        
    if "votes" in item:
        liz.setInfo( type="Video", infoLabels={ "votes": item['votes'] })
    
    if "trailer" in item:
        liz.setInfo( type="Video", infoLabels={ "trailer": item['trailer'] })
        liz.setProperty("trailer", item['trailer'])
        
    if "dateadded" in item:
        liz.setInfo( type="Video", infoLabels={ "dateadded": item['dateadded'] })
        
    if "album" in item:
        liz.setInfo( type="Video", infoLabels={ "album": item['album'] })
        
    if "plotoutline" in item:
        liz.setInfo( type="Video", infoLabels={ "plotoutline ": item['plotoutline'] })
        
    if "studio" in item:
        liz.setInfo( type="Video", infoLabels={ "studio": " / ".join(item['studio']) })
        
    if "playcount" in item:
        liz.setInfo( type="Video", infoLabels={ "playcount ": item['playcount'] })
        
    if "mpaa" in item:
        liz.setInfo( type="Video", infoLabels={ "mpaa": item['mpaa'] })
        
    if "tagline" in item:
        liz.setInfo( type="Video", infoLabels={ "tagline": item['tagline'] })
    
    if "showtitle" in item:
        liz.setInfo( type="Video", infoLabels={ "TVshowTitle": item['showtitle'] })
    
    if "rating" in item:
        liz.setInfo( type="Video", infoLabels={ "Rating": str(round(float(item['rating']),1)) })
    
    if "playcount" in item:
        liz.setInfo( type="Video", infoLabels={ "Playcount": item['playcount'] })
    
    if "director" in item:
        liz.setInfo( type="Video", infoLabels={ "Director": " / ".join(item['director']) })
    
    if "writer" in item:
        liz.setInfo( type="Video", infoLabels={ "Writer": " / ".join(item['writer']) })
    
    if "genre" in item:
        liz.setInfo( type="Video", infoLabels={ "genre": " / ".join(item['genre']) })
        
    if "year" in item:
        liz.setInfo( type="Video", infoLabels={ "year": item['year'] })
    
    if "firstaired" in item:
        liz.setInfo( type="Video", infoLabels={ "premiered": item['firstaired'] })

    if "premiered" in item:
        liz.setInfo( type="Video", infoLabels={ "premiered": item['premiered'] })
        
    if "cast" in item:
        listCast = []
        listCastAndRole = []
        for castmember in item["cast"]:
            listCast.append( castmember["name"] )
            listCastAndRole.append( (castmember["name"], castmember["role"]) ) 
        cast = [listCast, listCastAndRole]
        liz.setInfo( type="Video", infoLabels={ "Cast": cast[0] })
        liz.setInfo( type="Video", infoLabels={ "CastAndRole": cast[1] })
    
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
    coverUrl = None
    fanartUrl = None
    title = '"%s"'%title
    videoTypes = ["tv","movie"]
    for videoType in videoTypes:
        try:
            content = opener.open("http://api.themoviedb.org/3/search/"+videoType+"?api_key="+apiKey+"&query="+urllib.quote_plus(title.strip())+"&language=en").read()
            coverUrl = re.compile('"poster_path":"(.+?)"', re.DOTALL).findall(content)
            fanartUrl = re.compile('"backdrop_path":"(.+?)"', re.DOTALL).findall(content)
        except Exception as e:
            if "429" in str(e):
                #delay and request again
                xbmc.sleep(250)
                try:
                    content = opener.open("http://api.themoviedb.org/3/search/"+videoType+"?api_key="+apiKey+"&query="+urllib.quote_plus(title.strip())+"&language=en").read()
                    coverUrl = re.compile('"poster_path":"(.+?)"', re.DOTALL).findall(content)
                    fanartUrl = re.compile('"backdrop_path":"(.+?)"', re.DOTALL).findall(content)
                except: pass
            else:
                logMsg("ERROR in getTMDBimage ! --> " + str(e), 0)
        
        if coverUrl:
            coverUrl = "http://image.tmdb.org/t/p/original"+coverUrl[0]
            try: opener.open(coverUrl).read()
            except: pass
        if fanartUrl:
            fanartUrl = "http://image.tmdb.org/t/p/original"+fanartUrl[0]
            try: opener.open(fanartUrl).read()
            except: pass
        
        if not coverUrl:
            coverUrl = None
            
        if not fanartUrl:
            fanartUrl = None

        if coverUrl and fanartUrl:
            break

    return (coverUrl, fanartUrl)

def getPVRThumbs(pvrArtCache,title,channel):
    dbID = title + channel
    cacheFound = False
    thumb = ""
    fanart = ""
    logo = ""
    poster = ""

    logMsg("getPVRThumb dbID--> " + dbID)
        
    #get the items from cache first
    if pvrArtCache.has_key(dbID + "SkinHelper.PVR.Thumb"):
        cacheFound = True
        thumb = pvrArtCache[dbID + "SkinHelper.PVR.Thumb"]
        if thumb == "None":
            thumb = None

    if pvrArtCache.has_key(dbID + "SkinHelper.PVR.FanArt"):
        cacheFound = True
        fanart = pvrArtCache[dbID + "SkinHelper.PVR.FanArt"]
        if fanart == "None":
            fanart = None
    
    if pvrArtCache.has_key(dbID + "SkinHelper.PVR.Poster"):
        cacheFound = True
        poster = pvrArtCache[dbID + "SkinHelper.PVR.Poster"]
        if poster == "None":
            poster = None
    
    if pvrArtCache.has_key(dbID + "SkinHelper.PVR.ChannelLogo"):
        cacheFound = True
        logo = pvrArtCache[dbID + "SkinHelper.PVR.ChannelLogo"]
        if logo == "None":
            logo = None
    
    if not cacheFound:
        logMsg("getPVRThumb no cache found for dbID--> " + dbID)
        
        poster, fanart = getTMDBimage(title)
        thumb = searchGoogleImage(title + " " + channel)
        
        #get logo from studio logos
        logo = searchChannelLogo(channel)
        
        pvrArtCache[dbID + "SkinHelper.PVR.Thumb"] = thumb
        pvrArtCache[dbID + "SkinHelper.PVR.FanArt"] = fanart
        pvrArtCache[dbID + "SkinHelper.PVR.Poster"] = poster
        pvrArtCache[dbID + "SkinHelper.PVR.ChannelLogo"] = logo
    else:
        logMsg("getPVRThumb cache found for dbID--> " + dbID)
    
    return (pvrArtCache,thumb,fanart,poster,logo)

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
    elif xbmc.getCondVisibility("Container.Content(artists)"):
        contenttype = "artists"
    elif xbmc.getCondVisibility("Container.Content(songs)"):
        contenttype = "songs"
    elif xbmc.getCondVisibility("Container.Content(albums)"):
        contenttype = "albums"
    elif xbmc.getCondVisibility("Window.IsActive(tvchannels) | Window.IsActive(radiochannels)"):
        contenttype = "tvchannels"
    elif xbmc.getCondVisibility("Window.IsActive(tvrecordings) | Window.IsActive(radiorecordings)"):
        contenttype = "tvrecordings"
    elif xbmc.getCondVisibility("Window.IsActive(programs) | Window.IsActive(addonbrowser)"):
        contenttype = "programs"
    elif xbmc.getCondVisibility("Window.IsActive(pictures)"):
        contenttype = "pictures"
    elif xbmc.getCondVisibility("SubString(Window.Property(xmlfile),MyPVR,left)"):
        contenttype = "pvr"
    elif xbmc.getCondVisibility("Container.Content(files)"):
        contenttype = "files"
    return contenttype
        
def searchChannelLogo(searchphrase):
    #get's a thumb image for the given search phrase
       
    image = ""
    if searchphrase:
        cache = WINDOW.getProperty("SkinHelperThumbs")
        if cache:
            cache = eval(cache)
        else:
            cache = {}
        
        if cache.has_key(searchphrase):
            return cache[searchphrase]
        else:
            try:
                #lookup in channel list
                # Perform a JSON query to get all channels
                json_query = getJSON('PVR.GetChannels', '{"channelgroupid": "alltv", "properties": [ "thumbnail", "channeltype", "hidden", "locked", "channel", "lastplayed", "broadcastnow" ]}' )
                for item in json_query:
                    channelname = item["label"]
                    channelicon = item['thumbnail']
                    if channelname == searchphrase:
                        image = channelicon
                        break

                #lookup with thelogodb
                if not image:
                    search = searchphrase.split()
                    search = '%20'.join(map(str, search))
                    url = 'http://www.thelogodb.com/api/json/v1/1/tvchannel.php?s=' + search
                    search_results = urllib2.urlopen(url)
                    js = json.loads(search_results.read().decode("utf-8"))
                    if js and js.has_key('channels'):
                        results = js['channels']
                        if results:
                            for i in results: 
                                rest = i['strLogoWide']
                                if rest:
                                    if ".jpg" in rest or ".png" in rest:
                                        image = rest
                                        break
                    
                if not image:
                    search = searchphrase.replace(" HD","").split()
                    search = '%20'.join(map(str, search))
                    url = 'http://www.thelogodb.com/api/json/v1/1/tvchannel.php?s=' + search
                    search_results = urllib2.urlopen(url)
                    js = json.loads(search_results.read().decode("utf-8"))
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
                logMsg("ERROR in searchChannelLogo ! --> " + str(e), 0)

    if image:
        if ".jpg/" in image:
            image = image.split(".jpg/")[0] + ".jpg"
        cache[searchphrase] = image
        WINDOW.setProperty("SkinHelperThumbs", repr(cache))
    return image

def searchGoogleImage(searchphrase):
    image = None
    try:
        search = searchphrase.split()
        search = '%20'.join(map(str, search))
        url = 'http://ajax.googleapis.com/ajax/services/search/images?v=1.0&q=%s&safe=off' % search
        search_results = urllib2.urlopen(url)
        js = json.loads(search_results.read().decode("utf-8"))
        if js:
            results = js['responseData']['results']
            for i in results: 
                rest = i['unescapedUrl']
                if rest:
                    if ".jpg" in rest or ".png" in rest:
                        image = rest
                        break
    except: pass
    return image
    
def searchThumb(searchphrase, searchphrase2=""):
    #get's a thumb image for the given search phrase
       
    image = ""
    if searchphrase:
        searchphrase = searchphrase.encode("utf-8").decode("utf-8")
        cache = WINDOW.getProperty("SkinHelperThumbs")
        if cache:
            cache = eval(cache)
        else:
            cache = {}
        
        if cache.has_key(searchphrase):
            return cache[searchphrase]
        else:
            WINDOW.setProperty("getthumbbusy","busy")
            #lookup TMDB
            image = getTMDBimage(searchphrase)[0]
            
            #lookup with Google images
            if not image:
                searchphrase = searchphrase + searchphrase2
                image = searchGoogleImage(searchphrase)
            
            # Do lookup with youtube addon as last resort
            if not image:
                #safety check: prevent multiple youtube searches at once...
                waitForYouTubeCount = 0
                while WINDOW.getProperty("youtubescanrunning") == "running":
                    xbmc.sleep(250)
                    waitForYouTubeCount += 1
                    if waitForYouTubeCount == 25:
                        return ""
                
                WINDOW.setProperty("youtubescanrunning","running")
                libPath = "plugin://plugin.video.youtube/kodion/search/query/?q=%s" %searchphrase
                media_array = getJSON('Files.GetDirectory','{ "properties": ["title","art"], "directory": "' + libPath + '", "media": "files" }')
                for media in media_array:
                    if not media["filetype"] == "directory":
                        if media.has_key('art'):
                            if media['art'].has_key('thumb'):
                                image = getCleanImage(media['art']['thumb'])
                                break
                WINDOW.clearProperty("youtubescanrunning")
    
    if image:
        if ".jpg/" in image:
            image = image.split(".jpg/")[0] + ".jpg"
        cache[searchphrase] = image
        WINDOW.setProperty("SkinHelperThumbs", repr(cache))
    WINDOW.clearProperty("getthumbbusy")
    return image

def getCleanImage(image):
    if "image://" in image:
        image = image.replace("image://","")
        image=urllib.unquote(image)
        if image.endswith("/"):
            image = image[:-1]
    return image