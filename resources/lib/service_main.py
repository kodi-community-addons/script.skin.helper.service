#!/usr/bin/python
# -*- coding: utf-8 -*-

from utils import log_msg, ADDON_VERSION, log_exception
from skinsettings import SkinSettings
from backgrounds_updater import BackgroundsUpdater
from listitem_monitor import ListItemMonitor
from kodi_monitor import KodiMonitor
from player_monitor import PlayerMonitor
from webservice import WebService
import xbmc, xbmcaddon
import time

class MainService:
    '''Service that holds the threads providing info to Kodi skins'''
    last_skin = ""

    def __init__(self):
        '''our main background service running the various threads'''
        self.win = xbmcgui.Window(10000)
        self.kodi_monitor = KodiMonitor()
        self.player_monitor = PlayerMonitor()
        self.win.clearProperty("SkinHelperShutdownRequested")
        listitem_monitor = ListItemMonitor()
        backgrounds_updater = BackgroundsUpdater()
        webservice = WebService()
        widget_task_interval = 520

        #start the extra threads
        listitem_monitor.start()
        backgrounds_updater.start()
        webservice.start()
        
        log_msg('skin helper service version %s started' % ADDON_VERSION, xbmc.LOGNOTICE)

        #run as service, check skin every 10 seconds and keep the other threads alive
        while not (self.kodi_monitor.abortRequested()):
            
            #check skin version info
            self.check_skin_version()
            
            #set generic widget reload
            widget_task_interval += 10
            if widget_task_interval >= 600:
                self.win.setProperty("widgetreload2", time.strftime("%Y%m%d%H%M%S", time.gmtime()))
                widget_task_interval = 0
            
            #sleep for 10 seconds
            self.kodi_monitor.waitForAbort(10)

        #Abort was requested while waiting. We should exit
        self.win.setProperty("SkinHelperShutdownRequested","shutdown")
        log_msg('Shutdown requested !',xbmc.LOGNOTICE)
        #stop the extra threads
        backgrounds_updater.stop()
        listitem_monitor.stop()
        webservice.stop()
        
        
    def __del__(self):
        '''Cleanup Kodi Cpython instances'''
        del self.win
        del self.kodi_kodi_monitor
        del self.player_monitor
        log_msg('skin helper service version %s stopped' % ADDON_VERSION, xbmc.LOGNOTICE)
        
    def check_skin_version(self):
        '''check if skin changed'''
        try:
            skin = xbmc.getSkinDir()
            skin_addon = xbmcaddon.Addon(id=skin)
            skin_label = skin_addon.getAddonInfo('name').decode("utf-8")
            skin_version = skin_addon.getAddonInfo('version').decode("utf-8")
            del skin_addon
            if self.last_skin != skin_label + skin_version:
                #auto correct skin settings
                self.last_skin = skin_label + skin_version
                self.win.setProperty("SkinHelper.skinTitle", "%s - %s: %s" 
                    %(skin_label, xbmc.getLocalizedString(19114),skin_version))
                self.win.setProperty("SkinHelper.skin_version", "%s: %s" 
                    %(xbmc.getLocalizedString(19114),skin_version))
                self.win.setProperty("SkinHelper.Version", ADDON_VERSION.replace(".",""))
                SkinSettings().correct_skin_settings()
        except Exception as exc:
            log_exception(__name__,exc)
