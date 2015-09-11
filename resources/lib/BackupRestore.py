import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import xbmcplugin
import os
import json
import shutil
import hashlib
import urllib
import time
import zipfile
import shutil
from Utils import *
import random
from xml.dom.minidom import parse

doDebugLog = False

def getSkinSettings(filter=None):
    newlist = []
    if KODI_VERSION < 16:
        guisettings_path = xbmc.translatePath('special://profile/guisettings.xml').decode("utf-8")
    else:
        #workaround - reload skin to get guisettings
        xbmc.executebuiltin("Reloadskin")
        xbmc.sleep(1500)
        guisettings_path = xbmc.translatePath('special://profile/addon_data/%s/settings.xml' %xbmc.getSkinDir()).decode("utf-8")
    if xbmcvfs.exists(guisettings_path):
        logMsg("guisettings.xml found")
        doc = parse(guisettings_path)
        skinsettings = doc.documentElement.getElementsByTagName('setting')
        
        for count, skinsetting in enumerate(skinsettings):
            
            if KODI_VERSION < 16:
                settingname = skinsetting.attributes['name'].nodeValue
            else:
                settingname = skinsetting.attributes['id'].nodeValue
            
            #only get settings for the current skin                    
            if ( KODI_VERSION < 16 and settingname.startswith(xbmc.getSkinDir()+".")) or KODI_VERSION >= 16:
                
                if skinsetting.childNodes:
                    settingvalue = skinsetting.childNodes[0].nodeValue
                else:
                    settingvalue = ""
                
                settingname = settingname.replace(xbmc.getSkinDir()+".","")
                if settingname.startswith("beta.") or settingname.startswith("helix."):
                    continue
                if not filter:
                    newlist.append((skinsetting.attributes['type'].nodeValue, settingname, settingvalue))
                else:
                    #filter
                    for filteritem in filter:
                        if filteritem.lower() in settingname.lower():
                            newlist.append((skinsetting.attributes['type'].nodeValue, settingname, settingvalue))
    else:
        xbmcgui.Dialog().ok(ADDON.getLocalizedString(32028), ADDON.getLocalizedString(32030))
        logMsg("skin settings file not found")
    
    return newlist

def backup(filterString=None,silent=None,promptfilename="false"):
    try:
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        if filterString:
            if "|" in filterString:
                filter = filterString.split("|")
            else:
                filter = []
                filter.append(filterString)
        else:
            filter = None

        #get backup destination
        backup_path = silent
        if not backup_path:
            backup_path = get_browse_dialog(dlg_type=3,heading=ADDON.getLocalizedString(32018))
        if promptfilename == "true":
            dialog = xbmcgui.Dialog()
            backup_name = dialog.input(ADDON.getLocalizedString(32068), type=xbmcgui.INPUT_ALPHANUM)
        else:
            from datetime import datetime
            i = datetime.now()
            backup_name = xbmc.getSkinDir().decode('utf-8').replace("skin.","") + "_SKIN_BACKUP_" + i.strftime('%Y%m%d-%H%M')
            
        if backup_path and backup_path != "protocol://":
            
                #get the skinsettings
                newlist = getSkinSettings(filter)

                if not xbmcvfs.exists(backup_path) and not silent:
                    xbmcvfs.mkdir(backup_path)
                
                #create temp path
                temp_path = xbmc.translatePath('special://temp/skinbackup/').decode("utf-8")
                if xbmcvfs.exists(temp_path):
                    shutil.rmtree(temp_path)
                xbmcvfs.mkdir(temp_path)
                    
                #get skinshortcuts preferences
                skinshortcuts_path = temp_path + "skinshortcuts/"
                skinshortcuts_path_source = xbmc.translatePath('special://profile/addon_data/script.skinshortcuts/').decode("utf-8")
                logMsg(skinshortcuts_path_source)
                if xbmcvfs.exists(skinshortcuts_path_source) and (filterString==None or filterString.lower() == "skinshortcutsonly"):
                    if not xbmcvfs.exists(skinshortcuts_path):
                        xbmcvfs.mkdir(skinshortcuts_path)
                    dirs, files = xbmcvfs.listdir(skinshortcuts_path_source)
                    for file in files:
                        if ".xml" in file:
                            sourcefile = skinshortcuts_path_source + file
                            destfile = skinshortcuts_path + file
                            logMsg("source --> " + sourcefile)
                            logMsg("destination --> " + destfile)
                            xbmcvfs.copy(sourcefile,destfile)
                        if file == xbmc.getSkinDir() + ".properties":
                            sourcefile = skinshortcuts_path_source + file
                            destfile = skinshortcuts_path + file.replace(xbmc.getSkinDir(), "SKINPROPERTIES")
                            logMsg("source --> " + sourcefile)
                            logMsg("destination --> " + destfile)
                            xbmcvfs.copy(sourcefile,destfile)
                
                if not filterString.lower() == "skinshortcutsonly":
                    #save guisettings
                    text_file_path = os.path.join(temp_path, "guisettings.txt")
                    text_file = xbmcvfs.File(text_file_path, "w")
                    json.dump(newlist, text_file)
                    text_file.close()

                
                #zip the backup
                zip_temp = xbmc.translatePath('special://temp/' + backup_name).decode("utf-8")
                zip(temp_path,zip_temp)
                
                if silent:
                    zip_final = silent
                else:
                    zip_final = backup_path + backup_name + ".zip"
                
                #copy to final location
                xbmcvfs.copy(zip_temp + ".zip", zip_final)
                
                #cleanup temp
                shutil.rmtree(temp_path)
                xbmcvfs.delete(zip_temp + ".zip")
                
                if not silent:
                    xbmcgui.Dialog().ok(ADDON.getLocalizedString(32028), ADDON.getLocalizedString(32029))
    
    except Exception as e:
        if not silent:
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(32028), ADDON.getLocalizedString(32030))
        logMsg("ERROR while creating backup ! --> " + str(e), 0)
        if silent:
            logMsg("ERROR while creating silent backup ! --> Make sure you provide the FULL VFS path, for example special://skin/extras/mybackup.zip", 0)            
    finally:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
        
def restore(silent=None):

    if silent and not xbmcvfs.exists(silent):
        logMsg("ERROR while creating backup ! --> Path invalid. Make sure you provide the FULL path, for example special://skin/extras/mybackup.zip", 0)
        return
    
    try:
        zip_path = silent
        progressDialog = None
        if not zip_path:
            zip_path = get_browse_dialog(dlg_type=1,heading=ADDON.getLocalizedString(32031),mask=".zip")
        
        if zip_path and zip_path != "protocol://":
            logMsg("zip_path " + zip_path)
            
            if silent:
                xbmc.executebuiltin( "ActivateWindow(busydialog)" )
            else:
                progressDialog = xbmcgui.DialogProgress(ADDON.getLocalizedString(32032))
                progressDialog.create(ADDON.getLocalizedString(32032))
                progressDialog.update(0, "unpacking backup...")
            
            #create temp path
            temp_path = xbmc.translatePath('special://temp/skinbackup/').decode("utf-8")
            if xbmcvfs.exists(temp_path):
                shutil.rmtree(temp_path)
            xbmcvfs.mkdir(temp_path)
            
            #unzip to temp
            if "\\" in zip_path:
                delim = "\\"
            else:
                delim = "/"
            
            zip_temp = xbmc.translatePath('special://temp/' + zip_path.split(delim)[-1]).decode("utf-8")
            xbmcvfs.copy(zip_path,zip_temp)
            zfile = zipfile.ZipFile(zip_temp)
            zfile.extractall(temp_path)
            zfile.close()
            xbmcvfs.delete(zip_temp)
            
            #copy skinshortcuts preferences
            skinshortcuts_path_source = None
            if xbmcvfs.exists(temp_path + "skinshortcuts/"):
                
                skinshortcuts_path_source = temp_path + "skinshortcuts/"
                skinshortcuts_path_dest = xbmc.translatePath('special://profile/addon_data/script.skinshortcuts/').decode("utf-8")
                
                if xbmcvfs.exists(skinshortcuts_path_dest):
                    shutil.rmtree(skinshortcuts_path_dest)
                xbmcvfs.mkdir(skinshortcuts_path_dest)
            
                dirs, files = xbmcvfs.listdir(skinshortcuts_path_source)
                for file in files:
                    if ".xml" in file:
                        sourcefile = skinshortcuts_path_source + file
                        destfile = skinshortcuts_path_dest + file
                        logMsg("source --> " + sourcefile)
                        logMsg("destination --> " + destfile)
                        xbmcvfs.copy(sourcefile,destfile)    
                    elif file == "SKINPROPERTIES.properties":
                        sourcefile = skinshortcuts_path_source + file
                        destfile = skinshortcuts_path_dest + file.replace("SKINPROPERTIES",xbmc.getSkinDir())
                        logMsg("source --> " + sourcefile)
                        logMsg("destination --> " + destfile)
                        xbmcvfs.copy(sourcefile,destfile)
                        
            #read guisettings
            if xbmcvfs.exists(os.path.join(temp_path, "guisettings.txt")):
                text_file_path = os.path.join(temp_path, "guisettings.txt")
                f = open(text_file_path,"r")
                importstring = json.load(f)
                f.close()
            
                xbmc.sleep(200)
                for count, skinsetting in enumerate(importstring):
                
                    if progressDialog:
                        if progressDialog.iscanceled():
                            return
                        
                    #some legacy...
                    setting = skinsetting[1].replace("TITANSKIN.helix", "").replace("TITANSKIN.", "")
                    
                    if progressDialog:
                        progressDialog.update((count * 100) / len(importstring), ADDON.getLocalizedString(32033) + ' %s' % setting)

                    if skinsetting[0] == "string":
                        if skinsetting[2] is not "":
                            xbmc.executebuiltin("Skin.SetString(%s,%s)" % (setting, skinsetting[2]))
                        else:
                            xbmc.executebuiltin("Skin.Reset(%s)" % setting)
                    elif skinsetting[0] == "bool":
                        if skinsetting[2] == "true":
                            xbmc.executebuiltin("Skin.SetBool(%s)" % setting)
                        else:
                            xbmc.executebuiltin("Skin.Reset(%s)" % setting)
                    xbmc.sleep(30)
            
            #cleanup temp
            xbmc.sleep(500)
            shutil.rmtree(temp_path)
            if not silent:
                xbmcgui.Dialog().ok(ADDON.getLocalizedString(32032), ADDON.getLocalizedString(32034))
    
    except Exception as e:
        if not silent:
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(32032), ADDON.getLocalizedString(32035))
        logMsg("ERROR while restoring backup ! --> " + str(e), 0)
    finally:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )

def zip(src, dst):
    zf = zipfile.ZipFile("%s.zip" % (dst), "w", zipfile.ZIP_DEFLATED)
    abs_src = os.path.abspath(src)
    for dirname, subdirs, files in os.walk(src):
        for filename in files:
            absname = os.path.abspath(os.path.join(dirname, filename))
            arcname = absname[len(abs_src) + 1:]
            logMsg('zipping %s as %s' % (os.path.join(dirname, filename),
                                        arcname))
            zf.write(absname, arcname)
    zf.close()
       
def reset():
    yeslabel=xbmc.getLocalizedString(107)
    nolabel=xbmc.getLocalizedString(106)
    dialog = xbmcgui.Dialog()
    
    ret = dialog.yesno(heading=ADDON.getLocalizedString(32036), line1=ADDON.getLocalizedString(32037), nolabel=nolabel, yeslabel=yeslabel)
    if ret:
        xbmc.executebuiltin("RunScript(script.skinshortcuts,type=resetall&warning=false)")
        xbmc.sleep(250)
        xbmc.executebuiltin("Skin.ResetSettings")
        xbmc.sleep(250)
        xbmc.executebuiltin("ReloadSkin")
             
def save_to_file(content, filename, path=""):
    if path == "":
        text_file_path = get_browse_dialog() + filename + ".txt"
    else:
        if not xbmcvfs.exists(path):
            xbmcvfs.mkdir(path)
        text_file_path = os.path.join(path, filename + ".txt")
    logMsg("save to textfile: " + text_file_path)
    text_file = xbmcvfs.File(text_file_path, "w")
    json.dump(content, text_file)
    text_file.close()
    return True

def read_from_file(path=""):
    if path == "":
        path = get_browse_dialog(dlg_type=1)
    if xbmcvfs.exists(path):
        f = open(path)
        fc = json.load(f)
        logMsg("loaded textfile " + path)
        return fc
    else:
        return False
       
def get_browse_dialog(default="protocol://", heading="Browse", dlg_type=3, shares="files", mask="", use_thumbs=False, treat_as_folder=False):
    dialog = xbmcgui.Dialog()
    value = dialog.browse(dlg_type, heading, shares, mask, use_thumbs, treat_as_folder, default)
    return value