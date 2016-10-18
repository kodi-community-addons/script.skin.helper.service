#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading, thread
from utils import WINDOW, log_msg, log_exception, get_current_content_type, get_kodi_json, try_encode, process_method_on_list
from simplecache import SimpleCache
from artutils import ArtUtils
import xbmc, xbmcgui
import time
from datetime import timedelta

class ListItemMonitor(threading.Thread):

    event = None
    exit = False
    delayedTaskInterval = 1795
    lastWeatherNotificationCheck = None
    lastNextAiredNotificationCheck = None
    widgetcontainer_prefix = ""
    content_type = ""
    all_window_props = []
    allPlayerWindowProps = []
    li_dbid = ""
    li_file = ""
    li_imdb = ""
    li_label = ""
    li_path = ""
    li_title = ""
    li_tvdb = ""

    def __init__(self, *args):
        log_msg("ListItemMonitor - started")
        self.event =  threading.Event()
        self.monitor = xbmc.Monitor()
        self.artutils = ArtUtils()
        self.cache = SimpleCache()
        self.enable_legacy_props = True
        self.artutils.studiologos_path = xbmc.getInfoLabel("Skin.String(SkinHelper.StudioLogos.Path)").decode("utf-8")
        threading.Thread.__init__(self, *args)

    def stop(self):
        log_msg("ListItemMonitor - stop called")
        self.exit = True
        self.event.set()

    def run(self):

        player_title = ""
        player_file = ""
        last_playeritem = ""
        player_item = ""
        li_pathLast = ""
        cur_folder = ""
        cur_folder_last = ""
        last_listitem = ""
        nextairedActive = False
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
            if self.delayedTaskInterval >= 1800 and not self.exit:
                thread.start_new_thread(self.do_background_work, ())
                self.delayedTaskInterval = 0

            if xbmc.getCondVisibility("System.HasModalDialog | Window.IsActive(progressdialog) | Window.IsActive(busydialog) | !IsEmpty(Window(Home).Property(TrailerPlaying))"):
                #skip when modal dialogs are opened (e.g. textviewer in musicinfo dialog)
                self.monitor.waitForAbort(1)
                self.delayedTaskInterval += 1
            elif xbmc.getCondVisibility("[Window.IsMedia | !IsEmpty(Window(Home).Property(SkinHelper.WidgetContainer))]") and not self.exit:
                try:
                    widgetContainer = WINDOW.getProperty("SkinHelper.WidgetContainer").decode('utf-8')
                    if xbmc.getCondVisibility("Window.IsActive(movieinformation)"):
                        self.widgetcontainer_prefix = ""
                        cur_folder = xbmc.getInfoLabel("movieinfo-$INFO[Container.FolderPath]$INFO[Container.NumItems]$INFO[Container.Content]").decode('utf-8')
                    elif widgetContainer:
                        self.widgetcontainer_prefix = "Container(%s)."%widgetContainer
                        cur_folder = xbmc.getInfoLabel("widget-%s-$INFO[Container(%s).NumItems]" %(widgetContainer,widgetContainer)).decode('utf-8')
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
                            if self.content_type: break
                            else: xbmc.sleep(250)
                        if not self.widgetcontainer_prefix and self.content_type:
                            self.setForcedView()
                            self.set_content_header()
                        WINDOW.setProperty("content_type",self.content_type)

                curListItem ="%s--%s--%s--%s" %(cur_folder, self.li_label, self.li_title, self.content_type)

                #only perform actions when the listitem has actually changed
                if curListItem and curListItem != last_listitem and self.content_type:
                    #clear all window props first
                    self.reset_win_props()
                    self.set_win_prop(("curListItem",curListItem))

                    #widget properties
                    if self.widgetcontainer_prefix:
                        self.set_widgetdetails()

                    #generic props
                    self.li_path = xbmc.getInfoLabel("%sListItem.Path" %self.widgetcontainer_prefix).decode('utf-8')
                    if not self.li_path: 
                        self.li_path = xbmc.getInfoLabel("%sListItem.FolderPath" %self.widgetcontainer_prefix).decode('utf-8')
                    self.li_file = xbmc.getInfoLabel("%sListItem.FileNameAndPath" %self.widgetcontainer_prefix).decode('utf-8')
                    self.li_dbid = ""
                    self.li_imdb = ""
                    self.li_tvdb = ""

                    if not self.li_label == "..":
                        # monitor listitem props for music content
                        if self.content_type in ["albums","artists","songs"]:
                            try:
                                thread.start_new_thread(self.set_musicdetails, (True,))
                                self.set_genre()
                            except Exception as exc:
                                log_exception(__name__,exc)

                        # monitor listitem props for video content
                        elif self.content_type in ["movies","setmovies","tvshows","seasons","episodes","sets","musicvideos"]:
                            try:
                                self.li_dbid = xbmc.getInfoLabel("%sListItem.DBID"%self.widgetcontainer_prefix).decode('utf-8')
                                if not self.li_dbid or self.li_dbid == "-1": 
                                    self.li_dbid = xbmc.getInfoLabel("%sListItem.Property(DBID)"%self.widgetcontainer_prefix).decode('utf-8')
                                self.year = xbmc.getInfoLabel("%sListItem.Year"%self.widgetcontainer_prefix)
                                self.set_imdb_id()
                                self.set_duration()
                                thread.start_new_thread(self.set_tmdb_info, (True,))
                                thread.start_new_thread(self.set_omdb_info, (True,))
                                thread.start_new_thread(self.set_animatedart, (True,))
                                thread.start_new_thread(self.set_extended_artwork, (True,))
                                thread.start_new_thread(self.set_extended_artwork, (True,))
                                self.set_studiologo()
                                self.set_genre()
                                self.set_director()
                                self.set_top250()
                                self.set_streamdetails()
                                self.set_movieset_details()
                                self.set_extrafanart()
                                if self.li_path.startswith("plugin://"):
                                    self.set_addonname()
                                #nextaired workaround for info dialog
                                if widgetContainer == "999" and xbmc.getCondVisibility("!IsEmpty(%sListItem.TvShowTitle) + System.HasAddon(script.tv.show.next.aired)" %self.widgetcontainer_prefix):
                                    xbmc.executebuiltin("RunScript(script.tv.show.next.aired,tvshowtitle=%s)" %xbmc.getInfoLabel("%sListItem.TvShowTitle"%self.widgetcontainer_prefix).replace("&",""))
                                    nextairedActive = True
                                elif nextairedActive:
                                    nextairedActive = False
                                    xbmc.executebuiltin("RunScript(script.tv.show.next.aired,tvshowtitle=165628787629692696)")
                            except Exception as exc:
                                log_exception(__name__,exc)

                        # monitor listitem props when PVR is active
                        elif self.content_type in ["tvchannels","tvrecordings"]:
                            try:
                                self.set_duration()
                                thread.start_new_thread(self.set_pvr_artwork, (True,))
                                thread.start_new_thread(self.set_pvr_channellogo, (True,))
                                self.set_genre()
                            except Exception as exc:
                                log_exception(__name__,exc)

                    #set some globals
                    li_pathLast = self.li_path
                    last_listitem = curListItem

                self.monitor.waitForAbort(0.1)
                self.delayedTaskInterval += 0.1
            elif last_listitem and not self.exit:
                #flush any remaining window properties
                self.reset_win_props()
                WINDOW.clearProperty("SkinHelper.ContentHeader")
                WINDOW.clearProperty("content_type")
                self.content_type = ""
                if nextairedActive:
                    nextairedActive = False
                    xbmc.executebuiltin("RunScript(script.tv.show.next.aired,tvshowtitle=165628787629692696)")
                last_listitem = ""
                curListItem = ""
                cur_folder = ""
                cur_folder_last = ""
                self.widgetcontainer_prefix = ""
                self.monitor.waitForAbort(0.5)
                self.delayedTaskInterval += 0.5
            elif xbmc.getCondVisibility("Window.IsActive(fullscreenvideo)"):
                #fullscreen video active
                self.monitor.waitForAbort(2)
                self.delayedTaskInterval += 2
            else:
                #other window visible
                self.monitor.waitForAbort(0.5)
                self.delayedTaskInterval += 0.5

    def do_background_work(self):
        try:
            if self.exit: return
            log_msg("Started Background worker...")
            self.set_generic_props()
            self.check_notifications()
            log_msg("Ended Background worker...")
        except Exception as exc:
            log_exception(__name__,exc)

    def check_notifications(self):
        try:
            currentHour = time.strftime("%H")
            #weather notifications
            winw = xbmcgui.Window(12600)
            if xbmc.getCondVisibility("Skin.HasSetting(EnableWeatherNotifications) + !IsEmpty(Window(Weather).Property(Alerts.RSS)) + !IsEmpty(Window(Weather).Property(Current.Condition))") and currentHour != self.lastWeatherNotificationCheck:
                dialog = xbmcgui.Dialog()
                dialog.notification(xbmc.getLocalizedString(31294), winw.getProperty("Alerts"), xbmcgui.NOTIFICATION_WARNING, 8000)
                self.lastWeatherNotificationCheck = currentHour

            #nextaired notifications
            if (xbmc.getCondVisibility("Skin.HasSetting(EnableNextAiredNotifications) + System.HasAddon(script.tv.show.next.aired)") and currentHour != self.lastNextAiredNotificationCheck):
                if (WINDOW.getProperty("NextAired.TodayShow")):
                    dialog = xbmcgui.Dialog()
                    dialog.notification(xbmc.getLocalizedString(31295), WINDOW.getProperty("NextAired.TodayShow"), xbmcgui.NOTIFICATION_WARNING, 8000)
                    self.lastNextAiredNotificationCheck = currentHour
        except Exception as exc:
            log_exception(__name__,exc)

    def set_generic_props(self):

        #GET TOTAL ADDONS COUNT
        allAddonsCount = 0
        media_array = get_kodi_json('Addons.GetAddons','{ }')
        for item in media_array:
            allAddonsCount += 1
        WINDOW.setProperty("SkinHelper.TotalAddons",str(allAddonsCount))

        addontypes = []
        addontypes.append( ["executable", "SkinHelper.TotalProgramAddons", 0] )
        addontypes.append( ["video", "SkinHelper.TotalVideoAddons", 0] )
        addontypes.append( ["audio", "SkinHelper.TotalAudioAddons", 0] )
        addontypes.append( ["image", "SkinHelper.TotalPicturesAddons", 0] )

        for type in addontypes:
            media_array = get_kodi_json('Addons.GetAddons','{ "content": "%s" }' %type[0])
            for item in media_array:
                type[2] += 1
            WINDOW.setProperty(type[1],str(type[2]))

        #GET FAVOURITES COUNT
        allFavouritesCount = 0
        media_array = get_kodi_json('Favourites.GetFavourites','{ }')
        for item in media_array:
            allFavouritesCount += 1
        WINDOW.setProperty("SkinHelper.TotalFavourites",str(allFavouritesCount))

        #GET TV CHANNELS COUNT
        allTvChannelsCount = 0
        if xbmc.getCondVisibility("Pvr.HasTVChannels"):
            media_array = get_kodi_json('PVR.GetChannels','{"channelgroupid": "alltv" }' )
            for item in media_array:
                allTvChannelsCount += 1
        WINDOW.setProperty("SkinHelper.TotalTVChannels",str(allTvChannelsCount))

        #GET MOVIE SETS COUNT
        allMovieSetsCount = 0
        allMoviesInSetCount = 0
        media_array = get_kodi_json('VideoLibrary.GetMovieSets','{}' )
        for item in media_array:
            allMovieSetsCount += 1
            media_array2 = get_kodi_json('VideoLibrary.GetMovieSetDetails','{"setid": %s}' %item["setid"])
            for item in media_array2:
                allMoviesInSetCount +=1
        WINDOW.setProperty("SkinHelper.TotalMovieSets",str(allMovieSetsCount))
        WINDOW.setProperty("SkinHelper.TotalMoviesInSets",str(allMoviesInSetCount))

        #GET RADIO CHANNELS COUNT
        allRadioChannelsCount = 0
        if xbmc.getCondVisibility("Pvr.HasRadioChannels"):
            media_array = get_kodi_json('PVR.GetChannels','{"channelgroupid": "allradio" }' )
            for item in media_array:
                allRadioChannelsCount += 1
        WINDOW.setProperty("SkinHelper.TotalRadioChannels",str(allRadioChannelsCount))

    def reset_win_props(self):
        #reset all window props set by the script...
        process_method_on_list(WINDOW.clearProperty,self.all_window_props)
        self.all_window_props = []
    
    def reset_player_props(self):
        #reset all window props provided by the script...
        for prop in self.allPlayerWindowProps:
            WINDOW.clearProperty(try_encode(prop))
        self.allPlayerWindowProps = []
    
    def set_imdb_id(self):
        li_imdb = xbmc.getInfoLabel("%sListItem.IMDBNumber"%self.widgetcontainer_prefix).decode('utf-8')
        if not li_imdb: 
            li_imdb = xbmc.getInfoLabel("%sListItem.Property(IMDBNumber)"%self.widgetcontainer_prefix).decode('utf-8')
        if li_imdb and not li_imdb.startswith("tt"):
            if self.content_type in ["tvshows","seasons","episodes"]:
                self.li_tvdb = li_imdb
            li_imdb = ""
        if not li_imdb:
            title = self.li_title
            if self.content_type in ["episodes","seasons"]:
                title = xbmc.getInfoLabel("%sListItem.TvShowTitle"%self.widgetcontainer_prefix).decode('utf-8')
            if self.year and title:
                li_imdb = self.artutils.omdb.get_details_by_title(title,self.year,self.content_type).get("imdbnumber","")
        self.li_imdb = li_imdb
    
    def set_win_prop(self,prop_tuple):
        if prop_tuple[1]:
            self.all_window_props.append(prop_tuple[0])
            WINDOW.setProperty(prop_tuple[0],prop_tuple[1])
            #log_msg("Setting Window Property --> %s  value --> %s" %(prop_tuple[0],prop_tuple[1]), xbmc.LOGNOTICE)
    
    def set_win_props(self,items):
        process_method_on_list(self.set_win_prop,items)
            
    def set_player_prop(self,key,value):
        self.allPlayerWindowProps.append(key)
        WINDOW.setProperty(try_encode(key),try_encode(value))

    def set_movieset_details(self):
        if self.li_path.startswith("videodb://movies/sets/"):
            self.set_win_props( self.artutils.get_moviesetdetails(self.li_dbid, tuple_list_prefix="SkinHelper.MovieSet.") )
        
    def set_content_header(self):
        WINDOW.clearProperty("SkinHelper.ContentHeader")
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
                WINDOW.setProperty("SkinHelper.ContentHeader","%s %s" %(itemscount,headerprefix) )

    def set_addonname(self):
        # set addon name as property
        if not xbmc.Player().isPlayingAudio():
            if (xbmc.getCondVisibility("Container.Content(plugins) | !IsEmpty(Container.PluginName)")):
                AddonName = xbmc.getInfoLabel('Container.PluginName').decode('utf-8')
                AddonName = xbmcaddon.Addon(AddonName).getAddonInfo('name')
                self.set_win_prop(("SkinHelper.Player.AddonName", AddonName))

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
                self.cache.set(cacheStr,widget_details,expiration=timedelta(hours=2))
        #set the window props
        self.set_win_props(widget_details)

    def set_pvr_artwork(self, multi_threaded=False):
        title = self.li_title
        channel = xbmc.getInfoLabel("%sListItem.ChannelName"%self.widgetcontainer_prefix).decode('utf-8')
        if xbmc.getCondVisibility("%sListItem.IsFolder"%self.widgetcontainer_prefix) and not channel and not title:
            title = self.li_label
        if not xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnablePVRThumbs)") or not title:
            return
        genre = xbmc.getInfoLabel("%sListItem.Genre"%self.widgetcontainer_prefix).decode('utf-8')
        details = self.artutils.get_pvr_artwork(title, channel, self.year, genre, tuple_list_prefix="SkinHelper.ListItem.")
        if self.enable_legacy_props:
            details += self.artutils.get_pvr_artwork(title, channel, self.year, genre, tuple_list_prefix="SkinHelper.PVR.")#legacy!

        #return if another listitem was focused in the meanwhile
        if multi_threaded and not (title == xbmc.getInfoLabel("ListItem.Title").decode('utf-8') or title == xbmc.getInfoLabel("%sListItem.Title"%self.widgetcontainer_prefix).decode('utf-8') or title == xbmc.getInfoLabel("%sListItem.Label"%self.widgetcontainer_prefix).decode('utf-8')):
            return
        self.set_win_props(details)

    def set_pvr_channellogo(self, multi_threaded=False):
        channel = xbmc.getInfoLabel("%sListItem.ChannelName"%self.widgetcontainer_prefix).decode('utf-8')
        if not channel:
            return
        details = self.artutils.get_channellogo(channel,tuple_list_prefix="SkinHelper.ListItem.")
        if self.enable_legacy_props:
            details += self.artutils.get_channellogo(channel,tuple_list_prefix="SkinHelper.PVR.")#legacy!
        
        #return if another listitem was focused in the meanwhile
        if multi_threaded and not (channel == xbmc.getInfoLabel("%sListItem.ChannelName"%self.widgetcontainer_prefix).decode('utf-8')):
            return
        self.set_win_props(details)

    def set_studiologo(self):
        studio = xbmc.getInfoLabel('%sListItem.Studio'%self.widgetcontainer_prefix).decode('utf-8')
        if studio and logos_path:
            details = self.artutils.get_studio_logo(studio,tuple_list_prefix="SkinHelper.ListItem.")
            if self.enable_legacy_props:
                details += self.artutils.get_studio_logo(studio,tuple_list_prefix="SkinHelper.ListItem")#legacy!
            self.set_win_props( details )

    def set_duration(self):
        if not xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.DisableHoursDuration)"):
            duration = xbmc.getInfoLabel("%sListItem.Duration"%self.widgetcontainer_prefix)
            if duration:
                result = self.artutils.get_duration(duration, tuple_list_prefix='SkinHelper.ListItem.')
                if self.enable_legacy_props:
                    result += self.artutils.get_duration(duration, tuple_list_prefix='SkinHelper.ListItem')#legacy
                self.set_win_props( result )

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

    def set_musicdetails(self,multi_threaded=False):
        artist = xbmc.getInfoLabel("%sListItem.Artist"%self.widgetcontainer_prefix).decode('utf-8')
        album = xbmc.getInfoLabel("%sListItem.Album"%self.widgetcontainer_prefix).decode('utf-8')
        title = self.li_title
        label = self.li_label
        details = self.artutils.get_musicartwork(artist,album,title,tuple_list_prefix="SkinHelper.ListItem.")
        if self.enable_legacy_props:
            details += self.artutils.get_musicartwork(artist,album,title,tuple_list_prefix="SkinHelper.Music.")#legacy!
        #return if another listitem was focused in the meanwhile
        if multi_threaded and label != xbmc.getInfoLabel("%sListItem.Label"%self.widgetcontainer_prefix).decode('utf-8'):
            return
        self.set_win_props(details)

    def set_streamdetails(self):
        if self.li_dbid and self.content_type in ["movies","episodes","musicvideos"]:
            details = self.artutils.get_streamdetails(self.li_dbid,self.content_type,tuple_list_prefix='SkinHelper.ListItem')
            if self.enable_legacy_props:
                details += self.artutils.get_streamdetails(self.li_dbid,self.content_type,tuple_list_prefix='SkinHelper.ListItem')#legacy!
            self.set_win_props( details )

    def setForcedView(self):
        currentForcedView = xbmc.getInfoLabel("Skin.String(SkinHelper.ForcedViews.%s)" %self.content_type)
        if xbmc.getCondVisibility("Control.IsVisible(%s) | IsEmpty(Container.Viewmode)" %currentForcedView):
            #skip if the view is already visible or if we're not in an actual media window
            return
        if self.content_type and currentForcedView and currentForcedView != "None" and xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.ForcedViews.Enabled)") and not "pvr://guide" in self.li_path:
            WINDOW.setProperty("SkinHelper.ForcedView",currentForcedView)
            xbmc.executebuiltin("Container.SetViewMode(%s)" %currentForcedView)
            if not xbmc.getCondVisibility("Control.HasFocus(%s)" %currentForcedView):
                xbmc.sleep(100)
                xbmc.executebuiltin("Container.SetViewMode(%s)" %currentForcedView)
                xbmc.executebuiltin("SetFocus(%s)" %currentForcedView)
        else:
            WINDOW.clearProperty("SkinHelper.ForcedView")

    def set_extrafanart(self):
        if xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnableExtraFanart)"):
            if self.content_type in ["movies","seasons","episodes","tvshows","setmovies","moviesets"]:
                details = self.artutils.get_extrafanart(self.li_dbid,self.content_type, tuple_list_prefix='SkinHelper.ListItem.')
                if self.enable_legacy_props:
                    details += self.artutils.get_extrafanart(self.li_dbid,self.content_type, tuple_list_prefix='SkinHelper.')#legacy!
                self.set_win_props( details )

    def set_animatedart(self,multi_threaded=False):
        #check animated posters
        title = self.li_title
        if self.li_imdb and xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnableAnimatedPosters)"):
            result = self.artutils.get_animated_artwork(self.li_imdb, tuple_list_prefix="SkinHelper.ListItem.")
            if self.enable_legacy_props:
                result += self.artutils.get_animated_artwork(self.li_imdb, tuple_list_prefix="SkinHelper.")#legacy!
            if multi_threaded and not title == xbmc.getInfoLabel("%sListItem.Title"%self.widgetcontainer_prefix).decode('utf-8'):
                return
            self.set_win_props( result )

    def set_omdb_info(self,multi_threaded=False):
        if self.li_imdb:
            title = self.li_title
            result = self.artutils.get_omdb_info(self.li_imdb, tuple_list_prefix="SkinHelper.ListItem.")
            if self.enable_legacy_props:
                result += self.artutils.get_omdb_info(self.li_imdb, tuple_list_prefix="SkinHelper.")#legacy!
            #return if another listitem was focused in the meanwhile
            if multi_threaded and not title == xbmc.getInfoLabel("%sListItem.Title"%self.widgetcontainer_prefix).decode('utf-8'):
                return
            #set properties
            self.set_win_props(result)
    
    def set_top250(self):
        if self.li_imdb:
            result = self.artutils.get_top250_rating(self.li_imdb,tuple_list_prefix="SkinHelper.ListItem.")
            if self.enable_legacy_props:
                result += self.artutils.get_top250_rating(self.li_imdb,tuple_list_prefix="SkinHelper.")
            self.set_win_props(result)
    
    def set_tmdb_info(self,multi_threaded=False):
        title = self.li_title
        result = self.artutils.get_tmdb_details(self.li_imdb, self.li_tvdb, self.li_title, self.year, self.content_type, tuple_list_prefix="SkinHelper.ListItem.TMDB.")
        if self.enable_legacy_props:
            result += self.artutils.get_tmdb_details(self.li_imdb, self.li_tvdb, self.li_title, self.year, self.content_type, tuple_list_prefix="SkinHelper.TMDB.")
        #return if another listitem was focused in the meanwhile
        if multi_threaded and not title == xbmc.getInfoLabel("%sListItem.Title"%self.widgetcontainer_prefix).decode('utf-8'):
            return
        self.set_win_props(result)

    def set_extended_artwork(self, multi_threaded=False):
        #try to lookup additional artwork
        title = self.li_title
        result = self.artutils.get_extended_artwork(self.li_imdb, self.li_tvdb, self.li_title, self.year, self.content_type, tuple_list_prefix="SkinHelper.ListItem.")
        if self.enable_legacy_props:
            result += self.artutils.get_extended_artwork(self.li_imdb, self.li_tvdb, self.li_title, self.year, self.content_type, tuple_list_prefix="SkinHelper.PVR.")
        #return if another listitem was focused in the meanwhile
        if multi_threaded and not title == xbmc.getInfoLabel("%sListItem.Title"%self.widgetcontainer_prefix).decode('utf-8'):
            return
        self.set_win_props(result)
