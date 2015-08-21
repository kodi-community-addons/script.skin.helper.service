import sys
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import os, sys
import urllib
import threading
import InfoDialog
import math

from xml.dom.minidom import parse
from operator import itemgetter
from Utils import *

#PIL fails on Android devices ?
hasPilModule = True
try:
    from PIL import Image
except:
    hasPilModule = False

class ColorPicker(xbmcgui.WindowXMLDialog):

    colorsList = None
    skinString = None
    colorsPath = None
    savedColor = None
    currentWindow = None
    
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.colorsPath = os.path.join(ADDON_PATH, 'resources', 'colors' ).decode("utf-8")
        
    def addColorToList(self, colorname, colorstring):
        
        colorImageFile = os.path.join(self.colorsPath,colorstring + ".png")
        
        if not xbmcvfs.exists(colorImageFile) and hasPilModule:
            colorstring = colorstring.strip()
            if colorstring[0] == '#': colorstring = colorstring[1:]
            if len(colorstring) != 8:
                raise ValueError, "input #%s is not in #AARRGGBB format" % colorstring
            a, r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:6], colorstring[6:]
            a, r, g, b = [int(n, 16) for n in (a, r, g, b)]
            color = (r, g, b, a)
            im = Image.new("RGBA", (64, 64), color)
            im.save(colorImageFile)
        elif not xbmcvfs.exists(colorImageFile) and not hasPilModule:
            return
        
        listitem = xbmcgui.ListItem(label=colorname, iconImage=colorImageFile)
        listitem.setProperty("colorstring",colorstring)
        self.colorsList.addItem(listitem)
        
    
    
    def onInit(self):
        self.action_exitkeys_id = [10, 13]
        
        self.currentWindow = xbmcgui.Window( xbmcgui.getCurrentWindowDialogId() )

        if not xbmcvfs.exists(self.colorsPath):
            xbmcvfs.mkdir(self.colorsPath)
        
        self.colorsList = self.getControl(3110)
        self.win = xbmcgui.Window( 10000 )
        
        #get current color that is stored in the skin setting
        self.currentWindow.setProperty("colorstring", xbmc.getInfoLabel("Skin.String(" + self.skinString + ')'))
        self.currentWindow.setProperty("colorname", xbmc.getInfoLabel("Skin.String(" + self.skinString + '.name)'))
        selectItem = 0
        
        #get all colors from the colors xml file and fill a list with tuples to sort later on
        allColors = []
        colors_file = os.path.join(ADDON_PATH, 'resources', 'colors','colors.xml' ).decode("utf-8")
        if xbmcvfs.exists( colors_file ):
            doc = parse( colors_file )
            listing = doc.documentElement.getElementsByTagName( 'color' )
            for count, color in enumerate(listing):
                name = color.attributes[ 'name' ].nodeValue.lower()
                colorstring = color.childNodes [ 0 ].nodeValue.lower()
                allColors.append((name,colorstring))
                
        #sort list and fill the panel
        count = 0
        allColors = sorted(allColors,key=itemgetter(1))
        colorstring = self.currentWindow.getProperty("colorstring")
        colorname = self.currentWindow.getProperty("colorname")
        for color in allColors:
            self.addColorToList(color[0], color[1])
            if (colorname == color[0] or colorstring == color[1]):
                selectItem = count
            count += 1

        #focus the current color
        if selectItem != 0:
            #select existing color in the list
            self.currentWindow.setFocusId(3110)
            self.colorsList.selectItem(selectItem)
        elif self.currentWindow.getProperty("colorstring"):
            #user has setup a manual color so focus the manual button
            self.currentWindow.setFocusId(3010)
        else:
            #no color setup so we just focus the colorslist
            self.currentWindow.setFocusId(3110)
            self.colorsList.selectItem(selectItem)
        
        #set opacity slider
        if self.currentWindow.getProperty("colorstring"):
            self.setOpacitySlider()

    def onFocus(self, controlId):
        pass
        
    def onAction(self, action):

        ACTION_CANCEL_DIALOG = ( 9, 10, 92, 216, 247, 257, 275, 61467, 61448, )
        ACTION_SHOW_INFO = ( 11, )
        ACTION_SELECT_ITEM = 7
        ACTION_PARENT_DIR = 9
        
        if action.getId() in ACTION_CANCEL_DIALOG:
            self.closeDialog()
        else:
            if self.currentWindow.getFocusId() == 3110:
                item =  self.colorsList.getSelectedItem()
                colorstring = item.getProperty("colorstring")
                self.currentWindow.setProperty("colorstring",colorstring)
                self.currentWindow.setProperty("colorname",item.getLabel())
                self.setOpacitySlider()


    def closeDialog(self):
        self.close()

    def setOpacitySlider(self):
        colorstring = self.currentWindow.getProperty("colorstring")
        a, r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:6], colorstring[6:]
        a, r, g, b = [int(n, 16) for n in (a, r, g, b)]
        a = 100.0 * a / 255
        self.getControl( 3015 ).setPercent( float(a) )
        
    def onClick(self, controlID):
        colorname = self.currentWindow.getProperty("colorname")
        colorstring = self.currentWindow.getProperty("colorstring")
        if controlID == 3110:       
            self.currentWindow.setFocusId(3012)
        elif controlID == 3010:  
            #manual input
            dialog = xbmcgui.Dialog()
            colorstring = dialog.input("Color", self.currentWindow.getProperty("colorstring"), type=xbmcgui.INPUT_ALPHANUM)
            self.currentWindow.setProperty("colorname", ADDON.getLocalizedString(32050))
            self.currentWindow.setProperty("colorstring", colorstring)
            self.setOpacitySlider()
        elif controlID == 3011:
            # none button
            colorname = ADDON.getLocalizedString(32013)
            xbmc.executebuiltin("Skin.SetString(" + self.skinString + '.name,'+ colorname + ')')
            xbmc.executebuiltin("Skin.SetString(" + self.skinString + ',None)')
            self.closeDialog()
        elif controlID == 3012:
            #save button clicked
            if self.skinString and colorstring:
                xbmc.executebuiltin("Skin.SetString(" + self.skinString + '.name,'+ colorname + ')')
                xbmc.executebuiltin("Skin.SetString(" + self.skinString + ','+ colorstring + ')')
                self.closeDialog()
          
        elif controlID == 3015:
            opacity = self.getControl( 3015 ).getPercent()
            
            num = opacity / 100.0 * 255
            e = num - math.floor( num )
            a = e < 0.5 and int( math.floor( num ) ) or int( math.ceil( num ) )
            
            colorstring = colorstring.strip()
            r, g, b = colorstring[2:4], colorstring[4:6], colorstring[6:]
            r, g, b = [int(n, 16) for n in (r, g, b)]
            color = (a, r, g, b)
            colorstringvalue = '%02x%02x%02x%02x' % color

            self.currentWindow.setProperty("colorstring",colorstringvalue)

            
            