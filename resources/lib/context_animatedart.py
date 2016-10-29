# -*- coding: utf-8 -*-
import xbmc, xbmcgui
from artutils import ArtUtils

def get_imdb_id(win):
    content_type = win.getProperty("contenttype")
    imdb_id = xbmc.getInfoLabel("ListItem.IMDBNumber").decode('utf-8')
    if not imdb_id: 
        imdb_id = xbmc.getInfoLabel("ListItem.Property(IMDBNumber)").decode('utf-8')
    if imdb_id and not imdb_id.startswith("tt"):
        imdb_id = ""
    if not imdb_id:
        year = xbmc.getInfoLabel("ListItem.Year").decode('utf-8')
        title = xbmc.getInfoLabel("ListItem.Title").decode('utf-8')
        if content_type in ["episodes","seasons"]:
            title = xbmc.getInfoLabel("ListItem.TvShowTitle").decode('utf-8')
        if title:
            imdb_id = ArtUtils().get_omdb_info("", title,year, content_type).get("imdbnumber","")
        if not imdb_id:
            return title
    return imdb_id

#Kodi contextmenu item to configure the artwork
if __name__ == '__main__':
    xbmc.executebuiltin("ActivateWindow(busydialog)")
    artutils = ArtUtils()
    win = xbmcgui.Window(10000)
    imdb_id = get_imdb_id(win)
    if imdb_id:
        win.setProperty("SkinHelper.Artwork.ManualLookup", "busy")
        artwork = artutils.get_animated_artwork(imdb_id, ignore_cache=True, manual_select=True)
    xbmc.executebuiltin("Container.Refresh")
    xbmc.executebuiltin("Dialog.Close(busydialog)")
    win.clearProperty("SkinHelper.Artwork.ManualLookup")
    del win