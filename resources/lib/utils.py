#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    script.skin.helper.service
    Helper service and scripts for Kodi skins
    utils.py
    Various helper methods
'''

import xbmc
import xbmcvfs
import os
import sys
import urllib
from traceback import format_exc

try:
    import simplejson as json
except Exception:
    import json

ADDON_ID = "script.skin.helper.service"
KODI_VERSION = int(xbmc.getInfoLabel("System.BuildVersion").split(".")[0])
KODILANGUAGE = xbmc.getLanguage(xbmc.ISO_639_1)


def log_msg(msg, loglevel=xbmc.LOGDEBUG):
    '''log message to kodi log'''
    if isinstance(msg, unicode):
        msg = msg.encode('utf-8')
    xbmc.log("Skin Helper Service --> %s" % msg, level=loglevel)


def log_exception(modulename, exceptiondetails):
    '''helper to properly log an exception'''
    log_msg(format_exc(sys.exc_info()), xbmc.LOGWARNING)
    log_msg("Exception in %s ! --> %s" % (modulename, exceptiondetails), xbmc.LOGERROR)


def kodi_json(jsonmethod, params=None, returntype=None):
    '''get info from the kodi json api'''
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
            if isinstance(json_object['result'], dict):
                for key, value in json_object['result'].iteritems():
                    if not key == "limits":
                        result = value
                        break
            else:
                return json_object['result']
    else:
        log_msg(json_response)
        log_msg(kodi_json)
    return result


def try_encode(text, encoding="utf-8"):
    '''helper to encode a string to utf-8'''
    try:
        return text.encode(encoding, "ignore")
    except Exception:
        return text


def try_decode(text, encoding="utf-8"):
    '''helper to decode a string into unicode'''
    try:
        return text.decode(encoding, "ignore")
    except Exception:
        return text


def urlencode(text):
    '''urlencode a string'''
    blah = urllib.urlencode({'blahblahblah': try_encode(text)})
    blah = blah[13:]
    return blah


def get_current_content_type(containerprefix=""):
    '''tries to determine the mediatype for the current listitem'''
    content_type = ""
    if not containerprefix:
        if getCondVisibility("Container.Content(episodes)"):
            content_type = "episodes"
        elif getCondVisibility("Container.Content(movies) + !String.Contains(Container.FolderPath,setid=)"):
            content_type = "movies"
        elif getCondVisibility("[Container.Content(sets) | "
                                    "String.IsEqual(Container.Folderpath,videodb://movies/sets/)] + "
                                    "!String.Contains(Container.FolderPath,setid=)"):
            content_type = "sets"
        elif getCondVisibility("String.Contains(Container.FolderPath,setid=)"):
            content_type = "setmovies"
        elif getCondVisibility("!String.IsEmpty(Container.Content) + !String.IsEqual(Container.Content,pvr)"):
            content_type = xbmc.getInfoLabel("Container.Content")
        elif getCondVisibility("Container.Content(tvshows)"):
            content_type = "tvshows"
        elif getCondVisibility("Container.Content(seasons)"):
            content_type = "seasons"
        elif getCondVisibility("Container.Content(musicvideos)"):
            content_type = "musicvideos"
        elif getCondVisibility("Container.Content(songs) | "
                                    "String.IsEqual(Container.FolderPath,musicdb://singles/)"):
            content_type = "songs"
        elif getCondVisibility("Container.Content(artists)"):
            content_type = "artists"
        elif getCondVisibility("Container.Content(albums)"):
            content_type = "albums"
        elif getCondVisibility("Window.IsActive(MyPVRChannels.xml) | Window.IsActive(MyPVRGuide.xml) | "
                                    "Window.IsActive(MyPVRSearch.xml) | Window.IsActive(pvrguideinfo)"):
            content_type = "tvchannels"
        elif getCondVisibility("Window.IsActive(MyPVRRecordings.xml) | Window.IsActive(MyPVRTimers.xml) | "
                                    "Window.IsActive(pvrrecordinginfo)"):
            content_type = "tvrecordings"
        elif getCondVisibility("Window.IsActive(programs) | Window.IsActive(addonbrowser)"):
            content_type = "addons"
        elif getCondVisibility("Window.IsActive(pictures)"):
            content_type = "pictures"
        elif getCondVisibility("Container.Content(genres)"):
            content_type = "genres"
        elif getCondVisibility("Container.Content(files)"):
            content_type = "files"
    # last resort: try to determine type by the listitem properties
    if not content_type and (containerprefix or getCondVisibility("Window.IsActive(movieinformation)")):
        if getCondVisibility("!String.IsEmpty(%sListItem.DBTYPE)" % containerprefix):
            content_type = xbmc.getInfoLabel("%sListItem.DBTYPE" % containerprefix) + "s"
        elif getCondVisibility("!String.IsEmpty(%sListItem.Property(DBTYPE))" % containerprefix):
            content_type = xbmc.getInfoLabel("%sListItem.Property(DBTYPE)" % containerprefix) + "s"
        elif getCondVisibility("String.Contains(%sListItem.FileNameAndPath,playrecording) | "
                                    "String.Contains(%sListItem.FileNameAndPath,tvtimer)"
                                    % (containerprefix, containerprefix)):
            content_type = "tvrecordings"
        elif getCondVisibility("String.Contains(%sListItem.FileNameAndPath,launchpvr)" % (containerprefix)):
            content_type = "tvchannels"
        elif getCondVisibility("String.Contains(%sListItem.FolderPath,pvr://channels)" % containerprefix):
            content_type = "tvchannels"
        elif getCondVisibility("String.Contains(%sListItem.FolderPath,flix2kodi) + String.Contains(%sListItem.Genre,Series)"
                                    % (containerprefix, containerprefix)):
            content_type = "tvshows"
        elif getCondVisibility("String.Contains(%sListItem.FolderPath,flix2kodi)" % (containerprefix)):
            content_type = "movies"
        elif getCondVisibility("!String.IsEmpty(%sListItem.Artist) + String.IsEqual(%sListItem.Label,%sListItem.Artist)"
                                    % (containerprefix, containerprefix, containerprefix)):
            content_type = "artists"
        elif getCondVisibility("!String.IsEmpty(%sListItem.Album) + String.IsEqual(%sListItem.Label,%sListItem.Album)"
                                    % (containerprefix, containerprefix, containerprefix)):
            content_type = "albums"
        elif getCondVisibility("!String.IsEmpty(%sListItem.Artist) + !String.IsEmpty(%sListItem.Album)"
                                    % (containerprefix, containerprefix)):
            content_type = "songs"
        elif getCondVisibility("!String.IsEmpty(%sListItem.TvShowTitle) + "
                                    "String.IsEqual(%sListItem.Title,%sListItem.TvShowTitle)"
                                    % (containerprefix, containerprefix, containerprefix)):
            content_type = "tvshows"
        elif getCondVisibility("!String.IsEmpty(%sListItem.Property(TotalEpisodes))" % (containerprefix)):
            content_type = "tvshows"
        elif getCondVisibility("!String.IsEmpty(%sListItem.TvshowTitle) + !String.IsEmpty(%sListItem.Season)"
                                    % (containerprefix, containerprefix)):
            content_type = "episodes"
        elif getCondVisibility("String.IsEmpty(%sListItem.TvshowTitle) + !String.IsEmpty(%sListItem.Year)"
                                    % (containerprefix, containerprefix)):
            content_type = "movies"
        elif getCondVisibility("String.Contains(%sListItem.FolderPath,movies)" % containerprefix):
            content_type = "movies"
        elif getCondVisibility("String.Contains(%sListItem.FolderPath,shows)" % containerprefix):
            content_type = "tvshows"
        elif getCondVisibility("String.Contains(%sListItem.FolderPath,episodes)" % containerprefix):
            content_type = "episodes"
        elif getCondVisibility("!String.IsEmpty(%sListItem.Property(ChannelLogo))" % (containerprefix)):
            content_type = "tvchannels"
    return content_type


def recursive_delete_dir(path):
    '''helper to recursively delete a directory'''
    success = True
    path = try_encode(path)
    dirs, files = xbmcvfs.listdir(path)
    for file in files:
        success = xbmcvfs.delete(os.path.join(path, file))
    for directory in dirs:
        success = recursive_delete_dir(os.path.join(path, directory))
    success = xbmcvfs.rmdir(path)
    return success


def prepare_win_props(details, prefix=u"SkinHelper.ListItem."):
    '''helper to pretty string-format a dict with details to key/value pairs so it can be used as window props'''
    items = []
    if details:
        for key, value in details.iteritems():
            if value or value == 0:
                key = u"%s%s" % (prefix, key)
                key = key.lower()
                if isinstance(value, (str, unicode)):
                    items.append((key, value))
                elif isinstance(value, int):
                    items.append((key, "%s" % value))
                elif isinstance(value, float):
                    items.append((key, "%.1f" % value))
                elif isinstance(value, dict):
                    for key2, value2 in value.iteritems():
                        if isinstance(value2, (str, unicode)):
                            items.append((u"%s.%s" % (key, key2), value2))
                elif isinstance(value, list):
                    list_strings = []
                    for listvalue in value:
                        if isinstance(listvalue, (str, unicode)):
                            list_strings.append(listvalue)
                    if list_strings:
                        items.append((key, u" / ".join(list_strings)))
                    elif len(value) == 1 and isinstance(value[0], (str, unicode)):
                        items.append((key, value))
    return items


def merge_dict(dict_a, dict_b, allow_overwrite=False):
    '''append values to a dict without overwriting any existing values'''
    if not dict_a and dict_b:
        return dict_b
    if not dict_b:
        return dict_a
    result = dict_a.copy()
    for key, value in dict_b.iteritems():
        if (allow_overwrite or not key in dict_a or not dict_a[key]) and value:
            result[key] = value
    return result


def clean_string(text):
    '''strip quotes and spaces from begin and end of a string'''
    text = text.strip("'\"")
    text = text.strip()
    return text
    
    
def getCondVisibility(text):
    '''executes the builtin getCondVisibility'''
    # temporary solution: check if strings needs to be adjusted for backwards compatability
    if KODI_VERSION < 17:
        text = text.replace("Integer.IsGreater", "IntegerGreaterThan")
        text = text.replace("String.Contains", "SubString")
        text = text.replace("String.IsEqual", "StringCompare")
    return xbmc.getCondVisibility(text)
