#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcgui
import xbmc
import xbmcvfs
import os
import sys
import urllib
from traceback import format_exc
import _strptime
import unicodedata
from simplecache import SimpleCache

try:
    from multiprocessing.pool import ThreadPool as Pool
    supportsPool = True
except Exception:
    supportsPool = False

try:
    import simplejson as json
except Exception:
    import json

ADDON_ID = "script.skin.helper.service"
KODI_VERSION = int(xbmc.getInfoLabel("System.BuildVersion").split(".")[0])
KODILANGUAGE = xbmc.getLanguage(xbmc.ISO_639_1)


def log_msg(msg, loglevel=xbmc.LOGNOTICE):
    if isinstance(msg, unicode):
        msg = msg.encode('utf-8')
    xbmc.log("Skin Helper Service --> %s" % msg, level=loglevel)


def log_exception(modulename, exceptiondetails):
    log_msg(format_exc(sys.exc_info()), xbmc.LOGWARNING)
    log_msg("ERROR in %s ! --> %s" % (modulename, exceptiondetails), xbmc.LOGERROR)


def kodi_json(jsonmethod, params=None, returntype=None):
    kodi_json = {}
    kodi_json["jsonrpc"] = "2.0"
    kodi_json["method"] = jsonmethod
    if not params:
        params = {}
    kodi_json["params"] = params
    kodi_json["id"] = 1
    json_response = xbmc.executeJSONRPC(try_encode(json.dumps(kodi_json)))
    json_object = json.loads(json_response.decode('utf-8', 'replace'))
    # set the default returntype to prevent errors
    if "details" in jsonmethod.lower():
        result = {}
    else:
        result = []
    if 'result' in json_object:
        if returntype and returntype in json_object['result']:
            # returntype specified, return immediately
            result = json_object['result'][returntype]
        else:
            # no returntype specified, we'll have to look for it
            for key, value in json_object['result'].iteritems():
                if not key == "limits" and (isinstance(value, list) or isinstance(value, dict)):
                    result = value
    else:
        log_msg(json_response)
        log_msg(kodi_json)
    return result


def try_encode(text, encoding="utf-8"):
    try:
        return text.encode(encoding, "ignore")
    except Exception:
        return text


def try_decode(text, encoding="utf-8"):
    try:
        return text.decode(encoding, "ignore")
    except Exception:
        return text


def detect_plugin_content(plugin):
    '''based on the properties in the listitem we try to detect the content'''
    content_type = ""
    # load from cache first
    cache_str = "widgetcontent_type-%s" % plugin
    simplecache = SimpleCache()
    cache = simplecache.get(cache_str)
    if cache:
        content_type = cache
    else:
        # no cache, we need to detect the content_type
        # detect content based on the path
        if ("movie" in plugin.lower() or
            "box" in plugin.lower() or
            "dvd" in plugin.lower() or
            "rentals" in plugin.lower() or
            "incinemas" in plugin.lower() or
            "comingsoon" in plugin.lower() or
            "upcoming" in plugin.lower() or
            "opening" in plugin.lower() or
                "intheaters" in plugin.lower()):
            content_type = "movies"
        elif "album" in plugin.lower():
            content_type = "albums"
        elif "show" in plugin.lower():
            content_type = "tvshows"
        elif "episode" in plugin.lower():
            content_type = "episodes"
        elif "media" in plugin.lower():
            content_type = "movies"
        elif "favourites" in plugin.lower():
            content_type = "movies"
        elif "song" in plugin.lower():
            content_type = "songs"
        elif "musicvideo" in plugin.lower():
            content_type = "musicvideos"
        elif "type=dynamic" in plugin.lower():
            content_type = "movies"
        elif "videos" in plugin.lower():
            content_type = "movies"
        elif "type=both" in plugin.lower():
            content_type = "movies"
        # if we didn't get the content based on the path, we need to probe the addon...
        if not content_type and not xbmc.getCondVisibility("Window.IsMedia"):  # safety check
            log_msg("detect_plugin_content probing content_type for: %s" % plugin)
            media_array = kodi_json('Files.GetDirectory', {
                "directory": plugin,
                "media": "files",
                "properties": ["title", "file", "thumbnail", "episode", "showtitle", "season", "album",
                               "artist", "imdbnumber", "firstaired", "mpaa", "trailer", "studio", "art"],
                "limits": {"end": 1}})
            for item in media_array:
                if item.get("filetype", "") == "directory":
                    content_type = "folder"
                    break
                elif "showtitle" not in item and "artist" not in item:
                    # these properties are only returned in the json response if we're looking at actual file content...
                    # if it's missing it means this is a main directory listing and no need to
                    # scan the underlying listitems.
                    content_type = "files"
                    break
                if "showtitle" not in item and "artist" in item:
                    # AUDIO ITEMS
                    if item["type"] == "artist":
                        content_type = "artists"
                        break
                    elif (isinstance(item["artist"], list) and len(item["artist"]) > 0 and
                          item["artist"][0] == item["title"]):
                        content_type = "artists"
                        break
                    elif item["type"] == "album" or item["album"] == item["title"]:
                        content_type = "albums"
                        break
                    elif ((item["type"] == "song" and "play_album" not in item["file"]) or
                          (item["artist"] and item["album"])):
                        content_type = "songs"
                        break
                else:
                    # VIDEO ITEMS
                    if (item["showtitle"] and not item["artist"]):
                        # this is a tvshow, episode or season...
                        if item["type"] == "season" or (item["season"] > -1 and item["episode"] == -1):
                            content_type = "seasons"
                            break
                        elif item["type"] == "episode" or item["season"] > -1 and item["episode"] > -1:
                            content_type = "episodes"
                            break
                        else:
                            content_type = "tvshows"
                            break
                    elif (item["artist"]):
                        # this is a musicvideo!
                        content_type = "musicvideos"
                        break
                    elif (item["type"] == "movie" or item["imdbnumber"] or item["mpaa"] or
                          item["trailer"] or item["studio"]):
                        content_type = "movies"
                        break
        # save to cache
        simplecache.set(cache_str, content_type)
    return content_type


def create_smartshortcuts_submenu(win_prop, icon_image):
    try:
        if xbmcvfs.exists("special://skin/shortcuts/"):
            shortcuts_file = xbmc.translatePath(
                "special://home/addons/script.skinshortcuts/resources/shortcuts/"
                "info-window-home-property-%s-title.DATA.xml" % win_prop.replace(".", "-")).decode("utf-8")
            templatefile = "special://home/addons/%s/resources/smartshortcuts/smartshortcuts-submenu-template.xml" \
                % (ADDON_ID)
            templatefile = xbmc.translatePath(templatefile)
            if not xbmcvfs.exists(shortcuts_file):
                with open(templatefile, 'r') as f:
                    data = f.read()
                data = data.replace("WINDOWPROP", win_prop)
                data = data.replace("ICONIMAGE", icon_image)
                with open(shortcuts_file, 'w') as f:
                    f.write(data)
    except Exception as e:
        log_exception(__name__, e)


def get_current_content_type(containerprefix=""):
    content_type = ""
    if not containerprefix:
        if xbmc.getCondVisibility("Container.Content(episodes)"):
            content_type = "episodes"
        elif xbmc.getCondVisibility("Container.Content(movies) + !substring(Container.FolderPath,setid=)"):
            content_type = "movies"
        elif xbmc.getCondVisibility("[Container.Content(sets) | "
                                    "StringCompare(Container.Folderpath,videodb://movies/sets/)] + "
                                    "!substring(Container.FolderPath,setid=)"):
            content_type = "sets"
        elif xbmc.getCondVisibility("substring(Container.FolderPath,setid=)"):
            content_type = "setmovies"
        elif xbmc.getCondVisibility("!IsEmpty(Container.Content) + !StringCompare(Container.Content,pvr)"):
            content_type = xbmc.getInfoLabel("Container.Content")
        elif xbmc.getCondVisibility("Container.Content(tvshows)"):
            content_type = "tvshows"
        elif xbmc.getCondVisibility("Container.Content(seasons)"):
            content_type = "seasons"
        elif xbmc.getCondVisibility("Container.Content(musicvideos)"):
            content_type = "musicvideos"
        elif xbmc.getCondVisibility("Container.Content(songs) | "
                                    "StringCompare(Container.FolderPath,musicdb://singles/)"):
            content_type = "songs"
        elif xbmc.getCondVisibility("Container.Content(artists)"):
            content_type = "artists"
        elif xbmc.getCondVisibility("Container.Content(albums)"):
            content_type = "albums"
        elif xbmc.getCondVisibility("Window.IsActive(MyPVRChannels.xml) | Window.IsActive(MyPVRGuide.xml) | "
                                    "Window.IsActive(MyPVRSearch.xml) | Window.IsActive(pvrguideinfo)"):
            content_type = "tvchannels"
        elif xbmc.getCondVisibility("Window.IsActive(MyPVRRecordings.xml) | Window.IsActive(MyPVRTimers.xml) | "
                                    "Window.IsActive(pvrrecordinginfo)"):
            content_type = "tvrecordings"
        elif xbmc.getCondVisibility("Window.IsActive(programs) | Window.IsActive(addonbrowser)"):
            content_type = "addons"
        elif xbmc.getCondVisibility("Window.IsActive(pictures)"):
            content_type = "pictures"
        elif xbmc.getCondVisibility("Container.Content(genres)"):
            content_type = "genres"
        elif xbmc.getCondVisibility("Container.Content(files)"):
            content_type = "files"
    # last resort: try to determine type by the listitem properties
    if not content_type and (containerprefix or xbmc.getCondVisibility("Window.IsActive(movieinformation)")):
        if xbmc.getCondVisibility("!IsEmpty(%sListItem.DBTYPE)" % containerprefix):
            content_type = xbmc.getInfoLabel("%sListItem.DBTYPE" % containerprefix) + "s"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.Property(DBTYPE))" % containerprefix):
            content_type = xbmc.getInfoLabel("%sListItem.Property(DBTYPE)" % containerprefix) + "s"
        elif xbmc.getCondVisibility("SubString(%sListItem.FileNameAndPath,playrecording) | "
                                    "SubString(%sListItem.FileNameAndPath,tvtimer)"
                                    % (containerprefix, containerprefix)):
            content_type = "tvrecordings"
        elif xbmc.getCondVisibility("SubString(%sListItem.FileNameAndPath,launchpvr)" % (containerprefix)):
            content_type = "tvchannels"
        elif xbmc.getCondVisibility("SubString(%sListItem.FolderPath,pvr://channels)" % containerprefix):
            content_type = "tvchannels"
        elif xbmc.getCondVisibility("SubString(%sListItem.FolderPath,flix2kodi) + SubString(%sListItem.Genre,Series)"
                                    % (containerprefix, containerprefix)):
            content_type = "tvshows"
        elif xbmc.getCondVisibility("SubString(%sListItem.FolderPath,flix2kodi)" % (containerprefix)):
            content_type = "movies"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.Artist) + StringCompare(%sListItem.Label,%sListItem.Artist)"
                                    % (containerprefix, containerprefix, containerprefix)):
            content_type = "artists"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.Album) + StringCompare(%sListItem.Label,%sListItem.Album)"
                                    % (containerprefix, containerprefix, containerprefix)):
            content_type = "albums"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.Artist) + !IsEmpty(%sListItem.Album)"
                                    % (containerprefix, containerprefix)):
            content_type = "songs"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.TvShowTitle) + "
                                    "StringCompare(%sListItem.Title,%sListItem.TvShowTitle)"
                                    % (containerprefix, containerprefix, containerprefix)):
            content_type = "tvshows"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.Property(TotalEpisodes))" % (containerprefix)):
            content_type = "tvshows"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.TvshowTitle) + !IsEmpty(%sListItem.Season)"
                                    % (containerprefix, containerprefix)):
            content_type = "episodes"
        elif xbmc.getCondVisibility("IsEmpty(%sListItem.TvshowTitle) + !IsEmpty(%sListItem.Year)"
                                    % (containerprefix, containerprefix)):
            content_type = "movies"
        elif xbmc.getCondVisibility("SubString(%sListItem.FolderPath,movies)" % containerprefix):
            content_type = "movies"
        elif xbmc.getCondVisibility("SubString(%sListItem.FolderPath,shows)" % containerprefix):
            content_type = "tvshows"
        elif xbmc.getCondVisibility("SubString(%sListItem.FolderPath,episodes)" % containerprefix):
            content_type = "episodes"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.Property(ChannelLogo))" % (containerprefix)):
            content_type = "tvchannels"
    return content_type


def get_clean_image(image):
    if image and "image://" in image:
        image = image.replace("image://", "").replace("music@", "")
        image = urllib.unquote(image.encode("utf-8"))
        if image.endswith("/"):
            image = image[:-1]
    return try_decode(image)


def normalize_string(text):
    text = text.replace(":", "")
    text = text.replace("/", "-")
    text = text.replace("\\", "-")
    text = text.replace("<", "")
    text = text.replace(">", "")
    text = text.replace("*", "")
    text = text.replace("?", "")
    text = text.replace('|', "")
    text = text.replace('(', "")
    text = text.replace(')', "")
    text = text.replace("\"", "")
    text = text.strip()
    text = text.rstrip('.')
    text = unicodedata.normalize('NFKD', try_decode(text))
    return text


def recursive_delete_dir(path):
    success = True
    path = try_encode(path)
    dirs, files = xbmcvfs.listdir(path)
    for file in files:
        success = xbmcvfs.delete(os.path.join(path, file))
    for dir in dirs:
        success = recursive_delete_dir(os.path.join(path, dir))
    success = xbmcvfs.rmdir(path)
    return success


def process_method_on_list(method_to_run, items):
    '''helper method that processes a method on each listitem with pooling if the system supports it'''
    all_items = []
    if supportsPool:
        pool = Pool()
        try:
            all_items = pool.map(method_to_run, items)
        except Exception:
            # catch exception to prevent threadpool running forever
            log_msg(format_exc(sys.exc_info()))
            log_msg("Error in %s" % method_to_run)
        pool.close()
        pool.join()
    else:
        all_items = [method_to_run(item) for item in items]
    all_items = filter(None, all_items)
    return all_items


def get_content_path(lib_path):
    '''helper to get the real browsable path'''
    if "$INFO" in lib_path and "reload=" not in lib_path:
        lib_path = lib_path.replace("$INFO[Window(Home).Property(", "")
        lib_path = lib_path.replace(")]", "")
        win = xbmcgui.Window(10000)
        lib_path = win.getProperty(lib_path)
        del win
    if "activate" in lib_path.lower():
        if "activatewindow(musiclibrary," in lib_path.lower():
            lib_path = lib_path.lower().replace("activatewindow(musiclibrary,", "musicdb://")
            lib_path = lib_path.replace(",return", "/")
            lib_path = lib_path.replace(", return", "/")
        else:
            lib_path = lib_path.lower().replace(",return", "")
            lib_path = lib_path.lower().replace(", return", "")
            if ", " in lib_path:
                lib_path = lib_path.split(", ", 1)[1]
            elif " , " in lib_path:
                lib_path = lib_path.split(" , ", 1)[1]
            elif " ," in lib_path:
                lib_path = lib_path.split(", ", 1)[1]
            elif "," in lib_path:
                lib_path = lib_path.split(",", 1)[1]
        lib_path = lib_path.replace(")", "")
        lib_path = lib_path.replace("\"", "")
        lib_path = lib_path.replace("musicdb://special://", "special://")
        lib_path = lib_path.replace("videodb://special://", "special://")
    if "&reload=" in lib_path:
        lib_path = lib_path.split("&reload=")[0]
    return lib_path
