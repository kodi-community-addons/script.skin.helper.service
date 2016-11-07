#!/usr/bin/python
# -*- coding: utf-8 -*-

import threading
import random
import io
import base64
import os
from datetime import timedelta, datetime
from utils import log_msg, log_exception, kodi_json, get_content_path, get_clean_image
import xbmc
import xbmcvfs
from simplecache import use_cache, SimpleCache
from conditional_backgrounds import DATE_FORMAT, CACHE_FILE


class BackgroundsUpdater(threading.Thread):

    event = None
    exit = False
    all_backgrounds = {}
    tempBlacklist = set()
    smartShortcuts = {}

    backgrounds_delay = 0
    walls_delay = 0
    lastWindow = None
    manualWallsLoaded = list()
    manualWalls = {}
    smartShortcutsFirstRunDone = False

    all_backgrounds_keys = []

    def __init__(self, *args, **kwargs):
        self.cache = kwargs.get("cache")
        self.artutils = kwargs.get("artutils")
        self.win = kwargs.get("win")
        self.kodimonitor = kwargs.get("monitor")
        self.event = threading.Event()
        threading.Thread.__init__(self, *args)

    def stop(self):
        log_msg("BackgroundsUpdater - stop called")
        self.exit = True
        self.event.set()

    def run(self):
        log_msg("BackgroundsUpdater - started")
        self.get_skinconfig()
        backgrounds_task_interval = 30
        walls_task_interval = 30

        while not self.exit:

            # Process backgrounds
            if xbmc.getCondVisibility(
                "![Window.IsActive(fullscreenvideo) | Window.IsActive(script.pseudotv.TVOverlay.xml) | "
                    "Window.IsActive(script.pseudotv.live.TVOverlay.xml)] | "
                    "Window.IsActive(script.pseudotv.live.EPG.xml)"):

                self.get_skinconfig()
                # force refresh smart shortcuts on request
                # if WINDOW.getProperty("refreshsmartshortcuts") and self.smartShortcutsFirstRunDone:
                # try: self.update_smartshortcuts(True)
                # except Exception as e: log_msg(format_exc(sys.exc_info()),xbmc.LOGERROR)
                # WINDOW.clearProperty("refreshsmartshortcuts")

                # Update home backgrounds every interval (if enabled by skinner)
                if self.backgrounds_delay != 0:
                    if (backgrounds_task_interval >= self.backgrounds_delay):
                        backgrounds_task_interval = 0
                        try:
                            self.update_backgrounds()
                            # self.update_smartshortcuts()
                            # self.update_wallbackgrounds()
                        except Exception as e:
                            log_exception(__name__, e)

                # Update manual wall images - if enabled by the skinner
                if self.walls_delay != 0:
                    if (walls_task_interval >= self.walls_delay):
                        walls_task_interval = 0
                        try:
                            self.updateWallImages()
                        except Exception as e:
                            log_exception(__name__, e)

            self.kodimonitor.waitForAbort(5)
            backgrounds_task_interval += 5
            walls_task_interval += 5

    def get_skinconfig(self):
        # gets the settings for the script as set by the skinner..
        try:
            self.backgrounds_delay = int(xbmc.getInfoLabel("Skin.String(SkinHelper.RandomFanartDelay)"))
        except Exception as e:
            log_exception(__name__, e)
            self.backgrounds_delay = 0
        self.custom_picturespath = xbmc.getInfoLabel(
            "skin.string(SkinHelper.CustomPicturesBackgroundPath)").decode("utf-8")

        try:
            walls_delay = xbmc.getInfoLabel("Skin.String(SkinHelper.wallImagesDelay)")
            if walls_delay:
                self.walls_delay = int(walls_delay)
                # enumerate through all background collections to check wether we should want a wall collection provided
                # store in memory so wo do not have to query the skin settings too often
                if self.walls_delay != 0:
                    for key, value in self.all_backgrounds.iteritems():
                        if value:
                            limitrange = xbmc.getInfoLabel("Skin.String(%s.EnableWallImages)" % key)
                            if limitrange:
                                self.manualWalls[key] = int(limitrange)
        except Exception as e:
            log_exception(__name__, e)
            self.walls_delay = 0

    @use_cache(0.1)
    def get_cond_backgrounds(self):
        all_backgrounds = []
        if xbmcvfs.exists(CACHE_FILE):
            text_file = xbmcvfs.File(CACHE_FILE)
            all_backgrounds = eval(text_file.read())
            text_file.close()
        return all_backgrounds

    def get_cond_background(self):
        background = ""
        all_cond_backgrounds = self.get_cond_backgrounds()
        if all_cond_backgrounds:
            date_today = datetime.now().strftime(DATE_FORMAT)
            for bg in all_cond_backgrounds:
                if time_in_range(bg["startdate"], bg["enddate"], date_today):
                    background = bg["background"]
                    break
        return background

    @use_cache(2, True)
    def get_images_from_path(self, lib_path):
        result = []
        # safety check: check if no library windows are active to prevent any addons setting the view
        if xbmc.getCondVisibility("Window.IsMedia") or self.exit:
            return None

        lib_path = get_content_path(lib_path)
        if "plugin.video.emby" in lib_path and "browsecontent" in lib_path and "filter" not in lib_path:
            lib_path = lib_path + "&filter=random"
        for media in self.artutils.kodidb.files(lib_path)[:100]:
            image = {}
            if media['label'].lower() == "next page":
                continue
            if media.get('art'):
                if media['art'].get('fanart'):
                    image["fanart"] = get_clean_image(media['art']['fanart'])
                elif media['art'].get('tvshow.fanart'):
                    image["fanart"] = get_clean_image(media['art']['tvshow.fanart'])
                if media['art'].get('thumb'):
                    image["thumbnail"] = get_clean_image(media['art']['thumb'])
            elif not media.get('fanart'):
                image["fanart"] = media.get('fanart', '')
            if not image.get("thumbnail"):
                image["thumbnail"] = media.get("thumbnail", "")

            # only append items which have a fanart image
            if image.get("fanart"):
                # also append other art to the dict
                image["title"] = media.get('title', media['label'])
                image["landscape"] = media.get('art', {}).get('landscape', '')
                image["poster"] = media.get('art', {}).get('poster', '')
                image["clearlogo"] = media.get('art', {}).get('clearlogo', '')
                result.append(image)
        return result

    def setPicturesBackground(self, win_prop):

        images = []
        # get images from cache
        cache = self.cache.get(win_prop, checksum=self.custom_picturespath)
        if cache:
            images = cache
        else:
            # load the pictures from the custom path or from all picture sources
            if self.custom_picturespath:
                # load images from custom path
                dirs, files = xbmcvfs.listdir(self.custom_picturespath)
                # pick all images from path
                for file in files:
                    if file.lower().endswith(".jpg") or file.lower().endswith(".png"):
                        image = os.path.join(self.custom_picturespath, file.decode("utf-8"))
                        images.append({"fanart": image, "title": file.decode("utf-8")})
            else:
                # load pictures from all sources
                media_array = kodi_json('Files.GetSources', {"media": "pictures"})
                for source in media_array:
                    if 'file' in source:
                        if "plugin://" not in source["file"]:
                            dirs, files = xbmcvfs.listdir(source["file"])
                            if dirs:
                                # pick 10 random dirs
                                randomdirs = []
                                randomdirs.append(
                                    os.path.join(source["file"], random.choice(dirs).decode("utf-8", "ignore")))
                                randomdirs.append(
                                    os.path.join(source["file"], random.choice(dirs).decode("utf-8", "ignore")))
                                randomdirs.append(
                                    os.path.join(source["file"], random.choice(dirs).decode("utf-8", "ignore")))
                                randomdirs.append(
                                    os.path.join(source["file"], random.choice(dirs).decode("utf-8", "ignore")))
                                randomdirs.append(
                                    os.path.join(source["file"], random.choice(dirs).decode("utf-8", "ignore")))
                                randomdirs.append(
                                    os.path.join(source["file"], random.choice(dirs).decode("utf-8", "ignore")))
                                randomdirs.append(
                                    os.path.join(source["file"], random.choice(dirs).decode("utf-8", "ignore")))
                                randomdirs.append(
                                    os.path.join(source["file"], random.choice(dirs).decode("utf-8", "ignore")))
                                randomdirs.append(
                                    os.path.join(source["file"], random.choice(dirs).decode("utf-8", "ignore")))
                                randomdirs.append(
                                    os.path.join(source["file"], random.choice(dirs).decode("utf-8", "ignore")))

                                # pick 5 images from each dir
                                for dir in randomdirs:
                                    subdirs, files2 = xbmcvfs.listdir(dir)
                                    count = 0
                                    for file in files2:
                                        if ((file.endswith(".jpg") or file.endswith(".png") or file.endswith(
                                                ".JPG") or file.endswith(".PNG")) and count < 5):
                                            image = os.path.join(dir, file.decode("utf-8", "ignore"))
                                            images.append({"fanart": image, "title": file})
                                            count += 1
                            if files:
                                # pick 10 images from root
                                count = 0
                                for file in files:
                                    if ((file.endswith(".jpg") or file.endswith(".png") or file.endswith(
                                            ".JPG") or file.endswith(".PNG")) and count < 10):
                                        image = os.path.join(source["file"], file.decode("utf-8", "ignore"))
                                        images.append({"fanart": image, "title": file})
                                        count += 1

            # store images in the cache
            self.cache.set(win_prop, images, checksum=self.custom_picturespath, expiration=timedelta(days=7))

        # return a random image
        if images:
            random.shuffle(images)
            image = images[0]
            for key, value in image.iteritems():
                if key == "fanart":
                    self.win.setProperty(win_prop, value)
                else:
                    self.win.setProperty(win_prop + "." + key, value)

    @use_cache(0.1)
    def get_global_background(self, win_prop, keys):
        images = []
        for key in keys:
            if win_prop in self.all_backgrounds_keys:
                images += self.get_images_from_path(key)
        return images

    def set_background(self, win_prop, images, fallback_image=""):
        if images:
            if win_prop not in self.all_backgrounds_keys:
                self.all_backgrounds_keys.append(win_prop)
            image = random.choice(images)
            for key, value in image.iteritems():
                if key == "fanart":
                    self.win.setProperty(win_prop, value)
                else:
                    self.win.setProperty("%s.%s" % (win_prop, key), value)
        else:
            self.win.setProperty(win_prop, fallback_image)

    def set_global_background(self, win_prop, keys):
        # gets a random background from multiple other collections
        images = self.get_global_background(win_prop, keys=keys)
        self.set_background(win_prop, images)

    def update_backgrounds(self):

        # conditional background
        self.win.setProperty("SkinHelper.ConditionalBackground", self.get_cond_background())

        # movies backgrounds
        if xbmc.getCondVisibility("Library.HasContent(movies)"):
            self.set_background("SkinHelper.AllMoviesBackground",
                                self.get_images_from_path("videodb://movies/titles/"))
            self.set_background("SkinHelper.InProgressMoviesBackground", self.get_images_from_path(
                "plugin://script.skin.helper.widgets?mediatype=movies&action=inprogress&limit=50"))
            self.set_background("SkinHelper.RecentMoviesBackground",
                                self.get_images_from_path("videodb://recentlyaddedmovies/"))
            self.set_background("SkinHelper.UnwatchedMoviesBackground", self.get_images_from_path(
                "plugin://script.skin.helper.widgets?mediatype=movies&action=unwatched&limit=50"))

        # tvshows backgrounds
        if xbmc.getCondVisibility("Library.HasContent(tvshows)"):
            self.set_background("SkinHelper.AllTvShowsBackground",
                                self.get_images_from_path("videodb://tvshows/titles/"))
            self.set_background("SkinHelper.InProgressShowsBackground", self.get_images_from_path(
                "plugin://script.skin.helper.widgets?mediatype=tvshows&action=inprogress&limit=50"))
            self.set_background("SkinHelper.RecentEpisodesBackground",
                                self.get_images_from_path("videodb://recentlyaddedepisodes/"))

        # all musicvideos
        if xbmc.getCondVisibility("Library.HasContent(musicvideos)"):
            self.set_background("SkinHelper.AllMusicVideosBackground",
                                self.get_images_from_path("videodb://musicvideos/titles"))

        # all music
        if xbmc.getCondVisibility("Library.HasContent(music)"):
            self.set_background("SkinHelper.AllMusicBackground",
                                self.get_images_from_path("musicdb://artists/"))
            self.set_background("SkinHelper.AllMusicSongsBackground", self.get_images_from_path(
                "plugin://script.skin.helper.widgets/?mediatype=songs&action=random&limit=50"))
            self.set_background("SkinHelper.RecentMusicBackground", self.get_images_from_path(
                "plugin://script.skin.helper.widgets/?mediatype=albums&action=recent&limit=50"))

        # tmdb backgrounds (extendedinfo)
        if xbmc.getCondVisibility("System.HasAddon(script.extendedinfo)"):
            self.set_background("SkinHelper.TopRatedMovies",
                                self.get_images_from_path("plugin://script.extendedinfo/?info=topratedmovies"))
            self.set_background("SkinHelper.TopRatedShows",
                                self.get_images_from_path("plugin://script.extendedinfo/?info=topratedtvshows"))

        # pictures background
        self.setPicturesBackground("SkinHelper.PicturesBackground")

        # pvr background
        if xbmc.getCondVisibility("PVR.HasTvChannels"):
            self.set_background("SkinHelper.PvrBackground", self.get_images_from_path(
                "plugin://script.skin.helper.widgets/?mediatype=pvr&action=recordings&limit=50"))

        # global backgrounds
        if xbmc.getCondVisibility("![Library.HasContent(movies) | Library.HasContent(tvshows) | "
                                  "Library.HasContent(music)] + System.HasAddon(script.extendedinfo)"):
            self.set_global_background(
                "SkinHelper.GlobalFanartBackground", [
                    "SkinHelper.TopRatedMovies", "SkinHelper.TopRatedShows"])
        else:
            self.set_global_background("SkinHelper.GlobalFanartBackground",
                                       ["SkinHelper.AllMoviesBackground",
                                        "SkinHelper.AllTvShowsBackground",
                                        "SkinHelper.AllMusicVideosBackground",
                                        "SkinHelper.AllMusicBackground"])
            self.set_global_background("SkinHelper.AllVideosBackground",
                                       ["SkinHelper.AllMoviesBackground",
                                        "SkinHelper.AllTvShowsBackground",
                                        "SkinHelper.AllMusicVideosBackground"])
            self.set_global_background(
                "SkinHelper.AllVideosBackground2", [
                    "SkinHelper.AllMoviesBackground", "SkinHelper.AllTvShowsBackground"])
            self.set_global_background(
                "SkinHelper.RecentVideosBackground", [
                    "SkinHelper.RecentMoviesBackground", "SkinHelper.RecentEpisodesBackground"])
            self.set_global_background(
                "SkinHelper.InProgressVideosBackground", [
                    "SkinHelper.InProgressMoviesBackground", "SkinHelper.InProgressShowsBackground"])
