#!/usr/bin/python
# -*- coding: utf-8 -*-
from utils import get_content_path
from simplecache import SimpleCache
import xbmc

# Various helpers to retrieve our smart shortcuts
    
def update_wallbackgrounds(self):
    if win.getProperty("SkinHelper.enablewall_backgrounds") == "true":
        setWallImageFromPath("SkinHelper.AllMoviesBackground.Wall","SkinHelper.AllMoviesBackground")
        setWallImageFromPath("SkinHelper.AllMoviesBackground.Poster.Wall","SkinHelper.AllMoviesBackground","poster")
        setWallImageFromPath("SkinHelper.AllMusicBackground.Wall","SkinHelper.AllMusicBackground")
        setWallImageFromPath("SkinHelper.AllMusicSongsBackground.Wall","SkinHelper.AllMusicSongsBackground","thumbnail")
        setWallImageFromPath("SkinHelper.AllTvShowsBackground.Wall","SkinHelper.AllTvShowsBackground")
        setWallImageFromPath("SkinHelper.AllTvShowsBackground.Poster.Wall","SkinHelper.AllTvShowsBackground","poster")

def createImageWall(self,images,win_prop,artart_type="fanart"):

    if addon.getSetting("maxNumWallImages"):
        numWallImages = int(addon.getSetting("maxNumWallImages"))
    else:
        log_msg("Building WALL background disabled",0)
        return []

    #PIL fails on Android devices ?
    hasPilModule = True
    try:
        from PIL import Image
        im = Image.new("RGB", (1, 1))
        del im
    except Exception:
        hasPilModule = False

    if not hasPilModule:
        log_msg("Building WALL background skipped - no PIL module present on this system!", xbmc.LOGWARNING)
        return []

    if artart_type=="thumbnail":
        #square images
        img_columns = 11
        img_rows = 7
        img_width = 260
        img_height = 260
    elif artart_type=="poster":
        #poster images
        img_columns = 15
        img_rows = 5
        img_width = 128
        img_height = 216
    else:
        #landscaped images
        img_columns = 8
        img_rows = 8
        img_width = 240
        img_height = 135
    size = img_width, img_height

    wallpath = "special://profile/addon_data/script.skin.helper.service/wall_backgrounds/"
    if not xbmcvfs.exists(wallpath):
        xbmcvfs.mkdirs(wallpath)

    wall_images = []
    return_images = []

    if addon.getSetting("reuseWall_backgrounds") == "true":
        #reuse the existing images - do not rebuild
        dirs, files = xbmcvfs.listdir(wallpath)
        for file in files:
            image = {}
            #return color and bw image combined - only if both are found
            if file.startswith(win_prop + "_BW.") and xbmcvfs.exists(os.path.join(wallpath.decode("utf-8"),file.replace("_BW",""))):
                return_images.append({"wallbw": os.path.join(wallpath.decode("utf-8"),file), "wall": os.path.join(wallpath.decode("utf-8"),file.replace("_BW",""))})

    #build wall images if we do not already have (enough) images
    if len(return_images) < numWallImages:
        #build the wall images
        log_msg("Building Wall background for %s - this might take a while..." %win_prop, xbmc.LOGNOTICE)
        images_required = img_columns*img_rows
        for image in images:
            image = image.get(artart_type,"")
            if exit: return []
            if image and not image.startswith("music@") and not ".mp3" in image:
                file = xbmcvfs.File(image)
                try:
                    img_obj = io.BytesIO(bytearray(file.readBytes()))
                    img = Image.open(img_obj)
                    img = img.resize(size)
                    wall_images.append(img)
                except Exception: pass
                finally: file.close()
        if wall_images:
            #duplicate images if we don't have enough

            while len(wall_images) < images_required:
                wall_images += wall_images

            for i in range(numWallImages):
                if exit: return []
                random.shuffle(wall_images)
                img_canvas = Image.new("RGBA", (img_width * img_columns, img_height * img_rows))
                counter = 0
                for x in range(img_rows):
                    for y in range(img_columns):
                        img_canvas.paste(wall_images[counter], (y * img_width, x * img_height))
                        counter += 1

                #save the files..
                out_file = xbmc.translatePath(os.path.join(wallpath.decode("utf-8"),win_prop + "." + str(i) + ".jpg")).decode("utf-8")
                if xbmcvfs.exists(out_file):
                    xbmcvfs.delete(out_file)
                    xbmc.sleep(500)
                img_canvas.save(out_file, "JPEG")

                out_file_bw = xbmc.translatePath(os.path.join(wallpath.decode("utf-8"),win_prop + "_BW." + str(i) + ".jpg")).decode("utf-8")
                if xbmcvfs.exists(out_file_bw):
                    xbmcvfs.delete(out_file_bw)
                    xbmc.sleep(500)
                img_canvas_bw = img_canvas.convert("L")
                img_canvas_bw.save(out_file_bw, "JPEG")

                #add our images to the dict
                return_images.append({"wall": out_file, "wallbw": out_file_bw })

        log_msg("Building Wall background %s DONE" %win_prop)
    return return_images
        
  
    
def setWallImageFromPath(self, win_prop, lib_path, art_type="fanart"):
    image = None
    win_propBW = win_prop + ".BW"

    #load wall from cache
    if all_backgrounds.get(win_prop):
        image = random.choice(all_backgrounds[win_prop])
        if image.get("wall"):
            if not xbmcvfs.exists(image.get("wall")):
                log_msg("Wall images cleared - starting rebuild...",xbmc.LOGWARNING)
                del all_backgrounds[win_prop]
            else:
                win.setProperty(win_prop, image.get("wall"))
                win.setProperty(win_propBW, image.get("wallbw"))
                return True

    #load images for lib_path and generate wall
    if all_backgrounds.get(lib_path):
        images = []
        try:
            images = createImageWall(all_backgrounds[lib_path],win_prop,art_type)
        except Exception as e:
            log_msg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)
            log_msg("ERROR in createImageWall ! --> %s" %e, xbmc.LOGERROR)
        all_backgrounds[win_prop] = images
        if images:
            image = random.choice(images)
            if image:
                win.setProperty(win_prop, image.get("wall",""))
                win.setProperty(win_propBW, image.get("wallbw",""))

def setManualWallFromPath(self, win_prop, numItems=20):
    #only continue if the cache is prefilled
    if all_backgrounds.get(win_prop):
        if win_prop in manualWallsLoaded:
            #only refresh one random image...
            image = random.choice(all_backgrounds[win_prop])
            if image:
                for key, value in image.iteritems():
                    if key == "fanart": win.setProperty("%s.Wall.%s" %(win_prop,random.randint(0, numItems)), value)
                    else: win.setProperty("%s.Wall.%s.%s" %(win_prop,random.randint(0, numItems),key), value)
        else:
            #first run: set all images
            for i in range(numItems):
                image = random.choice(all_backgrounds[win_prop])
                if image:
                    for key, value in image.iteritems():
                        if key == "fanart": win.setProperty("%s.Wall.%s" %(win_prop,i), value)
                        else: win.setProperty("%s.Wall.%s.%s" %(win_prop,i,key), value)
                manualWallsLoaded.append(win_prop)

def updateWallImages(self):
    #manual wall images, provides a collection of images which are randomly changing
    if wallImagesDelay == 0 or not manualWalls:
        return

    #we have a list stored in memory for the wall collections the skinner wants to be generated
    for key, value in manualWalls.iteritems():
        setManualWallFromPath(key, value)
