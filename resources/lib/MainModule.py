import xbmcplugin
import xbmcgui
import xbmc
import xbmcaddon
import xbmcaddon
import xbmcvfs
import os, sys
import time
import urllib
import xml.etree.ElementTree as etree
from xml.dom.minidom import parse
import json
import random

from Utils import *

from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.etree import ElementTree
from xml.dom import minidom
import xml.etree.cElementTree as ET

      
def musicSearch():
    xbmc.executebuiltin( "ActivateWindow(MusicLibrary)" )
    xbmc.executebuiltin( "SendClick(8)" )

def addShortcutWorkAround():
    xbmc.executebuiltin('SendClick(301)')
    
    count = 0
    #wait for the empy item is focused
    while (count != 60 and xbmc.getCondVisibility("Window.IsActive(script-skinshortcuts.xml)")):
        if not xbmc.getCondVisibility("StringCompare(Container(211).ListItem.Property(path), noop)"):
            xbmc.sleep(100)
            count += 1
        else:
            break
        
    if xbmc.getCondVisibility("StringCompare(Container(211).ListItem.Property(path), noop) + Window.IsActive(script-skinshortcuts.xml)"):
        xbmc.executebuiltin('SendClick(401)')
                    
def selectOverlayTexture():
    overlaysList = []
    overlaysList.append("Custom Overlay Image")
    dirs, files = xbmcvfs.listdir("special://skin/extras/bgoverlays/")
    for file in files:
        if file.endswith(".png"):
            label = file.replace(".png","")
            overlaysList.append(label)
    
    overlaysList.append("None")
    
    dialog = xbmcgui.Dialog()
    ret = dialog.select(ADDON.getLocalizedString(32015), overlaysList)
    if ret == 0:
        dialog = xbmcgui.Dialog()
        custom_texture = dialog.browse( 2 , ADDON.getLocalizedString(32016), 'files')
        if custom_texture:
            xbmc.executebuiltin("Skin.SetString(ColorThemeTexture,Custom)")
            xbmc.executebuiltin("Skin.SetString(CustomColorThemeTexture,%s)" % custom_texture)
    else:
        xbmc.executebuiltin("Skin.SetString(ColorThemeTexture,%s)" % overlaysList[ret])
        xbmc.executebuiltin("Skin.Reset(CustomColorThemeTexture)")

def selectBusyTexture():
    
    xbmc.executebuiltin( "ActivateWindow(busydialog)" )
    import Dialogs as dialogs
    spinnersList = []
    
    currentSpinnerTexture = xbmc.getInfoLabel("Skin.String(SkinHelper.SpinnerTexture)")
    
    listitem = xbmcgui.ListItem(label="None")
    listitem.setProperty("icon","None")
    spinnersList.append(listitem)
    
    listitem = xbmcgui.ListItem(label=ADDON.getLocalizedString(32052))
    listitem.setProperty("icon","")
    spinnersList.append(listitem)
    
    listitem = xbmcgui.ListItem(label=ADDON.getLocalizedString(32053))
    listitem.setProperty("icon","")
    spinnersList.append(listitem)
    
    path = "special://skin/extras/busy_spinners/"
    if xbmcvfs.exists(path):
        dirs, files = xbmcvfs.listdir(path)
        
        for dir in dirs:
            listitem = xbmcgui.ListItem(label=dir)
            listitem.setProperty("icon",path + dir)
            spinnersList.append(listitem)
        
        for file in files:
            if file.endswith(".gif"):
                label = file.replace(".gif","")
                listitem = xbmcgui.ListItem(label=label)
                listitem.setProperty("icon",path + file)
                spinnersList.append(listitem)

    w = dialogs.DialogSelectBig( "DialogSelect.xml", ADDON_PATH, listing=spinnersList, windowtitle=ADDON.getLocalizedString(32051),multiselect=False )
    
    count = 0
    for li in spinnersList:
        if li.getLabel() == currentSpinnerTexture:
            w.autoFocusId = count
        count += 1
         
    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
    w.doModal()
    selectedItem = w.result
    del w
    
    if selectedItem == -1:
        return
    
    if selectedItem == 1:
        dialog = xbmcgui.Dialog()
        custom_texture = dialog.browse( 2 , ADDON.getLocalizedString(32052), 'files', mask='.gif')
        if custom_texture:
            xbmc.executebuiltin("Skin.SetString(SkinHelper.SpinnerTexture,%s)" %spinnersList[selectedItem].getLabel())
            xbmc.executebuiltin("Skin.SetString(SkinHelper.SpinnerTexturePath,%s)" % custom_texture)
    elif selectedItem == 2:
        dialog = xbmcgui.Dialog()
        custom_texture = dialog.browse( 0 , ADDON.getLocalizedString(32053), 'files')
        if custom_texture:
            xbmc.executebuiltin("Skin.SetString(SkinHelper.SpinnerTexture,%s)" %spinnersList[selectedItem].getLabel())
            xbmc.executebuiltin("Skin.SetString(SkinHelper.SpinnerTexturePath,%s)" % custom_texture)
    else:
        xbmc.executebuiltin("Skin.SetString(SkinHelper.SpinnerTexture,%s)" %spinnersList[selectedItem].getLabel())
        xbmc.executebuiltin("Skin.SetString(SkinHelper.SpinnerTexturePath,%s)" % spinnersList[selectedItem].getProperty("icon"))
                
def enableViews():
    import Dialogs as dialogs
    
    allViews = []   
    views_file = xbmc.translatePath( 'special://skin/extras/views.xml' ).decode("utf-8")
    if xbmcvfs.exists( views_file ):
        doc = parse( views_file )
        listing = doc.documentElement.getElementsByTagName( 'view' )
        for count, view in enumerate(listing):
            id = view.attributes[ 'value' ].nodeValue
            label = xbmc.getLocalizedString(int(view.attributes[ 'languageid' ].nodeValue)) + " (" + str(id) + ")"
            type = view.attributes[ 'type' ].nodeValue
            listitem = xbmcgui.ListItem(label=label)
            listitem.setProperty("id",id)
            if not xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.View.Disabled.%s)" %id):
                listitem.select(selected=True)
            allViews.append(listitem)
    
    w = dialogs.DialogSelectSmall( "DialogSelect.xml", ADDON_PATH, listing=allViews, windowtitle=ADDON.getLocalizedString(32017),multiselect=True )
    w.doModal()
    
    selectedItems = w.result
    if selectedItems != -1:
        itemcount = len(allViews) -1
        while (itemcount != -1):
            viewid = allViews[itemcount].getProperty("id")
            if itemcount in selectedItems:
                #view is enabled
                xbmc.executebuiltin("Skin.Reset(SkinHelper.View.Disabled.%s)" %viewid)
            else:
                #view is disabled
                xbmc.executebuiltin("Skin.SetBool(SkinHelper.View.Disabled.%s)" %viewid)
            itemcount -= 1    
    del w        

def setForcedView(contenttype):
    print "setforcedview called for " + contenttype
    currentView = xbmc.getInfoLabel("Skin.String(SkinHelper.ForcedViews.%s)" %contenttype)
    if not currentView:
        currentView = "0"
    selectedItem = selectView(contenttype, currentView, True, True)
    
    if selectedItem != -1 and selectedItem != None:
        xbmc.executebuiltin("Skin.SetString(SkinHelper.ForcedViews.%s,%s)" %(contenttype, selectedItem))
    
def setView():
    #sets the selected viewmode for the container
    import Dialogs as dialogs
    
    #get current content type
    contenttype="other"
    if xbmc.getCondVisibility("Container.Content(episodes)"):
        contenttype = "episodes"
    elif xbmc.getCondVisibility("Container.Content(movies) + !substring(Container.FolderPath,setid=)"):
        contenttype = "movies"  
    elif xbmc.getCondVisibility("[Container.Content(sets) | StringCompare(Container.Folderpath,videodb://movies/sets/)] + !substring(Container.FolderPath,setid=)"):
        contenttype = "sets"
    elif xbmc.getCondVisibility("substring(Container.FolderPath,setid=)"):
        contenttype = "setmovies" 
    elif xbmc.getCondVisibility("Container.Content(tvshows)"):
        contenttype = "tvshows"
    elif xbmc.getCondVisibility("Container.Content(seasons)"):
        contenttype = "seasons"
    elif xbmc.getCondVisibility("Container.Content(musicvideos)"):
        contenttype = "musicvideos"
    elif xbmc.getCondVisibility("Container.Content(artists)"):
        contenttype = "artists"
    elif xbmc.getCondVisibility("Container.Content(songs)"):
        contenttype = "songs"
    elif xbmc.getCondVisibility("Container.Content(albums)"):
        contenttype = "albums"
    elif xbmc.getCondVisibility("Container.Content(songs)"):
        contenttype = "songs"
    elif xbmc.getCondVisibility("Window.IsActive(tvchannels) | Window.IsActive(radiochannels)"):
        contenttype = "tvchannels"
    elif xbmc.getCondVisibility("Window.IsActive(tvrecordings) | Window.IsActive(radiorecordings)"):
        contenttype = "tvrecordings"
    elif xbmc.getCondVisibility("Window.IsActive(programs) | Window.IsActive(addonbrowser)"):
        contenttype = "programs"
    elif xbmc.getCondVisibility("Window.IsActive(pictures)"):
        contenttype = "pictures"
    elif xbmc.getCondVisibility("SubString(Window.Property(xmlfile),MyPVR,left)"):
        contenttype = "pvr"
        
    currentView = xbmc.getInfoLabel("Container.Viewmode")
    selectedItem = selectView(contenttype, currentView)
    currentForcedView = xbmc.getInfoLabel("Skin.String(SkinHelper.ForcedViews.%s)" %contenttype)
    
    #also store forced view    
    if currentForcedView != "None":
        xbmc.executebuiltin("Skin.SetString(SkinHelper.ForcedViews.%s,%s)" %(contenttype, selectedItem))
    
    #set view
    if selectedItem != -1 and selectedItem != None:
        xbmc.executebuiltin("Container.SetViewMode(%s)" %selectedItem)
    
def searchYouTube(title,windowHeader=""):
    xbmc.executebuiltin( "ActivateWindow(busydialog)" )
    import Dialogs as dialogs
    libPath = "plugin://plugin.video.youtube/kodion/search/query/?q=" + title
    media_array = None
    allResults = []
    media_array = getJSON('Files.GetDirectory','{ "properties": ["title","art","plot"], "directory": "%s", "media": "files", "limits": {"end":25} }' %libPath)
    if(media_array != None and media_array.has_key('files')):
        for media in media_array['files']:
            
            if not media["filetype"] == "directory":
                label = media["label"]
                label2 = media["plot"]
                image = None
                if media.has_key('art'):
                    if media['art'].has_key('thumb'):
                        image = (media['art']['thumb'])
                        
                path = media["file"]
                listitem = xbmcgui.ListItem(label=label, label2=label2, iconImage=image)
                listitem.setProperty("path",path)
                listitem.setProperty("icon",image)
                allResults.append(listitem)

    w = dialogs.DialogSelectBig( "DialogSelect.xml", ADDON_PATH, listing=allResults, windowtitle=windowHeader,multiselect=False )
    xbmc.executebuiltin( "Dialog.Close(busydialog)" )
    w.doModal()
    selectedItem = w.result
    del w
    if selectedItem != -1:
        path = allResults[selectedItem].getProperty("path")
        xbmc.executebuiltin("PlayMedia(%s)" %path)
            
def selectView(contenttype="other", currentView=None, displayNone=False, displayViewId=False):
    import Dialogs as dialogs
    currentViewSelectId = None

    allViews = []
    if displayNone:
        listitem = xbmcgui.ListItem(label="None")
        listitem.setProperty("id","None")
        allViews.append(listitem)
        
    views_file = xbmc.translatePath( 'special://skin/extras/views.xml' ).decode("utf-8")
    if xbmcvfs.exists( views_file ):
        doc = parse( views_file )
        listing = doc.documentElement.getElementsByTagName( 'view' )
        itemcount = 0
        for count, view in enumerate(listing):
            label = xbmc.getLocalizedString(int(view.attributes[ 'languageid' ].nodeValue))
            id = view.attributes[ 'value' ].nodeValue
            if displayViewId:
                label = label + " (" + str(id) + ")"
            type = view.attributes[ 'type' ].nodeValue.lower()
            if label.lower() == currentView.lower() or id == currentView:
                currentViewSelectId = itemcount
                if displayNone == True:
                    currentViewSelectId += 1
            if (type == "all" or contenttype.lower() in type) and not xbmc.getCondVisibility("Skin.HasSetting(SkinHelper.View.Disabled.%s)" %id):
                image = "special://skin/extras/viewthumbs/%s.jpg" %id
                listitem = xbmcgui.ListItem(label=label, iconImage=image)
                listitem.setProperty("id",id)
                listitem.setProperty("icon",image)
                allViews.append(listitem)
                itemcount +=1
    w = dialogs.DialogSelectBig( "DialogSelect.xml", ADDON_PATH, listing=allViews, windowtitle=ADDON.getLocalizedString(32054),multiselect=False )
    w.autoFocusId = currentViewSelectId
    w.doModal()
    selectedItem = w.result
    del w
    if selectedItem != -1:
        id = allViews[selectedItem].getProperty("id")
        return id

def toggleKodiSetting(settingname):
    #toggle kodi setting
    curValue = xbmc.getCondVisibility("system.getbool(%s)"%settingname)
    if curValue == True:
        newValue = "false"
    else:
        newValue = "true"
    xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Settings.SetSettingValue","params":{"setting":"%s","value":%s}}' %(settingname,newValue))
   