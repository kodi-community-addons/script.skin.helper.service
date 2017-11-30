#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
    script.skin.helper.service
    Helper service and scripts for Kodi skins
    webservice.py
    Simple webservice to directly retrieve metadata from artwork module
'''

import cherrypy
import threading
from utils import log_msg, log_exception, json
import xbmc
import xbmcvfs
import sys

# port is hardcoded as there is no way in Kodi to pass a INFO-label inside a panel,
# otherwise the portnumber could be passed to the skin through a skin setting or window prop
PORT = 52307


class Root:
    __mutils = None

    def __init__(self, mutils):
        self.__mutils = mutils

    @cherrypy.expose
    def default(self, path):
        '''all other requests go here'''
        log_msg("Webservice: Unknown method called ! (%s)" % path, xbmc.LOGWARNING)
        raise cherrypy.HTTPError(404, "Unknown method called")

    @cherrypy.expose
    def getartwork(self, **kwargs):
        '''get video artwork and metadata'''
        log_msg("webservice.getartwork called with args: %s" % kwargs)
        title = kwargs.get("title", "")
        year = kwargs.get("year", "")
        media_type = kwargs.get("mediatype", "")
        imdb_id = kwargs.get("imdbid", "")
        artwork = {}
        if not kwargs.get("type"):
            kwargs["json"] = "true"
        if not imdb_id:
            omdb_details = self.__mutils.get_omdb_info(imdb_id, title, year, media_type)
            if omdb_details:
                imdb_id = omdb_details.get("imdbnumber")
                if not media_type:
                    media_type = omdb_details.get("media_type","")
        if imdb_id:
            artwork = self.__mutils.get_extended_artwork(imdb_id, "", "", media_type)
        return self.handle_artwork(artwork, kwargs)

    def genreimages(self, params):
        '''get images for given genre'''
        log_msg("webservice.genreimages called with args: %s" % params)
        genre = params.get("title", "")
        arttype = params.get("type", "").split(".")[0]
        mediatype = params["mediatype"]
        randomize = params["randomize"]
        artwork = {}
        lib_path = u"plugin://script.skin.helper.service/?action=genrebackground"\
            "&genre=%s&arttype=%s&mediatype=%s&random=%s" % (genre, arttype, mediatype, randomize)
        for count, item in enumerate(self.__mutils.kodidb.files(lib_path, limits=(0, 5))):
            artwork["%s.%s" % (arttype, count)] = item["file"]
        return self.handle_artwork(artwork, params)

    @cherrypy.expose
    def getmoviegenreimages(self, **kwargs):
        kwargs["mediatype"] = "movies"
        kwargs["randomize"] = "false"
        return self.genreimages(kwargs)

    @cherrypy.expose
    def gettvshowgenreimages(self, **kwargs):
        kwargs["mediatype"] = "tvshows"
        kwargs["randomize"] = "false"
        return self.genreimages(**kwargs)

    @cherrypy.expose
    def getmoviegenreimagesrandom(self, **kwargs):
        kwargs["mediatype"] = "movies"
        kwargs["randomize"] = "true"
        return self.genreimages(kwargs)

    @cherrypy.expose
    def gettvshowgenreimagesrandom(self, **kwargs):
        kwargs["mediatype"] = "tvshows"
        kwargs["randomize"] = "true"
        return self.genreimages(**kwargs)

    @cherrypy.expose
    def getpvrthumb(self, **kwargs):
        '''get pvr images'''
        log_msg("webservice.getpvrthumb called with args: %s" % kwargs)
        title = kwargs.get("title", "")
        channel = kwargs.get("channel", "")
        genre = kwargs.get("genre", "")
        artwork = self.__mutils.get_pvr_artwork(title, channel, genre)
        return self.handle_artwork(artwork, kwargs)

    @cherrypy.expose
    def getallpvrthumb(self, **kwargs):
        '''get all pvr images'''
        kwargs["json"] = "true"
        return self.getpvrthumb(**kwargs)

    @cherrypy.expose
    def getmusicart(self, **kwargs):
        '''get pvr images'''
        log_msg("webservice.getmusicart called with args: %s" % kwargs)
        artist = kwargs.get("artist", "")
        album = kwargs.get("album", "")
        track = kwargs.get("track", "")
        artwork = self.__mutils.get_music_artwork(artist, album, track)
        return self.handle_artwork(artwork, kwargs)

    @cherrypy.expose
    def getthumb(self, **kwargs):
        '''get generic thumb image from google/youtube'''
        log_msg("webservice.getthumb called with args: %s" % kwargs)
        title = kwargs.get("title", "")
        preferred_types, is_json_request, fallback = self.get_common_params(kwargs)
        image = self.__mutils.google.search_image(title)
        if not image:
            image = fallback
        return self.handle_image(image)

    @cherrypy.expose
    def getvarimage(self, **kwargs):
        '''get image from kodi variable/resource addon'''
        log_msg("webservice.getvarimage called with args: %s" % kwargs)
        preferred_types, is_json_request, fallback = self.get_common_params(kwargs)
        title = kwargs.get("title", "")
        title = title.replace("{", "[").replace("}", "]")
        image = xbmc.getInfoLabel(title)
        if not xbmcvfs.exists(image):
            if "resource.images" in image:
                log_msg(
                    "Texture packed resource addons are not supported by the webservice! - %s" %
                    image, xbmc.LOGWARNING)
            image = ""
        if not image:
            image = fallback
        return self.handle_image(image)

    def handle_artwork(self, artwork, params):
        '''handle the requested images'''
        preferred_types, is_json_request, fallback = self.get_common_params(params)
        if is_json_request:
            return self.handle_json(artwork)
        else:
            image = self.get_image(artwork, preferred_types, fallback)
            return self.handle_image(image)

    def handle_image(self, image):
        '''serve image'''
        if image:
            # send single image
            try:
                ext = image.split(".")[-1]
                cherrypy.response.headers['Content-Type'] = 'image/%s' % ext
                modified = xbmcvfs.Stat(image).st_mtime()
                cherrypy.response.headers['Last-Modified'] = "%s" % modified
                image = xbmcvfs.File(image)
                cherrypy.response.headers['Content-Length'] = str(image.size())
                if cherrypy.request.method.upper() == 'GET':
                    img_data = image.readBytes()
                    image.close()
                    return str(img_data)
                else:
                    image.close()
            except Exception as exc:
                log_exception(__name__, exc)
        else:
            raise cherrypy.HTTPError(404, "No image found matching the criteria")

    def handle_json(self, artwork):
        '''send the complete details as json object'''
        artwork = json.dumps(artwork)
        cherrypy.response.headers['Content-Type'] = 'application/json'
        cherrypy.response.headers['Content-Length'] = len(artwork)
        if cherrypy.request.method.upper() == 'GET':
            return artwork

    @staticmethod
    def get_common_params(params):
        '''parse the common parameters from the arguments'''
        preferred_types = params.get("type")
        if preferred_types:
            preferred_types = preferred_types.split(",")
        else:
            preferred_types = []
        fallback = params.get("fallback", "")
        is_json_request = params.get("json", "") == "true"
        if fallback and not xbmcvfs.exists(fallback):
            fallback = "special://skin/media/" + fallback
            if not xbmcvfs.exists(fallback):
                fallback = ""
                log_msg(
                    "Webservice --> Non existent fallback image detected - "
                    "please use a full path to the fallback image!",
                    xbmc.LOGWARNING)
        return preferred_types, is_json_request, fallback

    @staticmethod
    def get_image(artwork, preferred_types, fallback):
        '''get the preferred image from the results'''
        image = ""
        if artwork and artwork.get("art"):
            artwork = artwork["art"]
        if preferred_types:
            for pref_type in preferred_types:
                if not image:
                    image = artwork.get(pref_type, "")
        elif not image and artwork.get("landscape"):
            image = artwork["landscape"]
        elif not image and artwork.get("fanart"):
            image = artwork["fanart"]
        elif not image and artwork.get("poster"):
            image = artwork["poster"]
        elif not image and artwork.get("thumb"):
            image = artwork["thumb"]
        # set fallback image if nothing else worked
        if not image or not xbmcvfs.exists(image):
            image = fallback
        return image


class WebService(threading.Thread):
    __root = None

    def __init__(self, metadatautils):
        self.__root = Root(metadatautils)
        cherrypy.config.update({
            'engine.autoreload.on' : False,
            'log.screen': False,
            'engine.timeout_monitor.frequency': 5,
            'server.shutdown_timeout': 1,
        })
        threading.Thread.__init__(self)

    def run(self):
        log_msg("Starting WebService on port %s" % PORT, xbmc.LOGNOTICE)
        conf = {
            'global': {
                'server.socket_host': '0.0.0.0',
                'server.socket_port': PORT
            }, '/': {}
        }
        cherrypy.quickstart(self.__root, '/', conf)

    def stop(self):
        cherrypy.engine.exit()
        self.join(0)
        del self.__root
 