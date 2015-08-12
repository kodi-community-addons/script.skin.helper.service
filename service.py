#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmc
from resources.lib.Utils import *
from resources.lib.BackgroundsUpdater import BackgroundsUpdater
from resources.lib.LibraryMonitor import LibraryMonitor
from resources.lib.LibraryMonitor import Kodi_Monitor
from resources.lib.HomeMonitor import HomeMonitor

class Main:
    
    def __init__(self):
        
        KodiMonitor = Kodi_Monitor()
        homeMonitor = HomeMonitor()
        backgroundsUpdater = BackgroundsUpdater()
        libraryMonitor = LibraryMonitor()
        lastSkin = None
                   
        #start the extra threads
        homeMonitor.start()
        backgroundsUpdater.start()
        libraryMonitor.start()
        
        while not (KodiMonitor.abortRequested() or xbmc.abortRequested):
            
            #set skin info
            if lastSkin != xbmc.getSkinDir():
                setSkinVersion()
            
            xbmc.sleep(150)
        else:
            # Abort was requested while waiting. We should exit
            xbmc.log('SKIN HELPER SERVICE --> shutdown requested !')
            #stop the extra threads
            backgroundsUpdater.stop()
            libraryMonitor.stop()
            homeMonitor.stop()
                              

xbmc.log('skin helper service version %s started' % ADDON_VERSION)
Main()
xbmc.log('skin helper service version %s stopped' % ADDON_VERSION)
