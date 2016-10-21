#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading, thread
from utils import log_msg, log_exception, get_current_content_type, get_kodi_json, try_encode, process_method_on_list
from simplecache import SimpleCache
from artutils import ArtUtils
import xbmc, xbmcgui, xbmcaddon
import time
from datetime import timedelta


class PlayerMonitor(xbmc.Player):
    '''monitor Kodi player to set window properties for currently playing item'''
    all_win_props = []
    content_type = ""
    
    def __init__(self):
        '''Initialization'''
        self.win = xbmcgui.Window(10000)
    
    def onPlayBackStarted(self):
        '''Will be called when xbmc starts playing a file'''
        log_msg("Playback started !")
        
    def onPlayBackStopped(self):
        '''Will be called when user stops xbmc playing a file'''
        log_msg("Playback stopped !")
        
        
    