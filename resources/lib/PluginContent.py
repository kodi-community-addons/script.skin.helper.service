import xbmcplugin
import xbmcgui
import xbmc
import xbmcaddon
import xbmcaddon
import xbmcvfs
import os, sys
import time
import urllib,urllib2
import xml.etree.ElementTree as xmltree
from xml.dom.minidom import parse
import json
import random

from Utils import *

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
    #addDirectoryItem("smart pvr channels", "plugin://script.skin.helper.service/?action=pvrchannelssmart&limit=10")
    
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def addSmartShortcutDirectoryItem(entry, isFolder=True, widget=None):
    
    label = "$INFO[Window(Home).Property(%s.title)]" %entry
    path = "$INFO[Window(Home).Property(%s.path)]" %entry
    content = "$INFO[Window(Home).Property(%s.content)]" %entry
    image = "$INFO[Window(Home).Property(%s.image)]" %entry
    type = "$INFO[Window(Home).Property(%s.type)]" %entry

    if isFolder:
        path = sys.argv[0] + "?action=SMARTSHORTCUTS&amp;path=" + entry
        li = xbmcgui.ListItem(label, path=path)
        icon = xbmc.getInfoLabel(image)
        li.setThumbnailImage(icon)
        li.setIconImage("special://home/addons/script.skin.helper.service/fanart.jpg")
    else:
        li = xbmcgui.ListItem(label, path=path)
        props = {}
        props["list"] = content
        if not xbmc.getInfoLabel(type):
            type = "media"
        props["type"] = type
        props["background"] = "$INFO[Window(Home).Property(%s.image)]" %entry
        props["backgroundName"] = "$INFO[Window(Home).Property(%s.title)]" %entry
        li.setInfo( type="Video", infoLabels={ "Title": "smartshortcut" })
        li.setThumbnailImage(image)
        li.setIconImage("special://home/addons/script.skin.helper.service/fanart.jpg")
        
        if widget:
            widgettype = "$INFO[Window(Home).Property(%s.type)]" %widget
            if not xbmc.getInfoLabel(type):
                widgettype = type
            if widgettype == "albums" or widgettype == "artists" or widgettype == "songs":
                widgettarget = "music"
            else:
                widgettarget = "video"
            props["widget"] = "addon"
            props["widgetName"] = "$INFO[Window(Home).Property(%s.title)]" %widget
            props["widgetType"] = widgettype
            props["widgetTarget"] = widgettarget
            props["widgetPath"] = "$INFO[Window(Home).Property(%s.content)]" %widget
            
        li.setInfo( type="Video", infoLabels={ "mpaa": repr(props) })
    
    li.setArt({"fanart":image})   
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=li, isFolder=isFolder)

def addSmartShortcutsSublevel(entry):
    
    if "emby" in entry:
        contentStrings = ["", ".recent", ".inprogress", ".unwatched", ".recentepisodes", ".inprogressepisodes", ".nextepisodes"]
    elif "plex" in entry:
        contentStrings = ["", ".ondeck", ".recent", ".unwatched"]
    elif "netflix" in entry:
        contentStrings = ["", ".mylist", ".recent", ".inprogress", ".suggestions"]
        
    for contentString in contentStrings:
        key = entry + contentString
        widget = None
        if contentString == "":
            #this is the main item so define our widgets
            type = xbmc.getInfoLabel("$INFO[Window(Home).Property(%s.type)]" %entry)
            if type == "movies" or type == "movie" or type == "artist" or "netflix" in entry:
                widget = entry + ".recent"
            elif type == "tvshows" and "emby" in "entry":
                widget = entry + ".nextepisodes"
            elif type == "show" and "plex" in "entry":
                widget = entry + ".ondeck"
            else:
                widget = entry
        
        if xbmc.getInfoLabel("$INFO[Window(Home).Property(%s.path)]" %key):
            addSmartShortcutDirectoryItem(key,False, widget)

def getSmartShortcuts(sublevel=None):
    xbmcplugin.setContent(int(sys.argv[1]), 'files')
    if sublevel:
        addSmartShortcutsSublevel(sublevel)
    else:
        allSmartShortcuts = WINDOW.getProperty("allSmartShortcuts")
        if allSmartShortcuts:
            for node in eval (allSmartShortcuts):
                if "emby" in node or "plex" in node or "netflix" in node:
                    #create main folder entry
                    addSmartShortcutDirectoryItem(node)
                else:
                    label = "$INFO[Window(Home).Property(%s.title)]" %node
                    #create final listitem entry (playlist, favorites)
                    addSmartShortcutDirectoryItem(node,False, node)
                    

    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def buildWidgetsListing():
    allWidgets = {}
    if WINDOW.getProperty("allwidgets"):
        allWidgets = eval(WINDOW.getProperty("allwidgets"))
    
    #skin provided playlists
    paths = ["special://skin/playlists/","special://skin/extras/widgetplaylists/"]
    playlistsFound = []
    for path in paths:
        path = xbmc.translatePath(path).decode('utf-8')
        if xbmcvfs.exists(path):
            media_array = getJSON('Files.GetDirectory','{ "directory": "%s", "media": "files" }' %path)
            if media_array != None and media_array.has_key('files'):
                for item in media_array['files']:
                    if item["file"].endswith(".xsp"):
                        playlist = item["file"] + "&amp;reload=$INFO[Window(Home).Property(widgetreload)]"
                        contents = xbmcvfs.File(item["file"], 'r')
                        contents_data = contents.read().decode('utf-8')
                        contents.close()
                        xmldata = xmltree.fromstring(contents_data.encode('utf-8'))
                        type = "unknown"
                        label = item["label"]
                        type2, image = detectPluginContent(item["file"])
                        for line in xmldata.getiterator():
                            if line.tag == "smartplaylist":
                                type = line.attrib['type']
                            if line.tag == "name":
                                label = line.text
                                
                        if type == "albums" or type == "artists" or type == "songs":
                            mediaLibrary = "MusicLibrary"
                        else:
                            mediaLibrary = "VideoLibrary"
                        path = "ActivateWindow(%s,%s,return)" %(mediaLibrary, playlist)
                        playlistsFound.append([label, path, playlist, image, type])
    allWidgets["skinplaylists"] = playlistsFound
        
    #addons that provide dynamic content for widgets
    #will only be loaded once so no cache refreshes
    addonList = []
    addonList.append(["plugin://service.library.data.provider", "librarydataprovider"])
    addonList.append(["plugin://script.extendedinfo", "extendedinfo"])
    addonList.append(["plugin://script.skin.helper.service", "scriptwidgets"])
    for addon in addonList:
        if not allWidgets.has_key(addon[1]):
            foundWidgets = []
            media_array = getJSON('Files.GetDirectory','{ "directory": "%s", "media": "files" }' %addon[0])
            if media_array != None and media_array.has_key('files'):
                for item in media_array['files']:
                    #safety check: check if no library windows are active to prevent any addons setting the view
                    curWindow = xbmc.getInfoLabel("$INFO[Window.Property(xmlfile)]")
                    if curWindow.endswith("Nav.xml") or curWindow == "AddonBrowser.xml" or curWindow.startswith("MyPVR"):
                        return
                    content = item["file"] + "&reload=$INFO[Window(Home).Property(widgetreload)]"
                    label = item["label"]
                    type = "video"
                    if "movie" in content or "box" in content or "dvd" in content or "rentals" in content:
                        type = "movies"
                    if "show" in content:
                        type = "tvshows"
                    image = None
                    mediaLibrary = "VideoLibrary"
                    path = "ActivateWindow(%s,%s,return)" %(mediaLibrary, content)
                    foundWidgets.append([label, path, content, image, type])
            if addon[1] == "extendedinfo":
                #some additional entrypoints for extendedinfo...
                entrypoints = ["plugin://script.extendedinfo?info=youtubeusersearch&&id=Eurogamer","plugin://script.extendedinfo?info=youtubeusersearch&&id=Engadget","plugin://script.extendedinfo?info=youtubeusersearch&&id=MobileTechReview"]
                for entry in entrypoints:
                    content = entry
                    label = entry.split("id=")[1]
                    type = "video"
                    mediaLibrary = "VideoLibrary"
                    path = "ActivateWindow(%s,%s,return)" %(mediaLibrary, content)
                    foundWidgets.append([label, path, content, "", type])

            allWidgets[addon[1]] = foundWidgets
    
    #widgets from favourites
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Favourites.GetFavourites", "params": {"type": null, "properties": ["path", "thumbnail", "window", "windowparameter"]}, "id": "1"}')
    json_result = json.loads(json_query_string.decode('utf-8','replace'))
    if json_result.has_key('result'):
        foundWidgets = []
        if json_result['result'].has_key('favourites') and json_result['result']['favourites']:
            for fav in json_result['result']['favourites']:
                matchFound = False
                if "windowparameter" in fav:
                    content = fav["windowparameter"]
                    if not "=play" in content.lower():
                        window = fav["window"]
                        label = fav["title"]
                        type, image = detectPluginContent(content)
                        if window == "music":
                            mediaLibrary = "MusicLibrary"
                        else:
                            mediaLibrary = "VideoLibrary"
                        path = "ActivateWindow(%s,%s,return)" %(mediaLibrary, content)
                        if type:
                            foundWidgets.append([label, path, content, image, type])
            allWidgets["favourites"] = foundWidgets
                        
    #some other widgets (by their direct endpoint) such as smartish widgets and PVR
    otherWidgets = ["pvr","smartishwidgets"]
    for widget in otherWidgets:
        if not allWidgets.has_key(widget):
            foundWidgets = []
            if widget=="pvr" and xbmc.getCondVisibility("PVR.HasTVChannels"):
                mediaLibrary = "VideoLibrary"
                path = "ActivateWindow(%s,%s,return)" %(mediaLibrary, content)
                foundWidgets.append(["TV Recordings", "ActivateWindow(VideoLibrary,pvr://recordings,return)", "pvr://recordings", "", "pvr"])
                foundWidgets.append(["TV Channels", "ActivateWindow(VideoLibrary,pvr://tvchannels,return)", "pvr://tvchannels", "", "pvr"])   
            if widget=="smartishwidgets" and xbmc.getCondVisibility("System.HasAddon(service.smartish.widgets) + Skin.HasSetting(enable.smartish.widgets)"):
                foundWidgets.append(["Smart(ish) Movies widget", "ActivateWindow(VideoLibrary,plugin://service.smartish.widgets?type=movies&reload=$INFO[Window.Property(smartish.movies)],return)", "plugin://service.smartish.widgets?type=movies&reload=$INFO[Window.Property(smartish.movies)]", "", "movies"])
                foundWidgets.append(["Smart(ish) Episodes widget", "ActivateWindow(VideoLibrary,plugin://service.smartish.widgets?type=episodes&reload=$INFO[Window.Property(smartish.episodes)],return)", "plugin://service.smartish.widgets?type=episodes&reload=$INFO[Window.Property(smartish.episodes)]", "", "episodes"])
                foundWidgets.append(["Smart(ish) PVR widget", "ActivateWindow(VideoLibrary,plugin://service.smartish.widgets?type=pvr&reload=$INFO[Window.Property(smartish.pvr)],return)", "plugin://service.smartish.widgets?type=pvr&reload=$INFO[Window.Property(smartish.pvr)]", "", "pvr"])
                foundWidgets.append(["Smart(ish) Albums widget", "ActivateWindow(VideoLibrary,plugin://service.smartish.widgets?type=albums&reload=$INFO[Window.Property(smartish.albums)],return)", "plugin://service.smartish.widgets?type=albums&reload=$INFO[Window.Property(smartish.albums)]", "", "albums"])
            allWidgets[widget] = foundWidgets
            
    WINDOW.setProperty("allwidgets",repr(allWidgets))    
       
def getWidgets(itemstoInclude = None):
    xbmcplugin.setContent(int(sys.argv[1]), 'files')
    
    if itemstoInclude:
        itemstoInclude = itemstoInclude.split(",")
    else:
        itemstoInclude = ["skinplaylists", "librarydataprovider", "scriptwidgets", "extendedinfo", "smartshortcuts","pvr", "smartishwidgets", "favourites" ]
    
    #load the widget listing from the cache
    allWidgets = WINDOW.getProperty("allwidgets")
    if not allWidgets:
        buildWidgetsListing()
        allWidgets = WINDOW.getProperty("allwidgets")
    
    if allWidgets:
        allWidgets = eval(allWidgets)
        for widgetType in itemstoInclude:
            if widgetType == "smartshortcuts":
                allSmartShortcuts = WINDOW.getProperty("allSmartShortcuts")
                if allSmartShortcuts:
                    for node in eval (allSmartShortcuts):
                        if "emby" in node or "plex" in node or "netflix" in node:
                            #create main folder entry
                            addSmartShortcutDirectoryItem(node)
                        else:
                            label = "$INFO[Window(Home).Property(%s.title)]" %node
                            #create final listitem entry (playlist, favorites)
                            addSmartShortcutDirectoryItem(node,False, node)
            elif allWidgets.has_key(widgetType):
                widgets = allWidgets[widgetType]
                for widget in widgets:
                    li = xbmcgui.ListItem(widget[0], path=widget[1])
                    props = {}
                    props["list"] = widget[2]
                    props["type"] = widget[4]
                    props["background"] = widget[3]
                    props["backgroundName"] = widget[0]
                    props["widgetPath"] = widget[2]
                    li.setInfo( type="Video", infoLabels={ "Title": "smartshortcut" })
                    li.setThumbnailImage(widget[3])
                    li.setIconImage("special://home/addons/script.skin.helper.service/fanart.jpg")
                        
                    li.setInfo( type="Video", infoLabels={ "mpaa": repr(props) })
                    
                    li.setArt({"fanart":widget[3]})   
                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=widget[1], listitem=li, isFolder=False)
    
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
def getBackgrounds():
    xbmcplugin.setContent(int(sys.argv[1]), 'files')
    
    globalBackgrounds = []
    globalBackgrounds.append((ADDON.getLocalizedString(32038), "SkinHelper.GlobalFanartBackground"))
    globalBackgrounds.append((ADDON.getLocalizedString(32039), "SkinHelper.AllMoviesBackground"))
    globalBackgrounds.append((ADDON.getLocalizedString(32040), "SkinHelper.RecentMoviesBackground"))
    globalBackgrounds.append((ADDON.getLocalizedString(32041), "SkinHelper.InProgressMoviesBackground"))
    globalBackgrounds.append((ADDON.getLocalizedString(32042), "SkinHelper.UnwatchedMoviesBackground"))
    globalBackgrounds.append((ADDON.getLocalizedString(32043), "SkinHelper.AllTvShowsBackground"))
    globalBackgrounds.append((ADDON.getLocalizedString(32044), "SkinHelper.RecentEpisodesBackground"))
    globalBackgrounds.append((ADDON.getLocalizedString(32045), "SkinHelper.InProgressShowsBackground"))
    globalBackgrounds.append((ADDON.getLocalizedString(32046), "SkinHelper.PicturesBackground"))
    globalBackgrounds.append((ADDON.getLocalizedString(32047), "SkinHelper.AllMusicVideosBackground"))
    globalBackgrounds.append((ADDON.getLocalizedString(32048), "SkinHelper.AllMusicBackground"))
    
    for node in globalBackgrounds:
        label = node[0]
        image = "$INFO[Window(Home).Property(%s)]" %node[1]
        if xbmc.getInfoLabel(image):
            li = xbmcgui.ListItem(label, path=image)
            li.setArt({"fanart":image})
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=image, listitem=li, isFolder=False)
    
    allSmartShortcuts = WINDOW.getProperty("allSmartShortcuts")
    if allSmartShortcuts:
        for node in eval (allSmartShortcuts):
            label = "$INFO[Window(Home).Property(%s.title)]" %node
            image = "$INFO[Window(Home).Property(%s.image)]" %node
            li = xbmcgui.ListItem(label, path=image)
            li.setArt({"fanart":image})
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=image, listitem=li, isFolder=False)

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
        logMsg("ERROR in PluginContent.getFavourites ! --> " + str(e), 0)       
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getPVRChannels(limit):
    xbmcplugin.setContent(int(sys.argv[1]), 'files')
    
    # Perform a JSON query to get all tv channel groups
    json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0",  "id": 1, "method": "PVR.GetChannelGroups", "params": {"channeltype": "tv"}}' )
    json_query = unicode(json_query, 'utf-8', errors='ignore')
    json_query = json.loads(json_query)

    if json_query.has_key('result') and json_query['result'].has_key('channelgroups'):
        for group in json_query['result']['channelgroups']:
            # Perform a JSON query to get all channels
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0",  "id": 1, "method": "PVR.GetChannels", "params": {"channelgroupid": %d, "properties": [ "thumbnail", "channeltype", "hidden", "locked", "channel", "lastplayed" ], "limits": {"end": 5}}}' %( group[ "channelgroupid" ] ) )
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            json_query = json.loads(json_query)
            if json_query.has_key('result') and json_query['result'].has_key('channels'):
                for item in json_query['result']['channels']:
                    channelname = item["label"]
                    channelid = item["channelid"]
                    # Get current show for the channel
                    json_query = xbmc.executeJSONRPC( '{ "jsonrpc": "2.0",  "id": 1, "method": "PVR.GetBroadcasts", "params": {"channelid": %d, "properties": [ "title", "plot", "plotoutline", "starttime", "endtime", "runtime", "progress", "progresspercentage", "genre", "episodename", "episodenum", "episodepart", "firstaired", "hastimer", "isactive", "parentalrating", "wasactive", "thumbnail" ], "limits": {"end": 1} } }' %( item[ "channelid" ] ) )
                    json_query = unicode(json_query, 'utf-8', errors='ignore')
                    json_query = json.loads(json_query)
                    if json_query.has_key( "result" ) and json_query[ "result" ].has_key( "broadcasts" ):
                        for item in json_query['result']['broadcasts']:
                            image = searchThumb(item["title"] + " " + channelname)
                            path="plugin://script.skin.helper.service/?action=launchpvr&path=" + str(channelid)
                            li = xbmcgui.ListItem(item["title"], path=path)
                            li.setThumbnailImage(image)
                            li.setProperty('IsPlayable', 'false')
                            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=li, isFolder=True)
                    if xbmc.abortRequested:
                        return None, None
    
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def getThumb(searchphrase):
    WINDOW.clearProperty("SkinHelper.ListItemThumb")
    
    while xbmc.getCondVisibility("Container.Scrolling") or WINDOW.getProperty("getthumbbusy")=="busy":
        xbmc.sleep(150)
    image = searchThumb(searchphrase)
    if image:
        WINDOW.setProperty("SkinHelper.ListItemThumb",image)
    else:
        WINDOW.clearProperty("SkinHelper.ListItemThumb")
    li = xbmcgui.ListItem(searchphrase, path=image)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=image, listitem=li)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
          
def getNextEpisodes(limit):
    if not limit:
        limit = 25
    count = 0
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    # First we get a list of all the in-progress TV shows
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": { "sort": { "order": "descending", "method": "lastplayed" }, "filter": {"and": [{"operator":"true", "field":"inprogress", "value":""}]}, "properties": [ "title", "studio", "mpaa", "file", "art" ] }, "id": "1"}')

    json_result = json.loads(json_query_string.decode('utf-8','replace'))
    # If we found any, find the oldest unwatched show for each one.
    if json_result.has_key('result') and json_result['result'].has_key('tvshows'):
        for item in json_result['result']['tvshows']:
            json_query2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "tvshowid": %d, "sort": {"method":"episode"}, "filter": {"and": [ {"field": "playcount", "operator": "lessthan", "value":"1"}, {"field": "season", "operator": "greaterthan", "value": "0"} ]}, "properties": [ "title", "playcount", "season", "episode", "showtitle", "plot", "file", "rating", "resume", "tvshowid", "art", "streamdetails", "firstaired", "runtime", "writer", "cast", "dateadded", "lastplayed" ], "limits":{"end":1}}, "id": "1"}' %item['tvshowid'])
            if json_query2:
                json_query2 = json.loads(json_query2.decode('utf-8','replace'))
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
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('tvshows'):
            for item in json_result['result']['tvshows']:
                json_query2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "tvshowid": %d, "sort": {"method":"episode"}, "filter": {"and": [ {"field": "playcount", "operator": "lessthan", "value":"1"}, {"field": "season", "operator": "greaterthan", "value": "0"} ]}, "properties": [ "title", "playcount", "season", "episode", "showtitle", "plot", "file", "rating", "resume", "tvshowid", "art", "streamdetails", "firstaired", "runtime", "writer", "cast", "dateadded", "lastplayed" ], "limits":{"end":1}}, "id": "1"}' %item['tvshowid'])
                if json_query2:
                    json_query2 = json.loads(json_query2.decode('utf-8','replace'))
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
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "sort": { "order": "descending", "method": "lastplayed" }, "filter": {"and": [{"operator":"true", "field":"inprogress", "value":""}]}, "properties": [ "title", "playcount", "plot", "file", "rating", "resume", "studio", "art", "streamdetails", "year", "runtime", "writer", "cast", "dateadded", "lastplayed" ] }, "id": "1"}')
    json_result = json.loads(json_query_string.decode('utf-8','replace'))
    # If we found any, find the oldest unwatched show for each one.
    if json_result.has_key('result') and json_result['result'].has_key('movies'):
        for item in json_result['result']['movies']:
            liz = createListItem(item)
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
            count +=1
            if count == limit:
                break
    
    # Fill the list with random items with a score higher then 7
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"},{"operator":"greaterthan", "field":"rating", "value":"7"}]}, "properties": [ "title", "playcount", "plot", "studio", "file", "rating", "resume", "art", "streamdetails", "year", "runtime", "writer", "cast", "dateadded", "lastplayed" ] }, "id": "1"}')
    json_result = json.loads(json_query_string.decode('utf-8','replace'))
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
    json_result = json.loads(json_query_string.decode('utf-8','replace'))
    if json_result.has_key('result') and json_result['result'].has_key('movies'):
        for item in json_result['result']['movies']:
            genres = item["genre"]
            originalTitle = item["title"]
            #get all movies from the same genre
            for genre in genres:
                json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"genre", "value":"' + genre.encode('utf-8') + '"}, {"operator":"is", "field":"playcount", "value":"0"}]}, "properties": [ "title", "playcount", "plot", "file", "genre", "rating", "resume", "art", "streamdetails", "year", "mpaa", "runtime", "writer", "cast", "dateadded", "lastplayed", "tagline" ],"limits":{"end":10} }, "id": "1"}')
                json_result = json.loads(json_query_string.decode('utf-8','replace'))
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
            json_result = json.loads(json_query_string.decode('utf-8','replace'))
            if json_result.has_key('result') and json_result['result'].has_key('files'):
                for item in json_result['result']['files']:
                    lastplayed = item["lastplayed"]
                    if not item["title"] in allTitles:
                        allItems.append((lastplayed,item))
                        allTitles.append(item["title"])
        
        # Get a list of all the in-progress Movies
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "sort": { "order": "descending", "method": "lastplayed" }, "filter": {"and": [{"operator":"true", "field":"inprogress", "value":""}]}, "properties": [ "title", "playcount", "plot", "file", "rating", "resume", "art", "streamdetails", "year", "mpaa", "runtime", "writer", "cast", "dateadded", "lastplayed", "tagline" ] }, "id": "1"}')
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('movies'):
            for item in json_result['result']['movies']:
                lastplayed = item["lastplayed"]
                if not item["title"] in allTitles:
                    allItems.append((lastplayed,item))
                    allTitles.append(item["title"])
        
        # Get a list of all the in-progress MusicVideos
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMusicVideos", "params": { "sort": { "order": "descending", "method": "lastplayed" }, "limits": { "start" : 0, "end": 25 }, "properties": [ "title", "playcount", "plot", "file", "resume", "art", "streamdetails", "year", "runtime", "dateadded", "lastplayed" ] }, "id": "1"}')
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('musicvideos'):
            for item in json_result['result']['musicvideos']:
                lastplayed = item["lastplayed"]
                if not item["title"] in allTitles and item["resume"]["position"] != 0:
                    allItems.append((lastplayed,item))
                    allTitles.append(item["title"])
        
        # Get a list of all the in-progress music songs
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetRecentlyPlayedSongs", "params": { "sort": { "order": "descending", "method": "lastplayed" }, "limits": { "start" : 0, "end": 5 }, "properties": [ "artist", "title", "rating", "fanart", "thumbnail", "duration", "playcount", "comment", "file", "album", "lastplayed" ] }, "id": "1"}')
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('songs'):
            for item in json_result['result']['songs']:
                lastplayed = item["lastplayed"]
                if not item["title"] in allTitles and lastplayed and item["thumbnail"]:
                    allItems.append((lastplayed,item))
                    allTitles.append(item["title"])
        
        # Get a list of all the in-progress tv recordings   
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0",  "id": 1, "method": "PVR.GetRecordings", "params": {"properties": [ "title", "plot", "plotoutline", "genre", "playcount", "resume", "channel", "starttime", "endtime", "runtime", "lifetime", "icon", "art", "streamurl", "file", "directory" ]}}' )
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('recordings'):
            for item in json_result['result']['recordings']:
                lastplayed = None
                if not item["title"] in allTitles and item["playcount"] == 0:
                    allItems.append((lastplayed,item))
                    allTitles.append(item["title"])
          

        # NextUp episodes
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": { "sort": { "order": "descending", "method": "lastplayed" }, "filter": {"and": [{"operator":"true", "field":"inprogress", "value":""}]}, "properties": [ "title", "studio", "mpaa", "file", "art" ] }, "id": "1"}')
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
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
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('movies'):
            for item in json_result['result']['movies']:
                rating = item["rating"]
                if not item["title"] in set(allTitles):
                    allItems.append((rating,item))
                    allTitles.append(item["title"])
                    
        # Random tvshows with a score higher then 7
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": { "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"},{"operator":"greaterthan", "field":"rating", "value":"7"}]}, "properties": [ "title", "playcount", "plot", "file", "rating", "art", "year", "genre", "mpaa", "cast", "dateadded", "lastplayed" ],"limits":{"end":25} }, "id": "1"}')
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('tvshows'):
            for item in json_result['result']['tvshows']:
                rating = item["rating"]
                if not item["title"] in set(allTitles):
                    
                    #get the first unwatched episode for this show
                    json_query2 = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "tvshowid": %d, "sort": {"method":"episode"}, "filter": {"and": [ {"field": "playcount", "operator": "lessthan", "value":"1"}, {"field": "season", "operator": "greaterthan", "value": "0"} ]}, "properties": [ "title", "file" ], "limits":{"end":1}}, "id": "1"}' %item['tvshowid'])
                    if json_query2:
                        json_query2 = json.loads(json_query2.decode('utf-8','replace'))
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
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "sort": { "order": "descending", "method": "dateadded" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"},{"operator":"false", "field":"inprogress", "value":""}]}, "properties": [ "title", "playcount", "studio", "plot", "file", "rating", "resume", "art", "streamdetails", "year", "mpaa", "runtime", "writer", "cast", "dateadded", "lastplayed", "tagline" ], "limits":{"end":15} }, "id": "1"}')
    json_result = json.loads(json_query_string.decode('utf-8','replace'))
    if json_result.has_key('result') and json_result['result'].has_key('movies'):
        for item in json_result['result']['movies']:
            dateadded = item["dateadded"]
            if not item["title"] in allTitles:
                allItems.append((dateadded,item))
                allTitles.append(item["title"])
    
    # Get a list of all the recent MusicVideos (unwatched and not in progress)
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMusicVideos", "params": { "limits": { "start" : 0, "end": 15 },"sort": { "order": "descending", "method": "dateadded" }, "filter": {"operator":"is", "field":"playcount", "value":"0"}, "properties": [ "title", "playcount", "plot", "file", "resume", "art", "streamdetails", "year", "runtime", "dateadded", "lastplayed" ] }, "id": "1"}')
    json_result = json.loads(json_query_string.decode('utf-8','replace'))
    if json_result.has_key('result') and json_result['result'].has_key('musicvideos'):
        for item in json_result['result']['musicvideos']:
            dateadded = item["dateadded"]
            if not item["title"] in allTitles and item["resume"]["position"] == 0:
                allItems.append((dateadded,item))
                allTitles.append(item["title"])
    
    # Get a list of all the recent music songs
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs", "params": { "limits": { "start" : 0, "end": 15 }, "sort": {"order": "descending", "method": "dateadded" }, "filter": {"operator":"is", "field":"playcount", "value":"0"}, "properties": [ "artist", "title", "rating", "fanart", "thumbnail", "duration", "playcount", "comment", "file", "album", "lastplayed" ] }, "id": "1"}')
    json_result = json.loads(json_query_string.decode('utf-8','replace'))
    if json_result.has_key('result') and json_result['result'].has_key('songs'):
        for item in json_result['result']['songs']:
            dateadded = ""
            if not item["title"] in allTitles and item["thumbnail"]:
                allItems.append((dateadded,item))
                allTitles.append(item["title"])
    
    
    # Get a list of all the recent episodes (unwatched and not in progress)
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "sort": { "order": "descending", "method": "dateadded" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"},{"operator":"false", "field":"inprogress", "value":""}]}, "properties": [ "title", "playcount", "season", "episode", "showtitle", "plot", "file", "rating", "resume", "tvshowid", "art", "streamdetails", "firstaired", "runtime", "writer", "cast", "dateadded", "lastplayed" ], "limits":{"end":15} }, "id": "1"}')
    json_result = json.loads(json_query_string.decode('utf-8','replace'))
    if json_result.has_key('result') and json_result['result'].has_key('episodes'):
        for item in json_result['result']['episodes']:
            dateadded = item["dateadded"]
            if not item["title"] in allTitles:
                allItems.append((dateadded,item))
                allTitles.append(item["title"])
            
    
    # Get a list of all the unwatched tv recordings   
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0",  "id": 1, "method": "PVR.GetRecordings", "params": {"properties": [ "title", "plot", "plotoutline", "genre", "playcount", "resume", "channel", "starttime", "endtime", "runtime", "lifetime", "icon", "art", "streamurl", "file", "directory" ]}}' )
    json_result = json.loads(json_query_string.decode('utf-8','replace'))
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
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('files'):
            for item in json_result['result']['files']:
                liz = createListItem(item)
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
    
    #emby favorites
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.emby) + Skin.HasSetting(SmartShortcuts.emby)"):
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter": {"operator":"contains", "field":"tag", "value":"Favorite movies"}, "properties": [ "title", "playcount", "plot", "file", "rating", "resume", "art", "streamdetails", "year", "mpaa", "runtime", "writer", "cast", "dateadded", "lastplayed", "tagline" ] }, "id": "1"}')
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('movies'):
            for item in json_result['result']['movies']:
                liz = createListItem(item)
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
        
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTvShows", "params": { "filter": {"operator":"contains", "field":"tag", "value":"Favorite tvshows"}, "properties": [ "title", "playcount", "plot", "file", "rating", "art", "premiered", "genre", "cast", "dateadded", "lastplayed" ] }, "id": "1"}')
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('tvshows'):
            for item in json_result['result']['tvshows']:
                liz = createListItem(item)
                tvshowpath = "ActivateWindow(Videos,videodb://tvshows/titles/%s/,return)" %str(item["tvshowid"])
                tvshowpath="plugin://script.skin.helper.service?LAUNCHAPP&&&" + tvshowpath
                liz.setProperty('IsPlayable', 'false')
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=tvshowpath, listitem=liz)
            
    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Favourites.GetFavourites", "params": {"type": null, "properties": ["path", "thumbnail", "window", "windowparameter"]}, "id": "1"}')
    json_result = json.loads(json_query_string.decode('utf-8','replace'))
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
                        json_result = json.loads(json_query_string.decode('utf-8','replace'))
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
                    if isinstance(path, unicode):
                        path = path.encode("utf-8")
                    if "/" in path:
                        sep = "/"
                    else:
                        sep = "\\"
                    path = try_decode(path)
                    pathpart = path.split(sep)[-1] #apparently only the filename can be used for the search
                    #is this a movie?
                    json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter": {"operator":"contains", "field":"filename", "value":"' + pathpart + '"}, "properties": [ "title", "playcount", "plot", "file", "rating", "resume", "art", "streamdetails", "year", "mpaa", "runtime", "writer", "cast", "dateadded", "lastplayed", "tagline" ] }, "id": "1"}')
                    json_result = json.loads(json_query_string.decode('utf-8','replace'))
                    if json_result.has_key('result') and json_result['result'].has_key('movies'):
                        for item in json_result['result']['movies']:
                            if item['file'] == path:
                                matchFound = True
                                liz = createListItem(item)
                                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
                    
                    if matchFound == False:
                        #is this an episode ?
                        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": { "filter": {"operator":"contains", "field":"filename", "value":"' + pathpart + '"}, "properties": [ "title", "playcount", "season", "episode", "showtitle", "plot", "file", "rating", "resume", "tvshowid", "art", "streamdetails", "firstaired", "runtime", "writer", "cast", "dateadded", "lastplayed" ] }, "id": "1"}')
                        json_result = json.loads(json_query_string.decode('utf-8','replace'))
                        if json_result.has_key('result') and json_result['result'].has_key('episodes'):
                            for item in json_result['result']['episodes']:
                                if item['file'] == path:
                                    matchFound = True
                                    liz = createListItem(item)
                                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
                    if matchFound == False:
                        #is this a song?
                        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetSongs", "params": { "filter": {"operator":"contains", "field":"filename", "value":"' + pathpart + '"}, "properties": [ "artist", "title", "rating", "fanart", "thumbnail", "duration", "playcount", "comment", "file", "album", "lastplayed" ] }, "id": "1"}')
                        json_result = json.loads(json_query_string.decode('utf-8','replace'))
                        if json_result.has_key('result') and json_result['result'].has_key('songs'):
                            for item in json_result['result']['songs']:
                                if item['file'] == path:
                                    matchFound = True
                                    liz = createListItem(item)
                                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
                                    
                    if matchFound == False:
                        #is this a musicvideo?
                        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMusicVideos", "params": { "filter": {"operator":"contains", "field":"filename", "value":"' + pathpart + '"}, "properties": [ "title", "playcount", "plot", "file", "resume", "art", "streamdetails", "year", "runtime", "dateadded", "lastplayed" ] }, "id": "1"}')
                        json_result = json.loads(json_query_string.decode('utf-8','replace'))
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
        
def getCast(movie=None,tvshow=None,movieset=None):
    
    itemId = None
    item = {}
    castList = []
    moviesetmovies = None
    try:
        if movieset:
            itemId = int(movieset)
        if tvshow:
            itemId = int(tvshow)
        else:
            itemId = int(movie)
    except:
        pass

    if movie and itemId:
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovieDetails", "params": { "movieid": %d, "properties": [ "title", "cast" ] }, "id": "1"}' %itemId)
        print json_query_string
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('moviedetails'):
            item = json_result['result']['moviedetails']
    elif movie and not itemId:
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": { "filter": {"operator":"is", "field":"title", "value":"%s"}, "properties": [ "title", "cast" ] }, "id": "1"}' %movie)
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('movies'):
            item = json_result['result']['movies'][0]
    elif tvshow and itemId:
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShowDetails", "params": { "tvshowid": %d, "properties": [ "title", "cast" ] }, "id": "1"}' %itemId)
        print json_query_string
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('tvshowdetails'):
            item = json_result['result']['tvshowdetails']
    elif tvshow and not itemId:
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTvShows", "params": { "filter": {"operator":"is", "field":"title", "value":"%s"}, "properties": [ "title", "cast" ] }, "id": "1"}' %tvshow)
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('tvshows'):
            item = json_result['result']['tvshows'][0]
    elif movieset and itemId:
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovieSetDetails", "params": { "setid": %d, "properties": [ "title", "cast" ] }, "id": "1"}' %itemId)
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('setdetails'):
            movieset = json_result['result']['setdetails']
            if movieset.has_key("movies"):
                moviesetmovies = movieset['movies']:        
    elif movieset and not itemId:
        json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovieSets", "params": { "filter": {"operator":"is", "field":"title", "value":"%s"}, "properties": [ "title", "cast" ] }, "id": "1"}' %tvshow)
        json_result = json.loads(json_query_string.decode('utf-8','replace'))
        if json_result.has_key('result') and json_result['result'].has_key('sets '):
            movieset = json_result['result']['sets '][0]
            if movieset.has_key("movies"):
                moviesetmovies = movieset['movies']:
    
    #process cast for regular movie or show
    if item and item.has_key("cast"):
        for cast in item["cast"]:
            liz = xbmcgui.ListItem(label=cast["name"],label2=cast["role"],iconImage=cast["thumbnail"])
            liz.setProperty('IsPlayable', 'false')
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url="", listitem=liz, isFolder=True)
    
    #process cast for all movies in a movieset
    elif moviesetmovies:
        for setmovie in moviesetmovies:
            json_query_string = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovieDetails", "params": { "movieid": %d, "properties": [ "title", "cast" ] }, "id": "1"}' %setmovie["movieid"])
            json_result = json.loads(json_query_string.decode('utf-8','replace'))
            if json_result.has_key('result') and json_result['result'].has_key('moviedetails'):
                item = json_result['result']['moviedetails']
                for cast in item["cast"]:
                    if not cast["name"] in castList:
                        liz = xbmcgui.ListItem(label=cast["name"],label2=cast["role"],iconImage=cast["thumbnail"])
                        liz.setProperty('IsPlayable', 'false')
                        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url="", listitem=liz, isFolder=True)
                        castList.append(cast["name"])
            
     
    xbmcplugin.endOfDirectory(int(sys.argv[1]))    