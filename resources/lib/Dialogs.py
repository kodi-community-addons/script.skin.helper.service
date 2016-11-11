#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcgui
import xbmc


class DialogContextMenu(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self)
        self.listing = kwargs.get("listing")
        self.windowtitle = kwargs.get("windowtitle")
        self.result = -1

    def onInit(self):
        '''Initialization when the window is loaded'''
        try:
            self.list_control = self.getControl(6)
            self.getControl(3).setVisible(False)
        except Exception:
            self.list_control = self.getControl(3)

        self.getControl(5).setVisible(False)
        self.getControl(1).setLabel(self.windowtitle)

        for item in self.listing:
            listitem = xbmcgui.ListItem(
                label=item.getLabel(),
                label2=item.getLabel2(),
                iconImage=item.getProperty("icon"),
                thumbnailImage=item.getProperty("thumbnail"))
            listitem.setProperty("Addon.Summary", item.getLabel2())
            self.list_control.addItem(listitem)

        self.setFocus(self.list_control)

    def onAction(self, action):
        '''Respond to Kodi actions e.g. exit'''
        if action.getId() in (9, 10, 92, 216, 247, 257, 275, 61467, 61448, ):
            self.result = -1
            self.close()

    def onClick(self, controlID):
        '''Fires if user clicks the dialog'''
        if controlID == 6 or controlID == 3:
            num = self.list_control.getSelectedPosition()
            self.result = num
        else:
            self.result = -1

        self.close()


class DialogSelectSmall(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self)
        self.listing = kwargs.get("listing")
        self.windowtitle = kwargs.get("windowtitle")
        self.multiselect = kwargs.get("multiselect")
        self.totalitems = 0
        self.result = -1
        self.autofocus_id = 0

    def onInit(self):
        '''Initialization when the window is loaded'''
        self.getControl(6).setVisible(False)
        self.getControl(3).setEnabled(True)
        self.getControl(1).setLabel(self.windowtitle)
        try:
            self.getControl(7).setLabel(xbmc.getLocalizedString(222))
        except Exception:
            pass

        if not self.multiselect:
            self.getControl(5).setVisible(False)

        self.list_control = self.getControl(3)

        for item in self.listing:
            listitem = xbmcgui.ListItem(
                label=item.getLabel(),
                label2=item.getLabel2(),
                iconImage=item.getProperty("icon"),
                thumbnailImage=item.getProperty("thumbnail"))
            listitem.setProperty("Addon.Summary", item.getLabel2())
            listitem.select(selected=item.isSelected())
            self.list_control.addItem(listitem)

        self.setFocus(self.list_control)
        try:
            self.list_control.selectItem(self.autofocus_id)
        except Exception:
            self.list_control.selectItem(0)
        self.totalitems = len(self.listing)

    def onAction(self, action):
        '''Respond to Kodi actions e.g. exit'''
        if action.getId() in (9, 10, 92, 216, 247, 257, 275, 61467, 61448, ):
            if self.multiselect:
                items_list = []
                itemcount = self.totalitems - 1
                while (itemcount != -1):
                    listitem = self.list_control.getListItem(itemcount)
                    if listitem.isSelected():
                        items_list.append(itemcount)
                    itemcount -= 1
                self.result = items_list
            else:
                self.result = -1
            self.close()

        # select item in list
        if (action.getId() == 7 or action.getId() == 100) and xbmc.getCondVisibility("Control.HasFocus(3)"):
            if self.multiselect:
                item = self.list_control.getSelectedItem()
                if item.isSelected():
                    item.select(selected=False)
                else:
                    item.select(selected=True)
            else:
                num = self.list_control.getSelectedPosition()
                self.result = num
                self.close()

    def onClick(self, controlID):
        '''Fires if user clicks the dialog'''
        # OK button
        if controlID == 5:
            items_list = []
            itemcount = self.totalitems - 1
            while (itemcount != -1):
                listitem = self.list_control.getListItem(itemcount)
                if listitem.isSelected():
                    items_list.append(itemcount)
                itemcount -= 1
            self.result = items_list
            self.close()

        # Other buttons (including cancel)
        else:
            self.result = -1
            self.close()


class DialogSelectBig(xbmcgui.WindowXMLDialog):

    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self)
        self.listing = kwargs.get("listing")
        self.windowtitle = kwargs.get("windowtitle")
        self.result = -1
        self.autofocus_id = 0

    def onInit(self):
        '''Initialization when the window is loaded'''
        try:
            self.list_control = self.getControl(6)
            self.getControl(1).setLabel(self.windowtitle)
            self.getControl(3).setVisible(False)
            try:
                self.getControl(7).setLabel(xbmc.getLocalizedString(222))
            except Exception:
                pass
        except Exception:
            self.list_control = self.getControl(3)

        self.getControl(5).setVisible(False)

        for item in self.listing:
            listitem = xbmcgui.ListItem(
                label=item.getLabel(),
                label2=item.getLabel2(),
                iconImage=item.getProperty("icon"),
                thumbnailImage=item.getProperty("thumbnail"))
            listitem.setProperty("Addon.Summary", "")
            self.list_control.addItem(listitem)

        self.setFocus(self.list_control)
        try:
            self.list_control.selectItem(self.autofocus_id)
        except Exception:
            self.list_control.selectItem(0)

    def onAction(self, action):
        '''Respond to Kodi actions e.g. exit'''
        if action.getId() in (9, 10, 92, 216, 247, 257, 275, 61467, 61448, ):
            self.result = -1
            self.close()

    def onClick(self, controlID):
        '''Fires if user clicks the dialog'''
        if controlID == 6 or controlID == 3:
            num = self.list_control.getSelectedPosition()
            self.result = num
        else:
            self.result = -1

        self.close()
