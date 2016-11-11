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


def log_msg(msg, loglevel=xbmc.LOGDEBUG):
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
    log_msg("requesting kodi json--> %s" %json.dumps(kodi_json))
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


def urlencode(text):
    blah = urllib.urlencode({'blahblahblah': try_encode(text)})
    blah = blah[13:]
    return blah

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

