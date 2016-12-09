# -*- coding: utf-8 -*-

'''
    script.skin.helper.service
    Contextmenu for Music art
'''

import xbmc
import xbmcgui
from artutils import ArtUtils

# Kodi contextmenu item to configure music artwork
if __name__ == '__main__':

    ##### Music Artwork ########
    win = xbmcgui.Window(10000)
    artutils = ArtUtils()
    win.setProperty("SkinHelper.Artwork.ManualLookup", "busy")
    track = xbmc.getInfoLabel("ListItem.Title").decode('utf-8')
    album = xbmc.getInfoLabel("ListItem.Album").decode('utf-8')
    artist = xbmc.getInfoLabel("ListItem.Artist").decode('utf-8')
    disc = xbmc.getInfoLabel("ListItem.DiscNumber").decode('utf-8')
    artutils.music_artwork_options(artist, album, track, disc)
    win.clearProperty("SkinHelper.Artwork.ManualLookup")
    artutils.close()
    del win
    del artutils
