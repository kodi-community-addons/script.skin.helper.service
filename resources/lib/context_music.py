# -*- coding: utf-8 -*-

'''
    script.skin.helper.service
    Contextmenu for Music art
'''

import xbmc, xbmcgui
from artutils import ArtUtils

#Kodi contextmenu item to configure music artwork
if __name__ == '__main__':

    ##### Music Artwork ########
    win = xbmcgui.Window(10000)
    win.setProperty("SkinHelper.Artwork.ManualLookup", "busy")
    xbmc.executebuiltin("ActivateWindow(busydialog)")
    track = xbmc.getInfoLabel("ListItem.Title").decode('utf-8')
    album = xbmc.getInfoLabel("ListItem.Album").decode('utf-8')
    artist = xbmc.getInfoLabel("ListItem.AlbumArtist").decode('utf-8')
    if not artist:
        artist = xbmc.getInfoLabel("ListItem.Artist").decode('utf-8')
    disc = xbmc.getInfoLabel("ListItem.DiscNumber").decode('utf-8')
    ArtUtils().music_artwork_options(artist, album, track, disc)
    xbmc.executebuiltin("Dialog.Close(busydialog)")
    win.clearProperty("SkinHelper.Artwork.ManualLookup")
    del win
