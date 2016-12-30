#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    script.skin.helper.service
    Helper service and scripts for Kodi skins
    main_service.py
    Background service running the various threads
'''

from utils import log_msg, ADDON_ID, log_exception
from skinsettings import SkinSettings
from listitem_monitor import ListItemMonitor
from kodi_monitor import KodiMonitor
from webservice import WebService
from artutils import ArtUtils
import xbmc
import xbmcaddon
import xbmcgui
import time


class MainService:
    '''our main background service running the various threads'''
    last_skin = ""

    def __init__(self):
        self.win = xbmcgui.Window(10000)
        self.addon = xbmcaddon.Addon(ADDON_ID)
        self.artutils = ArtUtils()
        self.addonname = self.addon.getAddonInfo('name').decode("utf-8")
        self.addonversion = self.addon.getAddonInfo('version').decode("utf-8")
        self.kodimonitor = KodiMonitor(artutils=self.artutils, win=self.win)
        listitem_monitor = ListItemMonitor(
            artutils=self.artutils, win=self.win, monitor=self.kodimonitor)
        webservice = WebService(artutils=self.artutils)
        widget_task_interval = 520

        # start the extra threads
        listitem_monitor.start()
        webservice.start()
        self.win.clearProperty("SkinHelperShutdownRequested")
        log_msg('%s version %s started' % (self.addonname, self.addonversion), xbmc.LOGNOTICE)

        # run as service, check skin every 10 seconds and keep the other threads alive
        while not self.kodimonitor.abortRequested():

            # check skin version info
            self.check_skin_version()

            # set generic widget reload
            widget_task_interval += 10
            if widget_task_interval >= 300:
                self.win.setProperty("widgetreload2", time.strftime("%Y%m%d%H%M%S", time.gmtime()))
                widget_task_interval = 0

            # sleep for 10 seconds
            self.kodimonitor.waitForAbort(10)

        # Abort was requested while waiting. We should exit
        self.win.setProperty("SkinHelperShutdownRequested", "shutdown")
        log_msg('Shutdown requested !', xbmc.LOGNOTICE)
        # stop the extra threads
        listitem_monitor.stop()
        webservice.stop()

        # cleanup objects
        self.close()

    def close(self):
        '''Cleanup Kodi Cpython instances'''
        self.artutils.close()
        del self.win
        del self.kodimonitor
        del self.artutils
        log_msg('%s version %s stopped' % (self.addonname, self.addonversion), xbmc.LOGNOTICE)

    def check_skin_version(self):
        '''check if skin changed'''
        try:
            skin = xbmc.getSkinDir()
            skin_addon = xbmcaddon.Addon(id=skin)
            skin_label = skin_addon.getAddonInfo('name').decode("utf-8")
            skin_version = skin_addon.getAddonInfo('version').decode("utf-8")
            del skin_addon
            if self.last_skin != skin_label + skin_version:
                # auto correct skin settings
                self.last_skin = skin_label + skin_version
                self.win.setProperty("SkinHelper.skinTitle", "%s - %s: %s"
                                     % (skin_label, xbmc.getLocalizedString(19114), skin_version))
                self.win.setProperty("SkinHelper.skin_version", "%s: %s"
                                     % (xbmc.getLocalizedString(19114), skin_version))
                self.win.setProperty("SkinHelper.Version", self.addonversion.replace(".", ""))
                SkinSettings().correct_skin_settings()
        except Exception as exc:
            log_exception(__name__, exc)
