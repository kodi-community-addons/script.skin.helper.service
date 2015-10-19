#!/usr/bin/python
# -*- coding: utf-8 -*-

import requests
import base64
from xml.dom.minidom import Document
import xml.etree.ElementTree as ET
from Utils import *


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
        artwork = getPVRartworkFromCacheFile(cachefile,artwork)
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
                for artType in PVRartTypes:
                    artpath = os.path.join(pvrThumbPath,artType[1])
                    if xbmcvfs.exists(artpath) and not artwork.get(artType[0]):
                        artwork[artType[0]] = artpath
                        logMsg("%s found on disk for %s" %(artType[0],title))
            
            #lookup local library
            if not cacheFound and WINDOW.getProperty("useLocalLibraryLookups") == "true":
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
                    cacheFound = True
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
                    for artType in PVRartTypes:
                        if artwork.has_key(artType[0]) and artType[0] != "channellogo": artwork[artType[0]] = downloadImage(artwork[artType[0]],pvrThumbPath,artType[1])
                
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
    #gets fanart.tv images for given tmdb id
    if not artwork: artwork={}
    api_key = "639191cb0774661597f28a47e7e2bad5"
    language = WINDOW.getProperty("scraper_language")
    logMsg("get fanart.tv images for type: %s - id: %s" %(type,id))
    
    if type == "movie":
        url = 'http://webservice.fanart.tv/v3/movies/%s?api_key=%s' %(id,api_key)
    else:
        url = 'http://webservice.fanart.tv/v3/tv/%s?api_key=%s' %(id,api_key)
    response = requests.get(url)
    if response and response.content:
        data = json.loads(response.content.decode('utf-8','replace'))
    else:
        return artwork
    if data:
        #we need to use a little mapping between fanart.tv arttypes and kodi artttypes
        fanartTVTypes = [ ("logo","clearlogo"),("disc","discart"),("clearart","clearart"),("banner","banner"),("thumb","landscape"),("clearlogo","clearlogo"),("poster","poster"),("background","fanart"),("showbackground","fanart"),("characterart","characterart") ]
        prefixes = ["",type,"hd","hd"+type]
        for fanarttype in fanartTVTypes:
            for prefix in prefixes:
                fanarttvimage = prefix+fanarttype[0]
                if data.has_key(fanarttvimage):
                    for item in data[fanarttvimage]:
                        if item["lang"] == language:
                            #select image in preferred language
                            artwork[fanarttype[1]] = item.get("url")
                            break
                    if not artwork.has_key(fanarttype[1]) and len(data.get(fanarttvimage)) > 0:
                        #just grab the first one as fallback
                        artwork[fanarttype[1]] = data.get(fanarttvimage)[0].get("url")
                        
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
    language = WINDOW.getProperty("scraper_language")
    if not type: type="multi"
    try: 
        url = 'http://api.themoviedb.org/3/search/%s?api_key=%s&language=%s&query=%s' %(type,apiKey,language,try_encode(title))
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
            artwork["plot"] = matchFound.get("overview")
            logMsg("getTMDBimage - TMDB match found for %s !" %title)
            #lookup external tmdb_id and perform artwork lookup on fanart.tv
            if WINDOW.getProperty("useFanArtTv") == "true" and id:
                if media_type == "movie":
                    url = 'http://api.themoviedb.org/3/movie/%s?api_key=%s' %(id,apiKey)
                    idparam = "imdb_id"
                elif not media_type:
                    #assume movie is media type empty
                    media_type = "movie"
                    artwork["tmdb_type"] = media_type
                    url = 'http://api.themoviedb.org/3/movie/%s?api_key=%s' %(id,apiKey)
                    idparam = "imdb_id"
                else:
                    url = 'http://api.themoviedb.org/3/tv/%s/external_ids?api_key=%s' %(id,apiKey)
                    idparam = "tvdb_id"
                response = requests.get(url)
                data = json.loads(response.content.decode('utf-8','replace'))
                if data: 
                    media_id = data.get(idparam)
                    artwork[idparam] = str(media_id)
        
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
    doc = Document()
    root = doc.createElement("pvrdetails")
    doc.appendChild(root)

    for key, value in artwork.iteritems():
        child = doc.createElement(key)
        if value:
            nodeText = doc.createTextNode(value) 
            child.appendChild(nodeText)
        root.appendChild(child)

    f = xbmcvfs.File(cachefile, 'w')
    f.write(doc.toprettyxml(encoding='utf-8'))
    f.close()
        
def getPVRartworkFromCacheFile(cachefile,artwork=None):
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
            logMsg("ERROR in getPVRartworkFromCacheFile --> " + str(e), 0)
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
    
