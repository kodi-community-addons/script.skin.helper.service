#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcplugin
import xbmcaddon
import xbmcgui
import xbmc
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
    json_response = xbmc.executeJSONRPC('{ "jsonrpc" : "2.0" , "method" : "' + method + '" , "params" : ' + params + ' , "id":1 }')

    jsonobject = json.loads(json_response.decode('utf-8','replace'))
   
    if(jsonobject.has_key('result')):
        return jsonobject['result']
    else:
        logMsg("no result " + str(jsonobject),0)
        logMsg('{ "jsonrpc" : "2.0" , "method" : "' + method + '" , "params" : ' + params + ' , "id":1 }',0)
        return {}

def try_decode(text, encoding="utf-8"):
    if isinstance(text, str):
        try:
            return text.encode(encoding)
        except:
            pass
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
    liz.setInfo( type="Video", infoLabels={ "Title": try_decode(item['title']) })
    liz.setProperty('IsPlayable', 'true')
    season = None
    episode = None
    
    if "runtime" in item:
        liz.setInfo( type="Video", infoLabels={ "duration": str(item['runtime']/60) })
    
    if "file" in item:
        liz.setPath(item['file'])
        liz.setProperty("path", try_decode(item['file']))
    
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
        liz.setLabel2(str(item['artist'][0]))
    
    if "channel" in item:
        liz.setLabel2(str(item['channel']))
        
    if "movieid" in item:
        liz.setProperty("DBID", str(item['movieid']))
        liz.setInfo( type="Video", infoLabels={ "DBID": str(item['movieid']) })
        liz.setIconImage('DefaultMovies.png')
    
    if "musicvideoid" in item:
        liz.setProperty("DBID", str(item['musicvideoid']))
        liz.setIconImage('DefaultMusicVideos.png')
    
    
    if "plot" in item:
        plot = try_decode(item['plot'])
    elif "comment" in item:
        plot = item['comment']
    else:
        plot = None
    
    liz.setInfo( type="Video", infoLabels={ "Plot": plot })
    
    if "artist" in item:
        liz.setInfo( type="Video", infoLabels={ "Artist": try_decode(item['artist']) })
        
    if "votes" in item:
        liz.setInfo( type="Video", infoLabels={ "votes": item['votes'] })
    
    if "trailer" in item:
        liz.setInfo( type="Video", infoLabels={ "trailer": try_decode(item['trailer']) })
        liz.setProperty("trailer", item['trailer'])
        
    if "dateadded" in item:
        liz.setInfo( type="Video", infoLabels={ "dateadded": item['dateadded'] })
        
    if "album" in item:
        liz.setInfo( type="Video", infoLabels={ "album": item['album'] })
        
    if "plotoutline" in item:
        liz.setInfo( type="Video", infoLabels={ "plotoutline ": try_decode(item['plotoutline']) })
        
    if "studio" in item:
        liz.setInfo( type="Video", infoLabels={ "studio": " / ".join(item['studio']) })
        
    if "playcount" in item:
        liz.setInfo( type="Video", infoLabels={ "playcount ": item['playcount'] })
        
    if "mpaa" in item:
        liz.setInfo( type="Video", infoLabels={ "mpaa": item['mpaa'] })
        
    if "tagline" in item:
        liz.setInfo( type="Video", infoLabels={ "tagline": try_decode(item['tagline']) })
    
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
    
def detectPluginContent(plugin):
    #based on the properties in the listitem we try to detect the content
    
    #safety check: check if no library windows are active to prevent any addons setting the view
    curWindow = xbmc.getInfoLabel("$INFO[Window.Property(xmlfile)]")
    if curWindow.endswith("Nav.xml") or curWindow == "AddonBrowser.xml" or curWindow.startswith("MyPVR"):
        return None, None
    
    media_array = getJSON('Files.GetDirectory','{ "directory": "%s", "media": "files", "properties": ["title", "file", "thumbnail", "episode", "showtitle", "season", "album", "artist", "imdbnumber", "firstaired", "mpaa", "trailer", "studio", "art"], "limits": {"end":3} }' %plugin)
    if media_array != None and media_array.has_key('files'):
        for item in media_array['files']:
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
                if item["artist"][0] == item["title"]:
                    return ("artists", image)
                elif item["album"] == item["title"]:
                    return ("albums", image)
                elif (item["type"] == "song" or (item["artist"] and item["album"])):
                    return ("songs", image)
            else:    
                ##### VIDEO ITEMS ####
                if (item["showtitle"] and not item["artist"]):
                    #this is a tvshow, episode or season...
                    if (item["season"] > -1 and item["episode"] == -1):
                        return ("seasons", image)
                    elif item["season"] > -1 and item["episode"] > -1:
                        return ("episodes", image)
                    else:
                        return ("tvshows", image)
                elif (item["artist"]):
                    #this is a musicvideo!
                    return ("musicvideos", image)
                elif (item["imdbnumber"] or item["mpaa"] or item["trailer"] or item["studio"]):
                    return ("movies", image)

    return (None, None)
    
def getTMDBimage(title):
    
    apiKey = base64.b64decode("NDc2N2I0YjJiYjk0YjEwNGZhNTUxNWM1ZmY0ZTFmZWM=")
    opener = urllib2.build_opener()
    userAgent = "Mozilla/5.0 (Windows NT 5.1; rv:25.0) Gecko/20100101 Firefox/25.0"
    opener.addheaders = [('User-agent', userAgent)]
    
    coverUrl = None
    fanartUrl = None
    
    videoTypes = ["tv","movie"]
    for videoType in videoTypes:
        if videoType == "tv":
            content = opener.open("http://api.themoviedb.org/3/search/"+videoType+"?api_key="+apiKey+"&query="+urllib.quote_plus(title.strip())+"&language=en").read()
            resultCount = re.compile('"total_results":(.+?)').findall(content)
            if resultCount[0] == str(0):
                #try again without the date
                content = opener.open("http://api.themoviedb.org/3/search/"+videoType+"?api_key="+apiKey+"&query="+urllib.quote_plus(title.strip())+"&language=en").read()
                resultCount = re.compile('"total_results":(.+?)').findall(content)
                if resultCount[0] == str(0):
                    if '(' in title:
                        title = title[:title.find('(')]
                        content = opener.open("http://api.themoviedb.org/3/search/"+videoType+"?api_key="+apiKey+"&query="+urllib.quote_plus(title.strip())+"&language=en").read()    
                    elif ':' in title:
                        title = title[:title.find(':')]
                        content = opener.open("http://api.themoviedb.org/3/search/"+videoType+"?api_key="+apiKey+"&query="+urllib.quote_plus(title.strip())+"&language=en").read()
        else:
            content = opener.open("http://api.themoviedb.org/3/search/"+videoType+"?api_key="+apiKey+"&query="+urllib.quote_plus(title.strip())+"&language=en").read()
            resultCount = re.compile('"total_results":(.+?)').findall(content)
            if resultCount[0] == str(0):
                content = opener.open("http://api.themoviedb.org/3/search/"+videoType+"?api_key="+apiKey+"&query="+urllib.quote_plus(title.strip())+"&language=en").read()
                resultCount = re.compile('"total_results":(.+?)').findall(content)
                if resultCount[0] == str(0):
                    if '(' in title:
                        title = title[:title.find('(')]
                        content = opener.open("http://api.themoviedb.org/3/search/"+videoType+"?api_key="+apiKey+"&query="+urllib.quote_plus(title.strip())+"&language=en").read()
                    elif ':' in title:
                        title = title[:title.find(':')]
                        content = opener.open("http://api.themoviedb.org/3/search/"+videoType+"?api_key="+apiKey+"&query="+urllib.quote_plus(title.strip())+"&language=en").read()

        match = re.compile('"poster_path":"(.+?)"', re.DOTALL).findall(content)
        match2 = None
        # maybe its a mini-series (TMDb calls them movies)
        if not match and videoType == "tv":
            content = opener.open("http://api.themoviedb.org/3/search/movie?api_key="+apiKey+"&query="+urllib.quote_plus(title.strip())+"&language=en").read()
            match = re.compile('"poster_path":"(.+?)"', re.DOTALL).findall(content)
            match2 = re.compile('"backdrop_path":"(.+?)"', re.DOTALL).findall(content)

        if match:
            coverUrl = "http://image.tmdb.org/t/p/original"+match[0]
        match = re.compile('"backdrop_path":"(.+?)"', re.DOTALL).findall(content)
        if match:
            fanartUrl = "http://image.tmdb.org/t/p/original"+match[0]
        elif match2:
            fanartUrl = "http://image.tmdb.org/t/p/original"+match2[0]
        
        if coverUrl and fanartUrl:
            break

    return (coverUrl, fanartUrl)

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
            WINDOW.setProperty("getthumbbusy","busy")
            
            #lookup with thelogodb
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
                            if ".jpg" in rest or ".png" in rest:
                                image = rest
                                break

    if image:
        if ".jpg/" in image:
            image = image.split(".jpg/")[0] + ".jpg"
        cache[searchphrase] = image
        WINDOW.setProperty("SkinHelperThumbs", repr(cache))
    WINDOW.clearProperty("getthumbbusy")
    return image
    
def searchThumb(searchphrase, searchphrase2=""):
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
            WINDOW.setProperty("getthumbbusy","busy")
            #lookup TMDB
            image = getTMDBimage(searchphrase)[0]
            
            #lookup with Google images
            if not image:
                searchphrase = searchphrase + searchphrase2
                search = searchphrase.split()
                search = '%20'.join(map(str, search))
                url = 'http://ajax.googleapis.com/ajax/services/search/images?v=1.0&q=%s&safe=off' % search
                search_results = urllib2.urlopen(url)
                js = json.loads(search_results.read().decode("utf-8"))
                results = js['responseData']['results']
                for i in results: rest = i['unescapedUrl']
                if ".jpg" in rest or ".png" in rest:
                    image = rest
            
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
                media_array = None
                media_array = getJSON('Files.GetDirectory','{ "properties": ["title","art"], "directory": "' + libPath + '", "media": "files" }')
                if(media_array != None and media_array.has_key('files')):
                    for media in media_array['files']:
                        if not media["filetype"] == "directory":
                            if media.has_key('art'):
                                if media['art'].has_key('thumb'):
                                    image = media['art']['thumb'].replace("image://","")
                                    image=urllib.unquote(image).decode('utf8')
                                    if image.endswith("/"):
                                        image = image[:-1]
                                    break
                WINDOW.clearProperty("youtubescanrunning")
    
    if image:
        if ".jpg/" in image:
            image = image.split(".jpg/")[0] + ".jpg"
        cache[searchphrase] = image
        WINDOW.setProperty("SkinHelperThumbs", repr(cache))
    WINDOW.clearProperty("getthumbbusy")
    return image
