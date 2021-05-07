#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    script.skin.helper.service
    Helper service and scripts for Kodi skins
    infodialog.py
    Wrapper around the videoinfodialog which can be used for widgets for example
    only used for Kodi Jarvis because as of Kodi Krypton this is handled by Kodi natively
'''

import os, sys
import xbmc
import xbmcgui
from metadatautils import MetadataUtils
from resources.lib.utils import get_current_content_type, getCondVisibility, try_decode


CANCEL_DIALOG = (9, 10, 92, 216, 247, 257, 275, 61467, 61448, )
ACTION_SHOW_INFO = (11, )


class DialogVideoInfo(xbmcgui.WindowXMLDialog):
    '''Wrapper around the videoinfodialog'''
    result = None

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self)
        self.listitem = kwargs.get("listitem")

    def onInit(self):
        '''triggered when the dialog is drawn'''
        if self.listitem:
            self.clearList()
            mutils = MetadataUtils()
            if isinstance(self.listitem, dict):
                self.listitem = mutils.kodidb.prepare_listitem(self.listitem)
                self.listitem = mutils.kodidb.create_listitem(self.listitem, False)
            del mutils
            self.addItem(self.listitem)

        # disable some controls if existing
        disable_controls = [9, 7, 101, 6]
        for item in disable_controls:
            try:
                self.getControl(item).setVisible(False)
            except Exception:
                pass

        # enable some controls if existing
        disable_controls = [351, 352]
        for item in disable_controls:
            try:
                self.getControl(item).setVisible(True)
                self.getControl(item).setEnabled(True)
            except Exception:
                pass

    def onClick(self, controlid):
        '''triggers if one of the controls is clicked'''
        if controlid == 9999:
            # play button
            self.result = True
            self.close()
            if "videodb:" in self.listitem.getfilename():
                xbmc.executebuiltin('ReplaceWindow(Videos,"%s")' % self.listitem.getfilename())
            else:
                xbmc.executebuiltin('PlayMedia("%s")' % self.listitem.getfilename())
        if controlid == 103:
            # trailer button
            pass

    def onAction(self, action):
        '''triggers on certain actions like user navigating'''
        if action.getId() in CANCEL_DIALOG:
            self.close()
        if action.getId() in ACTION_SHOW_INFO:
            self.close()


def get_cur_listitem(cont_prefix):
    '''gets the current selected listitem details'''
    if getCondVisibility("Window.IsActive(busydialog)"):
        xbmc.executebuiltin("Dialog.Close(busydialog)")
        xbmc.sleep(500)
    dbid = try_decode(xbmc.getInfoLabel("%sListItem.DBID" % cont_prefix))
    if not dbid or dbid == "-1":
        dbid = try_decode(xbmc.getInfoLabel("%sListItem.Property(DBID)" % cont_prefix))
        if dbid == "-1":
            dbid = ""
    dbtype = try_decode(xbmc.getInfoLabel("%sListItem.DBTYPE" % cont_prefix))
    if not dbtype:
        dbtype = try_decode(xbmc.getInfoLabel("%sListItem.Property(DBTYPE)" % cont_prefix))
    if not dbtype:
        dbtype = get_current_content_type(cont_prefix)
    return (dbid, dbtype)


def get_cont_prefix():
    '''gets the container prefix if we're looking at a widget container'''
    widget_container = xbmc.getInfoLabel("Window(Home).Property(SkinHelper.WidgetContainer)")
    if widget_container:
        cont_prefix = "Container(%s)." % widget_container
    else:
        cont_prefix = ""
    return cont_prefix


def show_infodialog(dbid="", media_type=""):
    '''shows the special info dialog for this media'''
    cont_prefix = get_cont_prefix()
    metadatautils = MetadataUtils()
    item_details = {}

    # if dbid is provided we prefer that info else we try to locate the dbid and dbtype
    if not (dbid and media_type):
        dbid, media_type = get_cur_listitem(cont_prefix)

    if media_type.endswith("s"):
        media_type = media_type[:-1]

    # get basic details from kodi db if we have a valid dbid and dbtype
    if dbid and media_type:
        if hasattr(metadatautils.kodidb.__class__, media_type):
            item_details = getattr(metadatautils.kodidb, media_type)(dbid)

    # only proceed if we have a media_type
    if media_type:
        title = try_decode(xbmc.getInfoLabel("%sListItem.Title" % cont_prefix))
        # music content
        if media_type in ["album", "artist", "song"]:
            artist = try_decode(xbmc.getInfoLabel("%sListItem.AlbumArtist" % cont_prefix))
            if not artist:
                artist = try_decode(xbmc.getInfoLabel("%sListItem.Artist" % cont_prefix))
            album = try_decode(xbmc.getInfoLabel("%sListItem.Album" % cont_prefix))
            disc = try_decode(xbmc.getInfoLabel("%sListItem.DiscNumber" % cont_prefix))
            if artist:
                item_details = metadatautils.extend_dict(item_details, metadatautils.get_music_artwork(artist, album, title, disc))
        # movieset
        elif media_type == "movieset" and dbid:
            item_details = metadatautils.extend_dict(item_details, metadatautils.get_moviesetdetails(dbid))
        # pvr item
        elif media_type in ["tvchannel", "tvrecording", "channel", "recording"]:
            channel = try_decode(xbmc.getInfoLabel("%sListItem.ChannelName" % cont_prefix))
            genre = xbmc.getInfoLabel("%sListItem.Genre" % cont_prefix)
            item_details["type"] = media_type
            item_details = metadatautils.extend_dict(item_details, metadatautils.get_pvr_artwork(title, channel, genre))

    metadatautils.close()
    # proceed with infodialog if we have details
    if item_details:
        widget_container = xbmc.getInfoLabel("Window(Home).Property(SkinHelper.WidgetContainer)")
        win = DialogVideoInfo("DialogVideoInfo.xml", "", listitem=item_details)
        xbmc.executebuiltin("SetProperty(SkinHelper.WidgetContainer,50,Home)")
        win.doModal()
        xbmc.executebuiltin("SetProperty(SkinHelper.WidgetContainer,%s,Home)" % widget_container)
        del win
