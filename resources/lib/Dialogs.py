#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcgui
import xbmc


class DialogSelect(xbmcgui.WindowXMLDialog):
    '''Wrapper around Kodi dialogselect to use for the custom skin settings etc.'''
    
    def __init__(self, *args, **kwargs):
        xbmcgui.WindowXMLDialog.__init__(self)
        self.listing = kwargs.get("listing")
        self.windowtitle = kwargs.get("windowtitle")
        self.multiselect = kwargs.get("multiselect")
        self.richlayout = kwargs.get("richlayout", False)
        self.totalitems = 0
        self.autofocus_id = 0

    def close_dialog(self, cancelled=False):
        '''close dialog and return value'''
        if cancelled:
            self.result = None
        elif self.multiselect:
            # for multiselect we return the entire listing
            items_list = []
            itemcount = self.totalitems - 1
            while (itemcount != -1):
                items_list.append(self.list_control.getListItem(itemcount))
                itemcount -= 1
            self.result = items_list
        else:
            self.result = self.list_control.getSelectedItem()
        self.close()

    def onInit(self):
        '''Initialization when the window is loaded'''

        # set correct list
        self.set_list_control()

        # set window header
        self.getControl(1).setLabel(self.windowtitle)

        self.list_control.addItems(self.listing)

        self.setFocus(self.list_control)
        try:
            self.list_control.selectItem(self.autofocus_id)
        except Exception:
            self.list_control.selectItem(0)
        self.totalitems = len(self.listing)

    def onAction(self, action):
        '''Respond to Kodi actions e.g. exit'''
        if action.getId() in (9, 10, 92, 216, 247, 257, 275, 61467, 61448, ):
            self.close_dialog(True)

        # an item in the list is clicked
        if (action.getId() == 7 or action.getId() == 100) and xbmc.getCondVisibility(
                "Control.HasFocus(3) | Control.HasFocus(6)"):
            if self.multiselect:
                # select/deselect the item
                item = self.list_control.getSelectedItem()
                if item.isSelected():
                    item.select(selected=False)
                else:
                    item.select(selected=True)
            else:
                # no multiselect so just close the dialog (and return results)
                self.close_dialog()

    def onClick(self, controlID):
        '''Fires if user clicks the dialog'''
        # OK button
        if controlID == 5:
            self.close_dialog()
            # items_list = []
            # itemcount = self.totalitems - 1
            # while (itemcount != -1):
            # listitem = self.list_control.getListItem(itemcount)
            # if listitem.isSelected():
            # items_list.append(itemcount)
            # itemcount -= 1
            # self.result = items_list
            # self.close()

        # Other buttons (including cancel)
        else:
            self.close_dialog(True)

    def set_list_control(self):
        '''select correct list (3=small, 6=big with icons)'''
        has_list3 = False
        has_list6 = False
        try:
            control = self.getControl(3)
            has_list3 = True
        except Exception:
            pass
        try:
            control = self.getControl(6)
            has_list6 = True
        except Exception:
            pass

        if has_list3:
            self.list_control = self.getControl(3)
        else:
            self.list_control = self.getControl(6)
        # set list id 6 if available for rich dialog
        if has_list6 and self.richlayout and not self.multiselect:
            self.list_control = self.getControl(6)
        self.list_control.setEnabled(True)
        self.list_control.setVisible(True)
        if self.multiselect:
            self.set_cancel_button()
        else:
            # disable OK button
            self.getControl(5).setVisible(False)

    def set_cancel_button(self):
        '''set cancel button if exists'''
        try:
            self.getControl(7).setLabel(xbmc.getLocalizedString(222))
            self.getControl(7).setVisible(True)
            self.getControl(7).setEnabled(True)
        except Exception:
            pass
