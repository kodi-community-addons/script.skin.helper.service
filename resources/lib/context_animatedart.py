# -*- coding: utf-8 -*-

'''
    script.skin.helper.service
    Contextmenu for Animated art
'''

import os, sys
import xbmc
import xbmcgui
from metadatautils import MetadataUtils
from utils import log_msg, try_decode
    

# pylint: disable-msg=invalid-constant-name


def get_imdb_id(win, metadatautils):
    '''get imdbnumber for listitem'''
    content_type = win.getProperty("contenttype")
    imdb_id = try_decode(xbmc.getInfoLabel("ListItem.IMDBNumber"))
    if not imdb_id:
        imdb_id = try_decode(xbmc.getInfoLabel("ListItem.Property(IMDBNumber)"))
    if imdb_id and not imdb_id.startswith("tt"):
        imdb_id = ""
    if not imdb_id:
        year = try_decode(xbmc.getInfoLabel("ListItem.Year"))
        title = try_decode(xbmc.getInfoLabel("ListItem.Title")).split(",")[0].split("(")[0]
        if content_type in ["episodes", "seasons"]:
            title = try_decode(xbmc.getInfoLabel("ListItem.TvShowTitle"))
        if title:
            log_msg("Animated Art: lookup imdbid by title and year: (%s - %s)" % (title, year), xbmc.LOGINFO)
            imdb_id = metadatautils.get_omdb_info("", title, year, content_type).get("imdbnumber", "")
        if not imdb_id:
            return title
    return imdb_id

# Kodi contextmenu item to configure the artwork
if __name__ == '__main__':
    log_msg("Contextmenu for Animated Art opened", xbmc.LOGINFO)
    ARTUTILS = MetadataUtils()
    WIN = xbmcgui.Window(10000)
    imdb_id = get_imdb_id(WIN, ARTUTILS)
    WIN.setProperty("SkinHelper.Artwork.ManualLookup", "busy")
    log_msg("Animated Art: Query animated art by IMDBID: %s" % imdb_id, xbmc.LOGINFO)
    artwork = ARTUTILS.get_animated_artwork(imdb_id, manual_select=True, ignore_cache=True)
    log_msg("Animated Art result: %s" % artwork, xbmc.LOGINFO)
    xbmc.executebuiltin("Container.Refresh")
    WIN.clearProperty("SkinHelper.Artwork.ManualLookup")
    del WIN
    ARTUTILS.close()
