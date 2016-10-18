import sys
import xbmc, xbmcgui, xbmcvfs
import Artworkutils as artutils
import PluginContent as plugincontent
from utils import *
import threading

CANCEL_DIALOG  = ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, )
ACTION_SHOW_INFO = ( 11, )

class GUI( xbmcgui.WindowXMLDialog ):

    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self )
        params = kwargs[ "params" ]
        if params.get("MOVIEID"):
            item = get_kodi_json('VideoLibrary.GetMovieDetails', '{ "movieid": %s, "properties": [ %s ] }' %(params["MOVIEID"],fields_movies))
            self.content = "movies"
        elif params.get("MUSICVIDEOID"):
            item = get_kodi_json('VideoLibrary.GetMusicVideoDetails', '{ "musicvideoid": %s, "properties": [ %s ] }' %(params["MUSICVIDEOID"],fields_musicvideos))
            self.content = "musicvideos"
        elif params.get("EPISODEID"):
            item = get_kodi_json('VideoLibrary.GetEpisodeDetails', '{ "episodeid": %s, "properties": [ %s ] }' %(params["EPISODEID"],fields_episodes))
            self.content = "episodes"
        elif params.get("TVSHOWID"):
            item = get_kodi_json('VideoLibrary.GetTVShowDetails', '{ "tvshowid": %s, "properties": [ %s ] }' %(params["TVSHOWID"],fields_tvshows))
            self.content = "tvshows"
        elif params.get("ALBUMID"):
            item = get_kodi_json('AudioLibrary.GetAlbumDetails', '{ "albumid": %s, "properties": [ %s ] }' %(params["ALBUMID"],fields_albums))
            self.content = "albums"
        elif params.get("SONGID"):
            item = get_kodi_json('AudioLibrary.GetSongDetails', '{ "songid": %s, "properties": [ %s ] }' %(params["SONGID"],fields_songs))
            self.content = "songs"
        elif params.get("RECORDINGID"):
            item = get_kodi_json('PVR.GetRecordingDetails', '{ "recordingid": %s, "properties": [ %s ]}' %( params["RECORDINGID"], fields_pvrrecordings))
            artwork = artutils.getPVRThumbs(item["title"],item["channel"],"recordings",item["file"])
            item["art"] = artwork
            for key, value in artwork.iteritems():
                if not item.get(key):
                    item[key] = value
            if artwork.get("tmdb_type") == "movies":
                self.content = "movies"
            elif artwork.get("tmdb_type") == "tv":
                self.content = "episodes"
            else:
                self.content = "tvrecordings"
        else:
            item = None
            self.listitem = None

        if item:
            liz = prepareListItem(item)
            liz = createListItem(item,False)
            self.listitem = liz
            self.lastwidgetcontainer = params.get("lastwidgetcontainer","")
            WINDOW.setProperty("SkinHelper.WidgetContainer","999")

    def onInit( self ):
        self._hide_controls()
        self._show_info()
        self.bginfoThread = BackgroundInfoThread()
        self.bginfoThread.setDialog(self)
        self.bginfoThread.start()

    def _hide_controls( self ):
        #self.getControl( 110 ).setVisible( False )
        pass

    def _show_info( self ):

        self.listitem.setProperty("contenttype",self.content)
        self.listitem.setProperty("type",self.content[:-1])

        list = self.getControl( 999 )
        list.addItem(self.listitem)

        self.setFocus( self.getControl( 5 ) )

        xbmc.executebuiltin( "Dialog.Close(busydialog)" )

    def _close_dialog( self, action=None ):
        self.action = action
        self.bginfoThread.stopRunning()
        WINDOW.setProperty("SkinHelper.WidgetContainer",self.lastwidgetcontainer)
        self.close()

    def onClick( self, controlId ):
        if controlId == 5:
            type = self.getControl( 999 ).getSelectedItem().getProperty('dbtype')
            dbid = self.getControl( 999 ).getSelectedItem().getProperty('dbid')
            if type and dbid and self.content != "tvshows":
                self._close_dialog('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "%sid": %s } }, "id": 1 }' % (type,dbid))
            elif self.content == 'tvshows':
                path = self.getControl( 999 ).getSelectedItem().getProperty('path')
                self._close_dialog('ActivateWindow(Videos,%s,return)' %path)
        if controlId == 997:
            path = self.getControl( 997 ).getSelectedItem().getfilename()
            self._close_dialog('{ "jsonrpc": "2.0", "method": "Player.Open", "params": { "item": { "file": "%s" } }, "id": 1 }' % path)
        if controlId == 998:
            path = self.getControl( 998 ).getSelectedItem().getProperty('path')
            xbmc.executebuiltin(path)



    def onFocus( self, controlId ):
        pass

    def onAction( self, action ):
        if ( action.getId() in CANCEL_DIALOG ) or ( action.getId() in ACTION_SHOW_INFO ):
            self._close_dialog()


class BackgroundInfoThread(threading.Thread):
    #fill cast and similar lists in the background
    active = True
    infoDialog = None

    def __init__(self, *args):
        threading.Thread.__init__(self, *args)

    def stopRunning(self):
        self.active = False

    def setDialog(self, infoDialog):
        self.infoDialog = infoDialog

    def run(self):

        lst_control = self.infoDialog.getControl( 999 )

        try: #optional: recommended list
            similarlist = self.infoDialog.getControl( 997 )
            similarcontent = []
            if self.infoDialog.content == 'movies':
                similarcontent = plugincontent.SIMILARMOVIES(25,lst_control.getSelectedItem().getProperty("imdbnumber"))
            elif self.infoDialog.content == 'tvshows':
                similarcontent = plugincontent.SIMILARSHOWS(25,lst_control.getSelectedItem().getProperty("imdbnumber"))
            for item in similarcontent:
                if not self.active: break
                item = plugincontent.prepareListItem(item)
                liz = plugincontent.createListItem(item,False)
                liz.setThumbnailImage(item["art"].get("poster"))
                similarlist.addItem(liz)
        except Exception:
            plugincontent.log_msg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)

        try: #optional: cast list
            castlist = self.infoDialog.getControl( 998 )
            castitems = []
            downloadThumbs = xbmc.getInfoLabel("Skin.String(actorthumbslookup)").lower() == "true"
            if self.infoDialog.content == 'movies':
                castitems = plugincontent.getCast(movie=lst_control.getSelectedItem().getLabel().decode("utf-8"),downloadThumbs=downloadThumbs,listOnly=True)
            elif self.infoDialog.content == 'tvshows':
                castitems = plugincontent.getCast(tvshow=lst_control.getSelectedItem().getLabel().decode("utf-8"),downloadThumbs=downloadThumbs,listOnly=True)
            elif self.infoDialog.content == 'episodes':
                castitems = plugincontent.getCast(episode=lst_control.getSelectedItem().getLabel().decode("utf-8"),downloadThumbs=downloadThumbs,listOnly=True)
            for cast in castitems:
                liz = xbmcgui.ListItem(label=cast.get("name"),label2=cast.get("role"),iconImage=cast.get("thumbnail"))
                liz.setProperty('IsPlayable', 'false')
                url = "RunScript(script.extendedinfo,info=extendedactorinfo,name=%s)"%cast.get("name")
                liz.setProperty("path",url)
                liz.setThumbnailImage(cast.get("thumbnail"))
                castlist.addItem(liz)

        except Exception:
            plugincontent.log_msg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)
