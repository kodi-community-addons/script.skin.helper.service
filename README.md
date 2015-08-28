# script.skin.helper.service
a helper service for Kodi skins

This is the first version of this script, currently only available as beta on Git. Once tested by a few skinners I will submit it to the official Kodi repo.

If you run into any issues , have some feedback or feature requests, feel free to ask and please report bugs !

IMPORTANT NOTE:  To use all the fancy integration options with skinshortcuts please use the latest version from Git because we haven't submitted this to the repo yet. This latest version of skinshortcuts contains lot's of cool stuff:
- speed improvements (you should really notice that)
- new widget selection system (browse anywhere in the system)
- support for this skininfo script off course ;-)
- template building system: this is really cool; it will auto build your skin's xml code for you. Just a couple of lines of codes is what's needed to build your entire widgets, menus etc. Look at the documentation and examples, great stuff!

Latest version of skinshortcuts: https://github.com/BigNoid/script.skinshortcuts/archive/master.zip

BTW: The logo and fanart image (now still from titan skin because of lack of something else) will be updated once I have some fancy new images.

Thanks all for testing!

Regards,

Marcel

________________________________________________________________________________________________________

### Settings for the script
The script does not have it's own settings dialog. The script is controlled by the skinner through skin settings to allow the skinner to fully integrate the settings of this script within the skin settings of the skin.

Important settings:

| setting name 		| how to set 		| description                           |
|:-------------- | :--------------- | :---------------------------------------- |
|SkinHelper.EnableExtraFanart	| Skin.ToggleSetting(SkinHelper.EnableExtraFanart)	| enables the extrafanart background scanner |
|SkinHelper.CustomStudioImagesPath | Skin.SetString(SkinHelper.CustomStudioImagesPath,[PATH])| if you want the user (or yourself as skinner) be able to set the path to the studio logos. If empty it will try to locate the images (later to be replaced with the new image resource packs in Kodi 16)|
|SkinHelper.ShowInfoAtPlaybackStart	| Skin.SetNumeric(SkinHelper.ShowInfoAtPlaybackStart)	| Show OSD info panel at playback start for number of seconds (0 disables this) |
|SkinHelper.RandomFanartDelay	| Skin.SetNumeric(SkinHelper.RandomFanartDelay)	| Sets the time in seconds for the interval of the rotating backgrounds provided by the script (0 disables this) |
|CustomPicturesBackgroundPath	| Skin.SetPath(CustomPicturesBackgroundPath)	| Sets a custom path from which the global pictures background should be pulled from. (empty uses all picture sources) |
|SmartShortcuts.playlists | Skin.SetBool(SmartShortcuts.playlists) | Enable smart shortcuts for Kodi playlists |
|SmartShortcuts.favorites | Skin.SetBool(SmartShortcuts.favorites) | Enable smart shortcuts for Kodi favorites |
|SmartShortcuts.plex | Skin.SetBool(SmartShortcuts.plex) | Enable smart shortcuts for plexbmc addon |
|SmartShortcuts.emby | Skin.SetBool(SmartShortcuts.emby) | Enable smart shortcuts for emby addon |
|SmartShortcuts.netflix | Skin.SetBool(SmartShortcuts.netflix) | Enable smart shortcuts for netflixbmc addon |
________________________________________________________________________________________________________
________________________________________________________________________________________________________

### Window Properties provided by the script
The script provides several window properties to provide additional info about your skin and media info.
The window properties can be called in your skin like this: $INFO[Window(Home).Property(propertyname)]

________________________________________________________________________________________________________



#### General window Properties
| property 			| description |
|:-----------------------------	| :----------- |
|Window(Home).Property(SkinHelper.skinTitle) | your skin name including the version |
|Window(Home).Property(SkinHelper.skinVersion) | only the version of your skin |
|Window(Home).Property(SkinHelper.TotalAddons) | total number of all installed addons |
|Window(Home).Property(SkinHelper.TotalAudioAddons) | total number of installed Audio addons |
|Window(Home).Property(SkinHelper.TotalVideoAddons) | total number of installed Video addons |
|Window(Home).Property(SkinHelper.TotalProgramAddons) | total number of installed Program addons |
|Window(Home).Property(SkinHelper.TotalPicturesAddons) | total number of installed Picture addons |
|Window(Home).Property(SkinHelper.TotalFavourites) | total number of favourites |
|Window(Home).Property(SkinHelper.TotalTVChannels) | total number of TV channels in the PVR |
|Window(Home).Property(SkinHelper.TotalRadioChannels) | total number of Radio channels in the PVR |
________________________________________________________________________________________________________
#### Video library window properties
Some additional window properties that can be used in the video library. 

| property 			| description |
|:-----------------------------	| :----------- |
|Window(Home).Property(SkinHelper.ExtraFanArtPath) | will return the extrafanart path for the listitem (to be used with multiimage control), empty if none is found. This window property is only available when browsing the video library and when the following Skin Bool is true: SkinHelper.EnableExtraFanart|
|Window(Home).Property(SkinHelper.ExtraFanArt.X) | Get extrafanart image X, only available when extrafanart is enabled. Start counting from 0 |
|Window(Home).Property(SkinHelper.Player.AddonName) | If you want to display the name of the addon in the player |
|Window(Home).Property(SkinHelper.Player.AddonName) | If you want to display the name of the addon in the player |
| Window(Home).Property(SkinHelper.ListItemDuration) | Formatted duration hours:minutes of the current listitem total runtime |
| Window(Home).Property(SkinHelper.ListItemDuration.Hours) | Only the hours part of the current listitem duration |
| Window(Home).Property(SkinHelper.ListItemDuration.Minutes) | Only the minutes part of the current listitem duration |

________________________________________________________________________________________________________


________________________________________________________________________________________________________
#### Studio Logos
The script can provide you the full path of the studio logo found for the selected listitem.
It will do that by looking up all found studio images and do a smart compare to match the correct one.
If the listitem has multiple studios it will return the logo from the first studio found in the list thas has a logo.
This will prevent you from having to sort out that logic yourself in your skin.

The script handles this logic to locate the fanart:

1. custom path set by you in the skin: Skin.String(SkinHelper.CustomStudioImagesPath)

2. try to locate the images in skin\extras\flags\studios  (and flags\studioscolor for coloured images)

3. try to locate the images in the new image resource addons provided by the Kodi team


| property 			| description |
|:-----------------------------	| :----------- |
|Window(Home).Property(SkinHelper.ListItemStudioLogo) | Will return the full image path of the (default/white) studio logo for the current selected item in a list. |
|Window(Home).Property(SkinHelper.ListItemStudioLogoColor) | Will return the full image path of the coloured studio logo for the current selected item in a list. |
|Window(Home).Property(SkinHelper.ListItemStudio) | Will just return the first studio of the listitem if you want to locate the images yourself. |

Note: If you also want to have the Studio logo and Duration Properties for your homescreen widgets, you need to set a Window Property "SkinHelper.WidgetContainer" with the ID of your widget container:
For example in home.xml: <onload>SetProperty(SkinHelper.WidgetContainer,301)</onload>

#### Movie sets window properties
If the selected listitem in the videolibrary is a movie set, some additional window properties are provided:

| property 			| description |
| :----------------------------	| :----------- |
| Window(Home).Property(SkinHelper.MovieSet.Title) | All titles in the movie set, separated by [CR] |
| Window(Home).Property(SkinHelper.MovieSet.Runtime) | Total runtime (in minutes) of the movie set |
| Window(Home).Property(SkinHelper.MovieSet.Duration) | Formatted duration hours:minutes of the movieset total runtime |
| Window(Home).Property(SkinHelper.MovieSet.Duration.Hours) | Only the hours part of the formatted duration |
| Window(Home).Property(SkinHelper.MovieSet.Duration.Minutes) | Only the minutes part of the formatted duration |
| Window(Home).Property(SkinHelper.MovieSet.Writer) | All writers of the movies in the set |
| Window(Home).Property(SkinHelper.MovieSet.Director) | All directors of the movies in the set |
| Window(Home).Property(SkinHelper.MovieSet.Genre) | All genres of the movies in the set |
| Window(Home).Property(SkinHelper.MovieSet.Country) | All countries of the movies in the set |
| Window(Home).Property(SkinHelper.MovieSet.Studio) | All studios of the movies in the set |
| Window(Home).Property(SkinHelper.MovieSet.Years) | All years of the movies in the set |
| Window(Home).Property(SkinHelper.MovieSet.Year) | Year of first movie - Year of last movie |
| Window(Home).Property(SkinHelper.MovieSet.Plot) | All plots of the movies in the set |
| Window(Home).Property(SkinHelper.MovieSet.ExtendedPlot) | Plots combined with movie title info |
| Window(Home).Property(SkinHelper.MovieSet.Count) | Total movies in the set |
| Window(Home).Property(SkinHelper.MovieSet.WatchedCount) | Total watched movies in the set |
| Window(Home).Property(SkinHelper.MovieSet.UnWatchedCount) | Total unwatched movies in the set |
| Window(Home).Property(SkinHelper.ExtraFanArtPath) | Rotating fanart images from movies in the set |
| Window(Home).Property(SkinHelper.MovieSet.X.Title) | Title of Movie X in the set |
| Window(Home).Property(SkinHelper.MovieSet.X.Poster) | Poster image of Movie X in the set |
| Window(Home).Property(SkinHelper.MovieSet.X.FanArt) | FanArt image of Movie X in the set |
| Window(Home).Property(SkinHelper.MovieSet.X.Landscape) | Landscape image of Movie X in the set |
| Window(Home).Property(SkinHelper.MovieSet.X.Banner) | Banner image of Movie X in the set |
| Window(Home).Property(SkinHelper.MovieSet.X.DiscArt) | DiscArt image of Movie X in the set |
| Window(Home).Property(SkinHelper.MovieSet.X.ClearLogo) | Clearlogo image of Movie X in the set |
| Window(Home).Property(SkinHelper.MovieSet.X.ClearArt) | ClearArt image of Movie X in the set |

For the individual items (MovieSet.X) replace X with the number of the movie in the set. Start counting at 0 and movies are ordered by year.
The ListItemStudioLogo and ListItemDuration properties will also be provided (if available) for the movie set.

________________________________________________________________________________________________________



#### Music library window properties
Some additional window properties that can be used in the music library. 

| property 			| description |
| :----------------------------	| :----------- |
| Window(Home).Property(SkinHelper.ExtraFanArtPath) | will return the extrafanart path for the artist, empty if none is found. This window property is only available when the following Skin Bool is true: SkinHelper.EnableExtraFanart|
| Window(Home).Property(SkinHelper.Music.BannerArt) | Will return the Artist's banner image for the current selected item in the list. |
| Window(Home).Property(SkinHelper.Music.LogoArt) | Will return the Artist's logo image for the current selected item in the list. |
| Window(Home).Property(SkinHelper.Music.DiscArt) | Will return the Album's cd art image for the current selected item in the list. |
| Window(Home).Property(SkinHelper.Music.Info) | Returns the album's description or if empty the artist info. Can be used at both album- and songlevel.  |
| Window(Home).Property(SkinHelper.Music.TrackList) | Returns the all tracks for the selected album or artist, separated by [CR] in the format tracknumber - title  |


________________________________________________________________________________________________________



#### Backgrounds provided by the script
The script has a background scanner to provide some rotating fanart backgrounds which can be used in your skin as backgrounds. The backgrounds are available in window properties.

Note: the default interval for the backgrounds is set at 30 seconds. If you want to change this interval you can set a Skin String "SkinHelper.RandomFanartDelay" with the number of seconds as value.

| property 			| description |
| :----------------------------	| :----------- |
| Window(Home).Property(SkinHelper.AllMoviesBackground) | Random fanart of movies in video database|
| Window(Home).Property(SkinHelper.AllTvShowsBackground) | Random fanart of TV shows in video database|
| Window(Home).Property(SkinHelper.AllMusicVideosBackground) | Random fanart of music videos in video database|
| Window(Home).Property(SkinHelper.AllMusicBackground) | Random fanart of music artists in database|
| Window(Home).Property(SkinHelper.GlobalFanartBackground) | Random fanart of all media types|
| Window(Home).Property(SkinHelper.InProgressMoviesBackground) | Random fanart of in progress movies|
| Window(Home).Property(SkinHelper.RecentMoviesBackground) | Random fanart of in recently added movies|
| Window(Home).Property(SkinHelper.UnwatchedMoviesBackground) | Random fanart of unwatched movies|
| Window(Home).Property(SkinHelper.InProgressShowsBackground) | Random fanart of in progress tv shows|
| Window(Home).Property(SkinHelper.RecentEpisodesBackground) | Random fanart of recently added episodes|
| Window(Home).Property(SkinHelper.PicturesBackground) | Random pictures from all picture sources. By default this pulls images from all picture sources the user has configured. It is however possible to provide a custom source from which the images should be pulled from by setting Skin String: SkinHelper.CustomPicturesBackgroundPath|
________________________________________________________________________________________________________
________________________________________________________________________________________________________

### Tools and actions provided by the script
The script provides several tools and actions which you can use in your skin.

________________________________________________________________________________________________________

#### Music library search
```
RunScript(script.skin.helper.service,action=musicsearch)
```
This command will open the default search window for the music library. Might come in handy if you want to create a shortcut to music search from outside the music library window.

________________________________________________________________________________________________________



#### Video library search (extended)
```
RunScript(script.skin.helper.service,action=videosearch)
```
This command will open the special search window in the script. It has a onscreen keyboard to quickly search for movies, tvshows and episodes. You can customize the look and feel of this search dialog. To do that include the files script-skin_helper_service-CustomSearch.xml and script-skin_helper_service-CustomInfo.xml in your skin and skin it to your needs.

________________________________________________________________________________________________________



#### Color Picker
```
RunScript(script.skin.helper.service,action=colorpicker,skinstring=XXX)
```
This command will open the color picker of the script. After the user selected a color, the color will be stored in the skin string. Required parameters:
- skinstring: Skin String inwhich the value of the color (ARGB) will be stored.

In your skin you can just use the skin string to color a control, example: <textcolor>$INFO[Skin.String(defaultLabelColor)]</textcolor>

Note: If you want to display the name of the selected color, add a prefix .name to your skin string.
For example: <label>Default color for labels: $INFO[Skin.String(defaultLabelColor.name)]</label>

If you want to customize the look and feel of the color picker window, make sure to include script-skin_helper_service-ColorPicker.xml in your skin and skin in to your needs.

TIP: By default the colorpicker will provide a list of available colors.
If you want to provide that list yourself, create a file "colors.xml" in skin\extras\colors\colors.xml
See the default colors file in the script's location, subfolder resources\colors





________________________________________________________________________________________________________



#### Auto thumb generator
The script has a feature to automatically retrieve a thumb/image for a specific search query
It will first query TMDB, if that fails Google images and if that fails it will try youtube to get a thumb.
This might come in handy if you want to provide a thumb for the currently selected show in the PVR channel list for example.
Note 1: The script will build a cache in the background to prevent too many queries to google/youtube.
Note 2: There is no way to guarantee which aspect ratio the retrieved image has, so use scale or keep as aspect ratio to display the images.

How to use ?
You must use a multiimage control for this thing to work, as that accepts a plugin path as the texturepath.
Use the path property to define the searchquery, the more info you supply, the more accurate the resulting image will be.
Note that if you want the TMDB poster to be returned the show or movie title has to be exact.
For example to display a thumb of the selected TV program in MyPVRChannels.xml:


```xml
<control type="multiimage">
	<width>300</width>
	<height>300</height>
	<imagepath>plugin://script.skin.helper.service/?action=getthumb&path=$INFO[ListItem.Title] $INFO[ListItem.ChannelName]</imagepath>
	<aspectratio>keep</aspectratio>
</control>
```

When the script is called it will also fill a window property with the image: SkinHelper.ListItemThumb

________________________________________________________________________________________________________




#### Youtube search
Shows a selectdialog with all searchresults found by the Youtube plugin, for example to search for trailers in DialogVideoInfo.xml.
The benefit of that is that user stays in the same window and is not moved away from the library to the youtube plugin.
You can supply a searchphrase to the script and optionally provide a label for the header in the DialogSelect.

RunScript(script.skin.helper.service,action=searchyoutube,title=[SEARCHPHRASE],header=[HEADER FOR THE DIALOGSELECT]

TIP: The results of the script displayed in DialogSelect.xml will have the label2 of the ListItem set to the description.

example 1: Search for trailers in DialogVideoInfo.xml
```xml
<control type="button">
	<label>YouTube $LOCALIZE[20410]</label>
	<onclick condition="System.HasAddon(plugin.video.youtube)">RunScript(script.skin.helper.service,action=searchyoutube,title=$INFO[ListItem.Title] Trailer,header=Search YouTube Trailers)</onclick>
	<onclick condition="!System.HasAddon(plugin.video.youtube)">ActivateWindow(Videos,plugin://plugin.video.youtube)</onclick>
	<visible>Container.Content(movies)</visible>
</control>
           
```
example 2: Search for artist videos in DialogAlbumInfo.xml
```
RunScript(script.skin.helper.service,action=searchyoutube,title=$INFO[ListItem.Artist], header=Videos for $INFO[ListItem.Artist])             
```


#### Busy spinner selector
Allows the user to select a busy spinner from some predefined ones in your skin. It supports both multiimage (folder with images) and single image (.gif) spinners. The user can provide his own texture(s) or select from predefined spinners in the skin.

```
RunScript(script.skin.helper.service,action=busytexture)             
```
The script fills this Skin Strings after selection: 
SkinHelper.SpinnerTexture --> the name of the selected busy texture
SkinHelper.SpinnerTexturePath --> The full path of the selected busy texture

#####To provide busy spinners with your skin:
- Make sure to create a directory "busy_spinners" in your skin's extras folder.
- Inside that directory you can put subdirectories for multimage spinners or just gif files in the root.

#####To use the busy texture
Make sure that you use a multiimage control in DialogBusy.xml. Example code:
```xml
<control type="multiimage">
	<width>150</width>
	<height>150</height>
	<aspectratio>keep</aspectratio>
	<imagepath>$INFO[Skin.String(SkinHelper.SpinnerTexturePath)]</imagepath>
	<timeperimage>100</timeperimage>
	<colordiffuse>$INFO[Skin.String(SpinnerTextureColor)]</colordiffuse>
	<fadetime>0</fadetime>
	<visible>!Skin.String(SkinHelper.SpinnerTexturePath,None)</visible>
</control>
```




________________________________________________________________________________________________________



#### Views selector
```
RunScript(script.skin.helper.service,action=setview)               
```
This feature shows the user a select dialog with all the views that are available. This replaces the default "toggle" button in the MyXXNav.xml windows. Note that you must create a views.xml file in your skin's extras folder. The selection dialog is built from that views.xml file and auto checks the visibility conditions so a view will only be shown if it's suitable for the current media content.

*example content of the views.xml file (to be placed in extras folder of your skin):*
```xml
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

Note: If you want a thumbnail of the view displayed in the select dialog, you need to create some small screenshots of your views and place them in your skin's extras folder:
- in your skin\extras folder, create a subfolder "viewthumbs"
- inside that viewthumbs folder save a .JPG file (screenshot) for all your views. Save them as [VIEWID].jpg where [VIEWID] is the numeric ID of the view.

________________________________________________________________________________________________________



#### Enable views
```
RunScript(script.skin.helper.service,action=enableviews)             
```
This will present a selection dialog to the user to enable (or disable) views. It uses the views.xml file to display the available views (see above). When a view is disabled it will be hidden from the view selection dialog. Also, a Skin String will be set so you can check in your skin if the view has been disabled (and not include it or set a visiblity condition).
The name of the Skin String that will be set by the script is: SkinHelper.View.Disabled.[VIEWID] where [VIEWID] is the numerical ID of the view.

Example: <include condition="!Skin.HasSetting(SkinHelper.View.Disabled.55)">View_55_BannerList</include>

________________________________________________________________________________________________________



#### Set Forced views
```
RunScript(script.skin.helper.service,action=setforcedview,contenttype=[TYPE])             
```
The script can help you to set a forced view for a specific contenttype in your skin. For example if the user wants to set the list view for all tvshow content etc. For [TYPE] you must fill in one of the content types, see above at "Views selector". When a button is pressed with the above command, a select dialog appears and the user can choose on of the available views. Disabled views and views that aren't suitable for the specified type are hidden from the list.
When the user made a choice from the list a Skin String will be filled by the script: SkinHelper.ForcedViews.[TYPE]
The value of that skin string is the numeric ID of the selected view.

Note: It is recommended that you create a Skin toggle to enable/disable the forced views feature.

Note 2: When the user select another view in the normal viewselector, the forcedview setting will also be set to the newly chosen view.



##### How to use the forced views feature in your skin?

Example code to use in your skin settings:

```xml
<control type="radiobutton" id="6009">
	<label>Enable forced views</label>
	<onclick>Skin.ToggleSetting(SkinHelper.ForcedViews.Enabled)</onclick>
	<selected>Skin.HasSetting(SkinHelper.ForcedViews.Enabled)</selected>
</control>
<control type="button" id="6010">
	<onclick>RunScript(script.skin.helper.service,action=setforcedview,contenttype=movies)</onclick>
	<visible>Skin.HasSetting(SkinHelper.ForcedViews.Enabled)</visible>
	<label>Forced view for movies: $INFO[Skin.String(SkinHelper.ForcedViews.movies)]</label>
</control>
<control type="button" id="6011">
	<onclick>RunScript(script.skin.helper.service,action=setforcedview,contenttype=tvshows)</onclick>
	<visible>Skin.HasSetting(SkinHelper.ForcedViews.Enabled)</visible>
	<label>Forced view for tv shows:  $INFO[Skin.String(SkinHelper.ForcedViews.tvshows)]</label>
</control>
<control type="button" id="6012">
	<onclick>RunScript(script.skin.helper.service,action=setforcedview,contenttype=seasons)</onclick>
	<visible>Skin.HasSetting(SkinHelper.ForcedViews.Enabled)</visible>
	<label>Forced view for seasons:  $INFO[Skin.String(SkinHelper.ForcedViews.seasons)]</label>
</control>
<control type="button" id="6013">
	<onclick>RunScript(script.skin.helper.service,action=setforcedview,contenttype=episodes)</onclick>
	<visible>Skin.HasSetting(SkinHelper.ForcedViews.Enabled)</visible>
	<label>Forced view for episodes: $INFO[Skin.String(SkinHelper.ForcedViews.episodes)]</label>
	<font>Reg28</font>
</control>
<control type="button" id="6014">
	<onclick>RunScript(script.skin.helper.service,action=setforcedview,contenttype=sets)</onclick>
	<visible>Skin.HasSetting(SkinHelper.ForcedViews.Enabled)</visible>
	<label>Forced view for movie sets: $INFO[Skin.String(SkinHelper.ForcedViews.sets)]</label>
</control>
<control type="button" id="6015">
	<onclick>RunScript(script.skin.helper.service,action=setforcedview,contenttype=setmovies)</onclick>
	<visible>Skin.HasSetting(SkinHelper.ForcedViews.Enabled)</visible>
	<label>Forced view for movies inside set: $INFO[Skin.String(SkinHelper.ForcedViews.setmovies)]</label>
</control>
```

Example code to use for your views visibility conditions:
```xml
<control type="panel" id="51">
	<visible>!Skin.HasSetting(SkinHelper.ForcedViews.Enabled) | 
	[Container.Content(movies) + Skin.String(SkinHelper.ForcedViews.movies,None)] | 
	[Container.Content(tvshows) + Skin.String(SkinHelper.ForcedViews.tvshows,None)] | 
	[Container.Content(seasons) + Skin.String(SkinHelper.ForcedViews.seasons,None)] | 
	[Container.Content(episodes) + Skin.String(SkinHelper.ForcedViews.episodes,None)] | 
	[Container.Content(movies) + Skin.String(SkinHelper.ForcedViews.movies,None)] | 
	[Container.Content(tvshows) + Skin.String(SkinHelper.ForcedViews.tvshows,None)] | 
	[Container.Content(seasons) + Skin.String(SkinHelper.ForcedViews.seasons,None)] | 
	[Container.Content(episodes) + Skin.String(SkinHelper.ForcedViews.episodes,None)] | 
	[[Container.Content(sets) | StringCompare(Container.Folderpath,videodb://movies/sets/)] + Skin.String(SkinHelper.ForcedViews.sets,51)] | 
	[Container.Content(movies) + Skin.String(SkinHelper.ForcedViews.movies,51) + !substring(Container.FolderPath,videodb://movies/sets/,left)] | 
	[Container.Content(movies) + Skin.String(SkinHelper.ForcedViews.setmovies,51) + substring(Container.FolderPath,setid=)] | 
	[Container.Content(tvshows) + Skin.String(SkinHelper.ForcedViews.tvshows,51)] | 
	[Container.Content(seasons) + Skin.String(SkinHelper.ForcedViews.seasons,51)] | 
	[Container.Content(episodes) + Skin.String(SkinHelper.ForcedViews.episodes,51)] | 
	[!Container.Content(movies) + !Container.Content(tvshows) + !Container.Content(seasons) + !Container.Content(episodes) + !Container.Content(sets)]
	</visible>
</control>
```
Note: The forced view code has to be added to all view controls in order to work properly.


________________________________________________________________________________________________________
________________________________________________________________________________________________________

### Color themes feature
The script comes with a color theme feature. Basically it's just a simplified version of the skin backup/restore feature but it only backs up the colorsettings. Color Themes has the following features:

- Present a list of skin provided color themes including screenshots.
- Let's the user save his custom settings to a color theme.
- Let's the user export his custom color theme to file.
- Let's the user import a custom color theme from file.

#####To present the dialog with all available color themes:
```
RunScript(script.skin.helper.service,action=colorthemes)             
```


#####Save the user's current customizations to a custom colortheme:
```
RunScript(script.skin.helper.service,action=createcolortheme)             
```

#####Import a custom colortheme from file:
```
RunScript(script.skin.helper.service,action=restorecolortheme)             
```

#####Provide color themes with your skin
It is possible to deliver skin provided color themes. Those colorthemes should be stored in the skin's extras\skinthemes folder.
If you want to create one or more skinprovided color themes (for example the defaults):
- Create a folder "skinthemes" in your skin's "extras" folder. 
- Make all color modifications in your skin to represent the colortheme
- Hit the button to save your colortheme (createcolortheme command)
- Name it and select the correct screenshot
- On the filesystem navigate to Kodi userdata\addon_data\[YOURSKIN]\themes
- Copy both the themename.theme and the themename.jpg file to your above created skinthemes directory
- Do this action for every theme you want to include in your skin.
- It is possible to change the description of the theme, just open the .themes file in a texteditor. You can change both the THEMENAME and the DESCRIPTION values to your needs.

#####What settings are stored in the theme file ?
All Skin Settings settings that contain one of these words: color, opacity, texture.
Also the skin's theme will be saved (if any). So, to make sure the skin themes feature works properly you must be sure that all of your color-settings contain the word color. If any more words should be supported, please ask.



________________________________________________________________________________________________________
________________________________________________________________________________________________________

### Skin backup feature
The script comes with a backup/restore feature. It supports backup of ALL skin settings including skin shortcuts (when script.skinshortcuts is also used). 

- Backup all settings to file
- Restore all settings from file
- Reset the skin to default settings (wipe all settings)

#####To backup the skin settings (including preferences for skinshortcuts):
```
RunScript(script.skin.helper.service,action=backup)             
```

It is possible to apply a filter to the backup. In that case only skin settings containing a specific phrase will be back upped.
Can be usefull if you want to use the backup function for something else in your skin.
To use the filter you have to add the filter= argument and supply one or more phrases (separated by |)
For example:
RunScript(script.skin.helper.service,action=backup,filter=color|view|font)    
The filter is not case sensitive

#####To restore the skin settings:
```
RunScript(script.skin.helper.service,action=restore)             
```

#####To reset the skin to defaults:
```
RunScript(script.skin.helper.service,action=reset)             
```


________________________________________________________________________________________________________
________________________________________________________________________________________________________

### Dynamic content provider
The script also has a plugin entrypoint to provide some dynamic content that can be used for example in widgets.
use the parameter [LIMIT] to define the number of items to show in the list. defaults to 25 if the parameter is not supplied.

```
Important Note: If you want to use these commands in the skinshortcuts overrides.xml,
you have to replace & with &amp;
```

#####Next Episodes
```
plugin://script.skin.helper.service/?action=nextepisodes&limit=[LIMIT]&reload=$INFO[Window(Home).Property(widgetreload)]
```
Provides a list of the nextup episodes. This can be the first episode in progress from a tv show or the next unwatched from a in progress show.
Note: the reload parameter is needed to auto refresh the widget when the content has changed.

________________________________________________________________________________________________________

#####Recommended Movies
```
plugin://script.skin.helper.service/?action=recommendedmovies&limit=[LIMIT]&reload=$INFO[Window(Home).Property(widgetreload)]
```
Provides a list of the in progress movies AND recommended movies based on rating.
Note: the reload parameter is needed to auto refresh the widget when the content has changed.

________________________________________________________________________________________________________

#####Recommended Media
```
plugin://script.skin.helper.service/?action=recommendedmedia&limit=[LIMIT]
```
Provides a list of recommended media (movies, tv shows, music)
Note: You can optionally provide the reload= parameter if you want to refresh the widget on library changes.


________________________________________________________________________________________________________

#####Recent Media
```
plugin://script.skin.helper.service/?action=recentmedia&limit=[LIMIT]
```
Provides a list of recently added media (movies, tv shows, music, tv recordings, musicvideos)
Note: You can optionally provide the reload= parameter if you want to refresh the widget on library changes.


________________________________________________________________________________________________________

#####Similar Movies (because you watched...)
```
plugin://script.skin.helper.service/?action=similarmovies&limit=[LIMIT]
```
This will provide a list with movies that are similar to a random watched movie from the library.
TIP: The listitem provided by this list will have a property "originaltitle" which contains the movie from which this list is generated. That way you can create a "Because you watched $INFO[Container.ListItem.Property(originaltitle)]" label....
Note: You can optionally provide the reload= parameter if you want to refresh the widget on library changes. If you want to refresh the widget on other circumstances just provide any changing info with the reload parameter, such as the window title or some window Property which you change on X interval.


________________________________________________________________________________________________________

#####In progress Media
```
plugin://script.skin.helper.service/?action=inprogressmedia&limit=[LIMIT]&reload=$INFO[Window(Home).Property(widgetreload)]
```
Provides a list of all in progress media (movies, tv shows, music, musicvideos)
Note: the reload parameter is needed to auto refresh the widget when the content has changed.


________________________________________________________________________________________________________

#####In progress and Recommended Media
```
plugin://script.skin.helper.service/?action=inprogressandrecommendedmedia&limit=[LIMIT]&reload=$INFO[Window(Home).Property(widgetreload)]
```
This combines in progress media and recommended media, usefull to prevent an empty widget when no items are in progress.
Note: the reload parameter is needed to auto refresh the widget when the content has changed.

________________________________________________________________________________________________________

#####Favourite Media
```
plugin://script.skin.helper.service/?action=favouritemedia&limit=[LIMIT]&reload=[YOURCUSTOMPROPERTY]
```
Provides a list of all media items that are added as favourite (movies, tv shows, songs, musicvideos)
Note: If you want the widget to refresh when the favourites have changed It's recommended to use the reload= parameter in combination with a window property. For example set a window prop in the onunload event of home.xml and clear it in the onload event of home.xml or the other way around.

________________________________________________________________________________________________________

#####My TV Shows Airing today
```
plugin://script.skin.helper.service/?action=nextairedtvshows&reload=[YOURCUSTOMPROPERTY]
```
Provides a list of the shows from the library that are airing today - requires script.tv.show.next.aired
Note: The widget will only be retrieved once a day. If you wan to refresh it more often it's recommended to use the reload= parameter in combination with a window property. For example set a window prop in the onunload event of home.xml and clear it in the onload event of home.xml or the other way around.

________________________________________________________________________________________________________

#####Favourites
```
plugin://script.skin.helper.service/?action=favourites&limit=[LIMIT]&reload=[YOURCUSTOMPROPERTY]
```
Provides the Kodi favourites as list content.
Note: If you want the widget to refresh when the favourites have changed It's recommended to use the reload= parameter in combination with a window property. For example set a window prop in the onunload event of home.xml and clear it in the onload event of home.xml or the other way around.


________________________________________________________________________________________________________

#####Cast Details
```
plugin://script.skin.helper.service/?action=getcast&movie=[MOVIENAME OR DBID]
plugin://script.skin.helper.service/?action=getcast&tvshow=[TVSHOW NAME OR DBID]
plugin://script.skin.helper.service/?action=getcast&movieset=[MOVIESET NAME OR DBID]
```
Provides the Cast list for the specified media type as a listing.
Label = Name of the actor
Label2 = Role
Icon = Thumb of the actor

You can use the name of the Movie or the DBID to perform the lookup.


________________________________________________________________________________________________________
________________________________________________________________________________________________________

### Smart shortcuts feature
This feature is introduced to be able to provide quick-access shortcuts to specific sections of Kodi, such as user created playlists and favourites and entry points of some 3th party addons such as Emby and Plex. What it does is provide some Window properties about the shortcut. It is most convenient used with the skin shortcuts script but can offcourse be used in any part of your skin. The most important behaviour of the smart shortcuts feature is that is pulls images from the library path so you can have content based backgrounds.


________________________________________________________________________________________________________

##### Smart shortcuts for playlists
Will only be available if this Skin Bool is true --> SmartShortcuts.playlists

| property 			| description |
| :----------------------------	| :----------- |
| Window(Home).Property(playlist.X.label) | Title of the playlist|
| Window(Home).Property(playlist.X.action) | Path of the playlist|
| Window(Home).Property(playlist.X.content) | Contentpath (without activatewindow) of the playlist, to display it's content in widgets.|
| Window(Home).Property(playlist.X.image) | Rotating fanart of the playlist|
--> replace X with the item count, starting at 0.


________________________________________________________________________________________________________


##### Smart shortcuts for Kodi Favourites
Will only be available if this Skin Bool is true --> SmartShortcuts.favorites

Note that only favourites will be processed that actually contain video/audio content.

| property 			| description |
| :----------------------------	| :----------- |
| Window(Home).Property(favorite.X.label) | Title of the favourite|
| Window(Home).Property(favorite.X.action) | Path of the favourite|
| Window(Home).Property(favorite.X.content) | Contentpath (without activatewindow) of the favourite, to display it's content in widgets.|
| Window(Home).Property(favorite.X.image) | Rotating fanart of the favourite|
--> replace X with the item count, starting at 0.


________________________________________________________________________________________________________



##### Smart shortcuts for Plex addon (plugin.video.plexbmc)
Will only be available if this Skin Bool is true --> SmartShortcuts.plex

Note that the plexbmc addon must be present on the system for this to function.

| property 			| description |
| :----------------------------	| :----------- |
| Window(Home).Property(plexbmc.X.title) | Title of the Plex collection|
| Window(Home).Property(plexbmc.X.path) | Path of the Plex collection|
| Window(Home).Property(plexbmc.X.content) | Contentpath (without activatewindow) of the Plex collection, to display it's content in widgets.|
| Window(Home).Property(plexbmc.X.background) | Rotating fanart of the Plex collection|
| Window(Home).Property(plexbmc.X.type) | Type of the Plex collection (e.g. movies, tvshows)|
| Window(Home).Property(plexbmc.X.recent) | Path to the recently added items node of the Plex collection|
| Window(Home).Property(plexbmc.X.recent.content) | Contentpath to the recently added items node of the Plex collection (for widgets)|
| Window(Home).Property(plexbmc.X.recent.background) | Rotating fanart of the recently added items node|
| Window(Home).Property(plexbmc.X.ondeck) | Path to the in progress items node of the Plex collection|
| Window(Home).Property(plexbmc.X.ondeck.content) | Contentpath to the in progress items node of the Plex collection (for widgets)|
| Window(Home).Property(plexbmc.X.ondeck.background) | Rotating fanart of the in progress items node|
| Window(Home).Property(plexbmc.X.unwatched) | Path to the in unwatched items node of the Plex collection|
| Window(Home).Property(plexbmc.X.unwatched.content) | Contentpath to the unwatched items node of the Plex collection (for widgets)|
| Window(Home).Property(plexbmc.X.unwatched.background) | Rotating fanart of the unwatched items node|
| |
| Window(Home).Property(plexbmc.channels.title) | Title of the Plex Channels collection|
| Window(Home).Property(plexbmc.channels.path) | Path to the Plex Channels|
| Window(Home).Property(plexbmc.channels.content) | Contentpath to the Plex Channels (for widgets)|
| Window(Home).Property(plexbmc.channels.background) | Rotating fanart of the Plex Channels|
| |
| Window(Home).Property(plexfanartbg) | A global fanart background from plex sources|
--> replace X with the item count, starting at 0.



________________________________________________________________________________________________________



##### Smart shortcuts for Emby addon (plugin.video.emby)
Will only be available if this Skin Bool is true --> SmartShortcuts.emby

Note that the Emby addon must be present on the system for this to function.

| property 			| description |
| :----------------------------	| :----------- |
| Window(Home).Property(emby.nodes.X.title) | Title of the Emby collection|
| Window(Home).Property(emby.nodes.X.path) | Path of the Emby collection|
| Window(Home).Property(emby.nodes.X.content) | Contentpath of the Emby collection (for widgets)|
| Window(Home).Property(emby.nodes.X.image) | Rotating Fanart of the Emby collection|
| Window(Home).Property(emby.nodes.X.type) | Type of the Emby collection (e.g. movies, tvshows)|
| |
| Window(Home).Property(emby.nodes.X.recent.title) | Title of the recently added node for the Emby collection|
| Window(Home).Property(emby.nodes.X.recent.path) | Path of the recently added node for the Emby collection|
| Window(Home).Property(emby.nodes.X.recent.content) | Contentpath of the recently added node for the Emby collection|
| Window(Home).Property(emby.nodes.X.recent.image) | Rotating Fanart of the recently added node for the Emby collection|
| |
| Window(Home).Property(emby.nodes.X.unwatched.title) | Title of the unwatched node for the Emby collection|
| Window(Home).Property(emby.nodes.X.unwatched.path) | Path of the unwatched node for the Emby collection|
| Window(Home).Property(emby.nodes.X.unwatched.content) | Contentpath of the unwatched node for the Emby collection|
| Window(Home).Property(emby.nodes.X.unwatched.image) | Rotating Fanart of the unwatched node for the Emby collection|
| |
| Window(Home).Property(emby.nodes.X.inprogress.title) | Title of the inprogress node for the Emby collection|
| Window(Home).Property(emby.nodes.X.inprogress.path) | Path of the inprogress node for the Emby collection|
| Window(Home).Property(emby.nodes.X.inprogress.content) | Contentpath of the inprogress node for the Emby collection|
| Window(Home).Property(emby.nodes.X.inprogress.image) | Rotating Fanart of the inprogress node for the Emby collection|
| |
| Window(Home).Property(emby.nodes.X.recentepisodes.title) | Title of the recent episodes node for the Emby collection|
| Window(Home).Property(emby.nodes.X.recentepisodes.path) | Path of the recent episodes node for the Emby collection|
| Window(Home).Property(emby.nodes.X.recentepisodes.content) | Contentpath of the recent episodes node for the Emby collection|
| Window(Home).Property(emby.nodes.X.recentepisodes.image) | Rotating Fanart of the recent episodes node for the Emby collection|
| |
| Window(Home).Property(emby.nodes.X.nextepisodes.title) | Title of the next episodes node for the Emby collection|
| Window(Home).Property(emby.nodes.X.nextepisodes.path) | Path of the next episodes node for the Emby collection|
| Window(Home).Property(emby.nodes.X.nextepisodes.content) | Contentpath of the next episodes node for the Emby collection|
| Window(Home).Property(emby.nodes.X.nextepisodes.image) | Rotating Fanart of the next episodes node for the Emby collection|
| |
| Window(Home).Property(emby.nodes.X.inprogressepisodes.title) | Title of the in progress episodes node for the Emby collection|
| Window(Home).Property(emby.nodes.X.inprogressepisodes.path) | Path of the in progress episodes node for the Emby collection|
| Window(Home).Property(emby.nodes.X.inprogressepisodes.content) | Contentpath of the in progress episodes node for the Emby collection|
| Window(Home).Property(emby.nodes.X.inprogressepisodes.image) | Rotating Fanart of the in progress episodes node for the Emby collection|



________________________________________________________________________________________________________



##### Smart shortcuts for Netflix addon (plugin.video.netflixbmc)
Will only be available if this Skin Bool is true --> SmartShortcuts.netflix

Note that the Netflixbmc addon must be present on the system for this to function.

| property 			| description |
| :----------------------------	| :----------- |
| Window(Home).Property(netflix.generic.title) | Title of the main Netflixbmc entry|
| Window(Home).Property(netflix.generic.path) | Path of the main Netflixbmc entry|
| Window(Home).Property(netflix.generic.content) | Contentpath of the main Netflixbmc entry (for widgets)|
| Window(Home).Property(netflix.generic.image) | Rotating Fanart from netflixbmc addon|
| |
| Window(Home).Property(netflix.generic.mylist.title) | Title of the Netflixbmc My List entry|
| Window(Home).Property(netflix.generic.mylist.path) | Path of the Netflixbmc My List entry|
| Window(Home).Property(netflix.generic.mylist.content) | Contentpath of the Netflixbmc My List entry (for widgets)|
| Window(Home).Property(netflix.generic.mylist.image) | Rotating Fanart from Netflixbmc My List entry|
| |
| Window(Home).Property(netflix.generic.suggestions.title) | Title of the Netflixbmc Suggestions entry|
| Window(Home).Property(netflix.generic.suggestions.path) | Path of the Netflixbmc Suggestions entry|
| Window(Home).Property(netflix.generic.suggestions.content) | Contentpath of the Netflixbmc Suggestions entry (for widgets)|
| Window(Home).Property(netflix.generic.suggestions.image) | Rotating Fanart from Netflixbmc Suggestions entry|
| |
| Window(Home).Property(netflix.generic.inprogress.title) | Title of the Netflixbmc Continue Watching entry|
| Window(Home).Property(netflix.generic.inprogress.path) | Path of the Netflixbmc Continue Watching entry|
| Window(Home).Property(netflix.generic.inprogress.content) | Contentpath of the Netflixbmc Continue Watching entry (for widgets)|
| Window(Home).Property(netflix.generic.inprogress.image) | Rotating Fanart from Netflixbmc Continue Watching entry|
| |
| Window(Home).Property(netflix.generic.recent.title) | Title of the Netflixbmc Latest entry|
| Window(Home).Property(netflix.generic.recent.path) | Path of the Netflixbmc Latest entry|
| Window(Home).Property(netflix.generic.recent.content) | Contentpath of the Netflixbmc Latest entry (for widgets)|
| Window(Home).Property(netflix.generic.recent.image) | Rotating Fanart from Netflixbmc Latest entry|
| |
| Window(Home).Property(netflix.movies.title) | Title of the Netflixbmc Movies entry|
| Window(Home).Property(netflix.movies.path) | Path of the Netflixbmc Movies entry|
| Window(Home).Property(netflix.movies.content) | Contentpath of the Netflixbmc Movies entry (for widgets)|
| Window(Home).Property(netflix.movies.image) | Rotating Fanart from Netflixbmc Movies entry|
| |
| Window(Home).Property(netflix.movies.mylist.title) | Title of the Netflixbmc Movies Mylist entry|
| Window(Home).Property(netflix.movies.mylist.path) | Path of the Netflixbmc Movies Mylist entry|
| Window(Home).Property(netflix.movies.mylist.content) | Contentpath of the Netflixbmc Movies Mylist entry (for widgets)|
| Window(Home).Property(netflix.movies.mylist.image) | Rotating Fanart from Netflixbmc Movies Mylist entry|
| |
| Window(Home).Property(netflix.movies.suggestions.title) | Title of the Netflixbmc Movies suggestions entry|
| Window(Home).Property(netflix.movies.suggestions.path) | Path of the Netflixbmc Movies suggestions entry|
| Window(Home).Property(netflix.movies.suggestions.content) | Contentpath of the Netflixbmc Movies suggestions entry (for widgets)|
| Window(Home).Property(netflix.movies.suggestions.image) | Rotating Fanart from Netflixbmc Movies suggestions entry|
| |
| Window(Home).Property(netflix.movies.inprogress.title) | Title of the Netflixbmc Movies In progress entry|
| Window(Home).Property(netflix.movies.inprogress.path) | Path of the Netflixbmc Movies In progress entry|
| Window(Home).Property(netflix.movies.inprogress.content) | Contentpath of the Netflixbmc Movies In progress entry (for widgets)|
| Window(Home).Property(netflix.movies.inprogress.image) | Rotating Fanart from Netflixbmc Movies In progress entry|
| |
| Window(Home).Property(netflix.movies.recent.title) | Title of the Netflixbmc Latest movies entry|
| Window(Home).Property(netflix.movies.recent.path) | Path of the Netflixbmc Latest movies entry|
| Window(Home).Property(netflix.movies.recent.content) | Contentpath of the Netflixbmc Latest movies entry (for widgets)|
| Window(Home).Property(netflix.movies.recent.image) | Rotating Fanart from Netflixbmc Latest movies entry|
| |
| Window(Home).Property(netflix.tvshows.title) | Title of the Netflixbmc tvshows entry|
| Window(Home).Property(netflix.tvshows.path) | Path of the Netflixbmc tvshows entry|
| Window(Home).Property(netflix.tvshows.content) | Contentpath of the Netflixbmc tvshows entry (for widgets)|
| Window(Home).Property(netflix.tvshows.image) | Rotating Fanart from Netflixbmc tvshows entry|
| |
| Window(Home).Property(netflix.tvshows.mylist.title) | Title of the Netflixbmc tvshows Mylist entry|
| Window(Home).Property(netflix.tvshows.mylist.path) | Path of the Netflixbmc tvshows Mylist entry|
| Window(Home).Property(netflix.tvshows.mylist.content) | Contentpath of the Netflixbmc tvshows Mylist entry (for widgets)|
| Window(Home).Property(netflix.tvshows.mylist.image) | Rotating Fanart from Netflixbmc tvshows Mylist entry|
| |
| Window(Home).Property(netflix.tvshows.suggestions.title) | Title of the Netflixbmc tvshows suggestions entry|
| Window(Home).Property(netflix.tvshows.suggestions.path) | Path of the Netflixbmc tvshows suggestions entry|
| Window(Home).Property(netflix.tvshows.suggestions.content) | Contentpath of the Netflixbmc tvshows suggestions entry (for widgets)|
| Window(Home).Property(netflix.tvshows.suggestions.image) | Rotating Fanart from Netflixbmc tvshows suggestions entry|
| |
| Window(Home).Property(netflix.tvshows.inprogress.title) | Title of the Netflixbmc tvshows In progress entry|
| Window(Home).Property(netflix.tvshows.inprogress.path) | Path of the Netflixbmc tvshows In progress entry|
| Window(Home).Property(netflix.tvshows.inprogress.content) | Contentpath of the Netflixbmc tvshows In progress entry (for widgets)|
| Window(Home).Property(netflix.tvshows.inprogress.image) | Rotating Fanart from Netflixbmc tvshows In progress entry|
| |
| Window(Home).Property(netflix.tvshows.recent.title) | Title of the Netflixbmc Latest tvshows entry|
| Window(Home).Property(netflix.tvshows.recent.path) | Path of the Netflixbmc Latest tvshows entry|
| Window(Home).Property(netflix.tvshows.recent.content) | Contentpath of the Netflixbmc Latest tvshows entry (for widgets)|
| Window(Home).Property(netflix.tvshows.recent.image) | Rotating Fanart from Netflixbmc Latest tvshows entry|
| |



________________________________________________________________________________________________________
________________________________________________________________________________________________________

### Use with skin shortcuts script
This addon is designed to fully work together with the skinshortcuts script, so it will save you a lot of time because the script provides skinshortcuts with all the info to display contents.
No need to manually skin all those window properties in your skin, just a few lines in your overrides file is enough.

#### Display Smart Shortcuts in skin shortcuts listing

When the smart shortcuts are used together with skinshortcuts it will auto assign the icon and background with rotating fanart and both the widget and submenu (if needed) are assigned by default. The user just adds the shortcut and is all set.

To display the complete listing of Smart Shortcuts in your skin, place the following line in your overrides file, in the groupings section:
```xml
<shortcut label="Smart Shortcuts" type="32010">||BROWSE||script.skin.helper.service/?action=smartshortcuts</shortcut>
```

full example:
```xml
<overrides>
	<groupings>
		<shortcut label="Smart Shortcuts" type="32010">||BROWSE||script.skin.helper.service/?action=smartshortcuts</shortcut>
	</groupings>
</overrides>	
```
Offcourse you can use a condition parameter to only show the smart shortcuts entry if it's enabled in your skin.
You can also choose to use display the smart shortcuts to be used as widgets, in that case include this line in your overrides.xml file:
```xml
<widget label="Smart Shortcuts" type="32010">||BROWSE||script.skin.helper.service/?action=smartshortcuts</widget>
```

#### Auto display Backgrounds provided by the script in skinshortcuts selector

You can choose to show all backgrounds (including those for smart shortcuts) that are provided by this addon in the skinshortcuts backgrounds selector.

To display all backgrounds automatically in skinshorts you only have to include the line below in your overrides file:
```xml
<background label="smartshortcuts">||BROWSE||plugin://script.skin.helper.service/?action=backgrounds</background>
```

Note: You can still use the default skinshortcuts method to assign a default background to a item by labelID or defaultID.
In that case use the full $INFO path of the background. For example, to assign the "all movies" background to the Movies shortcut:
```xml
<backgrounddefault defaultID="movies">$INFO[Window(Home).Property(SkinHelper.AllMoviesBackground)]</backgrounddefault>
```
For more info, see skinshortcut's documentation.


#### Auto display widgets in skinshortcuts

Coding all widgets in your skin can be a pain, especially to keep up with all the fancy scripts like extendedinfo and library data provider. This addon, combined with skinshortcuts can make things a little easier for you...
By including just one line of code in your skinshortcuts override.xml you can display a whole bunch of widgets, ready to be selected by the user:

```xml
<widget label="Widgets" type="32010">||BROWSE||script.skin.helper.service/?action=widgets&amp;path=skinplaylists,librarydataprovider,scriptwidgets,extendedinfo,smartshortcuts,pvr,smartishwidgets</widget>
```

This will display a complete list of widgets available to select if the user presses the select widget button in skinshortcuts. In the path parameter you can specify which widgettypes should be listed. The widgets will be displayed in the order of which you type them as parameters (comma separated). You can also leave out the whole path parameterm in that case all available widgets will be displayed.

Currently available widgets (more to be added soon):

skinplaylist --> all playlists that are stored in "yourskin\extras\widgetplaylists" or "yourskin\playlists"

librarydataprovider --> all widgets that are provided by the Library Data Provider script

scriptwidgets --> the special widgets that are provided by this addon, like favourites and favourite media etc.

extendedinfo --> All widgets that are provided by the Extended info script

smartshortcuts --> all smartshortcuts

pvr --> pvr widgets

smartishwidgets --> widget supplied by the smartish widgets addon

favourites --> any browsable nodes in the user's favourites that can be used as widget


Note: the script will auto check the existence of the addons on the system so no need for complex visibility conditions in your skin.



________________________________________________________________________________________________________
________________________________________________________________________________________________________


