#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import get_content_path
from simplecache import SimpleCache
import xbmc

# Various helpers to retrieve our smart shortcuts
    


def update_smartshortcuts(self,buildSmartshortcuts=False):

    #smart shortcuts --> emby nodes
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.emby) + Skin.HasSetting(SmartShortcuts.emby)"):
        if self.smartShortcuts.get("emby") and not buildSmartshortcuts:
            #randomize background image from cache
            nodes = self.smartShortcuts["emby"]
            for node in nodes:
                self.set_image_from_path(node[0] + ".image",node[2])
        #build node listing
        elif self.win.getProperty("emby.nodes.total"):
            embyProperty = self.win.getProperty("emby.nodes.total")
            contentStrings = ["", ".recent", ".inprogress", ".unwatched", ".recentepisodes", ".inprogressepisodes", ".nextepisodes", "recommended"]
            nodes = []
            totalNodes = int(embyProperty)
            for i in range(totalNodes):
                #stop if shutdown requested in the meanwhile
                if self.exit: return
                for contentString in contentStrings:
                    key = "emby.nodes.%s%s"%(str(i),contentString)
                    path = self.win.getProperty("emby.nodes.%s%s.path"%(str(i),contentString))
                    label = self.win.getProperty("emby.nodes.%s%s.title"%(str(i),contentString))
                    if path:
                        nodes.append( (key, label, path ) )
                        self.set_image_from_path("emby.nodes.%s%s.image"%(str(i),contentString),path)
                        if contentString == "":
                            if not "emby.nodes.%s"%i in self.smartShortcuts["allSmartShortcuts"]: self.smartShortcuts["allSmartShortcuts"].append("emby.nodes.%s"%i )
                            create_smartshortcuts_submenu("emby.nodes.%s"%i,"special://home/addons/plugin.video.emby/icon.png")
            self.smartShortcuts["emby"] = nodes
            log_msg("Generated smart shortcuts for emby nodes: %s" %nodes)

    #stop if shutdown requested in the meanwhile
    if self.exit: return

    #smart shortcuts --> playlists
    if xbmc.getCondVisibility("Skin.HasSetting(SmartShortcuts.playlists)"):
        playlists = []
        if self.smartShortcuts.has_key("playlists") and not buildSmartshortcuts:
            #randomize background image from cache
            playlists = self.smartShortcuts["playlists"]
        else:
            #build node listing
            playlistCount = 0
            paths = [['special://videoplaylists/','VideoLibrary'], ['special://musicplaylists/','MusicLibrary']]
            for playlistpath in paths:
                if not xbmcvfs.exists(playlistpath[0]): continue
                media_array = kodi_json('Files.GetDirectory', { "directory": playlistpath[0], "media": "files" } )
                for item in media_array:
                    try:
                        label = ""
                        if item["file"].endswith(".xsp") and not "Emby" in item["file"]:
                            playlist = item["file"]
                            contents = xbmcvfs.File(playlist, 'r')
                            contents_data = contents.read()
                            contents.close()
                            xmldata = xmltree.fromstring(contents_data)
                            art_type = "unknown"
                            label = item["label"]
                            if self.set_image_from_path("playlist." + str(playlistCount) + ".image",playlist):
                                for line in xmldata.getiterator():
                                    if line.tag == "smartplaylist":
                                        art_type = line.attrib['art_type']
                                    if line.tag == "name":
                                        label = line.text
                                path = "ActivateWindow(%s,%s,return)" %(playlistpath[1],playlist)
                                if not "playlist.%s"%playlistCount in self.smartShortcuts["allSmartShortcuts"]: self.smartShortcuts["allSmartShortcuts"].append("playlist.%s"%playlistCount )
                                playlists.append( (playlistCount, label, path, playlist, art_type ))
                                playlistCount += 1
                    except Exception:
                        log_msg("Error while processing smart shortcuts for playlist %s  --> This file seems to be corrupted, please remove it from your system to prevent any further errors."%item["file"], xbmc.LOGWARNING)
            self.smartShortcuts["playlists"] = playlists
            log_msg("Generated smart shortcuts for playlists: %s" %playlists)

        for playlist in playlists:
            self.set_image_from_path("playlist." + str(playlist[0]) + ".image",playlist[3])
            if not self.smartShortcutsFirstRunDone or buildSmartshortcuts:
                self.win.setProperty("playlist." + str(playlist[0]) + ".label", playlist[1])
                self.win.setProperty("playlist." + str(playlist[0]) + ".title", playlist[1])
                self.win.setProperty("playlist." + str(playlist[0]) + ".action", playlist[2])
                self.win.setProperty("playlist." + str(playlist[0]) + ".path", playlist[2])
                self.win.setProperty("playlist." + str(playlist[0]) + ".content", playlist[3])
                self.win.setProperty("playlist." + str(playlist[0]) + ".type", playlist[4])

    #stop if shutdown requested in the meanwhile
    if self.exit: return

    #smart shortcuts --> favorites
    if xbmc.getCondVisibility("Skin.HasSetting(SmartShortcuts.favorites)"):
        favourites = []
        if self.smartShortcuts.has_key("favourites") and not buildSmartshortcuts:
            #randomize background image from cache
            favourites = self.smartShortcuts["favourites"]
        else:
            #build node listing
            try:
                json_result = kodi_json('Favourites.GetFavourites', {"art_type": None, "properties": ["path", "thumbnail", "window", "windowparameter"] })
                for count, fav in enumerate(json_result):
                    if "windowparameter" in fav:
                        content = fav["windowparameter"]
                        #check if this is a valid path with content
                        if not "script://" in content.lower() and not "mode=9" in content.lower() and not "search" in content.lower() and not "play" in content.lower():
                            path = "ActivateWindow(%s,%s,return)" %(fav["window"],content)
                            if "&" in content and "?" in content and "=" in content and not content.endswith("/"):
                                content += "&widget=true"
                            art_type = detect_plugin_content(content)
                            if art_type:
                                if not "favorite.%s" %count in self.smartShortcuts["allSmartShortcuts"]:
                                    self.smartShortcuts["allSmartShortcuts"].append("favorite.%s" %count )
                                favourites.append( (count, fav["title"], path, content, art_type) )
            except Exception as e:
                #something wrong so disable the smartshortcuts for this section for now
                xbmc.executebuiltin("Skin.Reset(SmartShortcuts.favorites)")
                log_msg("Error while processing smart shortcuts for favourites - set disabled.... ",xbmc.LOGWARNING)
                log_msg(str(e),0)
            self.smartShortcuts["favourites"] = favourites
            log_msg("Generated smart shortcuts for favourites: %s" %favourites)

        for favourite in favourites:
            self.set_image_from_path("favorite." + str(favourite[0]) + ".image",favourite[2])
            if not self.smartShortcutsFirstRunDone or buildSmartshortcuts:
                self.win.setProperty("favorite." + str(favourite[0]) + ".label", favourite[1] )
                self.win.setProperty("favorite." + str(favourite[0]) + ".title", favourite[1] )
                self.win.setProperty("favorite." + str(favourite[0]) + ".action", favourite[2] )
                self.win.setProperty("favorite." + str(favourite[0]) + ".path", favourite[2] )
                self.win.setProperty("favorite." + str(favourite[0]) + ".content", favourite[3] )
                self.win.setProperty("favorite." + str(favourite[0]) + ".type", favourite[4] )

    #stop if shutdown requested in the meanwhile
    if self.exit: return

    #smart shortcuts --> plex nodes
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.plexbmc) + Skin.HasSetting(SmartShortcuts.plex)"):
        nodes = []
        if self.smartShortcuts.has_key("plex") and not buildSmartshortcuts:
            #get plex nodes from cache...
            nodes = self.smartShortcuts["plex"]
        else:
            #build the plex listing...
            nodes = self.get_plex_nodes()
            self.smartShortcuts["plex"] = nodes
            log_msg("Generated smart shortcuts for plex: %s" %nodes)
        for node in nodes:
            #randomize background image from cache
            self.set_image_from_path(node[0] + ".image",node[3])
            if buildSmartshortcuts or not self.smartShortcutsFirstRunDone:
                #set other properties at first load only
                self.win.setProperty(node[0] + ".label", node[1])
                self.win.setProperty(node[0] + ".title", node[1])
                self.win.setProperty(node[0] + ".action", node[2])
                self.win.setProperty(node[0] + ".path", node[2])
                self.win.setProperty(node[0] + ".content", node[3])
                self.win.setProperty(node[0] + ".type", node[4])

    #stop if shutdown requested in the meanwhile
    if self.exit: return

    #smart shortcuts --> netflix nodes
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.flix2kodi) + Skin.HasSetting(SmartShortcuts.netflix)"):
        nodes = []
        if self.smartShortcuts.has_key("netflix") and not buildSmartshortcuts:
            #get the netflix nodes from cache...
            nodes = self.smartShortcuts["netflix"]
        else:
            #build the netflix listing...
            nodes = self.get_netflix_nodes()
            self.smartShortcuts["netflix"] = nodes
        if nodes:
            for node in nodes:
                key = node[0]
                if len(node) == 6: imagespath = node[5]
                else: imagespath = node[2]
                #randomize background image from cache
                if not key.startswith("netflix.generic.suggestions"):
                    self.set_image_from_path(key + ".image",imagespath,"special://home/addons/plugin.video.flix2kodi/fanart.jpg")
                if buildSmartshortcuts or not self.smartShortcutsFirstRunDone:
                    #set other properties at first load only
                    self.win.setProperty(key + ".title", node[1])
                    self.win.setProperty(key + ".content", node[2])
                    self.win.setProperty(key + ".path", node[4])
                    self.win.setProperty(key + ".type", node[3])

    #store all smart shortcuts for exchange with skinshortcuts
    self.win.setProperty("allSmartShortcuts", repr(self.smartShortcuts["allSmartShortcuts"]))

    self.smartShortcutsFirstRunDone = True

def get_plex_nodes(self):
    nodes = []
    if xbmc.getCondVisibility("System.HasAddon(plugin.video.plexbmc) + Skin.HasSetting(SmartShortcuts.plex)") and not self.exit:
        xbmc.executebuiltin('RunScript(plugin.video.plexbmc,amberskin)')
        #wait a few seconds for the initialization to be finished
        self.kodimonitor.waitForAbort(5)

        #get the plex setting if there are subnodes
        plexaddon = xbmcaddon.Addon(id='plugin.video.plexbmc')
        hasSecondaryMenus = plexaddon.getSetting("secondary") == "true"
        del plexaddon

        contentStrings = ["", ".ondeck", ".recent", ".unwatched"]
        totalNodes = 50
        for i in range(totalNodes):
            if not self.win.getProperty("plexbmc.%s.title"%i): break
            if self.exit: return
            for contentString in contentStrings:
                key = "plexbmc.%s%s"%(i,contentString)
                label = self.win.getProperty("plexbmc.%s.title"%i).decode("utf-8")
                media_type = self.win.getProperty("plexbmc.%s.type"%i).decode("utf-8")
                if media_type == "movie": media_type = "movies"
                if hasSecondaryMenus: path = self.win.getProperty("plexbmc.%s.all"%i).decode("utf-8")
                else: path = self.win.getProperty("plexbmc.%s.path"%i).decode("utf-8")
                path = path.replace("VideoLibrary","Videos") #fix for krypton ?
                alllink = path
                alllink = alllink.replace("mode=1", "mode=0")
                alllink = alllink.replace("mode=2", "mode=0")
                if contentString == ".recent":
                    label += " - Recently Added"
                    if media_type == "show": media_type = "episodes"
                    if hasSecondaryMenus: path = self.win.getProperty(key).decode("utf-8")
                    else: path = alllink.replace("/all", "/recentlyAdded")
                elif contentString == ".ondeck":
                    label += " - On deck"
                    if media_type == "show": media_type = "episodes"
                    if hasSecondaryMenus: path = self.win.getProperty(key).decode("utf-8")
                    else: path = alllink.replace("/all", "/onDeck")
                elif contentString == ".unwatched":
                    if media_type == "show": media_type = "episodes"
                    label += " - Unwatched"
                    path = alllink.replace("/all", "/unwatched")
                elif contentString == "":
                    if media_type == "show": media_type = "tvshows"
                    if not key in self.smartShortcuts["allSmartShortcuts"]: self.smartShortcuts["allSmartShortcuts"].append(key)
                    create_smartshortcuts_submenu("plexbmc.%s"%i,"special://home/addons/plugin.video.plexbmc/icon.png")

                #append media_type to path
                if "&" in path:
                    path = path + "&art_type=" + media_type
                else:
                    path = path + "?art_type=" + media_type
                content = get_content_path(path)
                nodes.append( (key, label, path, content, media_type ) )

        #add plex channels as entry
        #extract path from one of the nodes as a workaround because main plex addon channels listing is in error
        if nodes:
            path = self.win.getProperty("plexbmc.0.path").decode("utf-8")
            if not path: path = self.win.getProperty("plexbmc.0.all").decode("utf-8")
            path = path.split("/library/")[0]
            path = path + "/channels/all&mode=21"
            path = path + ", return)"
            key = "plexbmc.channels"
            label = "Channels"
            content = get_content_path(path)
            nodes.append( (key, label, path, content, "episodes" ) )
            if not key in self.smartShortcuts["allSmartShortcuts"]: self.smartShortcuts["allSmartShortcuts"].append(key)

    return nodes

def get_netflix_nodes(self):
    #build a listing of netflix nodes...

    if not xbmc.getCondVisibility("System.HasAddon(plugin.video.flix2kodi) + Skin.HasSetting(SmartShortcuts.netflix)") or self.exit:
        return []

    nodes = []
    netflixAddon = xbmcaddon.Addon('plugin.video.flix2kodi')
    profilename = netflixAddon.getSetting('profile_name').decode("utf-8")

    if profilename and netflixAddon.getSetting("username") and netflixAddon.getSetting("authorization_url"):
        log_msg("Generating netflix entries for profile %s .... "%profilename)
        #generic netflix shortcut
        key = "netflix.generic"
        label = netflixAddon.getAddonInfo('name')
        content = "plugin://plugin.video.flix2kodi/?mode=main&widget=true&url&widget=true"
        path = "ActivateWindow(Videos,%s,return)" %content
        imagespath = "plugin://plugin.video.flix2kodi/?mode=list_videos&thumb&art_type=both&url=list%3f%26mylist&widget=true"
        media_type = "media"
        nodes.append( (key, label, content, media_type, path, imagespath ) )
        create_smartshortcuts_submenu("netflix.generic","special://home/addons/plugin.video.flix2kodi/icon.png")

        #generic netflix mylist
        key = "netflix.generic.mylist"
        label = netflixAddon.getLocalizedString(30104)
        content = "plugin://plugin.video.flix2kodi/?mode=list_videos&thumb&art_type=both&url=list%3f%26mylist&widget=true"
        path = "ActivateWindow(Videos,%s,return)" %content
        media_type = "movies"
        nodes.append( (key, label, content, media_type, path ) )

        if self.exit: return

        #get mylist items...
        mylist = []
        media_array = kodi_json('Files.GetDirectory',{ "properties": ["title"], "directory": "plugin://plugin.video.flix2kodi/?mode=list_videos&thumb&art_type=both&url=list%3f%26mylist&widget=true", "media": "files", "limits": {"end":50} })
        for item in media_array:
            mylist.append(item["label"])

        #get dynamic entries...
        media_array = kodi_json('Files.GetDirectory',{ "properties": ["title"], "directory": "plugin://plugin.video.flix2kodi/?mode=main&art_type=dynamic&widget=true", "media": "files", "limits": {"end":50} })
        if not media_array:
            #if no result the plugin is in error, exit processing
            return []
        elif media_array:
            itemscount = 0
            suggestionsNodefound = False
            for item in media_array:
                if self.exit: return
                if ("list_viewing_activity" in item["file"]) or ("mode=search" in item["file"]) or ("mylist" in item["file"]):
                    continue
                elif profilename in item["label"] and not suggestionsNodefound:
                    #this is the suggestions node!
                    suggestionsNodefound = True
                    #generic suggestions node
                    key = "netflix.generic.suggestions"
                    content = item["file"] + "&widget=true"
                    path = "ActivateWindow(Videos,%s,return)" %content
                    nodes.append( (key, item["label"], content, "movies", path ) )
                    #movies suggestions node
                    key = "netflix.movies.suggestions"
                    newpath = item["file"].replace("art_type=both","art_type=movie")
                    content = newpath + "&widget=true"
                    path = "ActivateWindow(Videos,%s,return)" %content
                    nodes.append( (key, item["label"], content, "movies", path ) )
                    #tvshows suggestions node
                    key = "netflix.tvshows.suggestions"
                    newpath = item["file"].replace("art_type=both","art_type=show")
                    content = newpath + "&widget=true"
                    path = "ActivateWindow(Videos,%s,return)" %content
                    nodes.append( (key, item["label"], content, "tvshows", path ) )
                elif profilename in item["label"] and suggestionsNodefound:
                    #this is the continue watching node!
                    #generic inprogress node
                    key = "netflix.generic.inprogress"
                    content = item["file"] + "&widget=true"
                    path = "ActivateWindow(Videos,%s,return)" %content
                    nodes.append( (key, item["label"], content, "movies", path ) )
                    #movies inprogress node
                    key = "netflix.movies.inprogress"
                    newpath = item["file"].replace("art_type=both","art_type=movie")
                    content = newpath + "&widget=true"
                    path = "ActivateWindow(Videos,%s,return)" %content
                    nodes.append( (key, item["label"], content, "movies", path ) )
                    #tvshows inprogress node
                    key = "netflix.tvshows.inprogress"
                    newpath = item["file"].replace("art_type=both","art_type=show")
                    content = newpath + "&widget=true"
                    path = "ActivateWindow(Videos,%s,return)" %content
                    nodes.append( (key, item["label"], content, "tvshows", path ) )
                elif item["label"].lower().endswith("releases"):
                    #this is the recent node!
                    #generic recent node
                    key = "netflix.generic.recent"
                    content = item["file"] + "&widget=true"
                    path = "ActivateWindow(Videos,%s,return)" %content
                    nodes.append( (key, item["label"], content, "movies", path ) )
                    #movies recent node
                    key = "netflix.movies.recent"
                    newpath = item["file"].replace("art_type=both","art_type=movie")
                    content = newpath + "&widget=true"
                    path = "ActivateWindow(Videos,%s,return)" %content
                    nodes.append( (key, item["label"], content, "movies", path ) )
                    #tvshows recent node
                    key = "netflix.tvshows.recent"
                    newpath = item["file"].replace("art_type=both","art_type=show")
                    content = newpath + "&widget=true"
                    path = "ActivateWindow(Videos,%s,return)" %content
                    nodes.append( (key, item["label"], content, "tvshows", path ) )
                elif item["label"] == "Trending":
                    #this is the trending node!
                    key = "netflix.generic.trending"
                    content = item["file"] + "&widget=true"
                    path = "ActivateWindow(Videos,%s,return)" %content
                    nodes.append( (key, item["label"], content, "movies", path ) )
                else:
                    key = "netflix.generic.suggestions.%s" %itemscount
                    content = item["file"] + "&widget=true"
                    path = "ActivateWindow(Videos,%s,return)" %content
                    media_type = "movies"
                    nodes.append( (key, item["label"], content, media_type, path ) )
                    itemscount += 1

                #get recommended node...
                for mylist_item in mylist:
                    if mylist_item in item["label"]:
                        key = "netflix.generic.recommended"
                        content = item["file"] + "&widget=true"
                        path = "ActivateWindow(Videos,%s,return)" %item["file"]
                        nodes.append( (key, item["label"], content, "movies", path ) )

        #netflix movies
        key = "netflix.movies"
        label = netflixAddon.getAddonInfo('name') + " " + netflixAddon.getLocalizedString(30100)
        content = "plugin://plugin.video.flix2kodi/?mode=main&thumb&art_type=movie&url&widget=true"
        path = "ActivateWindow(Videos,%s,return)" %content
        imagespath = "plugin://plugin.video.flix2kodi/?mode=list_videos&thumb&art_type=movie&url=list%3f%26mylist&widget=true"
        media_type = "movies"
        nodes.append( (key, label, content, media_type, path, imagespath ) )
        create_smartshortcuts_submenu("netflix.movies","special://home/addons/plugin.video.flix2kodi/icon.png")

        #netflix movies mylist
        key = "netflix.movies.inprogress"
        label = netflixAddon.getLocalizedString(30100) + " - " + netflixAddon.getLocalizedString(30104)
        content = "plugin://plugin.video.flix2kodi/?mode=list_videos&thumb&art_type=movie&url=list%3f%26mylist&widget=true"
        path = "ActivateWindow(Videos,%s,return)" %content
        media_type = "movies"
        nodes.append( (key, label, content, media_type, path ) )

        #netflix movies genres
        key = "netflix.movies.genres"
        label = netflixAddon.getLocalizedString(30100) + " - " + netflixAddon.getLocalizedString(30108)
        content = "plugin://plugin.video.flix2kodi/?mode=list_genres&thumb&art_type=movie&url&widget=true"
        path = "ActivateWindow(Videos,%s,return)" %content
        media_type = "genres"
        nodes.append( (key, label, content, media_type, path ) )

        #netflix tvshows
        key = "netflix.tvshows"
        label = netflixAddon.getAddonInfo('name') + " " + netflixAddon.getLocalizedString(30101)
        content = "plugin://plugin.video.flix2kodi/?mode=main&thumb&art_type=show&url&widget=true"
        path = "ActivateWindow(Videos,%s,return)" %content
        imagespath = "plugin://plugin.video.flix2kodi/?mode=list_videos&thumb&art_type=show&url=list%3f%26mylist&widget=true"
        media_type = "tvshows"
        nodes.append( (key, label, content, media_type, path, imagespath ) )
        create_smartshortcuts_submenu("netflix.tvshows","special://home/addons/plugin.video.flix2kodi/icon.png")

        #netflix tvshows mylist
        key = "netflix.tvshows.inprogress"
        label = netflixAddon.getLocalizedString(30101) + " - " + netflixAddon.getLocalizedString(30104)
        content = "plugin://plugin.video.flix2kodi/?mode=list_videos&thumb&art_type=show&url=list%3f%26mylist&widget=true"
        path = "ActivateWindow(Videos,%s,return)" %content
        media_type = "tvshows"
        nodes.append( (key, label, content, media_type, path ) )

        #netflix tvshows genres
        key = "netflix.tvshows.genres"
        label = netflixAddon.getLocalizedString(30101) + " - " + netflixAddon.getLocalizedString(30108)
        content = "plugin://plugin.video.flix2kodi/?mode=list_genres&thumb&art_type=show&url&widget=true"
        path = "ActivateWindow(Videos,%s,return)" %content
        media_type = "genres"
        nodes.append( (key, label, content, media_type, path ) )

        if not "netflix.generic" in self.smartShortcuts["allSmartShortcuts"]: self.smartShortcuts["allSmartShortcuts"].append("netflix.generic")
        if not "netflix.generic.movies" in self.smartShortcuts["allSmartShortcuts"]: self.smartShortcuts["allSmartShortcuts"].append("netflix.movies")
        if not "netflix.generic.tvshows" in self.smartShortcuts["allSmartShortcuts"]: self.smartShortcuts["allSmartShortcuts"].append("netflix.tvshows")

        log_msg("DONE Generating netflix entries --> %s"%repr(nodes))

    else:
        log_msg("SKIP Generating netflix entries - addon is not ready!")

    return nodes
