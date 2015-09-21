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
    addDirectoryItem(ADDON.getLocalizedString(32086), "plugin://script.skin.helper.service/?action=inprogressmedia&limit=100")
    addDirectoryItem(ADDON.getLocalizedString(32007), "plugin://script.skin.helper.service/?action=inprogressandrecommendedmedia&limit=100")
    if xbmc.getCondVisibility("System.HasAddon(script.tv.show.next.aired)"):
        addDirectoryItem(ADDON.getLocalizedString(32055), "plugin://script.skin.helper.service/?action=nextairedtvshows&limit=100")

    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
def addSmartShortcutDirectoryItem(entry, isFolder=True, widget=None, widget2=None):
    
    label = "$INFO[Window(Home).Property(%s.title)]" %entry
    path = "$INFO[Window(Home).Property(%s.path)]" %entry
    content = "$INFO[Window(Home).Property(%s.content)]" %entry
    image = "$INFO[Window(Home).Property(%s.image)]" %entry
    type = "$INFO[Window(Home).Property(%s.type)]" %entry

    if isFolder:
        path = sys.argv[0] + "?action=SMARTSHORTCUTS&path=" + entry
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
            
        if widget2:
            widgettype = "$INFO[Window(Home).Property(%s.type)]" %widget2
            if not xbmc.getInfoLabel(type):
                widgettype = type
            if widgettype == "albums" or widgettype == "artists" or widgettype == "songs":
                widgettarget = "music"
            else:
                widgettarget = "video"
            props["widget.1"] = "addon"
            props["widgetName.1"] = "$INFO[Window(Home).Property(%s.title)]" %widget2
            props["widgetType.1"] = widgettype
            props["widgetTarget.1"] = widgettarget
            props["widgetPath.1"] = "$INFO[Window(Home).Property(%s.content)]" %widget2
            
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
        widget2 = None
        if contentString == "":
            #this is the main item so define our widgets
            type = xbmc.getInfoLabel("$INFO[Window(Home).Property(%s.type)]" %entry)
            if "plex" in "entry":
                widget = entry + ".ondeck"
                widget2 = entry + ".recent"
            elif type == "movies" or type == "movie" or type == "artist" or "netflix" in entry:
                widget = entry + ".recent"
                widget2 = entry + ".inprogress"
            elif type == "tvshows" and "emby" in "entry":
                widget = entry + ".nextepisodes"
                widget2 = entry + ".recent"
            else:
                widget = entry
        
        if xbmc.getInfoLabel("$INFO[Window(Home).Property(%s.path)]" %key):
            addSmartShortcutDirectoryItem(key,False, widget,widget2)

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
    
    #addons that provide dynamic content for widgets
    #will only be loaded once so no cache refreshes
    addonList = []
    addonList.append(["script.skin.helper.service", "scriptwidgets"])
    addonList.append(["service.library.data.provider", "librarydataprovider"])
    addonList.append(["script.extendedinfo", "extendedinfo"])
    
    for addon in addonList:
        if not allWidgets.has_key(addon[1]):
            foundWidgets = []
            if xbmc.getCondVisibility("System.HasAddon(%s)" %addon[0]):
                media_array = getJSON('Files.GetDirectory','{ "directory": "plugin://%s", "media": "files" }' %addon[0])
                for item in media_array:
                    #safety check: check if no library windows are active to prevent any addons setting the view
                    curWindow = xbmc.getInfoLabel("$INFO[Window.Property(xmlfile)]")
                    if curWindow.endswith("Nav.xml") or curWindow == "AddonBrowser.xml" or curWindow.startswith("MyPVR"):
                        return
                    content = item["file"]
                    if not "reload=" in content and not addon[0] == "script.extendedinfo":
                        content = content + "&reload=$INFO[Window(Home).Property(widgetreload)]"
                    content = content.replace("&limit=100","&limit=25")
                    label = item["label"]
                    if addon[1] == "extendedinfo":
                        type, image = detectPluginContent(item["file"], True)
                    else:
                        type, image = detectPluginContent(item["file"], False)
                    foundWidgets.append([label, content, image, type])
                if addon[1] == "extendedinfo":
                    #some additional entrypoints for extendedinfo...
                    entrypoints = ["plugin://script.extendedinfo?info=youtubeusersearch&&id=Eurogamer","plugin://script.extendedinfo?info=youtubeusersearch&&id=Engadget","plugin://script.extendedinfo?info=youtubeusersearch&&id=MobileTechReview"]
                    for entry in entrypoints:
                        content = entry
                        label = entry.split("id=")[1]
                        type = "video"
                        foundWidgets.append([label, content, "", type])

            allWidgets[addon[1]] = foundWidgets
    
    #skin provided playlists
    paths = ["special://skin/playlists/","special://skin/extras/widgetplaylists/"]
    playlistsFound = []
    for path in paths:
        if xbmcvfs.exists(path):
            media_array = getJSON('Files.GetDirectory','{ "directory": "%s", "media": "files" }' %path)
            for item in media_array:
                if item["file"].endswith(".xsp"):
                    playlist = item["file"]
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
                    playlistsFound.append([label, playlist, image, type])
    allWidgets["skinplaylists"] = playlistsFound
        
    #widgets from favourites
    json_result = getJSON('Favourites.GetFavourites', '{"type": null, "properties": ["path", "thumbnail", "window", "windowparameter"]}')
    foundWidgets = []
    for fav in json_result:
        matchFound = False
        if "windowparameter" in fav:
            content = fav["windowparameter"]
            if content.startswith("plugin://") and not content.endswith("/"):
                content = content + "&reload=$INFO[Window(Home).Property(widgetreload2)]"
            #check if this is a valid path with content
            if not "script://" in content.lower() and not "mode=9" in content.lower() and not "search" in content.lower() and not "play" in content.lower():
                window = fav["window"]
                label = fav["title"]
                type, image = detectPluginContent(content)
                if type:
                    foundWidgets.append([label, content, image, type])
    allWidgets["favourites"] = foundWidgets
                        
    #some other widgets (by their direct endpoint) such as smartish widgets and PVR
    otherWidgets = ["pvr","smartishwidgets","static"]
    for widget in otherWidgets:
        if not allWidgets.has_key(widget):
            foundWidgets = []
            if widget=="pvr" and xbmc.getCondVisibility("PVR.HasTVChannels"):
                foundWidgets.append(["$LOCALIZE[19023]", "plugin://script.skin.helper.service/?action=pvrchannels&limit=25&reload=$INFO[Window(home).Property(widgetreload2)]", "", "pvr"])
                foundWidgets.append(["$LOCALIZE[19017]", "plugin://script.skin.helper.service/?action=pvrrecordings&limit=25&reload=$INFO[Window(home).Property(widgetreload2)]", "", "pvr"])   
            if widget=="smartishwidgets" and xbmc.getCondVisibility("System.HasAddon(service.smartish.widgets) + Skin.HasSetting(enable.smartish.widgets)"):
                foundWidgets.append(["Smart(ish) Movies widget", "plugin://service.smartish.widgets?type=movies&reload=$INFO[Window.Property(smartish.movies)]", "", "movies"])
                foundWidgets.append(["Smart(ish) Episodes widget", "plugin://service.smartish.widgets?type=episodes&reload=$INFO[Window.Property(smartish.episodes)]", "", "episodes"])
                foundWidgets.append(["Smart(ish) PVR widget", "plugin://service.smartish.widgets?type=pvr&reload=$INFO[Window.Property(smartish.pvr)]", "", "pvr"])
                foundWidgets.append(["Smart(ish) Albums widget", "plugin://service.smartish.widgets?type=albums&reload=$INFO[Window.Property(smartish.albums)]", "", "albums"])
            
            if widget=="static":
                foundWidgets.append(["$LOCALIZE[8]", "$INCLUDE[WeatherWidget]", "", "static"])
                foundWidgets.append(["$LOCALIZE[130]", "$INCLUDE[SystemInfoWidget]", "", "static"])
                foundWidgets.append(["$LOCALIZE[31196]", "$INCLUDE[skinshortcuts-submenu]", "", "static"])
                if xbmc.getCondVisibility("System.HasAddon(script.games.rom.collection.browser)"):
                    foundWidgets.append(["RCB Most played games", "$INCLUDE[RCBWidget]", "", "static"])
            
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
                    type = widget[3]
                    if type == "songs" or type == "albums" or type == "artists":
                        mediaLibrary = "10502"
                        target = "music"
                    else:
                        mediaLibrary = "VideoLibrary"
                        target = "video"
                    widgetpath = "ActivateWindow(%s,%s,return)" %(mediaLibrary, widget[1])
                    li = xbmcgui.ListItem(widget[0], path=widgetpath)
                    props = {}
                    props["list"] = widget[1]
                    props["type"] = widget[3]
                    props["background"] = widget[2]
                    props["backgroundName"] = widget[0]
                    props["widgetPath"] = widget[1]
                    props["widgetTarget"] = target
                    props["widget"] = widgetType
                    li.setInfo( type="Video", infoLabels={ "Title": "smartshortcut" })
                    li.setThumbnailImage(widget[2])
                    li.setIconImage("special://home/addons/script.skin.helper.service/fanart.jpg")
                        
                    li.setInfo( type="Video", infoLabels={ "mpaa": repr(props) })
                    
                    li.setArt({"fanart":widget[2]})   
                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=widgetpath, listitem=li, isFolder=False)
    
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
    
    if xbmc.getCondVisibility("System.HasAddon(script.extendedinfo)"):
        globalBackgrounds.append((xbmc.getInfoLabel("$ADDON[script.extendedinfo 32046]") + " (TheMovieDB)", "SkinHelper.TopRatedMovies"))
        globalBackgrounds.append((xbmc.getInfoLabel("$ADDON[script.extendedinfo 32040]") + " (TheMovieDB)", "SkinHelper.TopRatedShows"))
    
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

def getPVRRecordings(limit):
    xbmcplugin.setContent(int(sys.argv[1]), 'livetv')

    pvrArtCache = WINDOW.getProperty("SkinHelper.pvrArtCache")
    if pvrArtCache:
        pvrArtCache = eval(pvrArtCache)
    else:
        pvrArtCache = {}
        
    json_query = getJSON('PVR.GetRecordings', '{ "properties": [ %s ], "limits": {"end": %d}}' %( fields_pvrrecordings, limit))
    for item in json_query:
        channelname = item["channel"]
        pvrArtCache,thumb,fanart,poster,logo = getPVRThumbs(pvrArtCache, item["title"], channelname)
        path=item["file"]
        li = xbmcgui.ListItem()
        li.setLabel(channelname)
        li.setLabel2(item['title'])
        li.setInfo( type="Video", infoLabels={ "Title": item['title'] })
        li.setProperty("StartTime",item['starttime'])
        li.setProperty("ChannelIcon",logo)
        li.setProperty("ChannelName",channelname)
        li.setInfo( type="Video", infoLabels={ "genre": " / ".join(item['genre']) })
        li.setInfo( type="Video", infoLabels={ "duration": item['runtime'] })
        li.setInfo( type="Video", infoLabels={ "Playcount": item['playcount'] })
        li.setProperty("resumetime", str(item['resume']['position']))
        li.setProperty("totaltime", str(item['resume']['total']))
        li.setThumbnailImage(thumb)
        li.setIconImage(item["icon"])
        li.setInfo( type="Video", infoLabels={ "Plot": item['plot'] })
        li.setProperty('IsPlayable', 'true')
        li.setArt({ 'poster': poster, 'fanart' : fanart })

        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=li, isFolder=False)
    WINDOW.setProperty("SkinHelper.pvrArtCache",repr(pvrArtCache))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))    
    
def getPVRChannels(limit):
    xbmcplugin.setContent(int(sys.argv[1]), 'livetv')

    pvrArtCache = WINDOW.getProperty("SkinHelper.pvrArtCache")
    if pvrArtCache:
        pvrArtCache = eval(pvrArtCache)
    else:
        pvrArtCache = {}
        
    # Perform a JSON query to get all channels
    json_query = getJSON('PVR.GetChannels', '{"channelgroupid": "alltv", "properties": [ "thumbnail", "channeltype", "hidden", "locked", "channel", "lastplayed", "broadcastnow" ], "limits": {"end": %d}}' %( limit ) )
    for item in json_query:
        channelname = item["label"]
        channelid = item["channelid"]
        channelicon = item['thumbnail']
        if item.has_key('broadcastnow'):
            currentprogram = item['broadcastnow']
            pvrArtCache,thumb,fanart,poster,logo = getPVRThumbs(pvrArtCache, currentprogram["title"], channelname)
            if not channelicon:
                channelicon = logo
            path="plugin://script.skin.helper.service/?action=launchpvr&path=" + str(channelid)
            li = xbmcgui.ListItem()
            li.setLabel(channelname)
            li.setLabel2(currentprogram['title'])
            li.setInfo( type="Video", infoLabels={ "Title": currentprogram['title'] })
            li.setProperty("StartTime",currentprogram['starttime'].split(" ")[1])
            li.setProperty("StartDate",currentprogram['starttime'].split(" ")[0])
            li.setProperty("EndTime",currentprogram['endtime'].split(" ")[1])
            li.setProperty("EndDate",currentprogram['endtime'].split(" ")[0])
            li.setProperty("ChannelIcon",channelicon)
            li.setProperty("ChannelName",channelname)
            li.setProperty("EpisodeName",currentprogram['episodename'])
            li.setProperty("Progress",str(currentprogram['progresspercentage']).split(".")[0])
            li.setInfo( type="Video", infoLabels={ "premiered": currentprogram['firstaired'] })
            li.setInfo( type="Video", infoLabels={ "genre": " / ".join(currentprogram['genre']) })
            li.setInfo( type="Video", infoLabels={ "duration": currentprogram['runtime'] })
            li.setInfo( type="Video", infoLabels={ "rating": str(currentprogram['rating']) })
            li.setThumbnailImage(thumb)
            li.setIconImage(channelicon)
            li.setInfo( type="Video", infoLabels={ "Plot": currentprogram['plot'] })
            li.setProperty('IsPlayable', 'false')
            li.setArt({ 'poster': poster, 'fanart' : fanart })

            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=li, isFolder=False)
    WINDOW.setProperty("SkinHelper.pvrArtCache",repr(pvrArtCache))
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

def buildNextEpisodesListing(limit):
    count = 0
    allItems = []
    # First we get a list of all the in-progress TV shows
    json_result = getJSON('VideoLibrary.GetTVShows', '{ "sort": { "order": "descending", "method": "lastplayed" }, "filter": {"and": [{"operator":"true", "field":"inprogress", "value":""}]}, "properties": [ "title", "studio", "mpaa", "file", "art" ] }')
    # If we found any, find the oldest unwatched show for each one.
    for item in json_result:
        json_episodes = getJSON('VideoLibrary.GetEpisodes', '{ "tvshowid": %d, "sort": {"method":"episode"}, "filter": {"and": [ {"field": "playcount", "operator": "lessthan", "value":"1"}, {"field": "season", "operator": "greaterthan", "value": "0"} ]}, "properties": [ %s ], "limits":{"end":1}}' %(item['tvshowid'],fields_episodes))
        for item in json_episodes:
            allItems.append(item)
            count +=1
            if count == limit:
                break
                            
    if count >= limit:
        # Fill the list with first episodes of unwatched tv shows
        json_result = getJSON('VideoLibrary.GetTVShows', '{ "sort": { "order": "ascending", "method": "dateadded" }, "filter": {"and": [{"operator":"false", "field":"inprogress", "value":""}]}, "properties": [ "title", "studio", "mpaa", "file", "art" ] }')
        for item in json_result:
            json_episodes = getJSON('VideoLibrary.GetEpisodes', '{ "tvshowid": %d, "sort": {"method":"episode"}, "filter": {"and": [ {"field": "playcount", "operator": "lessthan", "value":"1"}, {"field": "season", "operator": "greaterthan", "value": "0"} ]}, "properties": [ %s ], "limits":{"end":1}}' %(item['tvshowid'],fields_episodes))
            for item in json_episodes:
                allItems.append(item)
                count +=1
                if count == limit:
                    break
    if allItems:
        reloadcache = WINDOW.getProperty("widgetreload")
        WINDOW.setProperty("skinhelper-nextepisodes-" + reloadcache, repr(allItems))
    return allItems
    
def getNextEpisodes(limit):
    count = 0
    allItems = []
    
    reloadcache = WINDOW.getProperty("widgetreload")
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    
    allItems = WINDOW.getProperty("skinhelper-nextepisodes-" + reloadcache)
    if allItems:
        allItems = eval(allItems)
    else:
        allItems = buildNextEpisodesListing(limit)
        
    directoryItems = list()
    for item in allItems:
        liz = createListItem(item)
        directoryItems.append((item['file'], liz, False))
        count += 1
        if count == limit:
            break
    
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), directoryItems)                
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

def buildNextAiredTvShowsListing(limit):
    count = 0
    allItems = []
    nextairedTotal = WINDOW.getProperty("NextAired.Total")
    if nextairedTotal:
        nextairedTotal = int(nextairedTotal)
        for count in range(nextairedTotal):
            tvshow = WINDOW.getProperty("NextAired.%s.Label"%str(count))
            json_result = getJSON('VideoLibrary.GetTvShows','{ "filter": {"operator":"is", "field":"title", "value":"%s"}, "properties": [ %s ] }' %(tvshow,fields_tvshows))
            if len(json_result) > 0:
                item = json_result[0]
                path = "videodb://tvshows/titles/%s/" %str(item["tvshowid"])
                item["airtime"] = WINDOW.getProperty("NextAired.%s.AirTime"%str(count))
                item["title"] = WINDOW.getProperty("NextAired.%s.NextTitle"%str(count))
                item["tvshowtitle"] = tvshow
                item["season"] = int(WINDOW.getProperty("NextAired.%s.NextSeasonNumber"%str(count)))
                item["episode"] = int(WINDOW.getProperty("NextAired.%s.NextEpisodeNumber"%str(count)))
                item["file"] = path
                allItems.append(item)
                count += 1
                if count == limit:
                    break
                    
    return allItems
    
def getNextAiredTvShows(limit):
    count = 0
    allItems = []
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows') 
    allItems = WINDOW.getProperty("skinhelper-nextairedtvshows")
    if allItems:   
        allItems = eval(allItems)    
    else:
        allItems = buildNextAiredTvShowsListing(limit) 
        if allItems:
            WINDOW.setProperty("skinhelper-nextairedtvshows", repr(allItems))
  
    directoryItems = list()
    for item in allItems:
        liz = createListItem(item)
        liz.setProperty("AirTime",item["airtime"])
        liz.setInfo( type="Video", infoLabels={ "Plot": item["airtime"] })
        liz.setProperty('IsPlayable', 'false')
        directoryItems.append((item['file'], liz, True))
        count += 1
        if count == limit:
            break
    
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), directoryItems)                
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
    
def getRecommendedMovies(limit):
    count = 0
    allItems = []
    reloadcache = WINDOW.getProperty("widgetreload")
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    
    allItems = WINDOW.getProperty("skinhelper-recommendedmovies-" + reloadcache)
    if allItems:
        allItems = eval(allItems)
    else:
        allItems = buildRecommendedMoviesListing(limit)
    
    directoryItems = list()
    for item in allItems:
        liz = createListItem(item)
        directoryItems.append((item['file'], liz, False))
        count += 1
        if count == limit:
            break
    
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), directoryItems)                
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

def buildRecommendedMoviesListing(limit):
    count = 0
    allItems = []
    # First we get a list of all the in-progress Movies
    json_result = getJSON('VideoLibrary.GetMovies','{ "sort": { "order": "descending", "method": "lastplayed" }, "filter": {"and": [{"operator":"true", "field":"inprogress", "value":""}]}, "properties": [ %s ] }' %fields_movies)
    # If we found any, find the oldest unwatched show for each one.
    for item in json_result:
        if count >= limit:
            break
        allItems.append(item)
        count +=1

    # Fill the list with random items with a score higher then 7
    json_result = getJSON('VideoLibrary.GetMovies','{ "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"},{"operator":"greaterthan", "field":"rating", "value":"7"}]}, "properties": [ %s ] }' %fields_movies)
    # If we found any, find the oldest unwatched show for each one.
    for item in json_result:
        if count >= limit:
            break
        allItems.append(item)
        count +=1
    if allItems:        
        reloadcache = WINDOW.getProperty("widgetreload")
        WINDOW.setProperty("skinhelper-recommendedmovies-" + reloadcache, repr(allItems))
    return allItems
   
def getSimilarMovies(limit):
    count = 0
    allItems = []
    allTitles = list()
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    #picks a random watched movie and finds similar movies in the library
    json_result = getJSON('VideoLibrary.GetMovies', '{ "sort": { "order": "descending", "method": "random" }, "filter": {"operator":"isnot", "field":"playcount", "value":"0"}, "properties": [ "title", "rating", "genre"],"limits":{"end":1}}')
    for item in json_result:
        genres = item["genre"]
        originalTitle = item["title"]
        #get all movies from the same genre
        for genre in genres:
            json_result = getJSON('VideoLibrary.GetMovies', '{ "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"genre", "value":"%s"}, {"operator":"is", "field":"playcount", "value":"0"}]}, "properties": [ %s ],"limits":{"end":10} }' %(genre,fields_movies))
            for item in json_result:
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
    
def buildRecommendedMediaListing(limit,ondeckContent=False,recommendedContent=True):
    count = 0
    allTitles = list()
    allItems = []
    
    pvrArtCache = WINDOW.getProperty("SkinHelper.pvrArtCache")
    if pvrArtCache:
        pvrArtCache = eval(pvrArtCache)
    else:
        pvrArtCache = {}
    
    if ondeckContent:
        allOndeckItems = []

        #netflix in progress
        if xbmc.getCondVisibility("System.HasAddon(plugin.video.netflixbmc) + Skin.HasSetting(SmartShortcuts.netflix)") and WINDOW.getProperty("netflixready") == "ready":
            json_result = getJSON('Files.GetDirectory', '{ "directory": "plugin://plugin.video.netflixbmc/?mode=listSliderVideos&thumb&type=both&widget=true&url=slider_0", "media": "files", "properties": [ %s ] }' %fields_files)
            for item in json_result:
                lastplayed = item["lastplayed"]
                if not item["title"] in allTitles:
                    allOndeckItems.append((lastplayed,item))
                    allTitles.append(item["title"])
        
        # Get a list of all the in-progress Movies
        json_result = getJSON('VideoLibrary.GetMovies', '{ "sort": { "order": "descending", "method": "lastplayed" }, "filter": {"and": [{"operator":"true", "field":"inprogress", "value":""}]}, "properties": [ %s ] }' %fields_movies)
        for item in json_result:
            lastplayed = item["lastplayed"]
            if not item["title"] in allTitles:
                allOndeckItems.append((lastplayed,item))
                allTitles.append(item["title"])
        
        # Get a list of all the in-progress MusicVideos
        json_result = getJSON('VideoLibrary.GetMusicVideos', '{ "sort": { "order": "descending", "method": "lastplayed" }, "limits": { "start" : 0, "end": 25 }, "properties": [ %s ] }' %fields_musicvideos)
        for item in json_result:
            lastplayed = item["lastplayed"]
            if not item["title"] in allTitles and item["resume"]["position"] != 0:
                allOndeckItems.append((lastplayed,item))
                allTitles.append(item["title"])
        
        # Get a list of all the in-progress music songs
        json_result = getJSON('AudioLibrary.GetRecentlyPlayedSongs', '{ "sort": { "order": "descending", "method": "lastplayed" }, "limits": { "start" : 0, "end": 5 }, "properties": [ %s ] }' %fields_songs)
        for item in json_result:
            lastplayed = item["lastplayed"]
            if not item["title"] in allTitles and lastplayed and item["thumbnail"]:
                allOndeckItems.append((lastplayed,item))
                allTitles.append(item["title"])
        
        # Get a list of all the in-progress tv recordings   
        json_result = getJSON('PVR.GetRecordings', '{"properties": [ %s ]}' %fields_pvrrecordings)
        for item in json_result:
            lastplayed = None
            if not item["title"] in allTitles and item["playcount"] == 0:
                pvrArtCache,thumb,fanart,poster,logo = getPVRThumbs(pvrArtCache, item["title"], item["channel"])
                art = { 'poster': poster, 'fanart' : fanart, 'thumb': thumb }
                item["art"] = art
                allOndeckItems.append((lastplayed,item))
                allTitles.append(item["title"])
          

        # NextUp episodes
        json_result = getJSON('VideoLibrary.GetTVShows', '{ "sort": { "order": "descending", "method": "lastplayed" }, "filter": {"and": [{"operator":"true", "field":"inprogress", "value":""}]}, "properties": [ "title" ] }')
        for item in json_result:
            json_query2 = getJSON('VideoLibrary.GetEpisodes', '{ "tvshowid": %d, "sort": {"method":"episode"}, "filter": {"and": [ {"field": "playcount", "operator": "lessthan", "value":"1"}, {"field": "season", "operator": "greaterthan", "value": "0"} ]}, "properties": [ %s ], "limits":{"end":1}}' %(item['tvshowid'], fields_episodes))
            for item in json_query2:
                lastplayed = item["lastplayed"]
                if not item["title"] in allTitles:
                    allOndeckItems.append((lastplayed,item))
                    allTitles.append(item["title"])         
        
        #sort the list with in progress items by lastplayed date   
        from operator import itemgetter
        allItems = sorted(allOndeckItems,key=itemgetter(0),reverse=True)
        
    
    if recommendedContent:
        allRecommendedItems = []
                        
        # Random movies with a score higher then 7
        json_result = getJSON('VideoLibrary.GetMovies', '{ "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"},{"operator":"greaterthan", "field":"rating", "value":"7"}]}, "properties": [ %s ], "limits":{"end":25} }' %fields_movies)
        for item in json_result:
            rating = item["rating"]
            if not item["title"] in set(allTitles):
                allRecommendedItems.append((rating,item))
                allTitles.append(item["title"])
                    
        # Random tvshows with a score higher then 7
        json_result = getJSON('VideoLibrary.GetTVShows', '{ "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"},{"operator":"greaterthan", "field":"rating", "value":"7"}]}, "properties": [ %s ],"limits":{"end":25} }' %fields_tvshows)
        for item in json_result:
            rating = item["rating"]
            if not item["title"] in set(allTitles):
                
                #get the first unwatched episode for this show
                json_query2 = getJSON('VideoLibrary.GetEpisodes', '{ "tvshowid": %d, "sort": {"method":"episode"}, "filter": {"and": [ {"field": "playcount", "operator": "lessthan", "value":"1"}, {"field": "season", "operator": "greaterthan", "value": "0"} ]}, "properties": [ "title", "file" ], "limits":{"end":1}}' %item['tvshowid'])
                if json_query2:
                    item["file"] = json_query2[0]["file"]
                    allRecommendedItems.append((rating,item))
                    allTitles.append(item["title"])
                    
        #sort the list with recommended items by rating 
        from operator import itemgetter
        allItems += sorted(allRecommendedItems,key=itemgetter(0),reverse=True)
     
    
    WINDOW.setProperty("SkinHelper.pvrArtCache",repr(pvrArtCache))
    return allItems

def getInProgressAndRecommendedMedia(limit):
    count = 0
    allItems = []
    
    reloadcache = WINDOW.getProperty("widgetreload")
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    
    allItems = WINDOW.getProperty("skinhelper-InProgressAndRecommendedMedia-" + reloadcache)
    if allItems:
        allItems = eval(allItems)
    else:
        allItems = buildRecommendedMediaListing(limit,ondeckContent=True,recommendedContent=True)
        if allItems:
            WINDOW.setProperty("skinhelper-InProgressAndRecommendedMedia-" + reloadcache, repr(allItems))

    directoryItems = list()
    for item in allItems:
        liz = createListItem(item[1])
        directoryItems.append((item[1]['file'], liz, False))
        count += 1
        if count == limit:
            break
    
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), directoryItems)                
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

def getInProgressMedia(limit):
    count = 0
    allItems = []
    
    reloadcache = WINDOW.getProperty("widgetreload")
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    
    allItems = WINDOW.getProperty("skinhelper-InProgressMedia-" + reloadcache)
    if allItems:
        allItems = eval(allItems)
    else:
        allItems = buildRecommendedMediaListing(limit,ondeckContent=True,recommendedContent=False)
        if allItems:
            WINDOW.setProperty("skinhelper-InProgressMedia-" + reloadcache, repr(allItems))

    directoryItems = list()
    for item in allItems:
        liz = createListItem(item[1])
        directoryItems.append((item[1]['file'], liz, False))
        count += 1
        if count == limit:
            break
    
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), directoryItems)                
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

def getRecommendedMedia(limit):
    count = 0
    allItems = []
    
    reloadcache = WINDOW.getProperty("widgetreload")
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    
    allItems = WINDOW.getProperty("skinhelper-RecommendedMedia-" + reloadcache)
    if allItems:
        allItems = eval(allItems)
    else:
        allItems = buildRecommendedMediaListing(limit,ondeckContent=False,recommendedContent=True)
        if allItems:
            WINDOW.setProperty("skinhelper-RecommendedMedia-" + reloadcache, repr(allItems))

    directoryItems = list()
    for item in allItems:
        liz = createListItem(item[1])
        directoryItems.append((item[1]['file'], liz, False))
        count += 1
        if count == limit:
            break
    
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), directoryItems)                
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))   
    
def getRecentMedia(limit):
    count = 0
    allItems = []
    allTitles = list()
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    
    pvrArtCache = WINDOW.getProperty("SkinHelper.pvrArtCache")
    if pvrArtCache:
        pvrArtCache = eval(pvrArtCache)
    else:
        pvrArtCache = {}
    
    # Get a list of all the recent Movies (unwatched and not in progress)
    json_result = getJSON('VideoLibrary.GetMovies', '{ "sort": { "order": "descending", "method": "dateadded" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"},{"operator":"false", "field":"inprogress", "value":""}]}, "properties": [ %s ], "limits":{"end":15} }' %fields_movies)
    for item in json_result:
        dateadded = item["dateadded"]
        if not item["title"] in allTitles:
            allItems.append((dateadded,item))
            allTitles.append(item["title"])
    
    # Get a list of all the recent MusicVideos (unwatched and not in progress)
    json_result = getJSON('VideoLibrary.GetMusicVideos', '{ "limits": { "start" : 0, "end": 15 },"sort": { "order": "descending", "method": "dateadded" }, "filter": {"operator":"is", "field":"playcount", "value":"0"}, "properties": [ %s ] }' %fields_musicvideos)
    for item in json_result:
        dateadded = item["dateadded"]
        if not item["title"] in allTitles and item["resume"]["position"] == 0:
            allItems.append((dateadded,item))
            allTitles.append(item["title"])
    
    # Get a list of all the recent music songs
    json_result = getJSON('AudioLibrary.GetSongs', '{ "limits": { "start" : 0, "end": 15 }, "sort": {"order": "descending", "method": "dateadded" }, "filter": {"operator":"is", "field":"playcount", "value":"0"}, "properties": [ %s ] }' %fields_songs)
    for item in json_result:
        dateadded = ""
        if not item["title"] in allTitles and item["thumbnail"]:
            allItems.append((dateadded,item))
            allTitles.append(item["title"])
    
    
    # Get a list of all the recent episodes (unwatched and not in progress)
    json_result = getJSON('VideoLibrary.GetEpisodes', '{ "sort": { "order": "descending", "method": "dateadded" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"},{"operator":"false", "field":"inprogress", "value":""}]}, "properties": [ %s ], "limits":{"end":15} }' %fields_episodes)
    for item in json_result:
        dateadded = item["dateadded"]
        if not item["title"] in allTitles:
            allItems.append((dateadded,item))
            allTitles.append(item["title"])
            
    
    # Get a list of all the unwatched tv recordings   
    json_result = getJSON('PVR.GetRecordings', '{"properties": [ %s ]}' %fields_pvrrecordings)
    for item in json_result:
        lastplayed = item["endtime"]
        if not item["title"] in allTitles and item["playcount"] == 0:
            pvrArtCache,thumb,fanart,poster,logo = getPVRThumbs(pvrArtCache, item["title"], item["channel"])
            art = { 'poster': poster, 'fanart' : fanart, 'thumb': thumb }
            item["art"] = art
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
    
    WINDOW.setProperty("SkinHelper.pvrArtCache",repr(pvrArtCache))
    
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

def getFavouriteMedia(limit):
    count = 0
    allItems = []
    allTitles = list()
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    
    #netflix favorites
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.netflixbmc) + Skin.HasSetting(SmartShortcuts.netflix)") and WINDOW.getProperty("netflixready") == "ready":
        json_result = getJSON('Files.GetDirectory', '{ "directory": "plugin://plugin.video.netflixbmc/?mode=listSliderVideos&thumb&type=both&widget=true&url=slider_38", "media": "files", "properties": [ %s ] }' %fields_files)
        for item in json_result:
            liz = createListItem(item)
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
    
    #emby favorites
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.emby) + Skin.HasSetting(SmartShortcuts.emby)"):
        json_result = getJSON('VideoLibrary.GetMovies', '{ "filter": {"operator":"contains", "field":"tag", "value":"Favorite movies"}, "properties": [ %s ] }' %fields_movies)
        for item in json_result:
            liz = createListItem(item)
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
        
        json_result = getJSON('VideoLibrary.GetTvShows', '{ "filter": {"operator":"contains", "field":"tag", "value":"Favorite tvshows"}, "properties": [ %s ] }' %fields_tvshows)
        for item in json_result:
            liz = createListItem(item)
            tvshowpath = "ActivateWindow(Videos,videodb://tvshows/titles/%s/,return)" %str(item["tvshowid"])
            tvshowpath="plugin://script.skin.helper.service?LAUNCHAPP&&&" + tvshowpath
            liz.setProperty('IsPlayable', 'false')
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=tvshowpath, listitem=liz)
    
    #Kodi favourites
    json_result = getJSON('Favourites.GetFavourites', '{"type": null, "properties": ["path", "thumbnail", "window", "windowparameter"]}')
    for fav in json_result:
        matchFound = False
        if "windowparameter" in fav:
            if fav["windowparameter"].startswith("videodb://tvshows/titles"):
                #it's a tv show
                try:
                    tvshowid = int(fav["windowparameter"].split("/")[-2])
                except: continue
                json_result = getJSON('VideoLibrary.GetTVShowDetails', '{ "tvshowid": %d, "properties": [ %s ]}' %(tvshowid, fields_tvshows))
                if json_result:
                    matchFound = True
                    liz = createListItem(json_result)
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
            pathpart = path.split(sep)[-1] #apparently only the filename can be used for the search
            #is this a movie?
            json_result = getJSON('VideoLibrary.GetMovies', '{ "filter": {"operator":"contains", "field":"filename", "value":"%s"}, "properties": [ %s ] }' %(pathpart,fields_movies))
            for item in json_result:
                if item['file'] == path:
                    matchFound = True
                    liz = createListItem(item)
                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
            
            if matchFound == False:
                #is this an episode ?
                json_result = getJSON('VideoLibrary.GetEpisodes', '{ "filter": {"operator":"contains", "field":"filename", "value":"%s"}, "properties": [ %s ] }' %(pathpart,fields_episodes))
                for item in json_result:
                    if item['file'] == path:
                        matchFound = True
                        liz = createListItem(item)
                        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
            if matchFound == False:
                #is this a song?
                json_result = getJSON('AudioLibrary.GetSongs', '{ "filter": {"operator":"contains", "field":"filename", "value":"%s"}, "properties": [ %s ] }' %(pathpart, fields_songs))
                for item in json_result:
                    if item['file'] == path:
                        matchFound = True
                        liz = createListItem(item)
                        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item['file'], listitem=liz)
                            
            if matchFound == False:
                #is this a musicvideo?
                json_result = getJSON('VideoLibrary.GetMusicVideos', '{ "filter": {"operator":"contains", "field":"filename", "value":"%s"}, "properties": [ %s ] }' %(pathpart, fields_musicvideos))
                for item in json_result:
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
    allCast = []
    castNames = list()
    moviesetmovies = None
    try:
        if movieset:
            cachedataStr = "movieset.castcache-" + str(movieset)
            itemId = int(movieset)
        if tvshow:
            cachedataStr = "tvshow.castcache-" + str(tvshow)
            itemId = int(tvshow)
        else:
            cachedataStr = "movie.castcache-" + str(movie)
            itemId = int(movie)
    except:
        pass
    
    cachedata = WINDOW.getProperty(cachedataStr)
    if cachedata:
        #get data from cache
        cachedata = eval(cachedata)
        for cast in cachedata:
            liz = xbmcgui.ListItem(label=cast[0],label2=cast[1],iconImage=cast[2])
            liz.setProperty('IsPlayable', 'false')
            castNames.append(cast[0])
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url="", listitem=liz, isFolder=True)
    else:
        #retrieve data from json api...
    
        if movie and itemId:
            json_result = getJSON('VideoLibrary.GetMovieDetails', '{ "movieid": %d, "properties": [ "title", "cast" ] }' %itemId)
            if json_result: item = json_result
        elif movie and not itemId:
            json_result = getJSON('VideoLibrary.GetMovies', '{ "filter": {"operator":"is", "field":"title", "value":"%s"}, "properties": [ "title", "cast" ] }' %movie)
            if json_result: item = json_result[0]
        elif tvshow and itemId:
            json_result = getJSON('VideoLibrary.GetTVShowDetails', '{ "tvshowid": %d, "properties": [ "title", "cast" ] }' %itemId)
            if json_result: item = json_result
        elif tvshow and not itemId:
            json_result = getJSON('VideoLibrary.GetTvShows', '{ "filter": {"operator":"is", "field":"title", "value":"%s"}, "properties": [ "title", "cast" ] }' %tvshow)
            if json_result: item = json_result[0]
        elif movieset and itemId:
            json_result = getJSON('VideoLibrary.GetMovieSetDetails', '{ "setid": %d, "properties": [ "title" ] }' %itemId)
            if json_result.has_key("movies"): moviesetmovies = json_result['movies']      
        elif movieset and not itemId:
            json_result = getJSON('VideoLibrary.GetMovieSets', '{ "filter": {"operator":"is", "field":"title", "value":"%s"}, "properties": [ "title" ] }' %tvshow)
            if json_result: 
                movieset = json_result[0]
                if movieset.has_key("movies"):
                    moviesetmovies = movieset['movies']
        
        
        #process cast for regular movie or show
        if item and item.has_key("cast"):
            for cast in item["cast"]:
                liz = xbmcgui.ListItem(label=cast["name"],label2=cast["role"],iconImage=cast["thumbnail"])
                liz.setProperty('IsPlayable', 'false')
                allCast.append([cast["name"],cast["role"],cast["thumbnail"]])
                castNames.append(cast["name"])
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url="", listitem=liz, isFolder=True)
        
        #process cast for all movies in a movieset
        elif moviesetmovies:
            moviesetCastList = []
            for setmovie in moviesetmovies:
                json_result = getJSON('VideoLibrary.GetMovieDetails', '{ "movieid": %d, "properties": [ "title", "cast" ] }' %setmovie["movieid"])
                if json_result:
                    for cast in json_result["cast"]:
                        if not cast["name"] in moviesetCastList:
                            liz = xbmcgui.ListItem(label=cast["name"],label2=cast["role"],iconImage=cast["thumbnail"])
                            liz.setProperty('IsPlayable', 'false')
                            allCast.append([cast["name"],cast["role"],cast["thumbnail"]])
                            castNames.append(cast["name"])
                            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url="", listitem=liz, isFolder=True)
                            moviesetCastList.append(cast["name"])
            
        WINDOW.setProperty(cachedataStr,repr(allCast))
    
    
    WINDOW.setProperty('SkinHelper.ListItemCast', "[CR]".join(castNames))
    
    xbmcplugin.endOfDirectory(int(sys.argv[1]))    