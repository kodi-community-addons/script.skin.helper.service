#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmc, xbmcplugin, xbmcgui
from simplecache import SimpleCache
from utils import log_msg, try_encode, normalize_string, timedelta, getCleanImage, KODI_VERSION, process_method_on_list,WINDOW,log_exception
from artutils import KodiDb, Tmdb
import urlparse, urllib
import sys

class PluginContent:
    
    params = {}
    
    def __init__(self):
    
        self.cache = SimpleCache()
        self.kodi_db = KodiDb()
        
        try:
            self.params = dict(urlparse.parse_qsl(sys.argv[2].replace('?','').lower().decode("utf-8")))
            log_msg("plugin called with parameters: %s" %self.params)
            action = self.params.get("action","")
            actions = ["launchpvr","playrecording","launch","playalbum","smartshortcuts","backgrounds","widgets","getthumb","extrafanart","getcast","getcastmedia","alphabet","alphabetletter"]
            
            if WINDOW.getProperty("SkinHelperShutdownRequested"):
                #do not proceed if kodi wants to exit
                log_msg("%s --> Not forfilling request: Kodi is exiting" %__name__ ,xbmc.LOGWARNING)
                xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
            if action in actions:
                #launch module for action
                getattr(self, action)()
            elif action:
                #legacy action called, start redirect...
                newaddon = "script.skin.helper.widgets"
                log_msg("Deprecated method: %s. Please call %s directly - This automatic redirect will be removed in the future" %(action,newaddon), xbmc.LOGWARNING )
                paramstring = ""
                for key, value in self.params.iteritems():
                    paramstring += ",%s=%s" %(key,value)
                if xbmc.getCondVisibility("System.HasAddon(%s)" %newaddon):
                    #TEMP: for legacy reasons only - to be removed in the near future
                    all_items = self.kodi_db.files("plugin://script.skin.helper.widgets%s"%sys.argv[2])
                    all_items = process_method_on_list(self.kodi_db.prepare_listitem,all_items)
                    all_items = process_method_on_list(self.kodi_db.create_listitem,all_items)
                    xbmcplugin.addDirectoryItems(int(sys.argv[1]), all_items, len(all_items))
                    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
                else:
                    #trigger install of the addon
                    if KODI_VERSION >= 17:
                        xbmc.executebuiltin("InstallAddon(%s)" %newaddon)
                    else:
                        xbmc.executebuiltin("RunPlugin(plugin://%s)" %newaddon)
            else:
                #invalid action
                xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
            
        except Exception as exc:
            log_exception(__name__,exc)
            xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
    
    def launch_pvr(self):
        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=False, listitem=xbmcgui.ListItem())
        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "id": 0, "method": "Player.Open", "params": { "item": {"channelid": %d} } }' %int(self.params["path"]))
        
    def playrecording(self):
        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=False, listitem=xbmcgui.ListItem())
        #retrieve the recording and play as listitem to get resume working
        json_result = kodi_db.tvrecording(self.params["path"])
        if json_result:
            xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "recordingid": %d } }, "id": 1 }' % int(self.params["path"]))
            if json_result["resume"].get("position"):
                for i in range(25):
                    if xbmc.getCondVisibility("Player.HasVideo"):
                        break
                    xbmc.sleep(250)
                xbmc.Player().seekTime(json_result["resume"].get("position"))
    
    def launch(self):
        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=False, listitem=xbmcgui.ListItem())
        xbmc.sleep(150)
        xbmc.executebuiltin(sys.argv[2].split("&path=")[1])
    
    def playalbum(self):
        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=False, listitem=xbmcgui.ListItem())
        xbmc.sleep(150)
        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "albumid": %d } }, "id": 1 }' % int(self.params["path"]))
    
    def smartshortcuts(self):
        import skinshortcuts
        skinshortcuts.getSmartShortcuts(self.params["path"])
    
    def backgrounds(self):
        import skinshortcuts
        skinshortcuts.getBackgrounds()
    
    def widgets(self):
        import skinshortcuts
        skinshortcuts.getWidgets(self.params["path"])
    
    def extrafanart(self):
        extrafanarts = []
        items_path = self.params["path"]
        cache_str = "getExtraFanArt.%s"%items_path
        cachedata = self.cache.get(cache_str)
        if cachedata:
            extrafanarts = cachedata
        else:
            if items_path.startswith("EFA_FROMWINDOWPROP_"):
                #get extrafanarts from window property
                extrafanarts = eval(WINDOW.getProperty(try_encode(items_path)).decode("utf-8"))
            elif items_path.startswith("EFA_FROMCACHE_"):
                #get extrafanarts from cache system by getting the cache for given cachestr
                items_path = items_path.split("_")[-1]
                cache = self.cache.get(items_path)
                if cache and "extrafanarts" in cache:
                    extrafanarts = cache["extrafanarts"]
                    if not isinstance(extrafanarts, list):
                        extrafanarts = eval(extrafanarts)
            else:
                #LEGACY: get extrafanarts by passing an artwork cache xml file
                if not xbmcvfs.exists(items_path.encode("utf-8")):
                    filepart = items_path.split("/")[-1]
                    items_path = items_path.replace(filepart,"") + normalize_string(filepart)
                    artwork = artutils.getArtworkFromCacheFile(items_path)
                    if artwork.get("extrafanarts"):
                        extrafanarts = eval( artwork.get("extrafanarts") )
            #store in cache
            self.cache.set(cache_str,extrafanarts,timedelta(days=2))

        #process extrafanarts
        for item in extrafanarts:
            li = xbmcgui.ListItem(item, items_path=item)
            li.setProperty('mimetype', 'image/jpeg')
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=item, listitem=li)
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

    def getcastmedia(self):
        name = self.params.get("name")
        if name:
            #use db counts as simple checksum
            cache_checksum = len( self.kodi_db.get_db('VideoLibrary.GetMovies',None,None,[],None,"movies") )
            cache_checksum += len( self.kodi_db.get_db('VideoLibrary.GetTvShows',None,None,[],None,"tvshows") )
            cache_str = "CastMedia.%s"%name
            cachedata = self.cache.get(cache_str,checksum=cache_checksum)
            if cachedata:
                all_items = cachedata
            else:
                all_items = []
                filters = [{"operator":"contains", "field":"actor","value":name}]
                movies = self.kodi_db.get_db('VideoLibrary.GetMovies',None,filters,self.kodi_db.FIELDS_MOVIES,None,"movies")
                tvshows = self.kodi_db.get_db('VideoLibrary.GetTvShows',None,filters,self.kodi_db.FIELDS_TVSHOWS,None,"tvshows")
                for item in movies:
                    url = "RunScript(script.skin.helper.service,action=showinfo,movieid=%s)" %item["movieid"]
                    item["file"] = "plugin://script.skin.helper.service/?action=launch&path=" + url
                    all_items.append(item)
                tvshows = self.kodi_db.get_db('VideoLibrary.GetTvShows',None,filters,self.kodi_db.FIELDS_TVSHOWS,None,"tvshows")
                for item in tvshows:
                    url = "RunScript(script.skin.helper.service,action=showinfo,tvshowid=%s)" %item["tvshowid"]
                    item["file"] = "plugin://script.skin.helper.service/?action=launch&path=" + url
                    all_items.append(item)
                all_items = process_method_on_list(self.kodi_db.prepare_listitem,all_items)
                self.cache.set(cache_str,all_items,checksum=cache_checksum)
            #display the listing
            all_items = process_method_on_list(self.kodi_db.create_listitem,all_items)
            xbmcplugin.addDirectoryItems(int(sys.argv[1]), all_items, len(all_items))
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

    def getcast(self):
        db_id = None
        all_cast = []
        all_cast_names = list()
        cache_str = ""
        download_thumbs = self.params.get("downloadthumbs","") == "true"
        tmdb = Tmdb()
        movie = self.params.get("movie")
        tvshow = self.params.get("tvshow")
        episode = self.params.get("episode")
        movieset = self.params.get("movieset")
        
        try: #try to parse db_id
            if movieset:
                cache_str = "movieset.castcache-%s-%s" %(self.params["movieset"],download_thumbs)
                db_id = int(movieset)
            elif tvshow:
                cache_str = "tvshow.castcache-%s-%s" %(self.params["tvshow"],download_thumbs)
                db_id = int(tvshow)
            elif movie:
                cache_str = "movie.castcache-%s-%s" %(self.params["movie"],download_thumbs)
                db_id = int(movie)
            elif episode:
                cache_str = "episode.castcache-%s-%s" %(self.params["episode"],download_thumbs)
                db_id = int(episode)
            elif not (movie or tvshow or episode or movieset) and xbmc.getCondVisibility("Window.IsActive(DialogVideoInfo.xml)"):
                cache_str = "castcache.%s.%s.%s" %(xbmc.getInfoLabel("ListItem.Title"),xbmc.getInfoLabel("ListItem.FileNameAndPath"),download_thumbs)
        except Exception: 
            pass
        
        cachedata = self.cache.get(cache_str)
        if cachedata:
            #get data from cache
            all_cast = cachedata
        else:
            #retrieve data from json api...
            if movie and db_id:
                all_cast = self.kodi_db.movie(db_id)["cast"]
            elif movie and not db_id:
                filters = [{"operator":"contains", "field":"title","value":movie}]
                result = self.kodi_db.get_db('VideoLibrary.GetMovies',None,filters,[ "title", "cast" ],None,"movies")
                all_cast = result[0]["cast"] if result else []
            elif tvshow and db_id:
                json_result = get_kodi_json('VideoLibrary.GetTVShowDetails', '{ "tvshowid": %d, "properties": [ "title", "cast" ] }' %db_id)
                if json_result and json_result.get("cast"): all_cast = json_result.get("cast")
            elif tvshow and not db_id:
                filters = [{"operator":"contains", "field":"title","value":tvshow}]
                result = self.kodi_db.get_db('VideoLibrary.GetTvShows',None,filters,[ "title", "cast" ],None,"tvshows")
                all_cast = result[0]["cast"] if result else []
            elif episode and db_id:
                json_result = get_kodi_json('VideoLibrary.GetEpisodeDetails', '{ "episodeid": %d, "properties": [ "title", "cast" ] }' %db_id)
                if json_result and json_result.get("cast"): all_cast = json_result.get("cast")
            elif episode and not db_id:
                filters = [{"operator":"contains", "field":"title","value":episode}]
                result = self.kodi_db.get_db('VideoLibrary.GetMovies',None,filters,[ "title", "cast" ],None,"episodes")
                all_cast = result[0]["cast"] if result else []
            elif movieset:
                moviesetmovies = []
                if not db_id:
                    for result in self.kodi_db.get_db('VideoLibrary.GetMovieSets',None,filters,[ "title" ],None,"moviesets"):
                        if result.get("title").lower() == movieset:
                            db_id = result['setid']
                            break
                if db_id:
                    params = {"setid": db_id, "movies": {"properties": ["title","cast"]}}
                    json_result = self.kodi_db.get_db('VideoLibrary.GetMovieSetDetails',None,None,None,None,"moviesets", params)
                    if json_result.has_key("movies"):
                        for movie in json_result['movies']:
                            all_cast += movie['cast']
            #no item provided, try to grab the cast list from container 50 (dialogvideoinfo)
            elif not (movie or tvshow or episode or movieset) and xbmc.getCondVisibility("Window.IsActive(DialogVideoInfo.xml)"):
                for i in range(250):
                    label = xbmc.getInfoLabel("Container(50).ListItemNoWrap(%s).Label" %i).decode("utf-8")
                    if not label: break
                    label2 = xbmc.getInfoLabel("Container(50).ListItemNoWrap(%s).Label2" %i).decode("utf-8")
                    thumb = getCleanImage( xbmc.getInfoLabel("Container(50).ListItemNoWrap(%s).Thumb" %i).decode("utf-8") )
                    all_cast.append( { "name": label, "role": label2, "thumbnail": thumb } )

            #optional: download missing actor thumbs
            if all_cast and download_thumbs:
                for cast in all_cast:
                    if cast.get("thumbnail"): 
                        cast["thumbnail"] = getCleanImage(cast.get("thumbnail"))
                    if not cast.get("thumbnail"):
                        artwork = tmdb.get_actor(cast["name"])
                        cast["thumbnail"] = artwork.get("thumb","")
            #lookup tmdb if item is requested that is not in local db
            if not all_cast:
                tmdbdetails = {}
                if movie and not db_id:
                    tmdbdetails = tmdb.search_movie(movie)
                elif tvshow and not db_id:
                    tmdbdetails = tmdb.search_tvshow(movie)
                if tmdbdetails.get("cast"):
                    all_cast = tmdbdetails["cast"]
            #save to cache
            self.cache.set(cache_str,all_cast)

        #process listing with the results...
        for cast in all_cast:
            if cast.get("name") not in all_cast_names:
                liz = xbmcgui.ListItem(label=cast.get("name"),label2=cast.get("role"),iconImage=cast.get("thumbnail"))
                liz.setProperty('IsPlayable', 'false')
                url = "RunScript(script.extendedinfo,info=extendedactorinfo,name=%s)"%cast.get("name")
                path="plugin://script.skin.helper.service/?action=launch&path=" + url
                all_cast_names.append(cast.get("name"))
                liz.setThumbnailImage(cast.get("thumbnail"))
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=path, listitem=liz, isFolder=False)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        
    @classmethod
    def alphabet(cls):
        '''display an alphabet scrollbar in listings'''
        all_letters = []
        if xbmc.getInfoLabel("Container.NumItems"):
            for i in range(int(xbmc.getInfoLabel("Container.NumItems"))):
                all_letters.append(xbmc.getInfoLabel("Listitem(%s).SortLetter"%i).upper())
            start_number = ""
            for number in ["2","3","4","5","6","7","8","9"]:
                if number in all_letters:
                    start_number = number
                    break
            for letter in [start_number,"A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]:
                if letter == start_number:
                    label = "#"
                else: label = letter
                li = xbmcgui.ListItem(label=label)
                if not letter in all_letters:
                    path = "noop"
                    li.setProperty("NotAvailable","true")
                else:
                    path = "plugin://script.skin.helper.service/?action=alphabetletter&letter=%s" %letter
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), path, li)
        xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
        
    def alphabetletter(self):
        '''used with the alphabet scrollbar to jump to a letter'''
        xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=False, listitem=xbmcgui.ListItem())
        letter = self.params.get("letter","")
        if letter in ["A", "B", "C", "2"]:
            jumpcmd = "2"
        elif letter in ["D", "E", "F", "3"]:
            jumpcmd = "3"
        elif letter in ["G", "H", "I", "4"]:
            jumpcmd = "4"
        elif letter in ["J", "K", "L", "5"]:
            jumpcmd = "5"
        elif letter in ["M", "N", "O", "6"]:
            jumpcmd = "6"
        elif letter in ["P", "Q", "R", "S", "7"]:
            jumpcmd = "7"
        elif letter in ["T", "U", "V", "8"]:
            jumpcmd = "8"
        elif letter in ["W", "X", "Y", "Z", "9"]:
            jumpcmd = "9"
        if jumpcmd:
            xbmc.executebuiltin("SetFocus(50)")
            for i in range(40):
                xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Input.ExecuteAction", "params": { "action": "jumpsms%s" }, "id": 1 }' % (jumpcmd))
                xbmc.sleep(50)
                if xbmc.getInfoLabel("ListItem.Sortletter").upper() == letter:
                    break
        