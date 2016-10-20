# -*- coding: utf-8 -*-
import xbmc
from artutils import AnimatedArt
from utils import WINDOW

def get_imdb_id():
    content_type = WINDOW.getProperty("contenttype")
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
        if year and title:
            from artutils import Omdb
            imdb_id = Omdb().get_details_by_title(title,year,content_type).get("imdbnumber","")
        if not imdb_id:
            return title
    return imdb_id

#Kodi contextmenu item to configure the artwork
if __name__ == '__main__':

    animated_art = AnimatedArt()
    imdb_id = get_imdb_id()
    if imdb_id:
        WINDOW.clearProperty("SkinHelper.AnimatedPoster")
        WINDOW.clearProperty("SkinHelper.AnimatedFanart")
        WINDOW.clearProperty("SkinHelper.ListItem.AnimatedPoster")
        WINDOW.clearProperty("SkinHelper.ListItem.AnimatedFanart")
        artwork = animated_art.get_animated_artwork(imdb_id,True)
    xbmc.executebuiltin("Container.Refresh")