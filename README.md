# script.skin.helper.service
a helper service for Kodi skins

### Settings for the script
The script does not have it's own settings dialog. The script is controlled by the skinner through skin settings to allow the skinner to fully integrate the settings of this script within the skin settings of the skin.

Important settings:

| setting name 		| how to set 				| description |
|:---------------------- | :------------------------------------- | :----------- |
|EnableExtraFanart	| Skin.ToggleSetting(EnableExtraFanart)	| enables the extrafanart background scanner |
|StudioImagesCustompath | Skin.SetString(StudioImagesCustompath)| if you want the user (or yourself as skinner) be able to set a custom path to studio logos. If empty it will use the logos provided by the script (later to be replaced with the new image resource packs in Kodi 16)|

### Window Properties provided by the script
The script provides several window properties to provide additional info about your skin and media info.
The window properties can be called in your skin like this: $INFO[Window(Home).Property(propertyname)]

#### General window Properties
The window properties can be called in your skin like this: $INFO[Window(Home).Property(propertyname)]
```
Window(Home).Property(skinTitle)  --> your skin name including the version
Window(Home).Property(skinVersion) --> only the version of your skin
```

#### Video library window properties
Some additional window properties that can be used in the video library. 

| property 			| description |
|:-----------------------------	| :----------- |
|Window(Home).Property(ExtraFanArtPath) | will return the extrafanart path for the listitem, empty if none is found. This window property is only available when browsing the video library and when the following Skin Bool is true: EnableExtraFanart|
|Window(Home).Property(ListItemStudioLogo) | Will return the full image path of the studio logo for the current selected item in a list. |
|Window(Home).Property(Player.AddonName) | If you want to display the name of the addon in the player |
|Window(Home).Property(Duration) | The duration of the current listitem in hours, for example 1:20 |

#### Movie sets window properties
If the selected listitem in the videolibrary is a movie set, some additional window properties are provided:

| property 			| description |
| :----------------------------	| :----------- |
| Window(Home).Property(MovieSet.Title) | Title of the movie set |
| Window(Home).Property(MovieSet.Runtime) | Total runtime (in minutes) of the movie set |
| Window(Home).Property(MovieSet.Duration) | Total runtime (in hours) of the movie set |
| Window(Home).Property(MovieSet.Writer) | All writers of the movies in the set |
| Window(Home).Property(MovieSet.Director) | All directors of the movies in the set |
| Window(Home).Property(MovieSet.Genre) | All genres of the movies in the set |
| Window(Home).Property(MovieSet.Country) | All countries of the movies in the set |
| Window(Home).Property(MovieSet.Studio) | All studios of the movies in the set |
| Window(Home).Property(MovieSet.Years) | All years of the movies in the set |
| Window(Home).Property(MovieSet.Year) | Year of first movie - Year of last movie |
| Window(Home).Property(MovieSet.Plot) | All plots of the movies in the set |
| Window(Home).Property(MovieSet.ExtendedPlot) | Plots combined with movie title info |
| Window(Home).Property(MovieSet.Count) | Total movies in the set |
| Window(Home).Property(MovieSet.WatchedCount) | Total watched movies in the set |
| Window(Home).Property(MovieSet.UnWatchedCount) | Total unwatched movies in the set |
both ExtraFanArtPath and ListItemStudioLogo will also be provided (if available) for the movie set

#### Music library window properties
Some additional window properties that can be used in the music library. 

| property 			| description |
| :----------------------------	| :----------- |
| Window(Home).Property(ExtraFanArtPath) | will return the extrafanart path for the artist, empty if none is found. This window property is only available when the following Skin Bool is true: EnableExtraFanart|
| Window(Home).Property(bannerArt) | Will return the Artist's banner image for the current selected item in the list. |
| Window(Home).Property(logoArt) | Will return the Artist's logo image for the current selected item in the list. |
| Window(Home).Property(cdArt) | Will return the Album's cd art image for the current selected item in the list. |
| Window(Home).Property(songInfo) | Returns the album's description or if empty the artist info. Can be used at songlevel.  |

### Music library search
```
RunScript(script.skin.helper.service,action=musicsearch)
```
This command will open the default search window for the music library. Might come in handy if you want to create a shortcut to music search from outside the music library window.

### Video library search (extended)
```
RunScript(script.skin.helper.service,action=videosearch)
```
This command will open the special search window in the script. It has a onscreen keyboard to quickly search for movies, tvshows and episodes. You can customize the look and feel of this search dialog. To do that include the files script-skin_helper_service-CustomSearch.xml and script-skin_helper_service-CustomInfo.xml in your skin and skin it to your needs.

### Color Picker
```
RunScript(script.skin.helper.service,action=colorpicker,skinstringName=XXX,skinstringValue=XXX)
```
This command will open the color picker of the script. After the user selected a color, the color will be stored in the skin string. Required parameters:
- skinstringName: Skin String in which the color name will be stored (like blue or magenta)
- skinstringValue: Skin String in which the value of the color (ARGB) will be stored.
In your skin you can just use the skin string to color a control, example: <textcolor>$INFO[Skin.String(defaultLabelColor)]</textcolor>

If you want to customize the look and feel of the color picker window, make sure to include script-skin_helper_service-ColorPicker.xml in your skin and skin in to your needs.


### Views selector
This feature shows the user a select dialog with all the views that are available. This replaces the default "toggle" button in the MyXXNav.xml windows. Note that you must create a views.xml file in your skin's extras folder. The selection dialog is built from that views.xml file and auto checks the visibility conditions so a view will only be shown if it's suitable for the current media content.

*action to call the dialog:*
```
RunScript(script.skin.helper.service,action=setview)               
```
*example content of the views.xml file (to be placed in extras folder of your skin):*
```
<views>
    <view id="List" value="50" languageid="31443" type="all"/>
	  <view id="Thumbs details" value="512" languageid="31439" type="movies,setmovies,tvshows,musicvideos,seasons,sets,episodes,artists,albums,songs,tvchannels,tvrecordings,programs,pictures" />
	  <view id="Poster Shift" value="514" languageid="31441" type="movies,setmovies,tvshows,musicvideos,seasons,sets" />
</views>
```
id = the unlocalized version of the views name.
value = the skin view ID.
languageid = localized label ID.
type = the type of content the view is suitable for, use "all" to support all types. 

Supported types are currently: movies,setmovies,tvshows,musicvideos,seasons,sets,episodes,artists,albums,songs,tvchannels,tvrecordings,programs,pictures

### Youtube trailer search
Shows a dialog with all trailers found by the Youtube plugin, replace [MOVIETITLE] with the movie title (or info label in the skin). To be used for example in DialogVideoInfo.xml to let the user select a trailer instead of playing the default one.
```
RunScript(script.skin.helper.service,action=searchtrailer,title=[MOVIETITLE])             
```

### Enable views
This will present a selection dialog to the user to enable (or disable) views. It uses the views.xml file to display the available views (see above). When a view is disabled it will be hidden from the view selection dialog. Also, a Skin String will be set so you can check in your skin if the view has been diable (and not include it or set a visiblity condition).
The name of the Skin String that will be set by the script is: View.Disabled.[VIEWID] where viewId is the numerical ID of the view.
Example: <include condition="!Skin.HasSetting(View.Disabled.55)">View_55_BannerList</include>

*the command below can be launched from a button your skin settings window.
```
RunScript(script.skin.helper.service,action=enableviews)             
```


