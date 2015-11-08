import xbmc, xbmcgui, time, urllib
from Utils import *

class SplashWindow(xbmcgui.WindowXMLDialog):
    imagePath = None
    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXMLDialog.__init__( self )
        
    def onInit(self):
        imageCtrl = self.getControl(2030)
        if self.imagePath: imageCtrl.setImage(self.imagePath)

def show_splash(file,duration=5):
    if not WINDOW.getProperty("skinhelper.splashshown"):
        viewer = SplashWindow("script-skin_helper_service-SplashScreen.xml", ADDON_PATH, "Default", "1080i")
        logMsg("show_splash --> " + file)
        if file.lower().endswith("jpg") or file.lower().endswith("gif") or file.lower().endswith("png") or file.lower().endswith("tiff"):
            #this is an image file
            viewer.imagePath = file
        viewer.show()
        
        if viewer.imagePath:
            #for images we just wait for X seconds to close the splash again
            start_time = time.time()
            while(time.time() - start_time <= duration):
                xbmc.sleep(500)
        else:
            #for video or audio we have to wait for the player to finish...
            xbmc.Player().play(file,windowed=False)
            xbmc.sleep(1000)
            while xbmc.getCondVisibility("Player.HasMedia"):
                xbmc.sleep(150)
        
        startupwindow = xbmc.getInfoLabel("$INFO[System.StartupWindow]")
        xbmc.executebuiltin("ReplaceWindow(%s)" %startupwindow)
        viewer.close()
        del viewer
        WINDOW.setProperty("skinhelper.splashshown","true")
    
    