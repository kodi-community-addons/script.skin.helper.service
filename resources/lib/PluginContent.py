import xbmcplugin
import xbmcgui
import xbmc
import xbmcaddon
import shutil
import xbmcaddon
import xbmcvfs
import os, sys
import time
import urllib
import xml.etree.ElementTree as etree
from xml.dom.minidom import parse
import json
import random

from Utils import *

from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.etree import ElementTree
from xml.dom import minidom
import xml.etree.cElementTree as ET

def addDirectoryItem(label, path, folder=True):
    li = xbmcgui.ListItem(label, path=path)
    li.setThumbnailImage("special://home/addons/script.skin.helper.service/icon.png")
    li.setArt({"fanart":"special://home/addons/script.skin.helper.service/fanart.jpg"})
    li.setArt({"landscape":"special://home/addons/script.skin.helper.service/fanart.jpg"})
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=li, isFolder=folder)

def doMainListing():
    xbmcplugin.setContent(int(sys.argv[1]), 'files')    
    addDirectoryItem(ADDON.getLocalizedString(32000), "plugin://script.skin.helper.service/?action=favourites&limit=100")
    addDirectoryItem(ADDON.getLocalizedString(32001), "plugin://script.skin.helper.service/?action=favouritemedia&limit=100")
    addDirectoryItem(ADDON.getLocalizedString(32002), "plugin://script.skin.helper.service/?action=nextepisodes&limit=100")
    addDirectoryItem(ADDON.getLocalizedString(32003), "plugin://script.skin.helper.service/?action=recommendedmovies&limit=100")
    addDirectoryItem(ADDON.getLocalizedString(32004), "plugin://script.skin.helper.service/?action=RecommendedMedia&limit=100")
    addDirectoryItem(ADDON.getLocalizedString(32005), "plugin://script.skin.helper.service/?action=recentmedia&limit=100")
    addDirectoryItem(ADDON.getLocalizedString(32006), "plugin://script.skin.helper.service/?action=similarmovies&limit=100")
    addDirectoryItem(ADDON.getLocalizedString(32007), "plugin://script.skin.helper.service/?action=inprogressandrecommendedmedia&limit=100")

    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
def getFavourites(limit):
    
    if not limit:
        limit = 25
    try:
        xbmcplugin.setContent(int(sys.argv[1]), 'files')
        fav_file = xbmc.translatePath( 'special://profile/favourites.xml' ).decode("utf-8")
        if xbmcvfs.exists( fav_file ):
            doc = parse( fav_file )
            listing = doc.documentElement.getElementsByTagName( 'favourite' )
            
            for count, favourite in enumerate(listing):
                label = ""
                image = "special://skin/extras/hometiles/favourites.png"
                for (name, value) in favourite.attributes.items():
                    if name == "name":
                        label = value
                    if name == "thumb":
                        image = value
                path = favourite.childNodes [ 0 ].nodeValue
                
                path="plugin://script.skin.helper.service/?action=launch&path=" + path
                li = xbmcgui.ListItem(label, path=path)
                li.setThumbnailImage(image)
                li.setProperty('IsPlayable', 'false')
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=li, isFolder=False)
                if count == limit:
                    break
                    
    except Exception as e: 
        print "exception ?"
        print e
        pass        
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
        
def getNextEpisodes(limit):
    if not limit:
        limit = 25
    count = 0
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    # First we get a list of all the in-progress TV shows
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": { "sort": { "order": "descending", "method": "lastplayed" }, "filter": {"and": [{"operator":"true", "field":"inprogress", "value":""}]}, "properties": [ "title", "studio", "mpaa", "file", "art" ] }, "id": "1"}')

    json_result = json.loads(json_query_string)
    # If we found any, find the oldest unwatched show for each one.
    if json_result.has_key('result') and json_result['result'].has_key('tvshows'):
        for item in json_result['result']['tvshows']:
            json_query2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "tvshowid": %d, "sort": {"method":"episode"}, "filter": {"and": [ {"field": "playcount", "operator": "lessthan", "value":"1"}, {"field": "season", "operator": "greaterthan", "value": "0"} ]}, "properties": [ "title", "playcount", "season", "episode", "showtitle", "plot", "file", "rating", "resume", "tvshowid", "art", "streamdetails", "firstaired", "runtime", "writer", "cast", "dateadded", "lastplayed" ], "limits":{"end":1}}, "id": "1"}' %item['tvshowid'])
            if json_query2:
                json_query2 = json.loads(json_query2)
                if json_query2.has_key('result') and json_query2['result'].has_key('episodes'):
                    
                    for item in json_query2['result']['episodes']:
                        liz = createListItem(item)
                        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
                        count +=1
                        if count == limit:
                            break
                            
    if count < limit:
        # Fill the list with first episodes of unwatched tv shows
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": { "sort": { "order": "ascending", "method": "dateadded" }, "filter": {"and": [{"operator":"false", "field":"inprogress", "value":""}]}, "properties": [ "title", "studio", "mpaa", "file", "art" ] }, "id": "1"}')
        json_result = json.loads(json_query_string)
        if json_result.has_key('result') and json_result['result'].has_key('tvshows'):
            for item in json_result['result']['tvshows']:
                json_query2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "tvshowid": %d, "sort": {"method":"episode"}, "filter": {"and": [ {"field": "playcount", "operator": "lessthan", "value":"1"}, {"field": "season", "operator": "greaterthan", "value": "0"} ]}, "properties": [ "title", "playcount", "season", "episode", "showtitle", "plot", "file", "rating", "resume", "tvshowid", "art", "streamdetails", "firstaired", "runtime", "writer", "cast", "dateadded", "lastplayed" ], "limits":{"end":1}}, "id": "1"}' %item['tvshowid'])
                if json_query2:
                    json_query2 = json.loads(json_query2)
                    if json_query2.has_key('result') and json_query2['result'].has_key('episodes'):
                        
                        for item in json_query2['result']['episodes']:
                            liz = createListItem(item)
                            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
                            count +=1
                            if count == limit:
                                break
        
        
    
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

def getRecommendedMovies(limit):
    if not limit:
        limit = 25
    count = 0
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    # First we get a list of all the in-progress Movies
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "sort": { "order": "descending", "method": "lastplayed" }, "filter": {"and": [{"operator":"true", "field":"inprogress", "value":""}]}, "properties": [ "title", "playcount", "plot", "file", "rating", "resume", "art", "streamdetails", "year", "runtime", "writer", "cast", "dateadded", "lastplayed" ] }, "id": "1"}')
    json_result = json.loads(json_query_string)
    # If we found any, find the oldest unwatched show for each one.
    if json_result.has_key('result') and json_result['result'].has_key('movies'):
        for item in json_result['result']['movies']:
            liz = createListItem(item)
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
            count +=1
            if count == limit:
                break
    
    # Fill the list with random items with a score higher then 7
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"},{"operator":"greaterthan", "field":"rating", "value":"7"}]}, "properties": [ "title", "playcount", "plot", "file", "rating", "resume", "art", "streamdetails", "year", "runtime", "writer", "cast", "dateadded", "lastplayed" ] }, "id": "1"}')
    json_result = json.loads(json_query_string)
    # If we found any, find the oldest unwatched show for each one.
    if json_result.has_key('result') and json_result['result'].has_key('movies'):
        for item in json_result['result']['movies']:
            liz = createListItem(item)
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
            count +=1
            if count == limit:
                break
        
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

def getSimilarMovies(limit):
    if not limit:
        limit = 25
    count = 0
    allItems = []
    allTitles = list()
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    #picks a random watched movie and finds similar movies in the library
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "sort": { "order": "descending", "method": "random" }, "filter": {"operator":"isnot", "field":"playcount", "value":"0"}, "properties": [ "title", "rating", "genre"],"limits":{"end":1}}, "id": "1"}')
    json_result = json.loads(json_query_string)
    if json_result.has_key('result') and json_result['result'].has_key('movies'):
        for item in json_result['result']['movies']:
            genres = item["genre"]
            originalTitle = item["title"]
            #get all movies from the same genre
            for genre in genres:
                json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"genre", "value":"' + genre + '"}, {"operator":"is", "field":"playcount", "value":"0"}]}, "properties": [ "title", "playcount", "plot", "file", "genre", "rating", "resume", "art", "streamdetails", "year", "mpaa", "runtime", "writer", "cast", "dateadded", "lastplayed", "tagline" ],"limits":{"end":10} }, "id": "1"}')
                json_result = json.loads(json_query_string)
                if json_result.has_key('result') and json_result['result'].has_key('movies'):
                    for item in json_result['result']['movies']:
                        if not item["title"] in allTitles and not item["title"] == originalTitle:
                            rating = item["rating"]
                            allItems.append((rating,item))
                            allTitles.append(item["title"])
    
    #sort the list by rating 
    from operator import itemgetter
    allItems = sorted(allItems,key=itemgetter(0),reverse=True)
    
    #build that listing
    for item in allItems:
        liz = createListItem(item[1])
        liz.setProperty("originaltitle", originalTitle)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item[1]['file'], listitem=liz)
        count +=1
        if count == limit:
            break       
            
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
    
    if count > 0:
        WINDOW.setProperty("widget.similarmovies.hascontent", "true")
    else:
        WINDOW.clearProperty("widget.similarmovies.hascontent")
    
def getRecommendedMedia(limit,ondeckContent=False,recommendedContent=True):
    if not limit:
        limit = 25
    count = 0
    allTitles = list()
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    
    if ondeckContent:
        allItems = []
        
        #netflix in progress
        if xbmc.getCondVisibility("System.HasAddon(plugin.video.netflixbmc) + Skin.HasSetting(SmartShortcuts.netflix)") and WINDOW.getProperty("netflixready") == "ready":
            json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": { "directory": "plugin://plugin.video.netflixbmc/?mode=listSliderVideos&thumb&type=both&widget=true&url=slider_0", "media": "files", "properties": [ "title", "playcount", "plot", "file", "rating", "resume", "art", "streamdetails", "year", "mpaa", "runtime", "writer", "cast", "dateadded", "lastplayed", "tagline" ] }, "id": "1"}')
            json_result = json.loads(json_query_string)
            if json_result.has_key('result') and json_result['result'].has_key('files'):
                for item in json_result['result']['files']:
                    lastplayed = item["lastplayed"]
                    if not item["title"] in allTitles:
                        allItems.append((lastplayed,item))
                        allTitles.append(item["title"])
        
        # Get a list of all the in-progress Movies
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "sort": { "order": "descending", "method": "lastplayed" }, "filter": {"and": [{"operator":"true", "field":"inprogress", "value":""}]}, "properties": [ "title", "playcount", "plot", "file", "rating", "resume", "art", "streamdetails", "year", "mpaa", "runtime", "writer", "cast", "dateadded", "lastplayed", "tagline" ] }, "id": "1"}')
        json_result = json.loads(json_query_string)
        if json_result.has_key('result') and json_result['result'].has_key('movies'):
            for item in json_result['result']['movies']:
                lastplayed = item["lastplayed"]
                if not item["title"] in allTitles:
                    allItems.append((lastplayed,item))
                    allTitles.append(item["title"])
        
        # Get a list of all the in-progress MusicVideos
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMusicVideos", "params": { "sort": { "order": "descending", "method": "lastplayed" }, "limits": { "start" : 0, "end": 25 }, "properties": [ "title", "playcount", "plot", "file", "resume", "art", "streamdetails", "year", "runtime", "dateadded", "lastplayed" ] }, "id": "1"}')
        json_result = json.loads(json_query_string)
        if json_result.has_key('result') and json_result['result'].has_key('musicvideos'):
            for item in json_result['result']['musicvideos']:
                lastplayed = item["lastplayed"]
                if not item["title"] in allTitles and item["resume"]["position"] != 0:
                    allItems.append((lastplayed,item))
                    allTitles.append(item["title"])
        
        # Get a list of all the in-progress music songs
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetRecentlyPlayedSongs", "params": { "sort": { "order": "descending", "method": "lastplayed" }, "limits": { "start" : 0, "end": 5 }, "properties": [ "artist", "title", "rating", "fanart", "thumbnail", "duration", "playcount", "comment", "file", "album", "lastplayed" ] }, "id": "1"}')
        json_result = json.loads(json_query_string)
        if json_result.has_key('result') and json_result['result'].has_key('songs'):
            for item in json_result['result']['songs']:
                lastplayed = item["lastplayed"]
                if not item["title"] in allTitles and lastplayed and item["thumbnail"]:
                    allItems.append((lastplayed,item))
                    allTitles.append(item["title"])
        
        # Get a list of all the in-progress tv recordings   
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0",  "id": 1, "method": "PVR.GetRecordings", "params": {"properties": [ "title", "plot", "plotoutline", "genre", "playcount", "resume", "channel", "starttime", "endtime", "runtime", "lifetime", "icon", "art", "streamurl", "file", "directory" ]}}' )
        json_result = json.loads(json_query_string)
        if json_result.has_key('result') and json_result['result'].has_key('recordings'):
            for item in json_result['result']['recordings']:
                lastplayed = None
                if not item["title"] in allTitles and item["playcount"] == 0:
                    allItems.append((lastplayed,item))
                    allTitles.append(item["title"])
          

        # NextUp episodes
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": { "sort": { "order": "descending", "method": "lastplayed" }, "filter": {"and": [{"operator":"true", "field":"inprogress", "value":""}]}, "properties": [ "title", "studio", "mpaa", "file", "art" ] }, "id": "1"}')
        json_result = json.loads(json_query_string)
        # If we found any, find the oldest unwatched show for each one.
        if json_result.has_key('result') and json_result['result'].has_key('tvshows'):
            for item in json_result['result']['tvshows']:
                json_query2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "tvshowid": %d, "sort": {"method":"episode"}, "filter": {"and": [ {"field": "playcount", "operator": "lessthan", "value":"1"}, {"field": "season", "operator": "greaterthan", "value": "0"} ]}, "properties": [ "title", "playcount", "season", "episode", "showtitle", "plot", "file", "rating", "resume", "tvshowid", "art", "streamdetails", "firstaired", "runtime", "writer", "cast", "dateadded", "lastplayed" ], "limits":{"end":1}}, "id": "1"}' %item['tvshowid'])
                if json_query2:
                    json_query2 = json.loads(json_query2)
                    if json_query2.has_key('result') and json_query2['result'].has_key('episodes'):
                        for item in json_query2['result']['episodes']:
                            lastplayed = item["lastplayed"]
                            if not item["title"] in allTitles:
                                allItems.append((lastplayed,item))
                                allTitles.append(item["title"])         
        
        #sort the list with in progress items by lastplayed date   
        from operator import itemgetter
        allItems = sorted(allItems,key=itemgetter(0),reverse=True)
        
        #build that listing
        for item in allItems:
            liz = createListItem(item[1])
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item[1]['file'], listitem=liz)
            count +=1
            if count == limit:
                break
    
    if recommendedContent:
        allItems = []
                        
        # Random movies with a score higher then 7
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"},{"operator":"greaterthan", "field":"rating", "value":"7"}]}, "properties": [ "title", "playcount", "plot", "file", "rating", "resume", "art", "genre", "streamdetails", "year", "runtime", "writer", "cast", "dateadded", "lastplayed" ], "limits":{"end":25} }, "id": "1"}')
        json_result = json.loads(json_query_string)
        if json_result.has_key('result') and json_result['result'].has_key('movies'):
            for item in json_result['result']['movies']:
                rating = item["rating"]
                if not item["title"] in set(allTitles):
                    allItems.append((rating,item))
                    allTitles.append(item["title"])
                    
        # Random tvshows with a score higher then 7
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": { "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"},{"operator":"greaterthan", "field":"rating", "value":"7"}]}, "properties": [ "title", "playcount", "plot", "file", "rating", "art", "year", "genre", "mpaa", "cast", "dateadded", "lastplayed" ],"limits":{"end":25} }, "id": "1"}')
        json_result = json.loads(json_query_string)
        if json_result.has_key('result') and json_result['result'].has_key('tvshows'):
            for item in json_result['result']['tvshows']:
                rating = item["rating"]
                if not item["title"] in set(allTitles):
                    
                    #get the first unwatched episode for this show
                    json_query2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "tvshowid": %d, "sort": {"method":"episode"}, "filter": {"and": [ {"field": "playcount", "operator": "lessthan", "value":"1"}, {"field": "season", "operator": "greaterthan", "value": "0"} ]}, "properties": [ "title", "file" ], "limits":{"end":1}}, "id": "1"}' %item['tvshowid'])
                    if json_query2:
                        json_query2 = json.loads(json_query2)
                        if json_query2.has_key('result') and json_query2['result'].has_key('episodes'):
                            item2 = json_query2['result']['episodes'][0]
                            item["file"] = item2["file"]
                            allItems.append((rating,item))
                            allTitles.append(item["title"])
                    
        #sort the list with recommended items by rating 
        from operator import itemgetter
        allItems = sorted(allItems,key=itemgetter(0),reverse=True)

        #build that listing
        for item in allItems:
            liz = createListItem(item[1])
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item[1]['file'], listitem=liz)
            count +=1
            if count == limit:
                break       
            
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
    
    if count > 0 and recommendedContent:
        WINDOW.setProperty("widget.recommendedmedia.hascontent", "true")
    else:
        WINDOW.clearProperty("widget.recommendedmedia.hascontent")
        
    if count > 0 and ondeckContent:
        WINDOW.setProperty("widget.ondeckmedia.hascontent", "true")
    else:
        WINDOW.clearProperty("widget.ondeckmedia.hascontent")
    
def getRecentMedia(limit):
    if not limit:
        limit = 25
    count = 0
    allItems = []
    allTitles = list()
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    
    # Get a list of all the recent Movies (unwatched and not in progress)
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "sort": { "order": "descending", "method": "dateadded" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"},{"operator":"false", "field":"inprogress", "value":""}]}, "properties": [ "title", "playcount", "plot", "file", "rating", "resume", "art", "streamdetails", "year", "mpaa", "runtime", "writer", "cast", "dateadded", "lastplayed", "tagline" ], "limits":{"end":15} }, "id": "1"}')
    json_result = json.loads(json_query_string)
    if json_result.has_key('result') and json_result['result'].has_key('movies'):
        for item in json_result['result']['movies']:
            dateadded = item["dateadded"]
            if not item["title"] in allTitles:
                allItems.append((dateadded,item))
                allTitles.append(item["title"])
    
    # Get a list of all the recent MusicVideos (unwatched and not in progress)
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMusicVideos", "params": { "limits": { "start" : 0, "end": 15 },"sort": { "order": "descending", "method": "dateadded" }, "filter": {"operator":"is", "field":"playcount", "value":"0"}, "properties": [ "title", "playcount", "plot", "file", "resume", "art", "streamdetails", "year", "runtime", "dateadded", "lastplayed" ] }, "id": "1"}')
    json_result = json.loads(json_query_string)
    if json_result.has_key('result') and json_result['result'].has_key('musicvideos'):
        for item in json_result['result']['musicvideos']:
            dateadded = item["dateadded"]
            if not item["title"] in allTitles and item["resume"]["position"] == 0:
                allItems.append((dateadded,item))
                allTitles.append(item["title"])
    
    # Get a list of all the recent music songs
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs", "params": { "limits": { "start" : 0, "end": 15 }, "sort": {"order": "descending", "method": "dateadded" }, "filter": {"operator":"is", "field":"playcount", "value":"0"}, "properties": [ "artist", "title", "rating", "fanart", "thumbnail", "duration", "playcount", "comment", "file", "album", "lastplayed" ] }, "id": "1"}')
    json_result = json.loads(json_query_string)
    if json_result.has_key('result') and json_result['result'].has_key('songs'):
        for item in json_result['result']['songs']:
            dateadded = ""
            if not item["title"] in allTitles and item["thumbnail"]:
                allItems.append((dateadded,item))
                allTitles.append(item["title"])
    
    
    # Get a list of all the recent episodes (unwatched and not in progress)
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "sort": { "order": "descending", "method": "dateadded" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"},{"operator":"false", "field":"inprogress", "value":""}]}, "properties": [ "title", "playcount", "season", "episode", "showtitle", "plot", "file", "rating", "resume", "tvshowid", "art", "streamdetails", "firstaired", "runtime", "writer", "cast", "dateadded", "lastplayed" ], "limits":{"end":15} }, "id": "1"}')
    json_result = json.loads(json_query_string)
    if json_result.has_key('result') and json_result['result'].has_key('episodes'):
        for item in json_result['result']['episodes']:
            dateadded = item["dateadded"]
            if not item["title"] in allTitles:
                allItems.append((dateadded,item))
                allTitles.append(item["title"])
            
    
    # Get a list of all the unwatched tv recordings   
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0",  "id": 1, "method": "PVR.GetRecordings", "params": {"properties": [ "title", "plot", "plotoutline", "genre", "playcount", "resume", "channel", "starttime", "endtime", "runtime", "lifetime", "icon", "art", "streamurl", "file", "directory" ]}}' )
    json_result = json.loads(json_query_string)
    if json_result.has_key('result') and json_result['result'].has_key('recordings'):
        for item in json_result['result']['recordings']:
            lastplayed = item["endtime"]
            if not item["title"] in allTitles and item["playcount"] == 0:
                allItems.append((lastplayed,item))
                allTitles.append(item["title"])
    
    #sort the list with in recent items by lastplayed date   
    from operator import itemgetter
    allItems = sorted(allItems,key=itemgetter(0),reverse=True)
    

    #build that listing
    for item in allItems:
        liz = createListItem(item[1])
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item[1]['file'], listitem=liz)
        count +=1
        if count == limit:
            break       
    
    
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
    
    if count > 0:
        WINDOW.setProperty("widget.recentmedia.hascontent", "true")
    else:
        WINDOW.clearProperty("widget.recentmedia.hascontent")
 
def getFavouriteMedia(limit):
    if not limit:
        limit = 25
    count = 0
    allItems = []
    allTitles = list()
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    
    #netflix favorites
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.netflixbmc) + Skin.HasSetting(SmartShortcuts.netflix)") and WINDOW.getProperty("netflixready") == "ready":
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": { "directory": "plugin://plugin.video.netflixbmc/?mode=listSliderVideos&thumb&type=both&widget=true&url=slider_38", "media": "files", "properties": [ "title", "playcount", "plot", "file", "rating", "resume", "art", "streamdetails", "year", "mpaa", "runtime", "writer", "cast", "dateadded", "lastplayed", "tagline" ] }, "id": "1"}')
        json_result = json.loads(json_query_string)
        if json_result.has_key('result') and json_result['result'].has_key('files'):
            for item in json_result['result']['files']:
                liz = createListItem(item)
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
    
    #emby favorites
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.emby) + Skin.HasSetting(SmartShortcuts.emby)"):
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter": {"operator":"contains", "field":"tag", "value":"Favorite movies"}, "properties": [ "title", "playcount", "plot", "file", "rating", "resume", "art", "streamdetails", "year", "mpaa", "runtime", "writer", "cast", "dateadded", "lastplayed", "tagline" ] }, "id": "1"}')
        json_result = json.loads(json_query_string)
        if json_result.has_key('result') and json_result['result'].has_key('movies'):
            for item in json_result['result']['movies']:
                liz = createListItem(item)
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
        
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTvShows", "params": { "filter": {"operator":"contains", "field":"tag", "value":"Favorite tvshows"}, "properties": [ "title", "playcount", "plot", "file", "rating", "art", "premiered", "genre", "cast", "dateadded", "lastplayed" ] }, "id": "1"}')
        json_result = json.loads(json_query_string)
        if json_result.has_key('result') and json_result['result'].has_key('tvshows'):
            for item in json_result['result']['tvshows']:
                liz = createListItem(item)
                tvshowpath = "ActivateWindow(Videos,videodb://tvshows/titles/%s/,return)" %str(item["tvshowid"])
                tvshowpath="plugin://script.skin.helper.service?LAUNCHAPP&&&" + tvshowpath
                liz.setProperty('IsPlayable', 'false')
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=tvshowpath, listitem=liz)
            
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Favourites.GetFavourites", "params": {"type": null, "properties": ["path", "thumbnail", "window", "windowparameter"]}, "id": "1"}')
    json_result = json.loads(json_query_string)
    if json_result.has_key('result'):
        if json_result['result'].has_key('favourites') and json_result['result']['favourites']:
            for fav in json_result['result']['favourites']:
                matchFound = False
                if "windowparameter" in fav:
                    if fav["windowparameter"].startswith("videodb://tvshows/titles"):
                        #it's a tv show
                        try:
                            tvshowid = int(fav["windowparameter"].split("/")[-2])
                        except: continue
                        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShowDetails", "params": { "tvshowid": %d, "properties": [ "title", "playcount", "plot", "file", "rating", "art", "premiered", "genre", "cast", "dateadded", "lastplayed" ]}, "id": "1"}' %tvshowid)
                        json_result = json.loads(json_query_string)
                        if json_result.has_key('result') and json_result['result'].has_key('tvshowdetails'):
                            matchFound = True
                            item = json_result['result']["tvshowdetails"]
                            liz = createListItem(item)
                            tvshowpath = "ActivateWindow(Videos,%s,return)" %fav["windowparameter"]
                            tvshowpath="plugin://script.skin.helper.service?LAUNCHAPP&&&" + tvshowpath
                            liz.setProperty('IsPlayable', 'false')
                            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=tvshowpath, listitem=liz)                   
                if fav["type"] == "media":
                    path = fav["path"]
                    if "/" in path:
                        sep = "/"
                    else:
                        sep = "\\"
                    pathpart = path.split(sep)[-1] #apparently only the filename can be used for the search
                    #is this a movie?
                    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter": {"operator":"contains", "field":"filename", "value":"' + pathpart + '"}, "properties": [ "title", "playcount", "plot", "file", "rating", "resume", "art", "streamdetails", "year", "mpaa", "runtime", "writer", "cast", "dateadded", "lastplayed", "tagline" ] }, "id": "1"}')
                    json_result = json.loads(json_query_string)
                    if json_result.has_key('result') and json_result['result'].has_key('movies'):
                        for item in json_result['result']['movies']:
                            if item['file'] == path:
                                matchFound = True
                                liz = createListItem(item)
                                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
                    
                    if matchFound == False:
                        #is this an episode ?
                        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "filter": {"operator":"contains", "field":"filename", "value":"' + pathpart + '"}, "properties": [ "title", "playcount", "season", "episode", "showtitle", "plot", "file", "rating", "resume", "tvshowid", "art", "streamdetails", "firstaired", "runtime", "writer", "cast", "dateadded", "lastplayed" ] }, "id": "1"}')
                        json_result = json.loads(json_query_string)
                        if json_result.has_key('result') and json_result['result'].has_key('episodes'):
                            for item in json_result['result']['episodes']:
                                if item['file'] == path:
                                    matchFound = True
                                    liz = createListItem(item)
                                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
                    if matchFound == False:
                        #is this a song?
                        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs", "params": { "filter": {"operator":"contains", "field":"filename", "value":"' + pathpart + '"}, "properties": [ "artist", "title", "rating", "fanart", "thumbnail", "duration", "playcount", "comment", "file", "album", "lastplayed" ] }, "id": "1"}')
                        json_result = json.loads(json_query_string)
                        if json_result.has_key('result') and json_result['result'].has_key('songs'):
                            for item in json_result['result']['songs']:
                                if item['file'] == path:
                                    matchFound = True
                                    liz = createListItem(item)
                                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
                                    
                    if matchFound == False:
                        #is this a musicvideo?
                        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMusicVideos", "params": { "filter": {"operator":"contains", "field":"filename", "value":"' + pathpart + '"}, "properties": [ "title", "playcount", "plot", "file", "resume", "art", "streamdetails", "year", "runtime", "dateadded", "lastplayed" ] }, "id": "1"}')
                        json_result = json.loads(json_query_string)
                        if json_result.has_key('result') and json_result['result'].has_key('musicvideos'):
                            for item in json_result['result']['musicvideos']:
                                if item['file'] == path:
                                    matchFound = True
                                    liz = createListItem(item)
                                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
                    
                    if matchFound:
                        count +=1
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
        if count > 0:
            WINDOW.setProperty("widget.favouritemedia.hascontent", "true")
        else:
            WINDOW.clearProperty("widget.favouritemedia.hascontent")
        
