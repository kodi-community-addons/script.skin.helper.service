#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import base64
from xml.dom.minidom import Document
import xml.etree.ElementTree as ET
from Utils import *
import musicbrainzngs as m

m.set_useragent("script.skin.helper.service", "0.01", "https://github.com/marcelveldt/script.skin.helper.service")

def getPVRThumbs(title,channel,type="channels",path="",genre=""):
    cacheFound = False
    ignore = False
    artwork = {}
    pvrThumbPath = None
    
    #should we ignore this path ?
    ignoretitles = WINDOW.getProperty("ignoretitles")
    ignorechannels = WINDOW.getProperty("ignorechannels")
    stripwords = WINDOW.getProperty("stripwords")
    if ignorechannels:
        for item in ignorechannels.split(";"):
            if item.lower() == channel.lower(): ignore = True
    if ignoretitles:
        for item in ignoretitles.split(";"):
            if item.lower() in title.lower(): ignore = True
    if stripwords:
        for word in stripwords.split(";"): title = title.replace(word,"")
        
    if ignore:
        logMsg("getPVRThumb ignore filter active for %s %s--> "%(title,channel))
        return {}
        
    comparetitle = normalize_string(title.lower().replace("_new","").replace("new_","").replace(channel,"").replace(" ","").replace("_","").replace("_",""))
    dbID = comparetitle + channel
    logMsg("getPVRThumb for %s %s--> "%(title,channel))
    
    #make sure we have our settings cached in memory...
    if not WINDOW.getProperty("pvrthumbspath"):
        setAddonsettings()
    
    if type=="channels" and WINDOW.getProperty("cacheGuideEntries")=="true":
        downloadLocal = True
    elif type=="recordings" and WINDOW.getProperty("cacheRecordings")=="true":
        downloadLocal = True
    else:
        downloadLocal = False
        
    #get the items from cache first
    cache = WINDOW.getProperty("SkinHelper.PVR.Artwork").decode('utf-8')
    if cache:
        cache = eval(cache)
        if cache.has_key(dbID): 
            artwork = cache[dbID]
            cacheFound = True
            logMsg("getPVRThumb cache found for dbID--> " + dbID)
    else: cache = {}
    
    if not cacheFound:
        logMsg("getPVRThumb no cache found for dbID--> " + dbID)
        
        #lookup existing pvrthumbs paths - try to find a match in custom path
        #images will be looked up or stored to that path
        customlookuppath = WINDOW.getProperty("customlookuppath").decode("utf-8")
        if customlookuppath: 
            dirs, files = xbmcvfs.listdir(customlookuppath)
            for dir in dirs:
                dir = dir.decode("utf-8")
                #try to find a match...
                comparedir = normalize_string(dir.lower().replace("_new","").replace("new_","").replace(channel,"").replace(" ","").replace("_","").replace("_",""))
                if comparedir == comparetitle:
                    pvrThumbPath = os.path.join(customlookuppath,dir)
                    break
                elif channel and dir.lower() == channel.lower():
                    #user has setup subfolders per channel on their pvr
                    dirs2, files2 = xbmcvfs.listdir(os.path.join(customlookuppath,dir))
                    for dir2 in dirs2:
                        dir2 = dir2.decode("utf-8")
                        comparedir = dir2.lower().replace(" ","").replace("_new","").replace("new_","").replace("_","").replace("-","").replace(channel,"")
                        if comparedir == comparetitle:
                            pvrThumbPath = os.path.join(customlookuppath,dir,dir2)
                            break
        
        if not pvrThumbPath:
            #nothing found in user custom path so use the global one...
            directory_structure = WINDOW.getProperty("directory_structure")
            pvrthumbspath = WINDOW.getProperty("pvrthumbspath").decode("utf-8")
            if directory_structure == "1": pvrThumbPath = os.path.join(pvrthumbspath,normalize_string(channel),normalize_string(title))
            elif directory_structure == "2": os.path.join(pvrthumbspath,normalize_string(channel + " - " + title))
            else: pvrThumbPath = pvrThumbPath = os.path.join(pvrthumbspath,normalize_string(title))
        
        #make sure our path ends with a slash
        if "/" in pvrThumbPath: sep = "/"
        else: sep = "\\"
        if not pvrThumbPath.endswith(sep): pvrThumbPath = pvrThumbPath + sep
        logMsg("pvr thumbs path --> " + pvrThumbPath)
        
        #Do we have a persistant cache file (pvrdetails.xml) for this item ?
        cachefile = os.path.join(pvrThumbPath, "pvrdetails.xml")
        artwork = getArtworkFromCacheFile(cachefile,artwork)
        if artwork:
            cacheFound = True
            #modify cachefile with last access date for future auto cleanup
            artwork["last_accessed"] = "%s" %datetime.now()
            createNFO(cachefile,artwork)
                
        if not cacheFound:
            
            #lookup actual recordings to get details for grouped recordings
            #also grab a thumb provided by the pvr
            #NOTE: for episode level in series recordings, skinners should just get the pvr provided thumbs (listitem.thumb) in the skin itself because the cache is based on title not episode
            #the thumb image will be filled with just one thumb from the series (or google image if pvr doesn't provide a thumb)
            json_query = getJSON('PVR.GetRecordings', '{ "properties": [ %s ]}' %( fields_pvrrecordings))
            for item in json_query:
                if (path and path in item["file"]) or (not path and title in item["file"]) or (not channel and title in item["file"]):
                    logMsg("getPVRThumbs - title or path matches an existing recording: " + title)
                    if not channel: 
                        channel = item["channel"]
                        artwork["channel"] = channel
                    if not genre:
                        artwork["genre"] = " / ".join(item["genre"])
                        genre = " / ".join(item["genre"])
                    if item.get("art"):
                        artwork = item["art"]
                    if item.get("plot"):
                        artwork["plot"] = item["plot"]
                        break
            
            #lookup existing artwork in pvrthumbs paths
            if xbmcvfs.exists(pvrThumbPath):
                logMsg("thumbspath found on disk for " + title)
                for artType in KodiArtTypes:
                    artpath = os.path.join(pvrThumbPath,artType[1])
                    if xbmcvfs.exists(artpath) and not artwork.get(artType[0]):
                        artwork[artType[0]] = artpath
                        logMsg("%s found on disk for %s" %(artType[0],title))
            
            #lookup local library
            if WINDOW.getProperty("useLocalLibraryLookups") == "true":
                item = None
                json_result = getJSON('VideoLibrary.GetTvShows','{ "filter": {"operator":"is", "field":"title", "value":"%s"}, "properties": [ %s ] }' %(title,fields_tvshows))
                if len(json_result) > 0:
                    item = json_result[0]
                else:
                    json_result = getJSON('VideoLibrary.GetMovies','{ "filter": {"operator":"is", "field":"title", "value":"%s"}, "properties": [ %s ] }' %(title,fields_movies))
                    if len(json_result) > 0:
                        item = json_result[0]
                if item and item.has_key("art"): 
                    artwork = item["art"]
                    if item.get("plot"): artwork["plot"] = item["plot"]
                    logMsg("getPVRThumb artwork found in local library for dbID--> " + dbID)
                    
            #get logo if none found
            if not artwork.has_key("channellogo") and channel:
                artwork["channellogo"] = searchChannelLogo(channel)
                    
            #if nothing in library or persistant cache, perform the internet scraping
            if not cacheFound and not WINDOW.getProperty("SkinHelper.DisableInternetLookups"):
                                
                #grab artwork from tmdb/fanart.tv
                if WINDOW.getProperty("useTMDBLookups") == "true":
                    if "movie" in genre.lower():
                        artwork = getOfficialArtWork(title,artwork,"movie")
                    else:
                        artwork = getOfficialArtWork(title,artwork)
                    
                #lookup thumb on google as fallback
                if not artwork.get("thumb") and channel and WINDOW.getProperty("useGoogleLookups") == "true":
                    artwork["thumb"] = searchGoogleImage(title + " " + channel)
                
                #lookup thumb on youtube as fallback
                if not artwork.get("thumb") and channel and WINDOW.getProperty("useYoutubeLookups") == "true":
                    artwork["thumb"] = searchYoutubeImage(title + " " + channel)
                
                if downloadLocal == True:
                    #download images if we want them local
                    for artType in KodiArtTypes:
                        if artwork.has_key(artType[0]) and artType[0] != "channellogo": artwork[artType[0]] = downloadImage(artwork[artType[0]],pvrThumbPath,artType[1])
                
                #extrafanart images
                if artwork.get("extrafanarts"):
                    if downloadLocal:
                        efadir = os.path.join(pvrThumbPath,"extrafanart/")
                        count = 1
                        for fanart in artwork.get("extrafanarts"):
                            downloadImage(fanart,efadir,"fanart%s.jpg"%count)
                            count += 1
                        artwork["extrafanart"] = efadir
                    else: artwork["extrafanart"] = "plugin://script.skin.helper.service/?action=EXTRAFANART&path=%s" %(single_urlencode(try_encode(cachefile)))
                    artwork["extrafanarts"] = repr(artwork["extrafanarts"])
                else:
                    artwork.pop("extrafanarts", None)
                
                #create persistant cache pvrdetails.xml file...
                if title and channel:
                    artwork["title"] = title
                    artwork["channel"] = channel
                    artwork["date_scraped"] = "%s" %datetime.now()
                    if path: artwork["path"] = path
                    if genre: artwork["genre"] = genre
                    if not xbmcvfs.exists(pvrThumbPath): xbmcvfs.mkdirs(pvrThumbPath)
                    createNFO(cachefile,artwork)
                    
        #store in cache for quick access later
        cache[dbID] = artwork
        WINDOW.setProperty("SkinHelper.PVR.ArtWork",repr(cache).encode('utf-8'))
    else:
        logMsg("getPVRThumb cache found for dbID--> " + dbID)
    
    return artwork

def getfanartTVimages(type,id,artwork=None):
    #gets fanart.tv images for given id
    if not artwork: artwork={}
    api_key = "639191cb0774661597f28a47e7e2bad5"
    language = WINDOW.getProperty("scraper_language")
    logMsg("get fanart.tv images for type: %s - id: %s" %(type,id))
    
    if type == "movie":
        url = 'http://webservice.fanart.tv/v3/movies/%s?api_key=%s' %(id,api_key)
    elif type == "artist":
        url = 'http://webservice.fanart.tv/v3/music/%s?api_key=%s' %(id,api_key)
    elif type == "album":
        url = 'http://webservice.fanart.tv/v3/music/albums/%s?api_key=%s' %(id,api_key)
    else:
        url = 'http://webservice.fanart.tv/v3/tv/%s?api_key=%s' %(id,api_key)
    try:
        response = requests.get(url)
    except Exception as e:
        logMsg("getfanartTVimages lookup failed--> " + str(e), 0)
        return artwork
    if response and response.content:
        data = json.loads(response.content.decode('utf-8','replace'))
    else:
        return artwork
    if data:
        cdart = None
        cover = None
        if type == "album" and data.has_key("albums"):
            for key, value in data["albums"].iteritems():
                if value.has_key("cdart") and not artwork.get("discart"):
                    artwork["discart"] = value["cdart"][0].get("url")
                elif value.has_key("albumcover") and not artwork.get("folder"):
                    artwork["folder"] = value["albumcover"][0].get("url")
        
        else:
            #we need to use a little mapping between fanart.tv arttypes and kodi artttypes
            fanartTVTypes = [ ("logo","clearlogo"),("disc","discart"),("clearart","clearart"),("banner","banner"),("artistthumb","folder"),("thumb","landscape"),("clearlogo","clearlogo"),("poster","poster"),("background","fanart"),("showbackground","fanart"),("characterart","characterart"),("artistbackground","fanart")]
            prefixes = ["",type,"hd","hd"+type]
            for fanarttype in fanartTVTypes:
                for prefix in prefixes:
                    fanarttvimage = prefix+fanarttype[0]
                    if data.has_key(fanarttvimage):
                        for item in data[fanarttvimage]:
                            if item.get("lang","") == KODILANGUAGE:
                                #select image in preferred language
                                artwork[fanarttype[1]] = item.get("url")
                                break
                        if not artwork.has_key(fanarttype[1]) and len(data.get(fanarttvimage)) > 0:
                            #just grab the first english one as fallback
                            for item in data[fanarttvimage]:
                                if item.get("lang","") == "en":
                                    artwork[fanarttype[1]] = item.get("url")
                                    break
                        #grab extrafanarts in list
                        if "background" in fanarttvimage:
                            if not artwork.get("extrafanarts"): 
                                artwork["extrafanarts"] = []
                            for item in data[fanarttvimage]:
                                artwork["extrafanarts"].append(item.get("url"))
                    
    return artwork

def getOfficialArtWork(title,artwork=None,type=None):
    #perform search on TMDB and return artwork
    if not artwork: artwork={}
    apiKey = base64.b64decode("NDc2N2I0YjJiYjk0YjEwNGZhNTUxNWM1ZmY0ZTFmZWM=")
    coverUrl = ""
    fanartUrl = ""
    matchFound = None
    media_id = None
    media_type = None
    if not type: type="multi"
    try: 
        url = 'http://api.themoviedb.org/3/search/%s?api_key=%s&language=%s&query=%s' %(type,apiKey,KODILANGUAGE,try_encode(title))
        response = requests.get(url)
        data = json.loads(response.content.decode('utf-8','replace'))
        #find exact match first
        if data and data.get("results",None):
            for item in data["results"]:
                name = item.get("name")
                if not name: name = item.get("title")
                original_name = item.get("original_name","")
                title_alt = title.lower().replace(" ","").replace("-","").replace(":","").replace("&","").replace(",","")
                name_alt = name.lower().replace(" ","").replace("-","").replace(":","").replace("&","").replace(",","")
                org_name_alt = original_name.lower().replace(" ","").replace("-","").replace(":","").replace("&","").replace(",","")
                if name == title or original_name == title:
                    #match found for exact title name
                    matchFound = item
                    break
                elif name.split(" (")[0] == title or title_alt == name_alt or title_alt == org_name_alt:
                    #match found with substituting some stuff
                    matchFound = item
                    break
        
            #if a match was not found, we accept the closest match from TMDB
            if not matchFound and len(data.get("results")) > 0 and not len(data.get("results")) > 5:
                matchFound = item = data.get("results")[0]
            
        if matchFound:
            coverUrl = matchFound.get("poster_path","")
            fanartUrl = matchFound.get("backdrop_path","")
            id = str(matchFound.get("id",""))
            media_type = matchFound.get("media_type","")
            name = item.get("name")
            if not name: name = item.get("title")
            artwork["tmdb_title"] = name
            artwork["tmdb_type"] = media_type
            logMsg("getTMDBimage - TMDB match found for %s !" %title)
            #lookup external tmdb_id and perform artwork lookup on fanart.tv
            languages = [KODILANGUAGE,"en"]
            for language in languages:
                if WINDOW.getProperty("useFanArtTv") == "true" and id:
                    if media_type == "movie" or not media_type:
                        url = 'http://api.themoviedb.org/3/movie/%s?api_key=%s&language=%s' %(id,apiKey,language)
                    else:
                        url = 'http://api.themoviedb.org/3/tv/%s?api_key=%s&append_to_response=external_ids&language=%s' %(id,apiKey,language)
                    response = requests.get(url)
                    data = json.loads(response.content.decode('utf-8','replace'))
                    if data:
                        if not media_id and data.get("imdb_id"):
                            media_id = str(data.get("imdb_id"))
                            artwork["imdb_id"] = media_id
                        if not media_id and data.get("external_ids"): 
                            media_id = str(data["external_ids"].get("tvdb_id"))
                            artwork["tvdb_id"] = media_id
                        if data.get("overview"):
                            artwork["plot"] = data.get("overview")
                            break
        
        #lookup artwork on fanart.tv
        if media_id and media_type:
            artwork = getfanartTVimages(media_type,media_id,artwork)
        
        #use tmdb art as fallback when no fanart.tv art
        if coverUrl and not artwork.get("poster"):
            artwork["poster"] = "http://image.tmdb.org/t/p/original"+coverUrl  
        if fanartUrl and not artwork.get("fanart"):
            artwork["fanart"] = "http://image.tmdb.org/t/p/original"+fanartUrl

        return artwork
    
    except Exception as e:
        if "getaddrinfo failed" in str(e):
            #no internet access - disable lookups for now
            WINDOW.setProperty("SkinHelper.DisableInternetLookups","disable")
            logMsg("getOfficialArtWork - no internet access, disabling internet lookups for now")
        else:
            logMsg("getOfficialArtWork - Error in getOfficialArtWork --> " + str(e),0)
    
def downloadImage(imageUrl,thumbsPath, filename):
    try:
        if not xbmcvfs.exists(thumbsPath):
            xbmcvfs.mkdirs(thumbsPath)
        newFile = os.path.join(thumbsPath,filename)
        if not xbmcvfs.exists(newFile):
            #do not overwrite existing images
            xbmcvfs.copy(imageUrl,newFile)
        return newFile
    except: return imageUrl

def createNFO(cachefile, artwork):
    try:
        tree = ET.ElementTree( ET.Element( "artdetails" ) )
        root = tree.getroot()
        for key, value in artwork.iteritems():
            if value:
                child = ET.SubElement( root, key )
                child.text = try_decode(value)
        
        indentXML( tree.getroot() )
        xmlstring = ET.tostring(tree.getroot(), encoding="utf-8")
        f = xbmcvfs.File(cachefile, 'w')
        f.write(xmlstring)
        f.close()
    except Exception as e:
        logMsg("ERROR in createNFO --> " + str(e), 0)
      
def getArtworkFromCacheFile(cachefile,artwork=None):
    if not artwork: artwork={}
    if xbmcvfs.exists(cachefile):
        try:
            f = xbmcvfs.File(cachefile, 'r')
            root = ET.fromstring(f.read())
            f.close()
            cacheFound = True
            for child in root:
                if not artwork.get(child.tag):
                    artwork[child.tag] = try_decode(child.text)
            del root
        except Exception as e:
            logMsg("ERROR in getArtworkFromCacheFile --> " + str(e), 0)
    return artwork
         
def searchChannelLogo(searchphrase):
    #get's a thumb image for the given search phrase
    image = ""
    
    cache = WINDOW.getProperty(searchphrase.encode('utf-8') + "SkinHelper.PVR.ChannelLogo")
    if cache: return cache
    else:
    
        try:
            #lookup in channel list
            # Perform a JSON query to get all channels
            json_query = getJSON('PVR.GetChannels', '{"channelgroupid": "alltv", "properties": [ "thumbnail", "channeltype", "hidden", "locked", "channel", "lastplayed", "broadcastnow" ]}' )
            for item in json_query:
                channelname = item["label"]
                if channelname == searchphrase:
                    channelicon = item['thumbnail']
                    if channelicon: 
                        channelicon = getCleanImage(channelicon)
                        if xbmcvfs.exists(channelicon):
                            image = getCleanImage(channelicon)
                    break

            #lookup with thelogodb
            if not image:
                url = 'http://www.thelogodb.com/api/json/v1/1/tvchannel.php?s=%s' %try_encode(searchphrase)
                response = requests.get(url)
                data = json.loads(response.content.decode('utf-8','replace'))
                if data and data.has_key('channels'):
                    results = data['channels']
                    if results:
                        for i in results: 
                            rest = i['strLogoWide']
                            if rest:
                                if ".jpg" in rest or ".png" in rest:
                                    image = rest
                                    break
                
            if not image:
                search_alt = searchphrase.replace(" HD","")
                url = 'http://www.thelogodb.com/api/json/v1/1/tvchannel.php?s=%s' %try_encode(search_alt)
                response = requests.get(url)
                data = json.loads(response.content.decode('utf-8','replace'))
                if data and data.has_key('channels'):
                    results = data['channels']
                    if results:
                        for i in results: 
                            rest = i['strLogoWide']
                            if rest:
                                if ".jpg" in rest or ".png" in rest:
                                    image = rest
                                    break
        except Exception as e:
            if "getaddrinfo failed" in str(e):
                #no internet access - disable lookups for now
                WINDOW.setProperty("SkinHelper.DisableInternetLookups","disable")
                logMsg("searchChannelLogo - no internet access, disabling internet lookups for now")
            else:
                logMsg("ERROR in searchChannelLogo ! --> " + str(e), 0)

        if image:
            if ".jpg/" in image:
                image = image.split(".jpg/")[0] + ".jpg"
        
        WINDOW.setProperty(searchphrase.encode('utf-8') + "SkinHelper.PVR.ChannelLogo",image)
        return image

def searchGoogleImage(searchphrase):
    image = ""
   
    try:
        ip_address = xbmc.getInfoLabel("Network.IPAddress")
        url = 'http://ajax.googleapis.com/ajax/services/search/images'
        params = {'v' : '1.0', 'safe': 'off', 'userip': ip_address, 'q': searchphrase, 'imgsz': 'medium|large|xlarge'}
        response = requests.get(url, params=params)
        data = json.loads(response.content.decode('utf-8','replace'))
        if data and data.get("responseData"):
            if data['responseData'].get("results"):
                results = data['responseData']['results']
                for i in results: 
                    image = i['unescapedUrl']
                    if image:
                        if ".jpg" in image or ".png" in image:
                            logMsg("getTMDBimage - GOOGLE match found for %s !" %searchphrase)
                            return image
    except Exception as e:
        if "getaddrinfo failed" in str(e):
            #no internet access - disable lookups for now
            WINDOW.setProperty("SkinHelper.DisableInternetLookups","disable")
            logMsg("searchGoogleImage - no internet access, disabling internet lookups for now")
        else:
            logMsg("getTMDBimage - ERROR in searchGoogleImage ! --> " + str(e))
    
    logMsg("getTMDBimage - GOOGLE match NOT found for %s" %searchphrase)
    return image
 
def searchYoutubeImage(searchphrase):
    image = ""
    matchFound = False
    #safety check: prevent multiple youtube searches at once...
    waitForYouTubeCount = 0
    if WINDOW.getProperty("youtubescanrunning") == "running":
        xbmc.sleep(100)
        return "skip"
    
    WINDOW.setProperty("youtubescanrunning","running")
    libPath = "plugin://plugin.video.youtube/kodion/search/query/?q=%s" %searchphrase
    media_array = getJSON('Files.GetDirectory','{ "properties": ["title","art"], "directory": "' + libPath + '", "media": "files" }')
    for media in media_array:
        if not media["filetype"] == "directory":
            if media.has_key('art'):
                if media['art'].has_key('thumb'):
                    image = getCleanImage(media['art']['thumb'])
                    matchFound = True
                    break
    if matchFound:
        logMsg("searchYoutubeImage - YOUTUBE match found for %s" %searchphrase)
    else:
        logMsg("searchYoutubeImage - YOUTUBE match NOT found for %s" %searchphrase)
    
    WINDOW.clearProperty("youtubescanrunning")
    return image
 
def searchThumb(searchphrase, searchphrase2=""):
    #get's a thumb image for the given search phrase
    
    #is this item already in the cache?
    image = WINDOW.getProperty(try_encode(searchphrase + searchphrase2) + "SkinHelper.PVR.Thumb").decode("utf-8")
    if not image and not WINDOW.getProperty("SkinHelper.DisableInternetLookups"):
        if searchphrase2:
            searchphrase = searchphrase + " " + searchphrase2
            
        WINDOW.setProperty("getthumbbusy","busy")
                  
        #lookup with Google images
        if not image:
            image = searchGoogleImage(searchphrase)
        
        # Do lookup with youtube addon as last resort
        if not image:
            searchYoutubeImage(searchphrase)
                
        if image:
            if ".jpg/" in image:
                image = image.split(".jpg/")[0] + ".jpg"
        WINDOW.clearProperty("getthumbbusy")
    return image

def getMusicBrainzId(artist, album="", track=""):
    albumid = ""
    artistid = ""
    try:
        if not WINDOW.getProperty("SkinHelper.TempDisableMusicBrainz"):
            MBalbum = None
            if artist and album:
                MBalbums = m.search_release_groups(query=single_urlencode(try_encode(album)),limit=1,offset=None, strict=False, artist=single_urlencode(try_encode(artist)))
                if MBalbums and MBalbums.get("release-group-list"): MBalbum = MBalbums.get("release-group-list")[0]
            elif artist and track:
                MBalbums = m.search_recordings(query=single_urlencode(try_encode(track)),limit=1,offset=None, strict=False, artist=single_urlencode(try_encode(artist)))
                if MBalbums and MBalbums.get("recording-list"): MBalbum = MBalbums.get("recording-list")[0]
            if MBalbum:
                albumid = MBalbum.get("id","")
                MBartist = MBalbum.get("artist-credit")[0]
                artistid = MBartist.get("artist").get("id")
    except Exception as e:
        if "HTTP Error 504" in str(e): 
            logMsg("MusicBrainz servers busy - temporary disabling musicbrainz lookups (fallback to theaudiodb)", 0)
            WINDOW.setProperty("SkinHelper.TempDisableMusicBrainz","disable")
        else: logMsg("getMusicArtworkByName MusicBrainz lookup failed --> " + str(e), 0)
    
    #use theaudiodb as fallback
    try:
        if not artistid and artist and album:
            audiodb_url = 'http://www.theaudiodb.com/api/v1/json/193621276b2d731671156g/searchalbum.php'
            params = {'s' : artist, 'a': album}
            response = requests.get(audiodb_url, params=params)
            if response and response.content:
                data = json.loads(response.content.decode('utf-8','replace'))
                if data and data.get("album") and len(data.get("album")) > 0:
                    adbdetails = data["album"][0]
                    albumid = adbdetails.get("strMusicBrainzID")
                    artistid = adbdetails.get("strMusicBrainzArtistID")
        
        elif not artistid and artist and track:
            audiodb_url = 'http://www.theaudiodb.com/api/v1/json/193621276b2d731671156g/searchtrack.php'
            params = {'s' : artist, 't': track}
            response = requests.get(audiodb_url, params=params)
            if response and response.content:
                data = json.loads(response.content.decode('utf-8','replace'))
                if data and data.get("track") and len(data.get("track")) > 0:
                    adbdetails = data["track"][0]
                    albumid = adbdetails.get("strMusicBrainzAlbumID")
                    artistid = adbdetails.get("strMusicBrainzArtistID")
    except Exception as e:
        logMsg("getMusicArtworkByDbId AudioDb lookup failed --> " + str(e), 0)
        return {}

    return (artistid, albumid)

def getArtistArtwork(musicbrainzartistid, artwork=None):
    if not artwork: artwork = {}
    #get fanart.tv artwork for artist
    artwork = getfanartTVimages("artist",musicbrainzartistid,artwork)
    #get audiodb info for artist  (and use as spare for artwork)
    try:
        audiodb_url = 'http://www.theaudiodb.com/api/v1/json/193621276b2d731671156g/artist-mb.php?i=%s' %musicbrainzartistid
        response = requests.get(audiodb_url)
    except Exception as e:
        logMsg("getMusicArtworkByDbId AudioDb lookup failed --> " + str(e), 0)
        return {}
    if response and response.content:
        data = json.loads(response.content.decode('utf-8','replace'))
        if data and data.get("artists") and len(data.get("artists")) > 0:
            adbdetails = data["artists"][0]
            if not artwork.get("banner") and adbdetails.get("strArtistBanner"): artwork["banner"] = adbdetails.get("strArtistBanner")
            artwork["extrafanarts"] = []
            if adbdetails.get("strArtistFanart"): artwork["extrafanarts"].append(adbdetails.get("strArtistFanart"))
            if adbdetails.get("strArtistFanart2"): artwork["extrafanarts"].append(adbdetails.get("strArtistFanart2"))
            if adbdetails.get("strArtistFanart3"): artwork["extrafanarts"].append(adbdetails.get("strArtistFanart3"))
            if not artwork.get("clearlogo") and adbdetails.get("strArtistLogo"): artwork["clearlogo"] = adbdetails.get("strArtistLogo")
            if not artwork.get("artistthumb") and adbdetails.get("strArtistThumb"): artwork["artistthumb"] = adbdetails.get("strArtistThumb")
            if not artwork.get("thumb") and adbdetails.get("strArtistThumb"): artwork["thumb"] = adbdetails.get("strArtistThumb")
            if not artwork.get("info") and adbdetails.get("strBiography" + KODILANGUAGE.upper()): artwork["info"] = adbdetails.get("strBiography" + KODILANGUAGE.upper())
            if not artwork.get("info") and adbdetails.get("strBiographyEN"): artwork["info"] = adbdetails.get("strBiographyEN")
            
            
    return artwork

def getAlbumArtwork(musicbrainzalbumid, artwork=None):
    if not artwork: artwork = {}
    #get fanart.tv artwork for album
    artwork = getfanartTVimages("album",musicbrainzalbumid,artwork)
    #get album info on theaudiodb (and use as spare for artwork)
    try:
        audiodb_url = 'http://www.theaudiodb.com/api/v1/json/193621276b2d731671156g/album-mb.php?i=%s' %musicbrainzalbumid
        response = requests.get(audiodb_url)
    except Exception as e:
        logMsg("getMusicArtworkByDbId AudioDB lookup failed --> " + str(e), 0)
        return {}
    if response and response.content:
        data = json.loads(response.content.decode('utf-8','replace'))
        if data and data.get("album") and len(data.get("album")) > 0:
            adbdetails = data["album"][0]
            if not artwork.get("thumb") and adbdetails.get("strAlbumThumb"): artwork["thumb"] = adbdetails.get("strAlbumThumb")
            if not artwork.get("discart") and adbdetails.get("strAlbumCDart"): artwork["discart"] = adbdetails.get("strAlbumCDart")
            if not artwork.get("info") and adbdetails.get("strDescription" + KODILANGUAGE.upper()): artwork["info"] = adbdetails.get("strDescription" + KODILANGUAGE.upper())
            if not artwork.get("info") and adbdetails.get("strDescriptionEN"): artwork["info"] = adbdetails.get("strDescriptionEN")
    
    if not artwork.get("thumb") and not artwork.get("folder") and not WINDOW.getProperty("SkinHelper.TempDisableMusicBrainz"): 
        try: 
            new_file = "special://profile/addon_data/script.skin.helper.service/musicart/%s.jpg" %musicbrainzalbumid
            thumbfile = m.get_image_front(musicbrainzalbumid)
            if thumbfile: 
                f = xbmcvfs.File(new_file, 'w')
                f.write(thumbfile)
                f.close()
            artwork["folder"] = new_file
        except: pass
    
    if not artwork.get("thumb") and not artwork.get("folder") and not WINDOW.getProperty("SkinHelper.TempDisableMusicBrainz"): 
        try: 
            new_file = "special://profile/addon_data/script.skin.helper.service/musicart/%s.jpg" %musicbrainzalbumid
            thumbfile = m.get_release_group_image_front(musicbrainzalbumid)
            if thumbfile: 
                f = xbmcvfs.File(new_file, 'w')
                f.write(thumbfile)
                f.close()
            artwork["folder"] = new_file
        except: pass
    
    
    
    return artwork
            
def getMusicArtworkByDbId(dbid,itemtype):
        
    albumartwork = {}
    path = None
    albumName = ""
    trackName = None
    artistid = 0
    artistCacheFound = False
    albumCacheFound = False
    
    enableMusicArtScraper = WINDOW.getProperty("enableMusicArtScraper") == "true"
    downloadMusicArt = WINDOW.getProperty("downloadMusicArt") == "true"
    enableLocalMusicArtLookup = WINDOW.getProperty("enableLocalMusicArtLookup") == "true"

    if itemtype == "artists":
        artistid = int(dbid)
    
    if itemtype == "songs":
        json_response = getJSON('AudioLibrary.GetSongDetails', '{ "songid": %s, "properties": [ "file","artistid","albumid","album","comment","fanart","thumbnail","displayartist"] }'%int(dbid))
        if json_response:
            if json_response.get("album") and json_response.get("albumid") and json_response.get("album","").lower() != "singles":
                #album level is lowest level we get info from so change context to album once we have the song details...
                itemtype = "albums"
                dbid = str(json_response["albumid"])
            else:
                #search by trackname as fallback for songs without albums (singles)
                return getMusicArtworkByName(json_response.get("displayartist"),json_response.get("label"))

    #ALBUM DETAILS
    if itemtype == "albums":
        albumartwork = getArtworkFromCacheFile("special://profile/addon_data/script.skin.helper.service/musicart/cache-albums-%s.xml" %int(dbid))
        if albumartwork: albumCacheFound = True
        json_response = getJSON('AudioLibrary.GetSongs', '{ "filter":{"albumid": %s}, "properties": [ "file","artistid","track","title","albumid","album","displayartist","albumartistid" ] }'%int(dbid))
        albumartwork["songcount"] = 0
        albumartwork["albumcount"] = 0
        albumartwork["albums"] = []
        albumartwork["tracklist"] = []
        for song in json_response:
            if not path: path = song["file"]
            if song.get("track"): albumartwork["tracklist"].append("%s - %s" %(song["track"], song["title"]))
            else: albumartwork["tracklist"].append(song["title"])
            albumartwork["songcount"] += 1
            if song.get("album") and song["album"] not in albumartwork["albums"]:
                albumartwork["albumcount"] +=1
                albumartwork["albums"].append(song["album"])   
            json_response2 = getJSON('AudioLibrary.GetAlbumDetails','{ "albumid": %s, "properties": [ "description","fanart","thumbnail" ] }'%int(dbid))
            if json_response2.get("description"): albumartwork["info"] = json_response2["description"]
            if json_response2["fanart"] and not albumartwork.get("fanart") and json_response2.get("fanart").endswith(".jpg"): albumartwork["fanart"] = getCleanImage(json_response2["fanart"])
            if json_response2["thumbnail"] and not albumartwork.get("folder") and json_response2.get("thumbnail").endswith(".jpg"): albumartwork["folder"] = getCleanImage(json_response2["thumbnail"])
            if json_response2.get("label") and not albumName: albumName = json_response2["label"]
            if song.get("albumartistid") and not artistid: artistid = song.get("albumartistid")[0]
            if song.get("artistid") and not artistid: artistid = song.get("artistid")[0]
            if albumCacheFound and artistid and albumName: break
        
    #ARTIST DETAILS
    artistartwork = getArtworkFromCacheFile("special://profile/addon_data/script.skin.helper.service/musicart/cache-artists-%s.xml" %artistid)
    if artistartwork: artistCacheFound = True
    else:
        json_response = getJSON('AudioLibrary.GetSongs', '{ "filter":{"artistid": %s}, "properties": [ "file","artistid","track","title","albumid","album","albumartistid" ] }'%artistid)
        artistartwork["songcount"] = 0
        artistartwork["albumcount"] = 0
        artistartwork["albums"] = []
        artistartwork["tracklist"] = []
        for song in json_response:
            if not path: path = song["file"]
            if song.get("artistid") and not artistid: artistid = song.get("artistid")[0]
            if song.get("track"): artistartwork["tracklist"].append("%s - %s" %(song["track"], song["title"]))
            else: artistartwork["tracklist"].append(song["title"])
            if song.get("album") and not albumName: albumName = song["album"]
            artistartwork["songcount"] += 1
            if song.get("album") and song["album"] not in artistartwork["albums"]:
                artistartwork["albumcount"] +=1
                artistartwork["albums"].append(song["album"])
        json_response2 = getJSON('AudioLibrary.GetArtistDetails', '{ "artistid": %s, "properties": [ "description","fanart","thumbnail" ] }'%artistid)
        if json_response2.get("description"): artistartwork["info"] = json_response2["description"]
        if json_response2.get("fanart") and not artistartwork.get("fanart") and json_response2.get("fanart").endswith(".jpg"): artistartwork["fanart"] = getCleanImage(json_response2["fanart"])
        if json_response2.get("thumbnail") and not artistartwork.get("folder") and json_response2.get("thumbnail").endswith(".jpg"): artistartwork["folder"] = getCleanImage(json_response2["thumbnail"])
        if json_response2.get("label") and not artistartwork.get("artistname",""): artistartwork["artistname"] = json_response2["label"]
    
    #LOOKUP PATH PASED ON SONG FILE PATH
    if path:
        path = song.get("file")
        if "\\" in path:
            delim = "\\"
        else:
            delim = "/"
        foldername = path.split(delim)[-2].lower()
        if foldername.startswith("disc"): 
            path = path.rsplit(delim, 1)[0] + delim #from disc level to album level
        albumpath = path.rsplit(delim, 1)[0] + delim #album level
        artistpath = path.rsplit(delim, 2)[0] + delim #artist level
        
        if enableLocalMusicArtLookup:
            #local artist artwork
            artistartwork["path"] = artistpath
            if normalize_string(artistartwork.get("artistname","").lower().replace("_","")) in normalize_string(artistpath.lower().replace("_","")):
                #lookup existing artwork in the paths (only if artistname in the path)
                for artType in KodiArtTypes:
                    artpath = os.path.join(artistpath,artType[1])
                    if xbmcvfs.exists(artpath) and not artistartwork.get(artType[0]):
                        artistartwork[artType[0]] = artpath
                        logMsg("%s found on disk for %s - itemtype: %s" %(artType[0],artistartwork.get("artistname",""), itemtype))
            if itemtype == "albums":
                albumartwork["path"] = albumpath
                #lookup existing artwork in the paths
                for artType in KodiArtTypes:
                    artpath = os.path.join(albumpath,artType[1])
                    if xbmcvfs.exists(artpath) and not albumartwork.get(artType[0]):
                        albumartwork[artType[0]] = artpath
                        logMsg("%s found on disk for %s - itemtype: %s" %(artType[0],albumName, itemtype))
        
        if enableMusicArtScraper:
            #lookup artist in musicbrainz
            if artistartwork.get("artistname") and albumName:
                #retrieve album id and artist id with a combined query of album name and artist name to get an accurate result
                musicbrainzartistid, musicbrainzalbumid = getMusicBrainzId(artistartwork.get("artistname"),albumName)
                if itemtype=="albums" and musicbrainzalbumid: albumartwork["musicbrainzalbumid"] = musicbrainzalbumid
                if musicbrainzartistid: artistartwork["musicbrainzartistid"] = musicbrainzartistid
            
            ########################################################## ARTIST LEVEL #########################################################
            if artistartwork.get("musicbrainzartistid") and not artistCacheFound:
                artistartwork = getArtistArtwork(artistartwork.get("musicbrainzartistid"), artistartwork)

                #download images if we want them local
                if downloadMusicArt and not "various artists" in artistpath.lower():
                    for artType in KodiArtTypes:
                        if artistartwork.has_key(artType[0]): artistartwork[artType[0]] = downloadImage(artistartwork[artType[0]],artistpath,artType[1])
                
                #extrafanart images
                if artistartwork.get("extrafanarts"):
                    if downloadMusicArt:
                        efadir = os.path.join(artistpath,"extrafanart/")
                        count = 1
                        for fanart in artistartwork.get("extrafanarts"):
                            downloadImage(fanart,efadir,"fanart%s.jpg"%count)
                            count += 1
                        artistartwork["extrafanart"] = efadir
                    else: artistartwork["extrafanart"] = "plugin://script.skin.helper.service/?action=EXTRAFANART&path=special://profile/addon_data/script.skin.helper.service/musicart/cache-artists-%s.xml" %(artistid)
                    artistartwork["extrafanarts"] = repr(artistartwork["extrafanarts"])
                else:
                    artistartwork["extrafanarts"] = ""
                
            ######################################################### ALBUM LEVEL #########################################################    
            if itemtype == "albums" and albumartwork.get("musicbrainzalbumid") and not albumCacheFound:
                albumartwork = getAlbumArtwork(albumartwork.get("musicbrainzalbumid"), albumartwork)
                
                #download images if we want them local
                if downloadMusicArt and not "various artists" in albumpath.lower():
                    for artType in KodiArtTypes:
                        if albumartwork.has_key(artType[0]): albumartwork[artType[0]] = downloadImage(albumartwork[artType[0]],albumpath,artType[1])
        if artistartwork:
            artistartwork["albums"] = "[CR]".join(artistartwork.get("albums",""))
            artistartwork["tracklist"] = "[CR]".join(artistartwork.get("tracklist",""))
            artistartwork["albumcount"] = "%s"%artistartwork.get("albumcount","")
            artistartwork["songcount"] = "%s"%artistartwork.get("songcount","")
            if artistartwork.get("folder") and not artistartwork.get("thumb"): artistartwork["thumb"] = artistartwork.get("folder")
        if itemtype == "albums" and albumartwork:
            albumartwork["albums"] = "[CR]".join(albumartwork.get("albums",""))
            albumartwork["tracklist"] = "[CR]".join(albumartwork.get("tracklist",""))
            albumartwork["albumcount"] = "%s"%albumartwork.get("albumcount","")
            albumartwork["songcount"] = "%s"%albumartwork.get("songcount","")
            albumartwork["albumname"] = albumName
            if albumartwork.get("folder") and not albumartwork.get("thumb"): albumartwork["thumb"] = albumartwork.get("folder")
        
        #write to persistant cache
        if artistartwork and not artistCacheFound:
            if artistartwork.get("landscape"): del artistartwork["landscape"]
            cachefile = "special://profile/addon_data/script.skin.helper.service/musicart/cache-artists-%s.xml" %(artistid)
            createNFO(cachefile,artistartwork)
        if albumartwork and itemtype=="albums" and not albumCacheFound:
            if albumartwork.get("landscape"): del albumartwork["landscape"]
            cachefile = "special://profile/addon_data/script.skin.helper.service/musicart/cache-albums-%s.xml" %(dbid)
            createNFO(cachefile,albumartwork)
    
    #return artwork combined
    artwork = artistartwork
    if itemtype == "albums" and albumartwork:
        for key, value in albumartwork.iteritems():
            if value: artwork[key] = value
    artwork["thumb"] = artwork.get("folder")
    return artwork

def getMusicArtworkByName(artist, title):

    logMsg("getMusicArtworkByName artist: %s  - track: %s" %(artist,title))
    #query database for this track
    json_response = getJSON('AudioLibrary.GetSongs', '{ "filter": {"and": [{"operator":"contains", "field":"artist", "value":"%s"},{"operator":"contains", "field":"title", "value":"%s"}]}, "properties": [ "file","artistid","track","title","albumid","album","displayartist","albumartistid" ] }'%(artist,title))
    if json_response:
        # local match found
        artwork = getMusicArtworkByDbId(str(json_response[0]["albumid"]),"albums")
        return artwork
    else:
        #manual lookup needed - try cache file first...
        cacheFile = "special://profile/addon_data/script.skin.helper.service/musicart/%s.xml" %normalize_string(artist)
        artistartwork = getArtworkFromCacheFile(cacheFile)
        if artistartwork: return artistartwork
        #lookup this artist by quering musicbrainz...
        
        if " & " in artist: artists= artist.split(" & ")
        elif " ft. " in artist: artists= artist.split(" ft. ")
        elif " Ft. " in artist: artists= artist.split(" Ft. ")
        elif " ft " in artist: artists= artist.split(" ft ")
        elif " feat. " in artist: artists= artist.split(" feat. ")
        elif " featuring " in artist: artists= artist.split(" featuring ")
        else: artists = [artist]
        for artist in artists:
            #retrieve musicbrainz id with a combined query of track name and artist name to get an accurate result
            artistid, albumid = getMusicBrainzId(artist,"",title)
            #get artwork for artist
            artistartwork = getArtistArtwork(artistid, artistartwork)
            if albumid:
                #if we also have album artwork use that too
                artistartwork = getAlbumArtwork(albumid, artistartwork)
            
        #process extrafanart
        if artistartwork.get("extrafanarts"):
            artistartwork["extrafanart"] = "plugin://script.skin.helper.service/?action=EXTRAFANART&path=%s" %(single_urlencode(try_encode(cacheFile)))
            artistartwork["extrafanarts"] = repr(artistartwork["extrafanarts"])
        else: artistartwork["extrafanarts"] = ""
        
        if artistartwork.get("folder") and not artistartwork.get("thumb"): artistartwork["thumb"] = artistartwork.get("folder")
            
        #write cachefile for later use
        createNFO(cacheFile,artistartwork)
    
        return artistartwork