#!/usr/bin/python
# -*- coding: utf-8 -*-

from xml.dom.minidom import parse
from operator import itemgetter
from Utils import *
from ArtworkUtils import *

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
    addDirectoryItem(ADDON.getLocalizedString(32130), "plugin://script.skin.helper.service/?action=similarshows&limit=100")
    addDirectoryItem(ADDON.getLocalizedString(32086), "plugin://script.skin.helper.service/?action=inprogressmedia&limit=100")
    addDirectoryItem(ADDON.getLocalizedString(32007), "plugin://script.skin.helper.service/?action=inprogressandrecommendedmedia&limit=100")
    addDirectoryItem(xbmc.getLocalizedString(359), "plugin://script.skin.helper.service/?action=recentalbums&limit=100")
    addDirectoryItem(ADDON.getLocalizedString(32087), "plugin://script.skin.helper.service/?action=recentsongs&limit=100")
    addDirectoryItem(xbmc.getLocalizedString(517), "plugin://script.skin.helper.service/?action=recentplayedalbums&limit=100")
    addDirectoryItem(ADDON.getLocalizedString(32088), "plugin://script.skin.helper.service/?action=recentplayedsongs&limit=100")
    addDirectoryItem(ADDON.getLocalizedString(32131), "plugin://script.skin.helper.service/?action=recommendedalbums&limit=100")
    addDirectoryItem(ADDON.getLocalizedString(32132), "plugin://script.skin.helper.service/?action=recommendedsongs&limit=100")
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
            if "plex" in entry:
                widget = entry + ".ondeck"
                widget2 = entry + ".recent"
            elif type == "movies" or type == "movie" or type == "artist" or "netflix" in entry:
                widget = entry + ".recent"
                widget2 = entry + ".inprogress"
            elif type == "tvshows" and "emby" in entry:
                widget = entry + ".nextepisodes"
                widget2 = entry + ".recent"
            else:
                widget = entry
        if xbmc.getInfoLabel("$INFO[Window(Home).Property(%s.path)]" %key):
            addSmartShortcutDirectoryItem(key,False, widget,widget2)

def getSmartShortcuts(sublevel=None):
    if xbmc.getCondVisibility("Window.IsActive(script-skinshortcuts.xml)"):
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
        
def getWidgets(itemstoInclude = None):
    xbmcplugin.setContent(int(sys.argv[1]), 'files')
    if itemstoInclude:
        itemstoInclude = itemstoInclude.split(",")
    else:
        itemstoInclude = ["skinplaylists", "librarydataprovider", "scriptwidgets", "extendedinfo", "smartshortcuts","pvr", "smartishwidgets", "favourites" ]
    
    allWidgets = buildWidgetsListing()
    if allWidgets: 
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
                    elif type == "pvr":
                        mediaLibrary = "TvChannels"
                        target = "pvr"
                    else:
                        mediaLibrary = "VideoLibrary"
                        target = "video"
                    widgetpath = "ActivateWindow(%s,%s,return)" %(mediaLibrary, widget[1].split("&")[0])
                    li = xbmcgui.ListItem(widget[0], path=widgetpath)
                    thumb = widget[2]
                    if not thumb: thumb = "DefaultAddonContextItem.png"
                    props = {}
                    props["list"] = widget[1]
                    props["type"] = widget[3]
                    props["background"] = thumb
                    props["backgroundName"] = widget[0]
                    props["widgetPath"] = widget[1]
                    props["widgetTarget"] = target
                    props["widgetName"] = widget[0]
                    props["widget"] = widgetType
                    li.setInfo( type="Video", infoLabels={ "Title": "smartshortcut" })
                    li.setThumbnailImage(thumb)
                        
                    li.setInfo( type="Video", infoLabels={ "mpaa": repr(props) })
                    
                    li.setArt({"fanart":thumb})   
                    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=widgetpath, listitem=li, isFolder=False)
    
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
def getBackgrounds():
    xbmcplugin.setContent(int(sys.argv[1]), 'files')
    
    globalBackgrounds = []
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
    globalBackgrounds.append((ADDON.getLocalizedString(32142), "SkinHelper.RecentMusicBackground"))
    globalBackgrounds.append((ADDON.getLocalizedString(32113), "SkinHelper.PvrBackground"))
    
    globalBackgrounds.append((ADDON.getLocalizedString(32038), "SkinHelper.GlobalFanartBackground"))
    globalBackgrounds.append((ADDON.getLocalizedString(32138), "SkinHelper.AllVideosBackground"))
    globalBackgrounds.append((ADDON.getLocalizedString(32139), "SkinHelper.RecentVideosBackground"))
    globalBackgrounds.append((ADDON.getLocalizedString(32140), "SkinHelper.InProgressVideosBackground"))
    
    #wall backgrounds
    globalBackgrounds.append((ADDON.getLocalizedString(32117), "SkinHelper.AllMoviesBackground.Wall"))
    globalBackgrounds.append((ADDON.getLocalizedString(32118), "SkinHelper.AllMusicBackground.Wall"))
    globalBackgrounds.append((ADDON.getLocalizedString(32119), "SkinHelper.AllMusicSongsBackground.Wall"))
    globalBackgrounds.append((ADDON.getLocalizedString(32127), "SkinHelper.AllTvShowsBackground.Wall"))
    
    if xbmc.getCondVisibility("System.HasAddon(script.extendedinfo)"):
        globalBackgrounds.append((xbmc.getInfoLabel("$ADDON[script.extendedinfo 32046]") + " (TheMovieDB)", "SkinHelper.TopRatedMovies"))
        globalBackgrounds.append((xbmc.getInfoLabel("$ADDON[script.extendedinfo 32040]") + " (TheMovieDB)", "SkinHelper.TopRatedShows"))
    
    for node in globalBackgrounds:
        label = node[0]
        image = "$INFO[Window(Home).Property(%s)]" %node[1]
        if xbmc.getInfoLabel(image):
            li = xbmcgui.ListItem(label, path=image )
            li.setArt({"fanart":image})
            li.setThumbnailImage(image)
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=image, listitem=li, isFolder=False)
    
    allSmartShortcuts = WINDOW.getProperty("allSmartShortcuts")
    if allSmartShortcuts:
        for node in eval (allSmartShortcuts):
            label = "$INFO[Window(Home).Property(%s.title)]" %node
            image = "$INFO[Window(Home).Property(%s.image)]" %node
            if xbmc.getInfoLabel(image):
                li = xbmcgui.ListItem(label, path=image )
                li.setArt({"fanart":image})
                li.setThumbnailImage(image)
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=image, listitem=li, isFolder=False)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
def FAVOURITES(limit):
    allItems = []
    xbmcplugin.setContent(int(sys.argv[1]), 'files')
    fav_file = xbmc.translatePath( 'special://profile/favourites.xml' ).decode("utf-8")
    if xbmcvfs.exists( fav_file ):
        doc = parse( fav_file )
        listing = doc.documentElement.getElementsByTagName( 'favourite' )
        for count, favourite in enumerate(listing):
            label = ""
            image = "DefaultFile.png"
            for (name, value) in favourite.attributes.items():
                if name == "name":
                    label = value
                if name == "thumb":
                    image = value
            path = favourite.childNodes [ 0 ].nodeValue
            path="plugin://script.skin.helper.service/?action=launch&path=" + path
            li = {"title": label, "thumbnail":image, "file":path}
            li["extraproperties"] = {"IsPlayable": "false"}
            allItems.append(li)
            if count == limit:
                break
    return allItems

def PVRRECORDINGS(limit):
    allItems = []
    allUnSortedItems = []
    if xbmc.getCondVisibility("PVR.HasTVChannels"):
        # Get a list of all the unwatched tv recordings   
        json_result = getJSON('PVR.GetRecordings', '{"properties": [ %s ]}' %fields_pvrrecordings)
        pvr_backend = xbmc.getInfoLabel("Pvr.BackendName").decode("utf-8")
        for item in json_result:
            #exclude live tv items from recordings list (mythtv hack)
            if item["playcount"] == 0 and not ("mythtv" in pvr_backend.lower() and "/livetv/" in item.get("file","").lower()):
                channelname = item["channel"]
                item["channel"] = channelname
                item["art"] = getPVRThumbs(item["title"], channelname, "recordings")
                if item.get("art") and item["art"].get("thumb"):
                    item["art"]["thumb"] = item["art"].get("thumb")
                item["channellogo"] = item["art"].get("channellogo","")
                item["cast"] = None
                allUnSortedItems.append((item["endtime"],item))
                
        #sort the list so we return a recently added list or recordings
        allUnSortedItems = sorted(allUnSortedItems,key=itemgetter(0),reverse=True)
        for item in allUnSortedItems:
            allItems.append(item[1])
    return allItems

def PVRCHANNELS(limit):
    count = 0
    allItems = []
    # Perform a JSON query to get all channels
    json_query = getJSON('PVR.GetChannels', '{"channelgroupid": "alltv", "properties": [ "thumbnail", "channeltype", "hidden", "locked", "channel", "lastplayed", "broadcastnow" ], "limits": {"end": %d}}' %( limit ) )
    for channel in json_query:
        channelname = channel["label"]
        channelid = channel["channelid"]
        channelicon = channel['thumbnail']
        if channel.has_key('broadcastnow'):
            #channel with epg data
            item = channel['broadcastnow']
            item["art"] = getPVRThumbs(item["title"], channelname, "channels")
            if not channelicon: channelicon = item["art"].get("channelicon")
        else:
            #channel without epg
            item = channel
            item["title"] = item["label"]
            channelname = channel["label"]
            channelid = channel["channelid"]
            channelicon = channel['thumbnail']
            if not channelicon: channelicon = searchChannelLogo(channelname)
        item["file"] = sys.argv[0] + "?action=launchpvr&path=" + str(channelid)
        item["channelicon"] = channelicon
        item["icon"] = channelicon
        item["channel"] = channelname
        item["cast"] = None
        allItems.append(item)
    return allItems

def PVRCHANNELGROUPS(limit):
    count = 0
    #Code is not yet working... not possible to navigate to a specific channel group in pvr windows
    xbmcplugin.setContent(int(sys.argv[1]), 'files')
    # Perform a JSON query to get all channels
    json_query = getJSON('PVR.GetChannelGroups', '{"channeltype": "tv"}' )
    for item in json_query:
        item["file"] = "pvr://channels/tv/%s/" %(item["label"])
        item["title"] = item["label"]
        liz = createListItem(item)
        liz.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), item['file'], liz, True)
        count += 1
        if count == limit:
            break
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1])) 
       
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

def RECENTALBUMS(limit,browse=""):
    allItems = []
    json_result = getJSON('AudioLibrary.GetRecentlyAddedAlbums', '{ "sort": { "order": "descending", "method": "dateadded" }, "properties": [ %s ], "limits":{"end":%d} }' %(fields_albums,limit))
    for item in json_result:
        item["art"] = getMusicArtworkByDbId(item["albumid"], "albums")
        item["type"] = "album"
        item["extraproperties"] = {"extrafanart": item["art"].get("extrafanart",""), "tracklist":item["art"].get("tracklist","")}
        item['album_description'] = item["art"].get("info","")
        if browse == "true":
            item["file"] = "musicdb://albums/%s/" %str(item["albumid"])
        else:
            item['file'] = "plugin://script.skin.helper.service/?action=playalbum&path=%s" %item['albumid']
        allItems.append(item)

    return allItems

def RECENTPLAYEDALBUMS(limit,browse=""):
    allItems = []
    json_result = getJSON('AudioLibrary.GetRecentlyPlayedAlbums', '{ "sort": { "order": "descending", "method": "lastplayed" }, "properties": [ %s ], "limits":{"end":%d} }' %(fields_albums,limit))
    for item in json_result:
        item["art"] = getMusicArtworkByDbId(item["albumid"], "albums")
        item["type"] = "album"
        item["extraproperties"] = {"extrafanart": item["art"].get("extrafanart",""), "tracklist":item["art"].get("tracklist","")}
        item['album_description'] = item["art"].get("info","")
        if browse == "true":
            item["file"] = "musicdb://albums/%s/" %str(item["albumid"])
        else:
            item['file'] = "plugin://script.skin.helper.service/?action=playalbum&path=%s" %item['albumid']
        allItems.append(item)

    return allItems

def RECENTPLAYEDSONGS(limit):
    allItems = []
    json_result = getJSON('AudioLibrary.GetRecentlyPlayedSongs', '{ "sort": { "order": "descending", "method": "lastplayed" }, "properties": [ %s ], "limits":{"end":%d} }' %(fields_songs,limit))
    for item in json_result:
        item["art"] = getMusicArtworkByDbId(item["songid"], "songs")
        item["type"] = "song"
        item["extraproperties"] = {"extrafanart": item["art"].get("extrafanart",""), "tracklist":item["art"].get("tracklist","")}
        item['album_description'] = item["art"].get("info","")
        allItems.append(item)
    return allItems    

def RECENTSONGS(limit):
    allItems = []
    json_result = getJSON('AudioLibrary.GetRecentlyAddedSongs', '{ "sort": { "order": "descending", "method": "dateadded" }, "properties": [ %s ], "limits":{"end":%d} }' %(fields_songs,limit))
    for item in json_result:
        item["art"] = getMusicArtworkByDbId(item["songid"], "songs")
        item["type"] = "song"
        item["extraproperties"] = {"extrafanart": item["art"].get("extrafanart",""), "tracklist":item["art"].get("tracklist","")}
        item['album_description'] = item["art"].get("info","")
        allItems.append(item)
    return allItems    

def getPluginListing(action,limit,refresh=None,optionalParam=None):
    count = 0
    allItems = []
    
    #get params for each action
    if "EPISODES" in action: type = "episodes"
    elif "MOVIE" in action: type = "movies"
    elif "SHOW" in action: type = "tvshows"
    elif "MEDIA" in action: type = "movies"
    elif "PVR" in action: type = "episodes"
    elif "ALBUM" in action: type = "albums"
    elif "SONG" in action: type = "songs"
    else: type = "files"
    #set widget content type
    xbmcplugin.setContent(int(sys.argv[1]), type)
    
    #try to get from cache first...
    cacheStr=""
    if refresh: 
        cacheStr = "skinhelper-%s-%s-%s-%s" %(action,limit,optionalParam,refresh)
        cache = WINDOW.getProperty(cacheStr).decode("utf-8")
        if cache: allItems = eval(cache)
    
    #get the content from json when no cache
    if not allItems:
        if optionalParam:
            allItems = eval(action)(limit,optionalParam)
        else:
            allItems = eval(action)(limit)
    
    #fill that listing...
    for item in allItems:
        liz = createListItem(item)
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), item['file'], liz, False)
        count += 1
        if count == limit:
            break
    
    #end directory listing
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
    
    #save the cache
    WINDOW.setProperty(cacheStr, repr(allItems).encode("utf-8"))
    
def NEXTEPISODES(limit):
    allItems = []
    count = 0
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
                    
    return allItems

def NEXTAIREDTVSHOWS(limit):
    count = 0
    allItems = []
    #get data from next aired script
    nextairedTotal = WINDOW.getProperty("NextAired.Total")
    if nextairedTotal:
        nextairedTotal = int(nextairedTotal)
        for count in range(nextairedTotal):
            tvshow = WINDOW.getProperty("NextAired.%s.Label"%str(count)).decode("utf-8")
            if tvshow:
                json_result = getJSON('VideoLibrary.GetTvShows','{ "filter": {"operator":"is", "field":"title", "value":"%s"}, "properties": [ %s ] }' %(tvshow,fields_tvshows))
                if len(json_result) > 0:
                    item = json_result[0]
                    path = "videodb://tvshows/titles/%s/" %str(item["tvshowid"])
                    extraprops = {}
                    extraprops["airtime"] = WINDOW.getProperty("NextAired.%s.AirTime"%str(count)).decode("utf-8")
                    extraprops["Path"] = WINDOW.getProperty("NextAired.%s.Path"%str(count)).decode("utf-8")
                    extraprops["Library"] = WINDOW.getProperty("NextAired.%s.Library"%str(count)).decode("utf-8")
                    extraprops["Status"] = WINDOW.getProperty("NextAired.%s.Status"%str(count)).decode("utf-8")
                    extraprops["StatusID"] = WINDOW.getProperty("NextAired.%s.StatusID"%str(count)).decode("utf-8")
                    extraprops["Network"] = WINDOW.getProperty("NextAired.%s.Network"%str(count)).decode("utf-8")
                    extraprops["Started"] = WINDOW.getProperty("NextAired.%s.Started"%str(count)).decode("utf-8")
                    extraprops["Genre"] = WINDOW.getProperty("NextAired.%s.Genre"%str(count)).decode("utf-8")
                    extraprops["Premiered"] = WINDOW.getProperty("NextAired.%s.Premiered"%str(count)).decode("utf-8")
                    extraprops["Country"] = WINDOW.getProperty("NextAired.%s.Country"%str(count)).decode("utf-8")
                    extraprops["Runtime"] = WINDOW.getProperty("NextAired.%s.Runtime"%str(count)).decode("utf-8")
                    extraprops["Fanart"] = WINDOW.getProperty("NextAired.%s.Fanart"%str(count)).decode("utf-8")
                    extraprops["Today"] = WINDOW.getProperty("NextAired.%s.Today"%str(count)).decode("utf-8")
                    extraprops["NextDate"] = WINDOW.getProperty("NextAired.%s.NextDate"%str(count)).decode("utf-8")
                    extraprops["NextDay"] = WINDOW.getProperty("NextAired.%s.NextDay"%str(count)).decode("utf-8")
                    extraprops["NextTitle"] = WINDOW.getProperty("NextAired.%s.NextTitle"%str(count)).decode("utf-8")
                    extraprops["NextNumber"] = WINDOW.getProperty("NextAired.%s.NextNumber"%str(count)).decode("utf-8")
                    extraprops["NextEpisodeNumber"] = WINDOW.getProperty("NextAired.%s.NextEpisodeNumber"%str(count)).decode("utf-8")
                    extraprops["NextSeasonNumber"] = WINDOW.getProperty("NextAired.%s.NextSeasonNumber"%str(count)).decode("utf-8")
                    extraprops["LatestDate"] = WINDOW.getProperty("NextAired.%s.LatestDate"%str(count)).decode("utf-8")
                    extraprops["LatestDay"] = WINDOW.getProperty("NextAired.%s.LatestDay"%str(count)).decode("utf-8")
                    extraprops["LatestTitle"] = WINDOW.getProperty("NextAired.%s.LatestTitle"%str(count)).decode("utf-8")
                    extraprops["LatestNumber"] = WINDOW.getProperty("NextAired.%s.LatestNumber"%str(count)).decode("utf-8")
                    extraprops["LatestEpisodeNumber"] = WINDOW.getProperty("NextAired.%s.LatestEpisodeNumber"%str(count)).decode("utf-8")
                    extraprops["LatestSeasonNumber"] = WINDOW.getProperty("NextAired.%s.LatestSeasonNumber"%str(count)).decode("utf-8")
                    extraprops["AirDay"] = WINDOW.getProperty("NextAired.%s.AirDay"%str(count)).decode("utf-8")
                    extraprops["ShortTime"] = WINDOW.getProperty("NextAired.%s.ShortTime"%str(count)).decode("utf-8")
                    extraprops["SecondWeek"] = WINDOW.getProperty("NextAired.%s.SecondWeek"%str(count)).decode("utf-8")
                    extraprops["Art(poster)"] = WINDOW.getProperty("NextAired.%s.Art(poster)"%str(count)).decode("utf-8")
                    extraprops["Art(fanart)"] = WINDOW.getProperty("NextAired.%s.Art(fanart)"%str(count)).decode("utf-8")
                    extraprops["Art(landscape)"] = WINDOW.getProperty("NextAired.%s.Art(landscape)"%str(count)).decode("utf-8")
                    extraprops["Art(clearlogo)"] = WINDOW.getProperty("NextAired.%s.Art(clearlogo)"%str(count)).decode("utf-8")
                    extraprops["Art(clearart)"] = WINDOW.getProperty("NextAired.%s.Art(clearart)"%str(count)).decode("utf-8")
                    extraprops["Art(characterart)"] = WINDOW.getProperty("NextAired.%s.Art(characterart)"%str(count)).decode("utf-8")
                    item["extraproperties"] = extraprops
                    item["file"] = path
                    allItems.append(item)
                    count += 1
                    if count == limit:
                        break
    return allItems

def RECOMMENDEDMOVIES(limit):
    count = 0
    allItems = []
    # First we get a list of all the in-progress Movies
    numitems = 0
    json_result = getJSON('VideoLibrary.GetMovies','{ "sort": { "order": "descending", "method": "lastplayed" }, "filter": {"and": [{"operator":"true", "field":"inprogress", "value":""}]}, "properties": [ %s ] }' %fields_movies)
    for item in json_result:
        if numitems >= limit:
            break
        allItems.append(item)
        numitems +=1
    # Fill the list with random items with a score higher then 7
    json_result = getJSON('VideoLibrary.GetMovies','{ "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"playcount", "value":"0"},{"operator":"greaterthan", "field":"rating", "value":"7"}]}, "properties": [ %s ] }' %fields_movies)
    # If we found any, find the oldest unwatched show for each one.
    for item in json_result:
        if numitems >= limit:
            break
        allItems.append(item)
        numitems +=1
    return allItems

def RECOMMENDEDALBUMS(limit,browse=False):
    count = 0
    allItems = []
    allTitles = list()
    #query last played albums and find albums of same genre and sort by rating
    json_result = getJSON('AudioLibrary.GetRecentlyPlayedAlbums', '{ "sort": { "order": "descending", "method": "lastplayed" }, "properties": [ %s ], "limits":{"end":%d} }' %(fields_albums,limit))
    if not json_result:
        #if no recent played albums just grab a list of random albums...
        json_result = getJSON('AudioLibrary.GetAlbums', '{ "sort": { "order": "descending", "method": "random" }, "properties": [ %s ], "limits":{"end":%d} }' %(fields_albums,limit))

    for item in json_result:
        genres = item["genre"]
        similartitle = item["title"]
        if count == limit: break
        #get all movies from the same genre
        for genre in genres:
            if count == limit: break
            json_result = getJSON('AudioLibrary.GetAlbums', '{ "sort": { "order": "descending", "method": "rating" }, "filter": {"operator":"is", "field":"genre", "value":"%s"}, "properties": [ %s ] }' %(genre,fields_albums))
            for item in json_result:
                if count == limit: break
                if not item["title"] in allTitles and not item["title"] == similartitle and genre in item["genre"]:
                    item["art"] = getMusicArtworkByDbId(item["albumid"], "albums")
                    item["type"] = "album"
                    item["extraproperties"] = {"extrafanart": item["art"].get("extrafanart",""), "tracklist":item["art"].get("tracklist","")}
                    item['album_description'] = item["art"].get("info","")
                    if browse == "true":
                        item["file"] = "musicdb://albums/%s/" %str(item["albumid"])
                    else:
                        item['file'] = "plugin://script.skin.helper.service/?action=playalbum&path=%s" %item['albumid']
                    allItems.append((item["rating"],item))
                    allTitles.append(item["title"])
                    count += 1

        #sort the list by rating 
        allItems = sorted(allItems,key=itemgetter(0),reverse=True)
        if allItems: WINDOW.setProperty("skinhelper-recommendedalbums", repr(allItems))

    #only return the listitems, we dont care about the sortkey
    allItemsDef = []
    for item in allItems:
        allItemsDef.append(item[1])
    return allItemsDef

def RECOMMENDEDSONGS(limit):
    count = 0
    allItems = []
    allTitles = list()
    #query last played songs and find songs of same genre and sort by rating
    json_result = getJSON('AudioLibrary.GetRecentlyPlayedSongs', '{ "sort": { "order": "descending", "method": "lastplayed" }, "properties": [ %s ], "limits":{"end":%d} }' %(fields_songs,limit))
    if not json_result:
        json_result = getJSON('AudioLibrary.GetSongs', '{ "sort": { "order": "descending", "method": "random" }, "properties": [ %s ], "limits":{"end":%d} }' %(fields_songs,limit))
    for item in json_result:
        genres = item["genre"]
        similartitle = item["title"]
        if count == limit: break
        #get all movies from the same genre
        for genre in genres:
            if count == limit: break
            json_result = getJSON('AudioLibrary.GetSongs', '{ "sort": { "order": "descending", "method": "rating" }, "filter": {"operator":"is", "field":"genre", "value":"%s"}, "properties": [ %s ],"limits":{"end":%d} }' %(genre,fields_songs,limit))
            for item in json_result:
                if count == limit: break
                if not item["title"] in allTitles and not item["title"] == similartitle:
                    item["art"] = getMusicArtworkByDbId(item["songid"], "songs")
                    item["type"] = "song"
                    item["extraproperties"] = {"extrafanart": item["art"].get("extrafanart",""), "tracklist":item["art"].get("tracklist","")}
                    item['album_description'] = item["art"].get("info","")
                    allItems.append((item["rating"],item))
                    allTitles.append(item["title"])
                    count += 1
                    

        #sort the list by rating 
        allItems = sorted(allItems,key=itemgetter(0),reverse=True)

    #only return the listitems, we dont care about the sortkey
    allItemsDef = []
    for item in allItems:
        allItemsDef.append(item[1])
    return allItemsDef
    
def SIMILARMOVIES(limit,imdbid=""):
    count = 0
    allItems = []
    allTitles = list()
    #lookup movie by imdbid or just pick a random watched movie
    if imdbid:
        match = []
        json_result = getJSON('VideoLibrary.GetMovies', '{ "properties": [ "title", "rating", "genre", "imdbnumber"]}')
        for item in json_result:
            if item.get("imdbnumber") == imdbid:
                match = [item]
                break
        json_result = match
    else: json_result = getJSON('VideoLibrary.GetMovies', '{ "sort": { "order": "descending", "method": "random" }, "filter": {"operator":"isnot", "field":"playcount", "value":"0"}, "properties": [ "title", "rating", "genre"],"limits":{"end":1}}')
    for item in json_result:
        if count == limit: break
        genres = item["genre"]
        similartitle = item["title"]
        #get all movies from the same genre
        for genre in genres:
            if count == limit: break
            json_result = getJSON('VideoLibrary.GetMovies', '{ "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"genre", "value":"%s"}, {"operator":"is", "field":"playcount", "value":"0"}]}, "properties": [ %s ],"limits":{"end":%d} }' %(genre,fields_movies,limit))
            for item in json_result:
                if count == limit: break
                if not item["title"] in allTitles and not item["title"] == similartitle:
                    item["extraproperties"] = {"similartitle": similartitle}
                    allItems.append((item["rating"],item))
                    allTitles.append(item["title"])
                    count +=1
    
    #sort the list by rating 
    allItems = sorted(allItems,key=itemgetter(0),reverse=True)
        
    #only return the listitems, we dont care about the sortkey
    allItemsDef = []
    for item in allItems:
        allItemsDef.append(item[1])
    return allItemsDef

def MOVIESFORGENRE(limit,genretitle=""):
    count = 0
    allItems = []

    if not genretitle:
        #get a random genre
        json_result = getJSON('VideoLibrary.GetGenres', '{ "sort": { "order": "descending", "method": "random" }, "type": "movie","limits":{"end":1}}')
        if json_result: genretitle = json_result[0].get("label")

    if genretitle:
        #get all movies from the same genre
        allTitles = list()
        json_result = getJSON('VideoLibrary.GetMovies', '{ "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"genre", "value":"%s"}, {"operator":"is", "field":"playcount", "value":"0"}]}, "properties": [ %s ],"limits":{"end":%d} }' %(genretitle,fields_movies,limit))
        for item in json_result:
            if not item["title"] in allTitles:
                item["extraproperties"] = {"genretitle": similartitle}
                allItems.append((item["rating"],item))
                allTitles.append(item["title"])

        #sort the list by rating
        allItems = sorted(allItems,key=itemgetter(0),reverse=True)

    #only return the listitems, we dont care about the sortkey
    allItemsDef = []
    for item in allItems:
        allItemsDef.append(item[1])
    return allItemsDef

def SIMILARSHOWS(limit,imdbid=""):
    count = 0
    allItems = []
    allTitles = list()
    #lookup show by imdbid or just pick a random in progress show
    if imdbid: 
        match = []
        json_result = getJSON('VideoLibrary.GetTVShows', '{ "properties": [ "title", "rating", "genre", "imdbnumber"]}')
        for item in json_result:
            if item.get("imdbnumber") == imdbid:
                match = [item]
                break
        json_result = match
    else: json_result = getJSON('VideoLibrary.GetTVShows', '{ "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"true", "field":"inprogress", "value":""}]}, "properties": [ "title", "rating", "genre"],"limits":{"end":1}}')
    for item in json_result:
        genres = item["genre"]
        similartitle = item["title"]
        #get all movies from the same genre
        for genre in genres:
            json_result = getJSON('VideoLibrary.GetTVShows', '{ "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"genre", "value":"%s"}, {"operator":"is", "field":"playcount", "value":"0"}]}, "properties": [ %s ],"limits":{"end":%d} }' %(genre,fields_tvshows,limit))
            for item in json_result:
                if not item["title"] in allTitles and not item["title"] == similartitle:
                    item["extraproperties"] = {"similartitle": similartitle}
                    tvshowpath = "ActivateWindow(Videos,videodb://tvshows/titles/%s/,return)" %str(item["tvshowid"])
                    item["file"]="plugin://script.skin.helper.service?action=LAUNCH&path=" + tvshowpath
                    allItems.append((item["rating"],item))
                    allTitles.append(item["title"])
        
        #sort the list by rating 
        allItems = sorted(allItems,key=itemgetter(0),reverse=True)
        
    #only return the listitems, we dont care about the sortkey
    allItemsDef = []
    for item in allItems:
        allItemsDef.append(item[1])
    return allItemsDef

def SHOWSFORGENRE(limit,genretitle=""):
    count = 0
    allItems = []
    
    if not genretitle:
        #get a random genre
        json_result = getJSON('VideoLibrary.GetGenres', '{ "sort": { "order": "descending", "method": "random" }, "type": "tvshow","limits":{"end":1}}')
        if json_result: genretitle = json_result[0].get("label")

    #get all shows from the same genre
    if genretitle:
        allTitles = list()
        json_result = getJSON('VideoLibrary.GetTVShows', '{ "sort": { "order": "descending", "method": "random" }, "filter": {"and": [{"operator":"is", "field":"genre", "value":"%s"}, {"operator":"is", "field":"playcount", "value":"0"}]}, "properties": [ %s ],"limits":{"end":%d} }' %(genretitle,fields_tvshows,limit))
        for item in json_result:
            if not item["title"] in allTitles:
                item["extraproperties"] = {"genretitle": similartitle}
                tvshowpath = "ActivateWindow(Videos,videodb://tvshows/titles/%s/,return)" %str(item["tvshowid"])
                item["file"]="plugin://script.skin.helper.service?action=LAUNCH&path=" + tvshowpath
                allItems.append((item["rating"],item))
                allTitles.append(item["title"])

        #sort the list by rating
        allItems = sorted(allItems,key=itemgetter(0),reverse=True)

    #only return the listitems, we dont care about the sortkey
    allItemsDef = []
    for item in allItems:
        allItemsDef.append(item[1])
    return allItemsDef
  
def buildRecommendedMediaListing(limit,ondeckContent=False,recommendedContent=True):
    count = 0
    allTitles = list()
    allItems = []
    
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
        json_result = PVRRECORDINGS(limit)
        for item in json_result:
            lastplayed = None
            if not item["title"] in allTitles:
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
                    item["tvshowtitle"] = item["title"]
                    allRecommendedItems.append((rating,item))
                    allTitles.append(item["title"])
                    
        #sort the list with recommended items by rating 
        allItems += sorted(allRecommendedItems,key=itemgetter(0),reverse=True)
        
    #only return the listitems, we dont care about the sortkey
    allItemsDef = []
    for item in allItems:
        allItemsDef.append(item[1])
    return allItemsDef

def INPROGRESSANDRECOMMENDEDMEDIA(limit):
    return buildRecommendedMediaListing(limit,ondeckContent=True,recommendedContent=True)

def INPROGRESSMEDIA(limit):
    return buildRecommendedMediaListing(limit,ondeckContent=True,recommendedContent=False)

def RECOMMENDEDMEDIA(limit):
    return buildRecommendedMediaListing(limit,ondeckContent=False,recommendedContent=True)

def RECENTMEDIA(limit):
    count = 0
    allItems = []
    allTitles = []
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
            
    # Get a list of all the unwatched recent tv recordings   
    json_result = PVRRECORDINGS(limit)
    for item in json_result:
        lastplayed = item["endtime"]
        if not item["title"] in allTitles:
            allItems.append((lastplayed,item))
            allTitles.append(item["title"])
    
    #sort the list with in recent items by lastplayed date   
    allItems = sorted(allItems,key=itemgetter(0),reverse=True)
    if allItems: WINDOW.setProperty("skinhelper-recentmedia", repr(allItems))
    
    #only return the listitems, we dont care about the sortkey
    allItemsDef = []
    for item in allItems:
        allItemsDef.append(item[1])
    return allItemsDef

def FAVOURITEMEDIA(limit):
    count = 0
    allItems = []
    #netflix favorites
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.netflixbmc) + Skin.HasSetting(SmartShortcuts.netflix)") and WINDOW.getProperty("netflixready") == "ready":
        json_result = getJSON('Files.GetDirectory', '{ "directory": "plugin://plugin.video.netflixbmc/?mode=listSliderVideos&thumb&type=both&widget=true&url=slider_38", "media": "files", "properties": [ %s ] }' %fields_files)
        for item in json_result:
            allItems.append(item)
    
    #emby favorites
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.emby) + Skin.HasSetting(SmartShortcuts.emby)"):
        json_result = getJSON('VideoLibrary.GetMovies', '{ "filter": {"operator":"contains", "field":"tag", "value":"Favorite movies"}, "properties": [ %s ] }' %fields_movies)
        for item in json_result:
            allItems.append(item)
        
        json_result = getJSON('VideoLibrary.GetTvShows', '{ "filter": {"operator":"contains", "field":"tag", "value":"Favorite tvshows"}, "properties": [ %s ] }' %fields_tvshows)
        for item in json_result:
            tvshowpath = "ActivateWindow(Videos,videodb://tvshows/titles/%s/,return)" %str(item["tvshowid"])
            tvshowpath="plugin://script.skin.helper.service?action=launch&path=" + tvshowpath
            item["file"] == tvshowpath
            allItems.append(item)
    
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
                    tvshowpath = "ActivateWindow(Videos,%s,return)" %fav["windowparameter"]
                    tvshowpath="plugin://script.skin.helper.service?action=launch&path=" + tvshowpath
                    json_result["file"] == tvshowpath
                    allItems.append(json_result)            
        if fav["type"] == "media":
            path = fav["path"]
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
                    allItems.append(item)
            
            if matchFound == False:
                #is this an episode ?
                json_result = getJSON('VideoLibrary.GetEpisodes', '{ "filter": {"operator":"contains", "field":"filename", "value":"%s"}, "properties": [ %s ] }' %(pathpart,fields_episodes))
                for item in json_result:
                    if item['file'] == path:
                        matchFound = True
                        allItems.append(item)
            if matchFound == False:
                #is this a song?
                json_result = getJSON('AudioLibrary.GetSongs', '{ "filter": {"operator":"contains", "field":"filename", "value":"%s"}, "properties": [ %s ] }' %(pathpart, fields_songs))
                for item in json_result:
                    if item['file'] == path:
                        matchFound = True
                        allItems.append(item)
                            
            if matchFound == False:
                #is this a musicvideo?
                json_result = getJSON('VideoLibrary.GetMusicVideos', '{ "filter": {"operator":"contains", "field":"filename", "value":"%s"}, "properties": [ %s ] }' %(pathpart, fields_musicvideos))
                for item in json_result:
                    if item['file'] == path:
                        matchFound = True
                        allItems.append(item)
                    
    return allItems
    
def getExtraFanArt(path):
    #get extrafanarts by passing an artwork cache xml file
    artwork = getArtworkFromCacheFile(path)
    if artwork.get("extrafanarts"):
        extrafanart = eval( artwork.get("extrafanarts") )
        for item in extrafanart:
            li = xbmcgui.ListItem(item, path=item)
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item, listitem=li)
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
    
def getCast(movie=None,tvshow=None,movieset=None,downloadThumbs=False):
    
    itemId = None
    item = {}
    allCast = []
    castNames = list()
    moviesetmovies = None
    cachedataStr = ""
    try:
        if movieset:
            cachedataStr = "movieset.castcache-" + str(movieset)+str(downloadThumbs)
            itemId = int(movieset)
        elif tvshow:
            cachedataStr = "tvshow.castcache-" + str(tvshow)+str(downloadThumbs)
            itemId = int(tvshow)
        elif movie:
            cachedataStr = "movie.castcache-" + str(movie)+str(downloadThumbs)
            itemId = int(movie)
        else:
            cachedataStr = xbmc.getInfoLabel("ListItem.Title")+xbmc.getInfoLabel("ListItem.FileNameAndPath")+str(downloadThumbs)
    except: pass
    
    cachedata = WINDOW.getProperty(cachedataStr)
    if cachedata:
        #get data from cache
        cachedata = eval(cachedata)
        for cast in cachedata:
            liz = xbmcgui.ListItem(label=cast[0],label2=cast[1],iconImage=cast[2])
            liz.setProperty('IsPlayable', 'false')
            url = "RunScript(script.extendedinfo,info=extendedactorinfo,name=%s)"%cast[0]
            path="plugin://script.skin.helper.service/?action=launch&path=" + url
            castNames.append(cast[0])
            liz.setThumbnailImage(cast[2])
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=liz, isFolder=False)
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
        else:
            #no item provided, try to grab the cast list from container 50 (dialogvideoinfo)
            for i in range(250):
                label = xbmc.getInfoLabel("Container(50).ListItemNoWrap(%s).Label" %i).decode("utf-8")
                if not label: break
                label2 = xbmc.getInfoLabel("Container(50).ListItemNoWrap(%s).Label2" %i).decode("utf-8")
                thumb = getCleanImage( xbmc.getInfoLabel("Container(50).ListItemNoWrap(%s).Thumb" %i).decode("utf-8") )
                if not thumb or not xbmcvfs.exists(thumb) and downloadThumbs: 
                    artwork = getOfficialArtWork(label,None,"person")
                    thumb = artwork.get("thumb","")
                url = "RunScript(script.extendedinfo,info=extendedactorinfo,name=%s)"%label
                path="plugin://script.skin.helper.service/?action=launch&path=" + url
                liz = xbmcgui.ListItem(label=label,label2=label2,iconImage=thumb)
                liz.setProperty('IsPlayable', 'false')
                liz.setThumbnailImage(thumb)
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=liz, isFolder=False)
                allCast.append([label,label2,thumb])
                
        
        #process cast for regular movie or show
        if item and item.has_key("cast"):
            for cast in item["cast"]:
                if not cast.get("thumbnail") or not xbmcvfs.exists(cast.get("thumbnail")) and downloadThumbs: 
                    artwork = getOfficialArtWork(cast["name"],None,"person")
                    cast["thumbnail"] = artwork.get("thumb","")
                liz = xbmcgui.ListItem(label=cast["name"],label2=cast["role"],iconImage=cast.get("thumbnail"))
                allCast.append([cast["name"],cast["role"],cast.get("thumbnail","")])
                castNames.append(cast["name"])
                url = "RunScript(script.extendedinfo,info=extendedactorinfo,name=%s)"%cast["name"]
                path="plugin://script.skin.helper.service/?action=launch&path=" + url
                liz.setProperty('IsPlayable', 'false')
                liz.setThumbnailImage(cast.get("thumbnail"))
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=liz, isFolder=False)
        
        #process cast for all movies in a movieset
        elif moviesetmovies:
            moviesetCastList = []
            for setmovie in moviesetmovies:
                json_result = getJSON('VideoLibrary.GetMovieDetails', '{ "movieid": %d, "properties": [ "title", "cast" ] }' %setmovie["movieid"])
                if json_result:
                    for cast in json_result["cast"]:
                        if not cast["name"] in moviesetCastList:
                            if not cast.get("thumbnail") or not xbmcvfs.exists(cast.get("thumbnail")) and downloadThumbs:
                                artwork = getOfficialArtWork(cast["name"],None,"person")
                                cast["thumbnail"] = artwork.get("thumb","")
                            liz = xbmcgui.ListItem(label=cast["name"],label2=cast["role"],iconImage=cast.get("thumbnail",""))
                            allCast.append([cast["name"],cast["role"],cast["thumbnail"]])
                            castNames.append(cast["name"])
                            url = "RunScript(script.extendedinfo,info=extendedactorinfo,name=%s)"%cast["name"]
                            path="plugin://script.skin.helper.service/?action=launch&path=" + url
                            liz.setProperty('IsPlayable', 'false')
                            liz.setThumbnailImage(cast.get("thumbnail"))
                            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=liz, isFolder=False)
                            moviesetCastList.append(cast["name"])
            
        WINDOW.setProperty(cachedataStr,repr(allCast))
    
    WINDOW.setProperty('SkinHelper.ListItemCast', "[CR]".join(castNames))
    
    xbmcplugin.endOfDirectory(int(sys.argv[1]))    