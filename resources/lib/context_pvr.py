# -*- coding: utf-8 -*-

'''
    script.skin.helper.service
    Contextmenu for Pvr art
'''

import os, sys
import xbmc
import xbmcgui
from metadatautils import MetadataUtils
from utils import try_decode

# pylint: disable-msg=invalid-constant-name

# Kodi contextmenu item to configure pvr artwork
if __name__ == '__main__':

    ##### PVR Artwork ########
    win = xbmcgui.Window(10000)
    win.setProperty("SkinHelper.Artwork.ManualLookup", "busy")
    title = try_decode(xbmc.getInfoLabel("ListItem.Title"))
    if not title:
        title = try_decode(xbmc.getInfoLabel("ListItem.Label"))
    channel = try_decode(xbmc.getInfoLabel("ListItem.ChannelName"))
    if not channel:
        channel = try_decode(xbmc.getInfoLabel("ListItem.Label"))
    genre = try_decode(xbmc.getInfoLabel("ListItem.Genre"))
    metadatautils = MetadataUtils()
    metadatautils.pvr_artwork_options(title, channel, genre)
    win.clearProperty("SkinHelper.Artwork.ManualLookup")
    metadatautils.close()
    del win
