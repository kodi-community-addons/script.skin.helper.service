#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcplugin
import xbmcaddon
import xbmcgui
import xbmc
import json
import urlparse
import sys

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_ICON = ADDON.getAddonInfo('icon')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_PATH = ADDON.getAddonInfo('path').decode("utf-8")
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_DATA_PATH = xbmc.translatePath("special://profile/addon_data/%s" % ADDON_ID).decode("utf-8")
WINDOW = xbmcgui.Window(10000)
SETTING = ADDON.getSetting

def logMsg(msg, level = 1):
    doDebugLog = False
    if doDebugLog == True or level == 0:
        xbmc.log("Skin Helper Service --> " + msg)

def getLocalizedString(label_id):
    if 31000 <= label_id <= 33000:
        return ADDON.getLocalizedString(label_id)
    else:
        return xbmc.getLocalizedString(label_id)        
        
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
    
    return libPath

def getJSON(method,params):
    json_response = xbmc.executeJSONRPC('{ "jsonrpc" : "2.0" , "method" : "' + method + '" , "params" : ' + params + ' , "id":1 }')

    jsonobject = json.loads(json_response.decode('utf-8','replace'))
   
    if(jsonobject.has_key('result')):
        return jsonobject['result']
    else:
        logMsg("no result " + str(jsonobject))
        return None

def setSkinVersion():
    skin = xbmc.getSkinDir()
    skinLabel = xbmcaddon.Addon(id=skin).getAddonInfo('name')
    skinVersion = xbmcaddon.Addon(id=skin).getAddonInfo('version')
    WINDOW.setProperty("skinTitle",skinLabel + " - " + xbmc.getLocalizedString(19114) + ": " + skinVersion)
    WINDOW.setProperty("skinVersion",xbmc.getLocalizedString(19114) + ": " + skinVersion)
    WINDOW.setProperty("skinhelper.Version",ADDON_VERSION.replace(".",""))
        
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