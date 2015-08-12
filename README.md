# script.skin.helper.service
a helper service for Kodi skins


### Available window Properties
The window properties can be called in your skin like this: $INFO[Window(Home).(Property(propertyname)]


### Music library search
```
*RunScript(script.skin.helper.service,action=musicsearch)*
```
This command will open the search window for the music library. Might come in handy if you want to create a shortcut to music search from outside the music library window.

### View selector
This feature shows the user a select dialog with all the views that are available. This replaces the default "toggle" button in the MyXXNav.xml windows. Note that you must create a views.xml file in your skin's extras folder. The selection dialog is built from that views.xml file and auto checks the visibility conditions so a view will only be shown if it's suitable for the current media content.

*action to call the dialog:*
```
*RunScript(script.skin.helper.service,action=setview)*               
-> Opens the View selection dialog. To be used in MyXXXNav.xml windows instead of default view selection button.
```
*example content of the views.xml file (to be placed in extras folder of your skin):*
```
<views>
    <view id="List" value="50" languageid="31443" type="all"/>
	  <view id="Thumbs details" value="512" languageid="31439" type="movies,setmovies,tvshows,musicvideos,seasons,sets,episodes,artists,albums,songs,tvchannels,tvrecordings,programs,pictures" />
	  <view id="Poster Shift" value="514" languageid="31441" type="movies,setmovies,tvshows,musicvideos,seasons,sets" />
</views>
```
id = the unlocalized version of the views name
value = the skin view ID
languageid = localized label ID
type = the type of content the view is suitable for, use "all" to support all types. Supported types are currently: movies,setmovies,tvshows,musicvideos,seasons,sets,episodes,artists,albums,songs,tvchannels,tvrecordings,programs,pictures


```
*RunScript(script.skin.helper.service,action=searchtrailer,title=[MOVIETITLE])*             
--> Shows a dialog with all trailers found by the Youtube plugin, replace [MOVIETITLE] with the movie title (or info label in the skin)
```

```
*RunScript(script.skin.helper.service,action=setview)*               
-> Opens the View selection dialog. To be used in MyXXXNav.xml windows instead of default view selection button.
```


