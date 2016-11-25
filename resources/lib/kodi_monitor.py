#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    script.skin.helper.service
    kodi_monitor.py
    monitor all kodi events
'''

from utils import log_msg, json
from artutils import process_method_on_list
from simplecache import use_cache
import xbmc
import time


class KodiMonitor(xbmc.Monitor):
    '''Monitor all events in Kodi'''
    update_video_widgets_busy = False
    update_music_widgets_busy = False
    all_window_props = []
    last_title = ""

    def __init__(self, **kwargs):
        xbmc.Monitor.__init__(self)
        self.cache = kwargs.get("cache")
        self.artutils = kwargs.get("artutils")
        self.win = kwargs.get("win")

    # def onDatabaseUpdated(self,database):
        # log_msg("Kodi_Monitor: onDatabaseUpdated: " + database)
        # if database == "video":
        # self.process_videodb_updated("",True)
        # artutils.preCacheAllAnimatedArt()
        # if database == "music" :
        # self.process_musicdb_updated({},True)

    def onNotification(self, sender, method, data):
        '''builtin function for the xbmc.Monitor class'''
        log_msg("Kodi_Monitor: sender %s - method: %s  - data: %s" % (sender, method, data))

        if method == "System.OnQuit":
            self.win.setProperty("SkinHelperShutdownRequested", "shutdown")

        if method == "VideoLibrary.OnUpdate":
            self.process_db_update(data)

        if method == "AudioLibrary.OnUpdate":
            self.process_db_update(data)

        if method == "Player.OnStop":
            log_msg("Playback ended !")
            self.last_title = ""
            self.win.clearProperty("Skinhelper.PlayerPlaying")
            self.win.clearProperty("TrailerPlaying")
            self.reset_win_props()
            self.last_title = ""

        if method == "Player.OnPlay" and not self.last_title:
            log_msg("Playback started !")
            self.reset_win_props()
            while xbmc.getCondVisibility("IsEmpty(Player.Title) | !Player.HasMedia"):
                log_msg("waiting for player...")
                xbmc.sleep(100)
            if xbmc.getCondVisibility("Player.HasAudio"):
                if xbmc.getCondVisibility("Player.IsInternetStream"):
                    log_msg("Monitoring radio stream !", xbmc.LOGNOTICE)
                    self.monitor_radiostream()
                else:
                    self.set_music_properties()
            if xbmc.getCondVisibility("VideoPlayer.Content(livetv)"):
                self.monitor_livetv()
            else:
                self.set_video_properties()
                self.show_info_panel()

    def refresh_music_widgets(self, media_type):
        '''refresh music widgets'''
        if not self.update_music_widgets_busy:
            self.update_music_widgets_busy = True
            log_msg("Music database changed - type: %s - refreshing widgets...." % media_type)
            xbmc.sleep(500)
            timestr = time.strftime("%Y%m%d%H%M%S", time.gmtime())
            self.win.setProperty("widgetreload-music", timestr)
            self.win.setProperty("widgetreloadmusic", timestr)
            if media_type:
                self.win.setProperty("widgetreload-%ss" % media_type, timestr)
            self.update_music_widgets_busy = False

    def refresh_video_widgets(self, media_type):
        '''refresh video widgets'''
        if not self.update_video_widgets_busy:
            self.update_video_widgets_busy = True
            log_msg("Video database changed - type: %s - refreshing widgets...." % media_type)
            xbmc.sleep(500)
            timestr = time.strftime("%Y%m%d%H%M%S", time.gmtime())
            self.win.setProperty("widgetreload", timestr)
            if media_type:
                self.win.setProperty("widgetreload-%ss" % media_type, timestr)
            self.update_video_widgets_busy = False

    def process_db_update(self, data):
        '''precache/refresh items when a kodi db item gets updated/added'''
        media_type = ""
        dbid = 0
        if data:
            data = json.loads(data.decode('utf-8'))
            if data and data.get("item"):
                media_type = data["item"].get("type", "")
                dbid = data["item"].get("id", 0)

        # refresh widgets
        if media_type in ["song", "artist", "album"]:
            self.refresh_music_widgets(media_type)
        else:
            self.refresh_video_widgets(media_type)

        # item specific actions
        if dbid and media_type == "movie":
            movie = self.artutils.kodidb.movie(dbid)
            imdb_id = movie["imdbnumber"]
            if imdb_id:
                self.artutils.get_animated_artwork(imdb_id)
        if dbid and media_type in ["movie", "episode", "musicvideo"]:
            self.artutils.get_streamdetails(dbid, media_type, ignore_cache=True)
        if dbid and media_type == "song":
            song = self.artutils.kodidb.song(dbid)
            self.artutils.get_music_artwork(
                song["artist"][0], song["album"], song["title"], str(
                    song["disc"], ignore_cache=True))
        elif dbid and media_type == "album":
            song = self.artutils.kodidb.album(dbid)
            self.artutils.get_music_artwork(item["artist"][0], item["title"], ignore_cache=True)
        elif dbid and media_type == "artist":
            song = self.artutils.kodidb.artist(dbid)
            self.artutils.get_music_artwork(item["artist"], ignore_cache=True)

    def reset_win_props(self):
        '''reset all window props set by the script...'''
        process_method_on_list(self.win.clearProperty, self.all_window_props)
        self.all_window_props = []

    def set_win_prop(self, prop_tuple):
        '''set window property from key/value tuple'''
        if prop_tuple[1] and not prop_tuple[0] in self.all_window_props:
            self.all_window_props.append(prop_tuple[0])
            self.win.setProperty(prop_tuple[0], prop_tuple[1])

    @staticmethod
    def prepare_win_props(details):
        '''helper to pretty string-format a dict with details so it can be used as window props'''
        items = []
        if details:
            for key, value in details.iteritems():
                if value:
                    key = u"SkinHelper.Player.%s" % key
                    if isinstance(value, (str, unicode)):
                        items.append((key, value))
                    elif isinstance(value, (int, float)):
                        items.append((key, "%s" % value))
                    elif isinstance(value, dict):
                        for key2, value2 in value.iteritems():
                            if isinstance(value2, (str, unicode)):
                                items.append((u"%s.%s" % (key, key2), value2))
                    elif isinstance(value, list):
                        list_strings = []
                        for listvalue in value:
                            if isinstance(listvalue, (str, unicode)):
                                list_strings.append(listvalue)
                        if list_strings:
                            items.append((key, u" / ".join(list_strings)))
                        elif len(value) == 1 and isinstance(value[0], (str, unicode)):
                            items.append((key, value))
        return items

    def show_info_panel(self):
        '''feature to auto show the OSD infopanel for X seconds'''
        try:
            sec_to_display = int(xbmc.getInfoLabel("Skin.String(SkinHelper.ShowInfoAtPlaybackStart)"))
        except Exception:
            return
        log_msg("ShowInfoAtPlaybackStart - number of seconds: %s" % sec_to_display)
        if sec_to_display > 0:
            retries = 0
            if self.win.getProperty("VideoScreensaverRunning") != "true":
                while retries != 50 and xbmc.getCondVisibility("!Player.ShowInfo"):
                    xbmc.sleep(100)
                    if xbmc.getCondVisibility("!Player.ShowInfo + Window.IsActive(fullscreenvideo)"):
                        xbmc.executebuiltin('Action(info)')
                    retries += 1

                # close info again after given amount of time
                xbmc.Monitor().waitForAbort(sec_to_display)
                if xbmc.getCondVisibility("Player.ShowInfo"):
                    xbmc.executebuiltin('Action(info)')

    def set_video_properties(self):
        '''sets the window props for a playing video item'''
        content_type = self.get_content_type()
        li_title = xbmc.getInfoLabel("Player.Title").decode('utf-8')
        li_year = xbmc.getInfoLabel("Player.Year").decode('utf-8')
        li_dbid = xbmc.getInfoLabel("VideoPlayer.DBID").decode('utf-8')
        if li_dbid == "-1":
            li_dbid = ""
        li_imdb = xbmc.getInfoLabel("VideoPlayer.IMDBNumber").decode('utf-8')
        li_showtitle = xbmc.getInfoLabel("VideoPlayer.TvShowTitle").decode('utf-8')
        self.last_title = li_title
        all_props = []

        log_msg("playermonitor set_video_properties  - title: %s  - contenttype: %s" % (li_title, content_type))

        # video content
        if content_type in ["movies", "episodes", "musicvideos"]:

            # get imdb_id
            li_imdb, li_tvdb = self.get_imdb_id(li_imdb, li_title, li_year, li_showtitle, content_type)

            # generic video properties (studio, streamdetails, omdb, top250)
            all_props += self.prepare_win_props(self.artutils.get_omdb_info(li_imdb))
            if li_dbid:
                all_props += self.prepare_win_props(self.artutils.get_streamdetails(li_dbid, content_type))
            all_props += self.prepare_win_props(self.artutils.get_top250_rating(li_imdb))

            if xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnableExtendedArt)"):
                all_props += self.prepare_win_props(self.artutils.get_extended_artwork(
                    li_imdb, li_tvdb, content_type))

            # tvshows-only properties (tvdb)
            if content_type == "episodes":
                all_props += self.prepare_win_props(self.artutils.get_tvdb_details(li_imdb, li_tvdb))

            # movies-only properties (tmdb, animated art)
            if content_type == "movies":
                all_props += self.prepare_win_props(self.artutils.get_tmdb_details(li_imdb))
                if li_imdb and xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnableAnimatedPosters)"):
                    all_props += self.prepare_win_props(self.artutils.get_animated_artwork(li_imdb))

        if self.last_title == li_title:
            process_method_on_list(self.set_win_prop, all_props)

    def set_music_properties(self):
        '''sets the window props for a playing song'''
        li_title = xbmc.getInfoLabel("MusicPlayer.Title").decode('utf-8')
        li_artist = xbmc.getInfoLabel("MusicPlayer.Artist").decode('utf-8')
        li_album = xbmc.getInfoLabel("MusicPlayer.Album").decode('utf-8')
        li_disc = xbmc.getInfoLabel("MusicPlayer.DiscNumber").decode('utf-8')

        if not li_artist:
            # fix for internet streams
            splitchar = None
            if " - " in li_title:
                splitchar = " - "
            elif "- " in li_title:
                splitchar = "- "
            elif " -" in li_title:
                splitchar = " -"
            elif "-" in li_title:
                splitchar = "-"
            if splitchar:
                li_artist = li_title.split(splitchar)[0]
                li_title = li_title.split(splitchar)[1]

        if xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnableMusicArt)"):
            self.last_title = li_title
            log_msg(
                "playermonitor setmusicproperties  - artist: %s  - album: %s  - track: %s" %
                (li_artist, li_album, li_title))
            result = self.artutils.get_music_artwork(li_artist, li_album, li_title, li_disc)
            all_props = self.prepare_win_props(result)
            if self.last_title == li_title:
                process_method_on_list(self.set_win_prop, all_props)

    def monitor_radiostream(self):
        '''
            for radiostreams we are not notified when the track changes
            so we have to monitor that ourself
        '''
        while not self.abortRequested() and xbmc.getCondVisibility("Player.HasAudio"):
            #check details every 5 seconds
            cur_title = xbmc.getInfoLabel("$INFO[MusicPlayer.Artist]-$INFO[MusicPlayer.Title]").decode('utf-8')
            if cur_title != self.last_title:
                self.last_title = cur_title
                self.reset_win_props()
                self.set_music_properties()
            self.waitForAbort(5)
            
    def monitor_livetv(self):
        '''
            for livetv we are not notified when the program changes
            so we have to monitor that ourself
        '''
        while not self.abortRequested() and xbmc.getCondVisibility("Player.HasVideo"):
            #check details every 5 seconds
            li_title = xbmc.getInfoLabel("Player.Title").decode('utf-8')
            if li_title != self.last_title:
                all_props = []
                self.last_title = li_title
                self.reset_win_props()
                li_channel = xbmc.getInfoLabel("VideoPlayer.ChannelName").decode('utf-8')
                # pvr artwork
                if xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.EnablePVRThumbs)"):
                    li_genre = xbmc.getInfoLabel("VideoPlayer.Genre").decode('utf-8')
                    pvrart = self.artutils.get_pvr_artwork(li_title, li_channel, li_genre)
                    all_props += self.prepare_win_props(pvrart)
                # pvr channellogo
                all_props.append(("SkinHelper.Player.ChannelLogo", self.artutils.get_channellogo(li_channel)))
                if self.last_title == li_title:
                    process_method_on_list(self.set_win_prop, all_props)
            self.waitForAbort(5)

    @staticmethod
    def get_content_type():
        '''get current content type'''
        if xbmc.getCondVisibility("VideoPlayer.Content(movies)"):
            content_type = "movies"
        elif xbmc.getCondVisibility("VideoPlayer.Content(episodes) | !IsEmpty(VideoPlayer.TvShowTitle)"):
            content_type = "episodes"
        elif xbmc.getInfoLabel("VideoPlayer.Content(musicvideos) | !IsEmpty(VideoPlayer.Artist)"):
            content_type = "musicvideos"
        else:
            content_type = "files"
        return content_type

    @use_cache(14)
    def get_imdb_id(self, li_imdb, li_title, li_year, li_showtitle, content_type):
        '''try to figure out the imdbnumber because that's what we use for all lookup actions'''
        li_tvdb = ""
        if content_type == "episodes":
            li_title = li_showtitle
            content_type = "tvshows"
        if li_imdb and not li_imdb.startswith("tt"):
            if content_type == "episodes":
                li_tvdb = li_imdb
                li_imdb = ""
        if not li_imdb and li_year:
            li_imdb = self.artutils.get_omdb_info("", li_title, li_year, content_type).get("imdbnumber", "")
        if not li_imdb:
            # repeat without year
            li_imdb = self.artutils.get_omdb_info("", li_title, "", content_type).get("imdbnumber", "")
        # return results
        return (li_imdb, li_tvdb)
