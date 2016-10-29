#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading, thread
from utils import log_msg, log_exception, get_current_content_type, kodi_json, try_encode, process_method_on_list
import xbmc
import time
from datetime import timedelta
from simplecache import use_cache

class ListItemMonitor(threading.Thread):

    event = None
    exit = False
    delayed_task_interval = 1795
    widgetcontainer_prefix = ""
    content_type = ""
    all_window_props = []
    cur_listitem = ""

    def __init__(self, *args, **kwargs):
        self.cache = kwargs.get("cache")
        self.artutils = kwargs.get("artutils")
        self.win = kwargs.get("win")
        self.kodimonitor = kwargs.get("monitor")
        self.enable_legacy_props = False #TODO: make dependant of skin bool
        self.event =  threading.Event()
        threading.Thread.__init__(self, *args)

    def stop(self):
        log_msg("ListItemMonitor - stop called")
        self.exit = True
        self.event.set()

    def run(self):

        cur_folder = ""
        cur_folder_last = ""
        last_listitem = ""
        screensaver_setting = None
        screensaver_disabled = False
        self.artutils.studiologos_path = xbmc.getInfoLabel("Skin.String(SkinHelper.StudioLogos.Path)").decode("utf-8")
        log_msg("ListItemMonitor - started")
        while (self.exit != True):

            #disable the screensaver if fullscreen music playback
            if xbmc.getCondVisibility("Window.IsActive(visualisation) + Skin.HasSetting(SkinHelper.DisableScreenSaverOnFullScreenMusic)"):
                if not screensaver_disabled:
                    #disable screensaver when fullscreen music active
                    screensaver_setting = kodi_json('Settings.GetSettingValue', '{"setting":"screensaver.mode"}')
                    kodi_json('Settings.SetSettingValue', {"setting":"screensaver.mode", "value": None} )
                    screensaver_disabled = True
                    log_msg("Disabled screensaver while fullscreen music playback - previous setting: %s" %screensaver_setting)
            elif screensaver_setting and screensaver_disabled:
                #enable screensaver again after fullscreen music playback was ended
                kodi_json('Settings.SetSettingValue', {"setting": "screensaver.mode", "value": screensaver_setting})
                screensaver_disabled = False
                log_msg("fullscreen music playback ended - restoring screensaver: %s" %screensaver_setting)

            #auto close OSD after X seconds of inactivity
            if xbmc.getCondVisibility("[Window.IsActive(videoosd) + Skin.String(SkinHelper.AutoCloseVideoOSD)] | \
                [Window.IsActive(musicosd) + Skin.String(SkinHelper.AutoCloseMusicOSD)]"):
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
            if (self.delayed_task_interval >= 1800) and not self.exit:
                thread.start_new_thread(self.do_background_work, ())
                self.delayed_task_interval = 0

            #skip if any of the artwork context menus is opened
            if self.win.getProperty("SkinHelper.Artwork.ManualLookup"):
                if self.cur_listitem:
                    self.reset_win_props()
                    self.cur_listitem = ""
                    last_listitem = ""
                self.kodimonitor.waitForAbort(3)
                self.delayed_task_interval += 3
            #skip when modal dialogs are opened (e.g. textviewer in musicinfo dialog)
            if xbmc.getCondVisibility("System.HasModalDialog | Window.IsActive(progressdialog) | Window.IsActive(busydialog) | !IsEmpty(Window(Home).Property(TrailerPlaying)) | !IsEmpty(Window(Home).Property(SkinHelper.Artwork.ManualLookup))"):
                self.kodimonitor.waitForAbort(2)
                self.delayed_task_interval += 2
            #media window is opened or widgetcontainer set - start listitem monitoring!
            elif xbmc.getCondVisibility("[Window.IsMedia | !IsEmpty(Window(Home).Property(SkinHelper.WidgetContainer))]"):
                try:
                    widget_container = self.win.getProperty("SkinHelper.WidgetContainer").decode('utf-8')
                    if xbmc.getCondVisibility("Window.IsActive(movieinformation)"):
                        self.cont_prefix = ""
                        cur_folder = xbmc.getInfoLabel("movieinfo-$INFO[Container.FolderPath]$INFO[Container.NumItems]$INFO[Container.Content]").decode('utf-8')
                    elif widget_container:
                        self.cont_prefix = "Container(%s)."%widget_container
                        cur_folder = xbmc.getInfoLabel("widget-%s-$INFO[Container(%s).NumItems]-$INFO[Container(%s).ListItemAbsolute(1).Label]" %(widget_container,widget_container,widget_container)).decode('utf-8')
                    else:
                        self.cont_prefix = ""
                        cur_folder = xbmc.getInfoLabel("$INFO[Container.FolderPath]$INFO[Container.NumItems]$INFO[Container.Content]").decode('utf-8')
                    self.li_title = xbmc.getInfoLabel("%sListItem.Title" %self.cont_prefix).decode('utf-8')
                    self.li_label = xbmc.getInfoLabel("%sListItem.Label" %self.cont_prefix).decode('utf-8')
                    self.li_path = xbmc.getInfoLabel("%sListItem.Path"%self.cont_prefix).decode('utf-8')
                    if not self.li_path:
                        self.li_path = xbmc.getInfoLabel("%sListItem.FolderPath"%self.cont_prefix).decode('utf-8')
                except Exception as exc:
                    log_exception(__name__,exc)
                    cur_folder = ""
                    cur_listitem = ""

                if self.exit:
                    return

                #perform actions if the container path has changed
                if (cur_folder != cur_folder_last):
                    self.reset_win_props()
                    self.content_type = ""
                    cur_folder_last = cur_folder
                    if cur_folder and self.li_label:
                        #always wait for the content_type because plugins can be slow
                        for i in range(20):
                            self.content_type = get_current_content_type(self.cont_prefix)
                            if self.exit:
                                return
                            if self.content_type:
                                break
                            else:
                                xbmc.sleep(250)
                        if not self.cont_prefix and self.content_type:
                            self.set_forcedview()
                            self.set_content_header()
                        self.win.setProperty("contenttype",self.content_type)

                self.cur_listitem ="%s--%s--%s--%s" %(cur_folder, self.li_label, self.li_title, self.content_type)
                #only perform actions when the listitem has actually changed
                if self.cur_listitem and self.cur_listitem != last_listitem and self.content_type:
                    #clear all window props first
                    self.reset_win_props()
                    self.set_win_prop(("curlistitem",self.cur_listitem))
                    if not self.li_label == "..":
                        #set listitem details multithreaded
                        thread.start_new_thread(self.set_listitem_details, (self.cur_listitem,))
                    last_listitem = self.cur_listitem

                self.kodimonitor.waitForAbort(0.05)
                self.delayed_task_interval += 0.05
            elif last_listitem or self.all_window_props:
                #flush any remaining window properties
                self.reset_win_props()
                self.win.clearProperty("SkinHelper.ContentHeader")
                self.win.clearProperty("contenttype")
                self.content_type = ""
                last_listitem = ""
                self.cur_listitem = ""
                cur_folder = ""
                cur_folder_last = ""
                self.cont_prefix = ""
            else:
                #fullscreen video active or any other window
                self.kodimonitor.waitForAbort(2)
                self.delayed_task_interval += 2

    def set_listitem_details(self, cur_listitem):
        '''set the window properties based on the current listitem'''
        try:
            all_props = []
            #get generic props
            prefix = self.cont_prefix
            li_title = self.li_title
            li_label = self.li_label
            content_type = self.content_type
            li_path = self.li_path
            li_file = xbmc.getInfoLabel("%sListItem.FileNameAndPath"%prefix).decode('utf-8')
            li_year = xbmc.getInfoLabel("%sListItem.Year"%prefix)
            li_dbid = xbmc.getInfoLabel("%sListItem.DBID"%prefix).decode('utf-8')
            if not li_dbid or li_dbid == "-1":
                li_dbid = xbmc.getInfoLabel("%sListItem.Property(DBID)"%prefix).decode('utf-8')
            li_genre = xbmc.getInfoLabel("%sListItem.Genre"%prefix)
            li_duration = xbmc.getInfoLabel("%sListItem.Duration"%prefix).decode("utf-8")
            li_studio = xbmc.getInfoLabel('%sListItem.Studio'%prefix).decode('utf-8')
            li_director = xbmc.getInfoLabel('%sListItem.Director'%prefix).decode('utf-8')
            li_imdb = xbmc.getInfoLabel("%sListItem.IMDBNumber"%prefix).decode('utf-8')
            if not li_imdb:
                li_imdb = xbmc.getInfoLabel("%sListItem.Property(IMDBNumber)"%prefix).decode('utf-8')
            li_showtitle = xbmc.getInfoLabel("%sListItem.TvShowTitle"%self.cont_prefix).decode('utf-8')
            li_channel = xbmc.getInfoLabel("%sListItem.ChannelName"%prefix).decode('utf-8')
            

            # widget properties
            if prefix:
                no_cache = True if content_type == "systeminfos" else False
                process_method_on_list( self.set_win_prop, self.get_widgetdetails(cur_listitem, li_label, li_file,
                    li_title, li_year, li_genre, content_type, ignore_cache=no_cache) )

            # music content
            if content_type in ["albums","artists","songs"]:
                artist = xbmc.getInfoLabel("%sListItem.AlbumArtist"%prefix).decode('utf-8')
                if not artist:
                    artist = xbmc.getInfoLabel("%sListItem.Artist"%prefix).decode('utf-8')
                album = xbmc.getInfoLabel("%sListItem.Album"%prefix).decode('utf-8')
                li_disc = xbmc.getInfoLabel("%sListItem.DiscNumber"%prefix).decode('utf-8')
                result = self.artutils.get_music_artwork(artist, album, li_title, li_disc)
                all_props += self.prepare_win_props(result, "SkinHelper.Music.")

            # moviesets
            elif li_path.startswith("videodb://movies/sets/") and li_dbid:
                result = self.artutils.get_moviesetdetails(li_dbid)
                all_props += self.prepare_win_props(result, "SkinHelper.MovieSet.")

            # video content
            elif content_type in ["movies","setmovies","tvshows","seasons","episodes", "musicvideos"]:

                #get imdb_id
                li_imdb, li_tvdb = self.get_imdb_id( li_imdb, li_title, li_year, li_showtitle, content_type )

                #generic video properties (studio, streamdetails, omdb, top250)
                all_props += self.get_studiologo(li_studio)
                all_props += self.prepare_win_props(self.artutils.get_omdb_info(li_imdb), "SkinHelper.")
                all_props += self.get_streamdetails(li_dbid, li_path, content_type)
                all_props += self.prepare_win_props(self.artutils.get_top250_rating(li_imdb), "SkinHelper.")
                all_props.append(self.get_directors(li_director))
                all_props += self.get_extrafanart(li_path, content_type)
                all_props += self.get_genres(li_genre)
                all_props += self.get_duration(li_duration)

                #tvshows-only properties (tvdb)
                if content_type in ["tvshows", "seasons", "episodes"]:
                    all_props += self.prepare_win_props(self.artutils.get_tvdb_details(li_imdb, li_tvdb))

                #movies-only properties (tmdb, animated art)
                if content_type in ["movies", "setmovies"]:
                    all_props += self.prepare_win_props(self.artutils.get_tmdb_details(li_imdb), "SkinHelper.TMDB.")
                    if li_imdb and xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnableAnimatedPosters)"):
                        all_props += self.prepare_win_props(self.artutils.get_animated_artwork(li_imdb), "SkinHelper.")

            # monitor listitem props when PVR is active
            elif self.content_type in ["tvchannels","tvrecordings", "channels", "recordings"]:
                #pvr artwork
                if xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnablePVRThumbs) + PVR.HasTVChannels"):
                    if xbmc.getCondVisibility("%sListItem.IsFolder"%prefix) and not li_channel and not li_title:
                        li_title = li_label
                    pvrart = self.artutils.get_pvr_artwork(li_title, li_channel, li_genre)
                    all_props += self.prepare_win_props(pvrart,"SkinHelper.PVR.")
                #pvr channellogo
                all_props.append( ("SkinHelper.ListItem.ChannelLogo", self.artutils.get_channellogo(li_channel)) )

            #safety check
            if not (cur_listitem == self.cur_listitem) or self.exit:
                return
            #process all properties
            process_method_on_list(self.set_win_prop,all_props)

        except Exception as exc:
            log_exception(__name__,exc)

    def do_background_work(self):
        try:
            if self.exit:
                return
            log_msg("Started Background worker...")
            self.set_generic_props()
            self.artutils.studiologos_path = xbmc.getInfoLabel("Skin.String(SkinHelper.StudioLogos.Path)").decode("utf-8")
            log_msg("Ended Background worker...")
        except Exception as exc:
            log_exception(__name__,exc)

    def set_generic_props(self):

        #GET TOTAL ADDONS COUNT
        allAddonsCount = 0
        media_array = kodi_json('Addons.GetAddons')
        for item in media_array:
            allAddonsCount += 1
        self.win.setProperty("SkinHelper.TotalAddons",str(allAddonsCount))

        addontypes = []
        addontypes.append( ["executable", "SkinHelper.TotalProgramAddons", 0] )
        addontypes.append( ["video", "SkinHelper.TotalVideoAddons", 0] )
        addontypes.append( ["audio", "SkinHelper.TotalAudioAddons", 0] )
        addontypes.append( ["image", "SkinHelper.TotalPicturesAddons", 0] )

        for type in addontypes:
            media_array = kodi_json('Addons.GetAddons',{ "content": type[0] } )
            for item in media_array:
                type[2] += 1
            self.win.setProperty(type[1],str(type[2]))

        #GET FAVOURITES COUNT
        allFavouritesCount = 0
        media_array = kodi_json('Favourites.GetFavourites')
        for item in media_array:
            allFavouritesCount += 1
        self.win.setProperty("SkinHelper.TotalFavourites",str(allFavouritesCount))

        #GET TV CHANNELS COUNT
        allTvChannelsCount = 0
        if xbmc.getCondVisibility("Pvr.HasTVChannels"):
            media_array = kodi_json('PVR.GetChannels',{"channelgroupid": "alltv" } )
            for item in media_array:
                allTvChannelsCount += 1
        self.win.setProperty("SkinHelper.TotalTVChannels",str(allTvChannelsCount))

        #GET MOVIE SETS COUNT
        allMovieSetsCount = 0
        allMoviesInSetCount = 0
        media_array = kodi_json('VideoLibrary.GetMovieSets')
        for item in media_array:
            allMovieSetsCount += 1
            media_array2 = kodi_json('VideoLibrary.GetMovieSetDetails',{"setid": item["setid"]})
            for item in media_array2:
                allMoviesInSetCount +=1
        self.win.setProperty("SkinHelper.TotalMovieSets",str(allMovieSetsCount))
        self.win.setProperty("SkinHelper.TotalMoviesInSets",str(allMoviesInSetCount))

        #GET RADIO CHANNELS COUNT
        allRadioChannelsCount = 0
        if xbmc.getCondVisibility("Pvr.HasRadioChannels"):
            media_array = kodi_json('PVR.GetChannels',{"channelgroupid": "allradio" } )
            for item in media_array:
                allRadioChannelsCount += 1
        self.win.setProperty("SkinHelper.TotalRadioChannels",str(allRadioChannelsCount))

    def reset_win_props(self):
        #reset all window props set by the script...
        process_method_on_list(self.win.clearProperty,self.all_window_props)
        self.all_window_props = []

    @use_cache(14,True)
    def get_imdb_id(self, li_imdb, li_title, li_year, li_showtitle, content_type):
        '''try to figure out the imdbnumber because that's what we use for all lookup actions'''
        li_tvdb = ""
        if content_type in ["seasons","episodes"]:
            li_title = li_showtitle
            content_type = "tvshows"
        if li_imdb and not li_imdb.startswith("tt"):
            if content_type in ["tvshows","seasons","episodes"]:
                li_tvdb = li_imdb
                li_imdb = ""
        if not li_imdb and li_year:
            li_imdb = self.artutils.get_omdb_info("", li_title, li_year, content_type).get("imdbnumber","")
        if not li_imdb:
            #repeat without year
            li_imdb = self.artutils.get_omdb_info("", li_title, "", content_type).get("imdbnumber","")
        #return results
        return (li_imdb, li_tvdb)

    def set_win_prop(self,prop_tuple):
        if prop_tuple[1] and not prop_tuple[0] in self.all_window_props:
            self.all_window_props.append(prop_tuple[0])
            self.win.setProperty(prop_tuple[0],prop_tuple[1])

    def set_win_props(self,items):
        process_method_on_list(self.set_win_prop,items)

    def prepare_win_props(self, details, legacyprefix="", sublevelprefix=""):
        '''helper to pretty string-format a dict with details so it can be used as window props'''
        items = []
        if details:
            for key, value in details.iteritems():
                if value:
                    if legacyprefix and self.enable_legacy_props:
                        key = u"%s%s"%(legacyprefix,key)
                    elif sublevelprefix:
                        key = "%s.%s"%(sublevelprefix,key)
                    else:
                        key = u"SkinHelper.ListItem.%s"%key
                    if isinstance(value,(str,unicode)):
                        items.append( (key, value) )
                    elif isinstance(value,(int,float)):
                        items.append( (key, "%s"%value) )
                    elif isinstance(value,dict):
                        for key2, value2 in value.iteritems():
                            if isinstance(value2,(str,unicode)):
                                items.append( (u"%s.%s" %(key,key2), value2) )
                    elif isinstance(value,list):
                        list_strings = []
                        for listvalue in value:
                            if isinstance(listvalue,(str,unicode)):
                                list_strings.append(listvalue)
                        if list_strings:
                            items.append( (key, u" / ".join(list_strings) ) )
                        elif len(value) == 1 and isinstance(value[0], (str,unicode)):
                            items.append( (key, value ) )
        return items

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

    @use_cache(0.08,True)
    def get_genres(self, li_genre):
        items = []
        genres = li_genre.split(" / ")
        items.append(('SkinHelper.ListItem.Genres', "[CR]".join(genres)))
        count = 0
        for genre in genres:
            items.append(("SkinHelper.ListItem.Genre.%s" %count,genre))
            count +=1
        return items

    def get_directors(self, director):
        directors = director.split(" / ")
        return ('SkinHelper.ListItem.Directors', "[CR]".join(directors))

    @use_cache(0.08,True)
    def get_widgetdetails(self, cur_listitem, li_label, li_file, li_title,
        li_year, li_genre, content_type, ignore_cache=False):
        '''gets all listitem properties as window prop for easy use in a widget details pane'''
        #collect all the infolabels
        widget_details = []
        widget_details.append( ("SkinHelper.ListItem.label", li_label) )
        widget_details.append( ("SkinHelper.ListItem.title", li_title) )
        widget_details.append( ("SkinHelper.ListItem.filenameandpath", li_file) )
        widget_details.append( ("SkinHelper.ListItem.year", li_year) )
        widget_details.append( ("SkinHelper.ListItem.genre", li_genre) )
        props = [
                    "Art(fanart)","Art(poster)","Art(clearlogo)","Art(clearart)","Art(landscape)",
                    "FileExtension","Duration","Plot", "PlotOutline","icon","thumb","Label2",
                    "Property(FanArt)","dbtype"
                ]
        if content_type in ["movies", "tvshows", "seasons", "episodes", "musicvideos", "setmovies"]:
            props += [ "Art(characterart)", "studio", "TvShowTitle","Premiered", "director", "writer",
                "firstaired", "VideoResolution","AudioCodec","AudioChannels", "VideoCodec", "VideoAspect",
                "SubtitleLanguage","AudioLanguage","MPAA", "IsStereoScopic","Property(Video3DFormat)",
                "tagline", "rating"]
            if content_type in ["episodes"]:
                props += ["season","episode", "Art(tvshow.landscape)","Art(tvshow.clearlogo)",
                    "Art(tvshow.poster)"]
        elif content_type in ["musicvideos", "artists", "albums", "songs"]:
            props += ["artist", "album", "rating"]
        elif content_type in ["tvrecordings", "tvchannels"]:
            props += ["Channel", "Property(StartDateTime)", "DateTime", "Date", "ChannelName",
                "StartTime","StartDate","EndTime", "EndDate" ]
        for prop in props:
            propvalue = xbmc.getInfoLabel('%sListItem.%s'%(self.cont_prefix, prop)).decode('utf-8')
            if cur_listitem != self.cur_listitem:
                return
            if not propvalue and not "Property" in prop:
                propvalue = xbmc.getInfoLabel(u'%sListItem.Property(%s)'%(self.cont_prefix, prop)).decode('utf-8')
            if propvalue:
                widget_details.append( (u'SkinHelper.ListItem.%s'%prop, propvalue) )
        return widget_details

    def get_studiologo(self, studio):
        items = []
        if studio and self.artutils.studiologos_path:
            result = self.artutils.get_studio_logo(studio)
            items = self.prepare_win_props(result, "SkinHelper.ListItem")
        return items

    def get_duration(self, duration):
        items = []
        if duration:
            result = self.artutils.get_duration(duration)
            items = self.prepare_win_props(result, "SkinHelper.ListItem")
        return items

    def get_streamdetails(self, li_dbid, li_path, content_type):
        items = []
        if li_dbid and content_type in ["movies","episodes","musicvideos"] and not li_path.startswith("videodb://movies/sets/"):
            result = self.artutils.get_streamdetails(li_dbid, content_type)
            items = self.prepare_win_props(result, "SkinHelper.ListItem")
        return items

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

    def get_extrafanart(self, li_dbid, content_type):
        items = []
        if xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnableExtraFanart)"):
            if li_dbid and content_type in ["movies","seasons","episodes","tvshows","setmovies","moviesets"]:
                result = self.artutils.get_extrafanart(li_dbid, content_type)
                items = self.prepare_win_props(result, "SkinHelper.")
        return items

    def set_extended_artwork(self):
        #try to lookup additional artwork
        cur_listitem = self.cur_listitem
        result = self.artutils.get_extended_artwork(self.li_imdb)
        if cur_listitem == self.cur_listitem:
            self.win_props_from_dict(result, "SkinHelper.PVR")
