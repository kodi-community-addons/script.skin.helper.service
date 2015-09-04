import sys
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import os, sys
import urllib
import threading
import InfoDialog
import json
from xml.dom.minidom import parse
from operator import itemgetter
from Utils import *
import datetime
import time

cachePath = os.path.join(ADDON_DATA_PATH,"conditionalbackgrounds.json")
dateFormat = "%Y-%m-%d"

class ConditionalBackgrounds(xbmcgui.WindowXMLDialog):

    backgroundsList = None
    allBackgrounds = []
    
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        #read all backgrounds that are setup
        if xbmcvfs.exists(cachePath):
            with open(cachePath) as data_file:    
                self.allBackgrounds = getConditionalBackgrounds()
    
    def refreshListing(self):
        count = 0
        
        #clear list first
        self.backgroundsList.reset()

        for bg in self.allBackgrounds:
            label = bg["name"]
            if time_in_range(bg["startdate"],bg["enddate"],datetime.datetime.now().strftime(dateFormat)):
                label = label + " " + xbmc.getLocalizedString(461)
            listitem = xbmcgui.ListItem(label=label,iconImage=bg["background"])
            desc = "[B]%s:[/B] %s [CR][B]%s:[/B] %s" %(xbmc.getLocalizedString(19128),bg["startdate"],xbmc.getLocalizedString(19129),bg["enddate"])
            listitem.setProperty("description",desc)
            listitem.setProperty("Addon.Summary",desc)
            listitem.setLabel2(desc)
            listitem.setProperty("id",str(count))
            self.backgroundsList.addItem(listitem)
            count += 1
        
        #set conditional backgrounds window prop
        WINDOW.setProperty("SkinHelper.ConditionalBackgrounds",repr(self.allBackgrounds))
        
        if count != 0:
            xbmc.executebuiltin("Control.SetFocus(6)")
        else:
            xbmc.executebuiltin("Control.SetFocus(5)")
    
    def onInit(self):
        self.action_exitkeys_id = [10, 13]
        
        self.backgroundsList = self.getControl(6)
        
        self.getControl(1).setLabel(ADDON.getLocalizedString(32056))
        self.getControl(5).setVisible(True)
        self.getControl(5).setLabel(xbmc.getLocalizedString(15019))
        self.getControl(7).setLabel(xbmc.getLocalizedString(117))
        
        self.refreshListing()

    def onFocus(self, controlId):
        pass
        
    def onAction(self, action):

        ACTION_CANCEL_DIALOG = ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, )
        ACTION_SHOW_INFO = ( 11, )
        ACTION_SELECT_ITEM = 7
        ACTION_PARENT_DIR = 9
        ACTION_CONTEXT_MENU = 117
        
        if action.getId() in ACTION_CANCEL_DIALOG:
            self.closeDialog()

    def closeDialog(self):
        if not xbmcvfs.exists(ADDON_DATA_PATH + os.sep):
            xbmcvfs.mkdir(ADDON_DATA_PATH)

        #cache file for all backgrounds
        json.dump(self.allBackgrounds, open(cachePath,'w'))
        self.close()
        
    def onClick(self, controlID):
        error = False
        item = self.backgroundsList.getSelectedItem()
        id = int(item.getProperty("id"))
        currentvalues = self.allBackgrounds[id]
                
        if(controlID == 6):
            name = xbmcgui.Dialog().input(ADDON.getLocalizedString(32058),currentvalues["name"], type=xbmcgui.INPUT_ALPHANUM)
            background = currentvalues["background"]
            startdate = xbmcgui.Dialog().input(xbmc.getLocalizedString(19128) + " (yyyy-mm-dd)",currentvalues["startdate"], type=xbmcgui.INPUT_ALPHANUM)
            enddate = xbmcgui.Dialog().input(xbmc.getLocalizedString(19129) + " (yyyy-mm-dd)",currentvalues["enddate"], type=xbmcgui.INPUT_ALPHANUM)
            try:
                #check if the dates are valid
                dt = datetime.datetime(*(time.strptime(startdate, dateFormat)[0:6]))
                dt = datetime.datetime(*(time.strptime(startdate, dateFormat)[0:6]))
            except:
                error = True
            
            if not name or not background or error:
                xbmcgui.Dialog().ok(xbmc.getLocalizedString(329), ADDON.getLocalizedString(32060))
            else:
                self.allBackgrounds[id] ={"name": name, "background": background, "startdate":startdate, "enddate":enddate}
                self.refreshListing()
        
        if controlID == 5:
            
            dateToday = datetime.datetime.now().strftime(dateFormat)
            name = xbmcgui.Dialog().input(ADDON.getLocalizedString(32058), type=xbmcgui.INPUT_ALPHANUM)
            background = xbmcgui.Dialog().browse( 2 , ADDON.getLocalizedString(32061), 'files')
            startdate = xbmcgui.Dialog().input(xbmc.getLocalizedString(19128) + " (yyyy-mm-dd)",dateToday, type=xbmcgui.INPUT_ALPHANUM)
            enddate = xbmcgui.Dialog().input(xbmc.getLocalizedString(19129) + " (yyyy-mm-dd)",dateToday, type=xbmcgui.INPUT_ALPHANUM)
            try:
                #check if the dates are valid
                dt = datetime.datetime(*(time.strptime(startdate, dateFormat)[0:6]))
                dt = datetime.datetime(*(time.strptime(startdate, dateFormat)[0:6]))
            except:
                error = True
            
            if not name or not background or error:
                xbmcgui.Dialog().ok(xbmc.getLocalizedString(329), ADDON.getLocalizedString(32060))
            else:
                self.allBackgrounds.append({"name": name, "background": background, "startdate":startdate, "enddate":enddate})
                self.refreshListing()
        
        if controlID == 7:
            #delete
            dialog = xbmcgui.Dialog()
            if dialog.yesno(xbmc.getLocalizedString(122) + " " + item.getLabel() + " ?", xbmc.getLocalizedString(125)):
                del self.allBackgrounds[int(item.getProperty("id"))]
                self.refreshListing()

                
def getConditionalBackgrounds():
    allBackgrounds = []
    #read all backgrounds that are setup
    if xbmcvfs.exists(cachePath):
        with open(cachePath) as data_file:    
            allBackgrounds = json.load(data_file)
    WINDOW.setProperty("SkinHelper.ConditionalBackgrounds",repr(allBackgrounds))
    return allBackgrounds                

def time_in_range(start, end, x):
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end
    
def getActiveConditionalBackground(backgroundsList=None):
    backgroundsList = WINDOW.getProperty("SkinHelper.ConditionalBackgrounds")
    if backgroundsList:
        backgroundsList = eval(backgroundsList)
    background = None
    dateToday = datetime.datetime.now().strftime(dateFormat)
    if not backgroundsList:
        backgroundsList = getConditionalBackgrounds()
    if backgroundsList:
        for bg in backgroundsList:
            if time_in_range(bg["startdate"],bg["enddate"],dateToday):
                background = bg["background"]
                break
    return background
        