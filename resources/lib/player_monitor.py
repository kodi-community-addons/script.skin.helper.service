#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading, thread
from utils import log_msg, log_exception, get_current_content_type, kodi_json, try_encode
import xbmc
import time
from datetime import timedelta


class PlayerMonitor(xbmc.Player):
    '''monitor Kodi player to set window properties for currently playing item'''
    all_win_props = []
    content_type = ""
    
    def __init__(self, *args, **kwargs):
        '''Initialization'''
        self.cache = kwargs.get("cache")
        self.artutils = kwargs.get("artutils")
        self.win = kwargs.get("win")
        
    
    def onPlayBackStarted(self):
        '''Will be called when xbmc starts playing a file'''
        log_msg("Playback started !")
        
    def onPlayBackStopped(self):
        '''Will be called when user stops xbmc playing a file'''
        log_msg("Playback stopped !")
        
        
    def reset_player_props(self):
        #reset all window props provided by the script...
        for prop in self.all_player_win_props:
            self.win.clearProperty(try_encode(prop))
        self.all_player_win_props = []

    def set_player_prop(self,key,value):
        self.all_player_win_props.append(key)
        self.win.setProperty(try_encode(key),try_encode(value))
            
    def setMusicPlayerDetails(self):
        artwork = {}
        artist = ""
        title = ""
        album = ""
        #get the playing item from the player...
        json_result = kodi_json('Player.GetActivePlayers', '{}')
        for item in json_result:
            if item.get("type","") == "audio":
                json_result = kodi_json('Player.GetItem', '{ "playerid": %d, "properties": [ "title","albumid","artist","album","displayartist" ] }' %item.get("playerid"))
                if json_result.get("title"):
                    if json_result.get("artist"):
                        artist = json_result.get("artist")
                        if isinstance(artist,list): artist = artist[0]
                        title = json_result.get("title")
                        album = json_result.get("album").split(" (")[0]
                    else:
                        if not artist:
                            #fix for internet streams
                            splitchar = None
                            if " - " in json_result.get("title"): splitchar = " - "
                            elif "- " in json_result.get("title"): splitchar = "- "
                            elif " -" in json_result.get("title"): splitchar = " -"
                            elif "-" in json_result.get("title"): splitchar = "-"
                            if splitchar:
                                artist = json_result.get("title").split(splitchar)[0]
                                title = json_result.get("title").split(splitchar)[1]
                    log_msg("setMusicPlayerDetails: " + repr(json_result))

        artwork = artutils.getMusicArtwork(artist,album,title)

        #merge comment from id3 tag with album info
        if artwork.get("info") and xbmc.getInfoLabel("MusicPlayer.Comment"):
            artwork["info"] = normalize_string(xbmc.getInfoLabel("MusicPlayer.Comment")).replace('\n', ' ').replace('\r', '').split(" a href")[0] + "  -  " + artwork["info"]

        #set properties
        for key, value in artwork.iteritems():
            self.set_player_prop(u"SkinHelper.Player.Music.%s" %key, value)


        
        
        player_title = ""
        player_file = ""
        last_playeritem = ""
        player_item = ""
        
    #if xbmc.getCondVisibility("Player.HasAudio"):
                # #set window props for music player
                # try:
                    # player_title = xbmc.getInfoLabel("Player.Title").decode('utf-8')
                    # player_file = xbmc.getInfoLabel("Player.Filenameandpath").decode('utf-8')
                    # player_item = player_title + player_file
                    # #only perform actions when the listitem has actually changed
                    # if player_item and player_item != last_playeritem:
                        # #clear all window props first
                        # self.reset_player_props()
                        # self.setMusicPlayerDetails()
                        # last_playeritem = player_item
                # except Exception as exc:
                    # log_exception(__name__,exc)

            # elif last_playeritem:
                # #cleanup remaining window props
                # self.reset_player_props()
                # player_item = ""
                # last_playeritem = ""
        
        
    