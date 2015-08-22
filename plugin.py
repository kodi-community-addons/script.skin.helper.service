#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import xbmc
import xbmcplugin
import xbmcgui

from resources.lib.Utils import *
from resources.lib.PluginContent import *

class Main:
    
    def __init__(self):
        
        logMsg('started loading pluginentry',0)
        
        #get params
        action = None
        limit = None
        path = None
        params = urlparse.parse_qs(sys.argv[2][1:])
        logMsg("Parameter string: %s" % sys.argv[2],0)

        try:
            action = params['action'][0].upper()
            limit = params['limit'][0]
        except:
            pass
        
        try:
            path = params['path'][0]
        except:
            pass
        
        if action:           
            if action == "NEXTEPISODES":
                getNextEpisodes(limit)
            elif action == "RECOMMENDEDMOVIES":
                getRecommendedMovies(limit)
            elif action == "RECOMMENDEDMEDIA":
                getRecommendedMedia(limit,ondeckContent=False,recommendedContent=True)
            elif action == "RECENTMEDIA":
                getRecentMedia(limit)
            elif action == "SIMILARMOVIES":
                getSimilarMovies(limit)
            elif action == "INPROGRESSMEDIA":
                getRecommendedMedia(limit,ondeckContent=True,recommendedContent=False) 
            elif action == "INPROGRESSANDRECOMMENDEDMEDIA":
                getRecommendedMedia(limit,ondeckContent=True,recommendedContent=True)
            elif action == "FAVOURITEMEDIA":
                getFavouriteMedia(limit)
            elif action == "PVRCHANNELSSMART":
                getPVRChannels(limit) 
            elif action == "FAVOURITES":
                getFavourites(limit)
            elif action == "SMARTSHORTCUTS":
                getSmartShortcuts(path)
            elif action == "BACKGROUNDS":
                getBackgrounds()
            elif action == "WIDGETS":
                getWidgets(path)
            elif action == "GETTHUMB":
                getThumb(path)
            elif action == "WIDGETS":
                getWidgets(path)
            elif action == "LAUNCHPVR":
                if path:
                    xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Player.Open", "params": { "item": {"channelid": ' + path + '} } }')
            elif action == "LAUNCH":
                if path:
                    xbmc.executebuiltin(path)
                    
            
        else:
            #do plugin main listing...
            doMainListing()

if (__name__ == "__main__"):
    Main()
logMsg('finished loading pluginentry')
