#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading, thread
from utils import log_msg, log_exception, get_current_content_type, get_kodi_json, try_encode, process_method_on_list
from simplecache import SimpleCache
from artutils import ArtUtils
import xbmc, xbmcgui, xbmcaddon
import time
from datetime import timedelta

class ListItemMonitor(threading.Thread):

    event = None
    exit = False
    delayed_task_interval = 1795
    widgetcontainer_prefix = ""
    content_type = ""
    all_window_props = []
    cur_listitem = ""
    li_dbid = ""
    li_file = ""
    li_imdb = ""
    li_label = ""
    li_path = ""
    li_title = ""
    li_tvdb = ""

    def __init__(self, *args):
        log_msg("ListItemMonitor - started")
        self.win = xbmcgui.Window(10000)
        self.event =  threading.Event()
        self.monitor = xbmc.Monitor()
        self.cache = SimpleCache(autocleanup=True)
        self.artutils = ArtUtils(self.cache)
        self.enable_legacy_props = False #TODO: make dependant of skin bool
        self.artutils.studiologos_path = xbmc.getInfoLabel("Skin.String(SkinHelper.StudioLogos.Path)").decode("utf-8")
        threading.Thread.__init__(self, *args)

    def stop(self):
        log_msg("ListItemMonitor - stop called")
        self.exit = True
        self.event.set()
        
    def __del__(self):
        '''Cleanup Kodi Cpython instances'''
        del self.addon
        del self.win
        log_msg("Exited")

    def run(self):

        player_title = ""
        player_file = ""
        last_playeritem = ""
        player_item = ""
        li_path_last = ""
        cur_folder = ""
        cur_folder_last = ""
        last_listitem = ""
        screensaver_setting = None
        screensaver_disabled = False

        while (self.exit != True):

            if xbmc.getCondVisibility("Player.HasAudio"):
                #set window props for music player
                try:
                    player_title = xbmc.getInfoLabel("Player.Title").decode('utf-8')
                    player_file = xbmc.getInfoLabel("Player.Filenameandpath").decode('utf-8')
                    player_item = player_title + player_file
                    #only perform actions when the listitem has actually changed
                    if player_item and player_item != last_playeritem:
                        #clear all window props first
                        self.reset_player_props()
                        self.setMusicPlayerDetails()
                        last_playeritem = player_item
                except Exception as exc:
                    log_exception(__name__,exc)
                    
            elif last_playeritem:
                #cleanup remaining window props
                self.reset_player_props()
                player_item = ""
                last_playeritem = ""

            #disable the screensaver if fullscreen music playback
            if xbmc.getCondVisibility("Window.IsActive(visualisation) + Skin.HasSetting(SkinHelper.DisableScreenSaverOnFullScreenMusic)") and not screensaver_disabled:
                screensaver_setting = get_kodi_json('Settings.GetSettingValue', '{"setting":"screensaver.mode"}')
                set_kodi_json('Settings.SetSettingValue', '{"setting":"screensaver.mode", "value": ""}')
                screensaver_disabled = True
                log_msg("Disabled screensaver while fullscreen music playback - previous setting: %s" %screensaver_setting)
            elif screensaver_setting and screensaver_disabled:
                set_kodi_json('Settings.SetSettingValue', '{"setting":"screensaver.mode", "value": "%s"}' %screensaver_setting)
                screensaver_disabled = False
                log_msg("fullscreen music playback ended - restoring screensaver: %s" %screensaver_setting)

            #auto close OSD after X seconds of inactivity
            if xbmc.getCondVisibility("Window.IsActive(videoosd) | Window.IsActive(musicosd)"):
                if xbmc.getCondVisibility("Window.IsActive(videoosd)"):
                    secondsToDisplay = xbmc.getInfoLabel("Skin.String(SkinHelper.AutoCloseVideoOSD)")
                    window = "videoosd"
                elif xbmc.getCondVisibility("Window.IsActive(musicosd)"):
                    secondsToDisplay = xbmc.getInfoLabel("Skin.String(SkinHelper.AutoCloseMusicOSD)")
                    window = "musicosd"
                else:
                    secondsToDisplay = ""

                if secondsToDisplay and secondsToDisplay != "0":
                    while xbmc.getCondVisibility("Window.IsActive(%s)"%window):
                        if xbmc.getCondVisibility("System.IdleTime(%s)" %secondsToDisplay):
                            if xbmc.getCondVisibility("Window.IsActive(%s)"%window):
                                xbmc.executebuiltin("Dialog.Close(%s)" %window)
                        else:
                            xbmc.sleep(500)

            #do some background stuff every 30 minutes
            if self.delayed_task_interval >= 1800 and not self.exit:
                thread.start_new_thread(self.do_background_work, ())
                self.delayed_task_interval = 0

            if xbmc.getCondVisibility("System.HasModalDialog | Window.IsActive(progressdialog) | Window.IsActive(busydialog) | !IsEmpty(Window(Home).Property(TrailerPlaying)) | !IsEmpty(Window(Home).Property(artworkcontextmenu))"):
                #skip when modal dialogs are opened (e.g. textviewer in musicinfo dialog)
                self.monitor.waitForAbort(1)
                self.delayed_task_interval += 1
            elif xbmc.getCondVisibility("[Window.IsMedia | !IsEmpty(Window(Home).Property(SkinHelper.WidgetContainer))]") and not self.exit:
                try:
                    widgetContainer = self.win.getProperty("SkinHelper.WidgetContainer").decode('utf-8')
                    if xbmc.getCondVisibility("Window.IsActive(movieinformation)"):
                        self.widgetcontainer_prefix = ""
                        cur_folder = xbmc.getInfoLabel("movieinfo-$INFO[Container.FolderPath]$INFO[Container.NumItems]$INFO[Container.Content]").decode('utf-8')
                    elif widgetContainer:
                        self.widgetcontainer_prefix = "Container(%s)."%widgetContainer
                        cur_folder = xbmc.getInfoLabel("widget-%s-$INFO[Container(%s).NumItems]-$INFO[Container(%s).ListItemAbsolute(1).Label]" %(widgetContainer,widgetContainer,widgetContainer)).decode('utf-8')
                    else:
                        self.widgetcontainer_prefix = ""
                        cur_folder = xbmc.getInfoLabel("$INFO[Container.FolderPath]$INFO[Container.NumItems]$INFO[Container.Content]").decode('utf-8')
                    self.li_title = xbmc.getInfoLabel("%sListItem.Title" %self.widgetcontainer_prefix).decode('utf-8')
                    self.li_label = xbmc.getInfoLabel("%sListItem.Label" %self.widgetcontainer_prefix).decode('utf-8')
                except Exception as exc:
                    log_exception(__name__,exc)
                    cur_folder = ""
                    self.li_label = ""
                    self.li_title = ""
                    self.li_file = ""

                #perform actions if the container path has changed
                if (cur_folder != cur_folder_last):
                    self.reset_win_props()
                    self.content_type = ""
                    cur_folder_last = cur_folder
                    if cur_folder and self.li_label:
                        #always wait for the content_type because plugins can be slow
                        for i in range(20):
                            self.content_type = get_current_content_type(self.widgetcontainer_prefix)
                            if self.content_type: 
                                break
                            else: 
                                xbmc.sleep(250)
                        if not self.widgetcontainer_prefix and self.content_type:
                            self.set_forcedview()
                            self.set_content_header()
                        self.win.setProperty("contenttype",self.content_type)
                
                self.cur_listitem ="%s--%s--%s--%s" %(cur_folder, self.li_label, self.li_title, self.content_type)

                #only perform actions when the listitem has actually changed
                if self.cur_listitem and self.cur_listitem != last_listitem and self.content_type:
                    #clear all window props first
                    self.reset_win_props()
                    self.set_win_prop(("curlistitem",self.cur_listitem))

                    #widget properties
                    if self.widgetcontainer_prefix:
                        self.set_widgetdetails()

                    #generic props
                    self.li_path = xbmc.getInfoLabel("%sListItem.Path"
                        %self.widgetcontainer_prefix).decode('utf-8')
                    if not self.li_path: 
                        self.li_path = xbmc.getInfoLabel("%sListItem.FolderPath"
                            %self.widgetcontainer_prefix).decode('utf-8')
                    self.li_file = xbmc.getInfoLabel("%sListItem.FileNameAndPath"
                        %self.widgetcontainer_prefix).decode('utf-8')
                    self.year = xbmc.getInfoLabel("%sListItem.Year"
                        %self.widgetcontainer_prefix)
                    self.li_dbid = ""
                    self.li_imdb = ""
                    self.li_tvdb = ""

                    if not self.li_label == "..":
                        # monitor listitem props for music content
                        if self.content_type in ["albums","artists","songs"]:
                            try:
                                thread.start_new_thread(self.set_musicdetails, ())
                                self.set_genre()
                            except Exception as exc:
                                log_exception(__name__,exc)

                        # monitor listitem props for video content
                        elif self.content_type in ["movies","setmovies","tvshows","seasons","episodes",
                            "sets","musicvideos"]:
                            try:
                                self.li_dbid = xbmc.getInfoLabel("%sListItem.DBID"
                                    %self.widgetcontainer_prefix).decode('utf-8')
                                if not self.li_dbid or self.li_dbid == "-1": 
                                    self.li_dbid = xbmc.getInfoLabel("%sListItem.Property(DBID)"
                                        %self.widgetcontainer_prefix).decode('utf-8')
                                self.set_imdb_id()
                                #run some stuff in seperate threads for a smoother experience
                                thread.start_new_thread(self.set_tmdb_info, ())
                                thread.start_new_thread(self.set_tvdb_info, ())
                                thread.start_new_thread(self.set_omdb_info, ())
                                thread.start_new_thread(self.set_animatedart, ())
                                thread.start_new_thread(self.set_extended_artwork, ())
                                thread.start_new_thread(self.set_streamdetails, ())
                                thread.start_new_thread(self.set_movieset_details, ())
                                thread.start_new_thread(self.set_top250, ())
                                thread.start_new_thread(self.set_studiologo, ())
                                #simple actions that can be processed in parallel
                                self.set_duration()
                                self.set_genre()
                                self.set_director()
                                self.set_extrafanart()
                                if self.li_path.startswith("plugin://"):
                                    self.set_addonname()
                            except Exception as exc:
                                log_exception(__name__,exc)

                        # monitor listitem props when PVR is active
                        elif self.content_type in ["tvchannels","tvrecordings"]:
                            try:
                                self.set_duration()
                                thread.start_new_thread(self.set_pvr_artwork, ())
                                thread.start_new_thread(self.set_pvr_channellogo, ())
                                self.set_genre()
                            except Exception as exc:
                                log_exception(__name__,exc)

                    #set some globals
                    li_path_last = self.li_path
                    last_listitem = self.cur_listitem

                self.monitor.waitForAbort(0.1)
                self.delayed_task_interval += 0.1
            elif last_listitem and not self.exit:
                #flush any remaining window properties
                self.reset_win_props()
                self.win.clearProperty("SkinHelper.ContentHeader")
                self.win.clearProperty("content_type")
                self.content_type = ""
                last_listitem = ""
                self.cur_listitem = ""
                cur_folder = ""
                cur_folder_last = ""
                self.widgetcontainer_prefix = ""
                self.monitor.waitForAbort(0.5)
                self.delayed_task_interval += 0.5
            elif xbmc.getCondVisibility("Window.IsActive(fullscreenvideo)"):
                #fullscreen video active
                self.monitor.waitForAbort(2)
                self.delayed_task_interval += 2
            else:
                #other window visible
                self.monitor.waitForAbort(0.5)
                self.delayed_task_interval += 0.5

    def do_background_work(self):
        try:
            if self.exit: return
            log_msg("Started Background worker...")
            self.set_generic_props()
            self.artutils.studiologos_path = xbmc.getInfoLabel("Skin.String(SkinHelper.StudioLogos.Path)").decode("utf-8")
            log_msg("Ended Background worker...")
        except Exception as exc:
            log_exception(__name__,exc)

    def set_generic_props(self):

        #GET TOTAL ADDONS COUNT
        allAddonsCount = 0
        media_array = get_kodi_json('Addons.GetAddons','{ }')
        for item in media_array:
            allAddonsCount += 1
        self.win.setProperty("SkinHelper.TotalAddons",str(allAddonsCount))

        addontypes = []
        addontypes.append( ["executable", "SkinHelper.TotalProgramAddons", 0] )
        addontypes.append( ["video", "SkinHelper.TotalVideoAddons", 0] )
        addontypes.append( ["audio", "SkinHelper.TotalAudioAddons", 0] )
        addontypes.append( ["image", "SkinHelper.TotalPicturesAddons", 0] )

        for type in addontypes:
            media_array = get_kodi_json('Addons.GetAddons','{ "content": "%s" }' %type[0])
            for item in media_array:
                type[2] += 1
            self.win.setProperty(type[1],str(type[2]))

        #GET FAVOURITES COUNT
        allFavouritesCount = 0
        media_array = get_kodi_json('Favourites.GetFavourites','{ }')
        for item in media_array:
            allFavouritesCount += 1
        self.win.setProperty("SkinHelper.TotalFavourites",str(allFavouritesCount))

        #GET TV CHANNELS COUNT
        allTvChannelsCount = 0
        if xbmc.getCondVisibility("Pvr.HasTVChannels"):
            media_array = get_kodi_json('PVR.GetChannels','{"channelgroupid": "alltv" }' )
            for item in media_array:
                allTvChannelsCount += 1
        self.win.setProperty("SkinHelper.TotalTVChannels",str(allTvChannelsCount))

        #GET MOVIE SETS COUNT
        allMovieSetsCount = 0
        allMoviesInSetCount = 0
        media_array = get_kodi_json('VideoLibrary.GetMovieSets','{}' )
        for item in media_array:
            allMovieSetsCount += 1
            media_array2 = get_kodi_json('VideoLibrary.GetMovieSetDetails','{"setid": %s}' %item["setid"])
            for item in media_array2:
                allMoviesInSetCount +=1
        self.win.setProperty("SkinHelper.TotalMovieSets",str(allMovieSetsCount))
        self.win.setProperty("SkinHelper.TotalMoviesInSets",str(allMoviesInSetCount))

        #GET RADIO CHANNELS COUNT
        allRadioChannelsCount = 0
        if xbmc.getCondVisibility("Pvr.HasRadioChannels"):
            media_array = get_kodi_json('PVR.GetChannels','{"channelgroupid": "allradio" }' )
            for item in media_array:
                allRadioChannelsCount += 1
        self.win.setProperty("SkinHelper.TotalRadioChannels",str(allRadioChannelsCount))

    def reset_win_props(self):
        #reset all window props set by the script...
        process_method_on_list(self.win.clearProperty,self.all_window_props)
        self.all_window_props = []
    
    def reset_player_props(self):
        #reset all window props provided by the script...
        for prop in self.all_player_win_props:
            self.win.clearProperty(try_encode(prop))
        self.all_player_win_props = []
    
    def set_imdb_id(self):
        li_imdb = xbmc.getInfoLabel("%sListItem.IMDBNumber"%self.widgetcontainer_prefix).decode('utf-8')
        if not li_imdb: 
            li_imdb = xbmc.getInfoLabel("%sListItem.Property(IMDBNumber)"%self.widgetcontainer_prefix).decode('utf-8')
        if li_imdb and not li_imdb.startswith("tt"):
            if self.content_type in ["tvshows","seasons","episodes"]:
                self.li_tvdb = li_imdb
            li_imdb = ""
        if not li_imdb:
            if self.year and self.li_title:
                li_imdb = self.artutils.get_omdb_info("",self.li_title,self.year,self.content_type).get("imdbnumber","")
        self.li_imdb = li_imdb
    
    def set_win_prop(self,prop_tuple):
        if prop_tuple[1] and not prop_tuple[0] in self.all_window_props:
            self.all_window_props.append(prop_tuple[0])
            self.win.setProperty(prop_tuple[0],prop_tuple[1])
    
    def set_win_props(self,items):
        process_method_on_list(self.set_win_prop,items)
            
    def win_props_from_dict(self, details, legacyprefix="", sublevelprefix=""):
        '''helper to pretty string-format a dict with details so it can be used as window props'''
        items = []
        if details:
            for key, value in details.iteritems():
                if value:
                    if legacyprefix and self.enable_legacy_props:
                        key = "%s%s"%(legacyprefix,key)
                    elif sublevelprefix:
                        key = "%s.%s"%(sublevelprefix,key)
                    else:
                        key = "SkinHelper.ListItem.%s"%key
                    if isinstance(value,(str,unicode)):
                        items.append( (key, value) )
                    elif isinstance(value,(int,float)):
                        items.append( (key, "%s"%value) )
                    elif isinstance(value,dict):
                        for key2, value2 in value.iteritems():
                            if isinstance(value2,(str,unicode)):
                                items.append( ("%s.%s" %(key,key2), value2) )
                    elif isinstance(value,list):
                        list_strings = []
                        for listvalue in value:
                            if isinstance(listvalue,(str,unicode)):
                                list_strings.append(listvalue)
                        if list_strings:
                            items.append( (key, " / ".join(list_strings) ) )
                        elif len(value) == 1 and isinstance(value[0], (str,unicode)):
                            items.append( (key, value ) )
        process_method_on_list(self.set_win_prop, items)
    
    def set_player_prop(self,key,value):
        self.all_player_win_props.append(key)
        self.win.setProperty(try_encode(key),try_encode(value))

    def set_movieset_details(self):
        if self.li_path.startswith("videodb://movies/sets/") and self.li_dbid:
            cur_listitem = self.cur_listitem
            result = self.artutils.get_moviesetdetails(self.li_dbid)
            if cur_listitem == self.cur_listitem:
                self.win_props_from_dict(result, "SkinHelper.MovieSet.")
        
    def set_content_header(self):
        self.win.clearProperty("SkinHelper.ContentHeader")
        itemscount = xbmc.getInfoLabel("Container.NumItems")
        if itemscount:
            if xbmc.getInfoLabel("Container.ListItemNoWrap(0).Label").startswith("*") or xbmc.getInfoLabel("Container.ListItemNoWrap(1).Label").startswith("*"):
                itemscount = int(itemscount) - 1

            headerprefix = ""
            if self.content_type == "movies":
                headerprefix = xbmc.getLocalizedString(36901)
            elif self.content_type == "tvshows":
                headerprefix = xbmc.getLocalizedString(36903)
            elif self.content_type == "seasons":
                headerprefix = xbmc.getLocalizedString(36905)
            elif self.content_type == "episodes":
                headerprefix = xbmc.getLocalizedString(36907)
            elif self.content_type == "sets":
                headerprefix = xbmc.getLocalizedString(36911)
            elif self.content_type == "albums":
                headerprefix = xbmc.getLocalizedString(36919)
            elif self.content_type == "songs":
                headerprefix = xbmc.getLocalizedString(36921)
            elif self.content_type == "artists":
                headerprefix = xbmc.getLocalizedString(36917)

            if headerprefix:
                self.win.setProperty("SkinHelper.ContentHeader","%s %s" %(itemscount,headerprefix) )

    def set_addonname(self):
        # set addon name as property
        if not xbmc.Player().isPlayingAudio():
            if (xbmc.getCondVisibility("Container.Content(plugins) | !IsEmpty(Container.PluginName)")):
                addon_name = xbmc.getInfoLabel('Container.PluginName').decode('utf-8')
                addon = xbmcaddon.Addon(addon_name)
                addon_name = addon.getAddonInfo('name')
                del addon
                self.set_win_prop(("SkinHelper.Player.addon_name", addon_name))

    def set_genre(self):
        genre = xbmc.getInfoLabel('%sListItem.Genre' %self.widgetcontainer_prefix).decode('utf-8')
        genres = []
        if "/" in genre:
            genres = genre.split(" / ")
        else:
            genres.append(genre)
        self.set_win_prop(('SkinHelper.ListItem.Genres', "[CR]".join(genres)))
        count = 0
        for genre in genres:
            self.set_win_prop(("SkinHelper.ListItem.Genre.%s" %count,genre))
            count +=1

    def set_director(self):
        director = xbmc.getInfoLabel('%sListItem.Director'%self.widgetcontainer_prefix).decode('utf-8')
        directors = []
        if "/" in director:
            directors = director.split(" / ")
        else:
            directors.append(director)
        self.set_win_prop(('SkinHelper.ListItem.Directors', "[CR]".join(directors)))

    def set_widgetdetails(self):
        #sets all listitem properties as window prop for easy use in a widget details pane
        widget_details = []
        cacheStr = u"SkinHelper.ListItemDetails.%s.%s.%s.%s" %(self.li_label,self.li_title,self.li_file,self.widgetcontainer_prefix)
        cache = self.cache.get(cacheStr)
        if cache:
            widget_details = cache
        else:
            widget_details.append( ("label", self.li_label) )
            widget_details.append( ("title", self.li_title) )
            widget_details.append( ("filenameandpath", self.li_file) )
            props = [
                        "Year","Genre","Filenameandpath","FileName","Label2",
                        "Art(fanart)","Art(poster)","Art(clearlogo)","Art(clearart)","Art(landscape)",
                        "FileExtension","Duration","Plot", "PlotOutline","icon","thumb",
                        "Property(FanArt)","dbtype","Property(dbtype)","Property(plot)","FolderPath"
                    ]
            if self.content_type in ["movies", "tvshows", "seasons", "episodes", "musicvideos", "setmovies"]:
                props += [
                            "imdbnumber","Art(characterart)", "studio", "TvShowTitle","Premiered", "director", "writer",
                            "firstaired", "VideoResolution","AudioCodec","AudioChannels", "VideoCodec",
                            "VideoAspect","SubtitleLanguage","AudioLanguage","MPAA", "IsStereoScopic",
                            "Property(Video3DFormat)", "tagline", "rating"
                         ]
            if self.content_type in ["episodes"]:
                props += [
                            "season","episode", "Art(tvshow.landscape)","Art(tvshow.clearlogo)","Art(tvshow.poster)"
                         ]
            if self.content_type in ["musicvideos", "artists", "albums", "songs"]:
                props += ["artist", "album", "rating"]
            if self.content_type in ["tvrecordings", "tvchannels"]:
                props += [
                            "Channel", "Property(Channel)", "Property(StartDateTime)", "DateTime", "Date", "Property(Date)",
                            "Property(DateTime)", "ChannelName", "Property(ChannelLogo)", "Property(ChannelName)",
                            "StartTime","Property(StartTime)","StartDate","Property(StartDate)","EndTime",
                            "Property(EndTime)","EndDate","Property(EndDate)"
                         ]

            for prop in props:
                propvalue = xbmc.getInfoLabel('%sListItem.%s'%(self.widgetcontainer_prefix, prop)).decode('utf-8')
                if propvalue:
                    widget_details.append( ('SkinHelper.ListItem.%s'%prop, propvalue) )
                    if prop.startswith("Property"):
                        prop = prop.replace("Property(","").replace(")","")
                        widget_details.append( ('SkinHelper.ListItem.%s'%prop, propvalue) )
            if self.li_title != xbmc.getInfoLabel('%sListItem.Title'%(self.widgetcontainer_prefix)).decode('utf-8'):
                return #abort if other listitem focused
            if not self.content_type in ["systeminfos","weathers"]:
                self.cache.set(cacheStr,widget_details,expiration=timedelta(hours=1))
        #set the window props
        process_method_on_list(self.set_win_prop, widget_details)

    def set_pvr_artwork(self):
        cur_listitem = self.cur_listitem
        title = self.li_title
        channel = xbmc.getInfoLabel("%sListItem.ChannelName"%self.widgetcontainer_prefix).decode('utf-8')
        if xbmc.getCondVisibility("%sListItem.IsFolder"%self.widgetcontainer_prefix) and not channel and not title:
            title = self.li_label
        if title and xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnablePVRThumbs)"):
            genre = xbmc.getInfoLabel("%sListItem.Genre"%self.widgetcontainer_prefix).decode('utf-8')
            result = self.artutils.get_pvr_artwork(title, channel, genre)
            if cur_listitem == self.cur_listitem:
                self.win_props_from_dict(result,"SkinHelper.PVR.")

    def set_pvr_channellogo(self):
        cur_listitem = self.cur_listitem
        channel = xbmc.getInfoLabel("%sListItem.ChannelName"%self.widgetcontainer_prefix).decode('utf-8')
        if channel:
            result = self.artutils.get_channellogo(channel)
            if cur_listitem == self.cur_listitem:
                self.win_props_from_dict(result, "SkinHelper.PVR")

    def set_studiologo(self):
        cur_listitem = self.cur_listitem
        studio = xbmc.getInfoLabel('%sListItem.Studio'%self.widgetcontainer_prefix).decode('utf-8')
        if studio and self.artutils.studiologos_path:
            result = self.artutils.get_studio_logo(studio)
            if cur_listitem == self.cur_listitem:
                self.win_props_from_dict(result, "SkinHelper.ListItem")

    def set_duration(self):
        if not xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.DisableHoursDuration)"):
            duration = xbmc.getInfoLabel("%sListItem.Duration"%self.widgetcontainer_prefix)
            if duration:
                result = self.artutils.get_duration(duration)
                self.win_props_from_dict(result, "SkinHelper.ListItem")

    def setMusicPlayerDetails(self):
        artwork = {}
        artist = ""
        title = ""
        album = ""
        #get the playing item from the player...
        json_result = get_kodi_json('Player.GetActivePlayers', '{}')
        for item in json_result:
            if item.get("type","") == "audio":
                json_result = get_kodi_json('Player.GetItem', '{ "playerid": %d, "properties": [ "title","albumid","artist","album","displayartist" ] }' %item.get("playerid"))
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

    def set_musicdetails(self):
        cur_listitem = self.cur_listitem
        artist = xbmc.getInfoLabel("%sListItem.Artist"%self.widgetcontainer_prefix).decode('utf-8')
        album = xbmc.getInfoLabel("%sListItem.Album"%self.widgetcontainer_prefix).decode('utf-8')
        title = self.li_title
        label = self.li_label
        result = self.artutils.get_musicartwork(artist,album,title)
        if cur_listitem == self.cur_listitem:
            self.win_props_from_dict(result, "SkinHelper.Music.")

    def set_streamdetails(self):
        cur_listitem = self.cur_listitem
        if self.li_dbid and self.content_type in ["movies","episodes","musicvideos"] and not self.li_path.startswith("videodb://movies/sets/"):
            result = self.artutils.get_streamdetails(self.li_dbid,self.content_type)
            if cur_listitem == self.cur_listitem:
                self.win_props_from_dict(result, "SkinHelper.ListItem")

    def set_forcedview(self):
        currentForcedView = xbmc.getInfoLabel("Skin.String(SkinHelper.ForcedViews.%s)" %self.content_type)
        if xbmc.getCondVisibility("Control.IsVisible(%s) | IsEmpty(Container.Viewmode)" %currentForcedView):
            #skip if the view is already visible or if we're not in an actual media window
            return
        if (self.content_type and currentForcedView and currentForcedView != "None" and 
            xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.ForcedViews.Enabled)") and not "pvr://guide" in self.li_path):
            self.win.setProperty("SkinHelper.ForcedView",currentForcedView)
            xbmc.executebuiltin("Container.SetViewMode(%s)" %currentForcedView)
            if not xbmc.getCondVisibility("Control.HasFocus(%s)" %currentForcedView):
                xbmc.sleep(100)
                xbmc.executebuiltin("Container.SetViewMode(%s)" %currentForcedView)
                xbmc.executebuiltin("SetFocus(%s)" %currentForcedView)
        else:
            self.win.clearProperty("SkinHelper.ForcedView")

    def set_extrafanart(self):
        if xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnableExtraFanart)"):
            if self.content_type in ["movies","seasons","episodes","tvshows","setmovies","moviesets"]:
                cur_listitem = self.cur_listitem
                result = self.artutils.get_extrafanart(self.li_dbid,self.content_type)
                if cur_listitem == self.cur_listitem:
                    self.win_props_from_dict(result, "SkinHelper.")

    def set_animatedart(self):
        #check animated posters
        title = self.li_title
        if self.li_imdb and xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnableAnimatedPosters)"):
            cur_listitem = self.cur_listitem
            result = self.artutils.get_animated_artwork(self.li_imdb)
            if cur_listitem == self.cur_listitem:
                self.win_props_from_dict(result, "SkinHelper.")

    def set_omdb_info(self):
        if self.li_imdb:
            cur_listitem = self.cur_listitem
            result = self.artutils.get_omdb_info(self.li_imdb)
            if cur_listitem == self.cur_listitem:
                self.win_props_from_dict(result, "SkinHelper.")
    
    def set_top250(self):
        if self.li_imdb:
            cur_listitem = self.cur_listitem
            result = self.artutils.get_top250_rating(self.li_imdb)
            if cur_listitem == self.cur_listitem:
                self.win_props_from_dict(result, "SkinHelper.")
    
    def set_tmdb_info(self):
        if self.content_type in ["movies", "setmovies"]:
            cur_listitem = self.cur_listitem
            if self.li_imdb:
                result = self.artutils.get_tmdb_details(self.li_imdb)
                if cur_listitem == self.cur_listitem:
                    self.win_props_from_dict(result, "SkinHelper.TMDB.")
                
    def set_tvdb_info(self):
        if self.content_type in ["tvshows", "seasons", "episodes"]:
            cur_listitem = self.cur_listitem
            if self.li_imdb:
                result = self.artutils.get_tvdb_details(self.li_imdb, self.li_tvdb)
                if cur_listitem == self.cur_listitem:
                    self.win_props_from_dict(result)

    def set_extended_artwork(self):
        #try to lookup additional artwork
        cur_listitem = self.cur_listitem
        result = self.artutils.get_extended_artwork(self.li_imdb)
        if cur_listitem == self.cur_listitem:
            self.win_props_from_dict(result, "SkinHelper.PVR")
        