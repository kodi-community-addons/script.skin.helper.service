# -*- coding: utf-8 -*-

'''
    script.skin.helper.service
    Contextmenu for Animated art
'''

import xbmc
import xbmcgui
from artutils import ArtUtils

def get_imdb_id(win, artutils):
    '''get imdbnumber for listitem'''
    content_type = win.getProperty("contenttype")
    imdb_id = xbmc.getInfoLabel("ListItem.IMDBNumber").decode('utf-8')
    if not imdb_id:
        imdb_id = xbmc.getInfoLabel("ListItem.Property(IMDBNumber)").decode('utf-8')
    if imdb_id and not imdb_id.startswith("tt"):
        imdb_id = ""
    if not imdb_id:
        year = xbmc.getInfoLabel("ListItem.Year").decode('utf-8')
        title = xbmc.getInfoLabel("ListItem.Title").decode('utf-8')
        if content_type in ["episodes", "seasons"]:
            title = xbmc.getInfoLabel("ListItem.TvShowTitle").decode('utf-8')
        if title:
            imdb_id = artutils.get_omdb_info("", title, year, content_type).get("imdbnumber", "")
        if not imdb_id:
            return title
    return imdb_id

# Kodi contextmenu item to configure the artwork
if __name__ == '__main__':
    xbmc.executebuiltin("ActivateWindow(busydialog)")
    ARTUTILS = ArtUtils()
    WIN = xbmcgui.Window(10000)
    imdb_id = get_imdb_id(WIN, ARTUTILS)
    if imdb_id:
        WIN.setProperty("SkinHelper.Artwork.ManualLookup", "busy")
        artwork = ARTUTILS.get_animated_artwork(imdb_id, ignore_cache=True, manual_select=True)
    xbmc.executebuiltin("Container.Refresh")
    xbmc.executebuiltin("Window.Close(busydialog)")
    WIN.clearProperty("SkinHelper.Artwork.ManualLookup")
    del WIN
    ARTUTILS.close()
