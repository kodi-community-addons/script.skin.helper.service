#!/usr/bin/python
# -*- coding: utf-8 -*-

from Utils import logMsg
import simplecache
import xbmc, xbmcvfs
import os
from datetime import timedelta

def getStudioLogo(studio):
    if not studio: return {}
    cacheStr = u"SkinHelper.StudioLogo.%s" %studio
    logosPath = xbmc.getInfoLabel("Skin.String(SkinHelper.StudioLogos.Path)").decode('utf-8')
    cache = simplecache.get(cacheStr,checksum=logosPath)
    if cache: return cache
    
    studios = []
    result = {}
    if isinstance(studio,list):
        studios = studio
    elif "/" in studio:
        studios = studio.split(" / ")
        result["SkinHelper.ListItemStudio"] = studios[0]
        result['SkinHelper.ListItemStudios'] = "[CR]".join(studios) 
    else:
        studios.append(studio)
        result["SkinHelper.ListItemStudio"] = studio
        result['SkinHelper.ListItemStudios'] = studio

    result['SkinHelper.ListItemStudioLogo'] = matchStudioLogo(studio, getStudioLogos())
    simplecache.set(cacheStr,result,checksum=logosPath)
    return result    
 
def getStudioLogos():
    studioImagesPath = xbmc.getInfoLabel("Skin.String(SkinHelper.StudioLogos.Path)").decode('utf-8')
    if not studioImagesPath: return {}
    
    cacheStr = u"SkinHelper.StudioLogos.%s"%studioImagesPath
    cache = simplecache.get( cacheStr )
    if cache: return cache
    
    #no cache - start lookup
    allLogos = {}
    if studioImagesPath.startswith("resource://"):
        allLogos = getResourceAddonFiles(studioImagesPath)
    else:
        if not (studioImagesPath.endswith("/") or studioImagesPath.endswith("\\")):
            studioImagesPath = studioImagesPath + os.sep()
            allLogos = listFilesInPath(studioImagesPath)
    
    #save in cache and return
    simplecache.set(cacheStr,allLogos,expiration=timedelta(days=7))
    return allLogos
        
def matchStudioLogo(studiostr,studiologos):
    #try to find a matching studio logo
    studiologo = ""
    studios = []
    if "/" in studiostr:
        studios = studiostr.split(" / ")
    else:
        studios.append(studiostr)
    
    for studio in studios:
        studio = studio.lower()
        #find logo normal
        if studiologos.has_key(studio):
            studiologo = studiologos[studio]
        
        if not studiologo:
            #find logo by substituting characters
            if " (" in studio:
                studio = studio.split(" (")[0]
                if studiologos.has_key(studio):
                    studiologo = studiologos[studio]
        
        if not studiologo:
            #find logo by substituting characters for pvr channels
            if " HD" in studio:
                studio = studio.replace(" HD","")
            elif " " in studio:
                studio = studio.replace(" ","")
            if studiologos.has_key(studio):
                studiologo = studiologos[studio]
                
    return studiologo

def getResourceAddonFiles(resourcePath):
    # get listing of all files (eg studio logos) inside a resource image addonName
    # read data from our permanent cache file to prevent that we have to query the resource addon
    cache = simplecache.get(resourcePath)
    if cache: return cache
    #read resource addon as file listing
    data = listFilesInPath(resourcePath)
    # safe data to our permanent cache file, high timedelta because reading the resource addon list causes strange behaviour.
    simplecache.set(resourcePath,data,expiration=timedelta(days=90))
    return data
     
def listFilesInPath( path):
    #used for easy matching of studio logos
    allFilesList = {}
    dirs, files = xbmcvfs.listdir(path)
    for file in files:
        file = file.decode("utf-8")
        name = file.split(".png")[0].lower()
        allFilesList[name] = path + file
    for dir in dirs:
        dirs2, files2 = xbmcvfs.listdir(os.path.join(path,dir)+os.sep)
        for file in files2:
            file = file.decode("utf-8")
            dir = dir.decode("utf-8")
            name = dir + "/" + file.split(".png")[0].lower()
            if "/" in path:
                sep = "/"
            else:
                sep = "\\"
            allFilesList[name] = path + dir + sep + file
    #return the list
    return allFilesList
   

