import xbmc, xbmcplugin, xbmcgui
import sys

def ShowAlphabetListing():
    allLetters = []
    if xbmc.getInfoLabel("Container.NumItems"):
        for i in range(int(xbmc.getInfoLabel("Container.NumItems"))):
            allLetters.append(xbmc.getInfoLabel("Listitem(%s).SortLetter"%i).upper())
        
        startNumber = ""
        for number in ["2","3","4","5","6","7","8","9"]:
            if number in allLetters:
                startNumber = number
                break
        
        for letter in [startNumber,"A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]:
            if letter == startNumber:
                label = "#"
            else: label = letter
            li = xbmcgui.ListItem(label=label)
            if not letter in allLetters:
                path = "noop"
                li.setProperty("NotAvailable","true")
            else:
                path = "plugin://script.skin.helper.service/?action=alphabetletter&letter=%s" %letter
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), path, li)
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))
    
def JumpLetterInList(letter):
    if letter in ["A", "B", "C", "2"]:
        jumpcmd = "2"
    elif letter in ["D", "E", "F", "3"]:
        jumpcmd = "3"
    elif letter in ["G", "H", "I", "4"]:
        jumpcmd = "4"
    elif letter in ["J", "K", "L", "5"]:
        jumpcmd = "5"
    elif letter in ["M", "N", "O", "6"]:
        jumpcmd = "6"
    elif letter in ["P", "Q", "R", "S", "7"]:
        jumpcmd = "7"
    elif letter in ["T", "U", "V", "8"]:
        jumpcmd = "8"
    elif letter in ["W", "X", "Y", "Z", "9"]:
        jumpcmd = "9"
    else:
        return

    xbmc.executebuiltin("SetFocus(50)")
    for i in range(40):
        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Input.ExecuteAction", "params": { "action": "jumpsms%s" }, "id": 1 }' % (jumpcmd))
        xbmc.sleep(50)
        if xbmc.getInfoLabel("ListItem.Sortletter").upper() == letter:
            break

