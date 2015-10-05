#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcgui
import threading
import thread
import xbmcvfs
import random
import xml.etree.ElementTree as etree
import base64
import time
from Utils import *

class HomeMonitor(threading.Thread):
    
    event = None
    exit = False
    delayedTaskInterval = 1795
    lastWeatherNotificationCheck = None
    lastNextAiredNotificationCheck = None
    
    def __init__(self, *args):
        logMsg("HomeMonitor - started")
        self.event =  threading.Event()
        threading.Thread.__init__(self, *args)

    
    def stop(self):
        logMsg("HomeMonitor - stop called",0)
        self.exit = True
        self.event.set()

    def run(self):
        
        listItem = None
        lastListItem = None

        while (self.exit != True):
            
            #do some background stuff every 30 minutes
            if (xbmc.getCondVisibility("!Window.IsActive(fullscreenvideo)")):
                if (self.delayedTaskInterval >= 1800):
                    thread.start_new_thread(self.doBackgroundWork, ())
                    self.delayedTaskInterval = 0
            
            # monitor main menu when home is active
            if (xbmc.getCondVisibility("Window.IsActive(home) + !Window.IsActive(fullscreenvideo)")):
                mainMenuContainer = WINDOW.getProperty("SkinHelper.MainMenuContainer")
                listItem = xbmc.getInfoLabel("Container(%s).ListItem.Property(defaultID)" %mainMenuContainer)
                if listItem != lastListItem and mainMenuContainer:
                    
                    #set the active widget
                    activewidget = xbmc.getInfoLabel("$INFO[Skin.String(widgetvalue-%s)]" %listItem)
                    if activewidget:
                        if activewidget != "0":
                            if not xbmc.getInfoLabel("$INFO[Container(%s).ListItem.Property(widget.%s)]" %(mainMenuContainer,activewidget)):
                                activewidget = "0"
                        WINDOW.setProperty("SkinHelper.ActiveWidget",activewidget)
                    else: 
                        WINDOW.setProperty("SkinHelper.ActiveWidget","0")
                    
                    # update the background
                    background = xbmc.getInfoLabel("Container(%s).ListItem.Property(Background)" %mainMenuContainer)
                    WINDOW.setProperty("SkinHelper.SectionBackground", background)
                    lastListItem = listItem           
            
            xbmc.sleep(150)
            self.delayedTaskInterval += 0.15
    
    def checkNetflixReady(self):
        if xbmc.getCondVisibility("System.HasAddon(plugin.video.netflixbmc)"):
            #set windowprop if netflix addon has a username filled in to prevent login loop box
            nfaddon = xbmcaddon.Addon(id='plugin.video.netflixbmc')
            if nfaddon.getSetting("username") and nfaddon.getSetting("html5MessageShown"):
                WINDOW.setProperty("netflixready","ready")
            else:
                WINDOW.clearProperty("netflixready")
    
    def doBackgroundWork(self):
        try:
            self.checkNetflixReady()
            self.updatePlexlinks()
            self.genericWindowProps()
            self.checkNotifications()
        except Exception as e:
            logMsg("ERROR in HomeMonitor doBackgroundWork ! --> " + str(e), 0)
       
    def updatePlexlinks(self):
        
        if xbmc.getCondVisibility("System.HasAddon(plugin.video.plexbmc) + Skin.HasSetting(SmartShortcuts.plex)"): 
            logMsg("update plexlinks started...")
            
            #initialize plex window props by using the amberskin entrypoint for now
            if not WINDOW.getProperty("plexbmc.0.title"):
                xbmc.executebuiltin('RunScript(plugin.video.plexbmc,amberskin)')
                #wait for max 20 seconds untill the plex nodes are available
                count = 0
                while (count < 80 and not WINDOW.getProperty("plexbmc.0.title")):
                    xbmc.sleep(250)
                    count += 1
            
            #fallback to normal skin init
            if not WINDOW.getProperty("plexbmc.0.title"):
                xbmc.executebuiltin('RunScript(plugin.video.plexbmc,skin)')
                count = 0
                while (count < 40 and not WINDOW.getProperty("plexbmc.0.title")):
                    xbmc.sleep(250)
                    count += 1
            
            #get the plex setting if there are subnodes
            plexaddon = xbmcaddon.Addon(id='plugin.video.plexbmc')
            hasSecondayMenus = plexaddon.getSetting("secondary") == "true"
            del plexaddon
            
            #update plex window properties
            linkCount = 0
            while linkCount !=50:
                plexstring = "plexbmc." + str(linkCount)
                link = WINDOW.getProperty(plexstring + ".title")
                if not link:
                    break
                logMsg(plexstring + ".title --> " + link)
                plexType = WINDOW.getProperty(plexstring + ".type")
                logMsg(plexstring + ".type --> " + plexType)            

                if hasSecondayMenus == True:
                    recentlink = WINDOW.getProperty(plexstring + ".recent")
                    progresslink = WINDOW.getProperty(plexstring + ".ondeck")
                    alllink = WINDOW.getProperty(plexstring + ".all")
                else:
                    link = WINDOW.getProperty(plexstring + ".path")
                    alllink = link
                    link = link.replace("mode=1", "mode=0")
                    link = link.replace("mode=2", "mode=0")
                    recentlink = link.replace("/all", "/recentlyAdded")
                    progresslink = link.replace("/all", "/onDeck")
                    WINDOW.setProperty(plexstring + ".recent", recentlink)
                    WINDOW.setProperty(plexstring + ".ondeck", progresslink)
                    
                logMsg(plexstring + ".all --> " + alllink)
                
                WINDOW.setProperty(plexstring + ".recent.content", getContentPath(recentlink))
                WINDOW.setProperty(plexstring + ".recent.path", recentlink)
                WINDOW.setProperty(plexstring + ".recent.title", "recently added")
                logMsg(plexstring + ".recent --> " + recentlink)       
                WINDOW.setProperty(plexstring + ".ondeck.content", getContentPath(progresslink))
                WINDOW.setProperty(plexstring + ".ondeck.path", progresslink)
                WINDOW.setProperty(plexstring + ".ondeck.title", "on deck")
                logMsg(plexstring + ".ondeck --> " + progresslink)
                
                unwatchedlink = alllink.replace("mode=1", "mode=0")
                unwatchedlink = alllink.replace("mode=2", "mode=0")
                unwatchedlink = alllink.replace("/all", "/unwatched")
                WINDOW.setProperty(plexstring + ".unwatched", unwatchedlink)
                WINDOW.setProperty(plexstring + ".unwatched.content", getContentPath(unwatchedlink))
                WINDOW.setProperty(plexstring + ".unwatched.path", unwatchedlink)
                WINDOW.setProperty(plexstring + ".unwatched.title", "unwatched")
                
                WINDOW.setProperty(plexstring + ".content", getContentPath(alllink))
                WINDOW.setProperty(plexstring + ".path", alllink)
                
                linkCount += 1
                
            #add plex channels as entry - extract path from one of the nodes as a workaround because main plex addon channels listing is in error
            link = WINDOW.getProperty("plexbmc.0.path")
            
            if link:
                link = link.split("/library/")[0]
                link = link + "/channels/all&mode=21"
                link = link + ", return)"
                plexstring = "plexbmc.channels"
                WINDOW.setProperty(plexstring + ".title", "Channels")
                logMsg(plexstring + ".path --> " + link)
                WINDOW.setProperty(plexstring + ".path", link)
                WINDOW.setProperty(plexstring + ".content", getContentPath(link))

    def checkNotifications(self):
        
        currentHour = time.strftime("%H")
        
        #weather notifications
        winw = xbmcgui.Window(12600)
        if (winw.getProperty("Alerts.RSS") and winw.getProperty("Current.Condition") and currentHour != self.lastWeatherNotificationCheck):
            dialog = xbmcgui.Dialog()
            dialog.notification(xbmc.getLocalizedString(31294), winw.getProperty("Alerts"), xbmcgui.NOTIFICATION_WARNING, 8000)
            self.lastWeatherNotificationCheck = currentHour
        
        #nextaired notifications
        if (xbmc.getCondVisibility("Skin.HasSetting(EnableNextAiredNotifications) + System.HasAddon(script.tv.show.next.aired)") and currentHour != self.lastNextAiredNotificationCheck):
            if (WINDOW.getProperty("NextAired.TodayShow")):
                dialog = xbmcgui.Dialog()
                dialog.notification(xbmc.getLocalizedString(31295), WINDOW.getProperty("NextAired.TodayShow"), xbmcgui.NOTIFICATION_WARNING, 8000)
                self.lastNextAiredNotificationCheck = currentHour
    
    def genericWindowProps(self):
        
        #GET TOTAL ADDONS COUNT       
        allAddonsCount = 0
        media_array = getJSON('Addons.GetAddons','{ }')
        for item in media_array:
            allAddonsCount += 1
        WINDOW.setProperty("SkinHelper.TotalAddons",str(allAddonsCount))
        
        addontypes = []
        addontypes.append( ["executable", "SkinHelper.TotalProgramAddons", 0] )
        addontypes.append( ["video", "SkinHelper.TotalVideoAddons", 0] )
        addontypes.append( ["audio", "SkinHelper.TotalAudioAddons", 0] )
        addontypes.append( ["image", "SkinHelper.TotalPicturesAddons", 0] )

        for type in addontypes:
            media_array = getJSON('Addons.GetAddons','{ "content": "%s" }' %type[0])
            for item in media_array:
                type[2] += 1
            WINDOW.setProperty(type[1],str(type[2]))    
                
        #GET FAVOURITES COUNT        
        allFavouritesCount = 0
        media_array = getJSON('Favourites.GetFavourites','{ }')
        for item in media_array:
            allFavouritesCount += 1
        WINDOW.setProperty("SkinHelper.TotalFavourites",str(allFavouritesCount))

        #GET TV CHANNELS COUNT
        if xbmc.getCondVisibility("Pvr.HasTVChannels"):
            allTvChannelsCount = 0
            media_array = getJSON('PVR.GetChannels','{"channelgroupid": "alltv" }' )
            for item in media_array:
                allTvChannelsCount += 1
            WINDOW.setProperty("SkinHelper.TotalTVChannels",str(allTvChannelsCount))        

        #GET RADIO CHANNELS COUNT
        if xbmc.getCondVisibility("Pvr.HasRadioChannels"):
            allRadioChannelsCount = 0
            media_array = getJSON('PVR.GetChannels','{"channelgroupid": "allradio" }' )
            for item in media_array:
                allRadioChannelsCount += 1
            WINDOW.setProperty("SkinHelper.TotalRadioChannels",str(allRadioChannelsCount))        
               


               