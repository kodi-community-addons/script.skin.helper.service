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
        params = urlparse.parse_qs(sys.argv[2][1:])
        logMsg("Parameter string: %s" % sys.argv[2],0)
        
        if params:        
            path=params.get("path",None)
            if path: path = path[0]
            limit=params.get("limit",None)
            if limit: limit = int(limit[0])
            action=params.get("action",25)
            if action: action = action[0].upper()
        
            if action:           
                if action == "NEXTEPISODES":
                    getNextEpisodes(limit)
                elif action == "RECOMMENDEDMOVIES":
                    getRecommendedMovies(limit)
                elif action == "RECOMMENDEDMEDIA":
                    getRecommendedMedia(limit)
                elif action == "RECENTMEDIA":
                    getRecentMedia(limit)
                elif action == "SIMILARMOVIES":
                    getSimilarMovies(limit)
                elif action == "INPROGRESSMEDIA":
                    getInProgressMedia(limit) 
                elif action == "INPROGRESSANDRECOMMENDEDMEDIA":
                    getInProgressAndRecommendedMedia(limit)
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
                elif action == "GETCAST":
                    movie=params.get("movie",None)
                    if movie: movie = movie[0]
                    tvshow=params.get("tvshow",None)
                    if tvshow: tvshow = tvshow[0]
                    movieset=params.get("movieset",None)
                    if movieset: movieset = movieset[0]
                    getCast(movie,tvshow,movieset)
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
