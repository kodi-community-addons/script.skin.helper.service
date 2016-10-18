#!/usr/bin/python
# -*- coding: utf-8 -*-

from resources.lib.utils import WINDOW, log_msg, ADDON_VERSION, log_exception
import resources.lib.MainModule as mainmodule
from resources.lib.BackgroundsUpdater import BackgroundsUpdater
from resources.lib.listitem_monitor import ListItemMonitor
from resources.lib.kodi_monitor import KodiMonitor
from resources.lib.WebService import WebService
import xbmc, xbmcaddon
import time

class Main:

    lastSkin = ""

    def checkSkinVersion(self):
        try:
            skin = xbmc.getSkinDir()
            skinLabel = xbmcaddon.Addon(id=skin).getAddonInfo('name').decode("utf-8")
            skinVersion = xbmcaddon.Addon(id=skin).getAddonInfo('version').decode("utf-8")
            if self.lastSkin != skinLabel+skinVersion:
                #auto correct skin settings
                self.lastSkin = skinLabel+skinVersion
                WINDOW.setProperty("SkinHelper.skinTitle",skinLabel + " - " + xbmc.getLocalizedString(19114) + ": " + skinVersion)
                WINDOW.setProperty("SkinHelper.skinVersion",xbmc.getLocalizedString(19114) + ": " + skinVersion)
                WINDOW.setProperty("SkinHelper.Version",ADDON_VERSION.replace(".",""))
                mainmodule.correctSkinSettings()
        except Exception as exc:
            log_exception(__name__,exc)

    def __init__(self):

        WINDOW.clearProperty("SkinHelperShutdownRequested")
        monitor = KodiMonitor()
        listItemMonitor = ListItemMonitor()
        backgroundsUpdater = BackgroundsUpdater()
        webService = WebService()
        widget_task_interval = 520

        #start the extra threads
        listItemMonitor.start()
        backgroundsUpdater.start()
        webService.start()

        #run as service, check skin every 10 seconds and keep the other threads alive
        while not (monitor.abortRequested()):
            self.checkSkinVersion()
            #set generic widget reload
            widget_task_interval += 10
            if widget_task_interval >= 600:
                WINDOW.setProperty("widgetreload2", time.strftime("%Y%m%d%H%M%S", time.gmtime()))
                widget_task_interval = 0
            monitor.waitForAbort(10)

        #Abort was requested while waiting. We should exit
        WINDOW.setProperty("SkinHelperShutdownRequested","shutdown")
        log_msg('Shutdown requested !',xbmc.LOGNOTICE)
        #stop the extra threads
        backgroundsUpdater.stop()
        listItemMonitor.stop()
        webService.stop()

log_msg('skin helper service version %s started' % ADDON_VERSION,xbmc.LOGNOTICE)
Main()
log_msg('skin helper service version %s stopped' % ADDON_VERSION,xbmc.LOGNOTICE)

