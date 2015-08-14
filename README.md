# script.skin.helper.service
a helper service for Kodi skins

________________________________________________________________________________________________________

### Settings for the script
The script does not have it's own settings dialog. The script is controlled by the skinner through skin settings to allow the skinner to fully integrate the settings of this script within the skin settings of the skin.

Important settings:

| setting name 		| how to set 				| description |
|:---------------------- | :------------------------------------- | :----------- |
|EnableExtraFanart	| Skin.ToggleSetting(EnableExtraFanart)	| enables the extrafanart background scanner |
|StudioImagesCustompath | Skin.SetString(StudioImagesCustompath,[PATH])| if you want the user (or yourself as skinner) be able to set a custom path to studio logos. If empty it will use the logos provided by the script (later to be replaced with the new image resource packs in Kodi 16)|
|ShowInfoAtPlaybackStart	| Skin.SetNumeric(ShowInfoAtPlaybackStart)	| Show OSD info panel at playback start for number of seconds (0 disables this) |
|RandomFanartDelay	| Skin.SetNumeric(RandomFanartDelay)	| Sets the time in seconds for the interval of the rotating backgrounds provided by the script (0 disables this) |
|CustomPicturesBackgroundPath	| Skin.SetPath(CustomPicturesBackgroundPath)	| Sets a custom path from which the global pictures background should be pulled from. (empty uses all picture sources) |
________________________________________________________________________________________________________
________________________________________________________________________________________________________

### Window Properties provided by the script
The script provides several window properties to provide additional info about your skin and media info.
The window properties can be called in your skin like this: $INFO[Window(Home).Property(propertyname)]

________________________________________________________________________________________________________



#### General window Properties
The window properties can be called in your skin like this: $INFO[Window(Home).Property(propertyname)]
```
Window(Home).Property(skinTitle)  --> your skin name including the version
Window(Home).Property(skinVersion) --> only the version of your skin
```
________________________________________________________________________________________________________
#### Video library window properties
Some additional window properties that can be used in the video library. 

| property 			| description |
|:-----------------------------	| :----------- |
|Window(Home).Property(ExtraFanArtPath) | will return the extrafanart path for the listitem, empty if none is found. This window property is only available when browsing the video library and when the following Skin Bool is true: EnableExtraFanart|
|Window(Home).Property(ListItemStudioLogo) | Will return the full image path of the studio logo for the current selected item in a list. |
|Window(Home).Property(Player.AddonName) | If you want to display the name of the addon in the player |
|Window(Home).Property(Duration) | The duration of the current listitem in hours, for example 1:20 |

________________________________________________________________________________________________________



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

________________________________________________________________________________________________________



#### Music library window properties
Some additional window properties that can be used in the music library. 

| property 			| description |
| :----------------------------	| :----------- |
| Window(Home).Property(ExtraFanArtPath) | will return the extrafanart path for the artist, empty if none is found. This window property is only available when the following Skin Bool is true: EnableExtraFanart|
| Window(Home).Property(bannerArt) | Will return the Artist's banner image for the current selected item in the list. |
| Window(Home).Property(logoArt) | Will return the Artist's logo image for the current selected item in the list. |
| Window(Home).Property(cdArt) | Will return the Album's cd art image for the current selected item in the list. |
| Window(Home).Property(songInfo) | Returns the album's description or if empty the artist info. Can be used at both album- and songlevel.  |


________________________________________________________________________________________________________



#### Backgrounds provided by the script
The script has a background scanner to provide some rotating fanart backgrounds which can be used in your skin as backgrounds. The backgrounds are available in window properties.

Note: the default interval for the backgrounds is set at 30 seconds. If you want to change this interval you can set a Skin String "RandomFanartDelay" with the number of seconds as value.

| property 			| description |
| :----------------------------	| :----------- |
| Window(Home).Property(AllMoviesBackground) | Random fanart of movies in video database|
| Window(Home).Property(AllTvShowsBackground) | Random fanart of TV shows in video database|
| Window(Home).Property(AllMusicVideosBackground) | Random fanart of music videos in video database|
| Window(Home).Property(AllMusicBackground) | Random fanart of music artists in database|
| Window(Home).Property(GlobalFanartBackground) | Random fanart of all media types|
| Window(Home).Property(InProgressMovieBackground) | Random fanart of in progress movies|
| Window(Home).Property(RecentMovieBackground) | Random fanart of in recently added movies|
| Window(Home).Property(UnwatchedMovieBackground) | Random fanart of unwatched movies|
| Window(Home).Property(InProgressShowsBackground) | Random fanart of in progress tv shows|
| Window(Home).Property(RecentEpisodesBackground) | Random fanart of recently added episodes|
| Window(Home).Property(PicturesBackground) | Random pictures from all picture sources. By default this pulls images from all picture sources the user has configured. It is however possible to provide a custom source from which the images should be pulled from by setting Skin String: CustomPicturesBackgroundPath|
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

________________________________________________________________________________________________________




#### Youtube trailer search
Shows a dialog with all trailers found by the Youtube plugin, replace [MOVIETITLE] with the movie title (or info label in the skin). To be used for example in DialogVideoInfo.xml to let the user select a trailer instead of playing the default one.
```
RunScript(script.skin.helper.service,action=searchtrailer,title=[MOVIETITLE])             
```



#### Busy spinner selector
Allows the user to select a busy spinner from some predefined ones in your skin. It supports both multiimage (folder with images) and single image (.gif) spinners. The user can provide his own texture(s) or select from predefined spinners in the skin.

```
RunScript(script.skin.helper.service,action=busytexture)             
```
The script fills this Skin Strings after selection: 
SpinnerTexture --> the name of the selected busy texture
SpinnerTexturePath --> The full path of the selected busy texture

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
	<imagepath>$INFO[Skin.String(SpinnerTexturePath)]</imagepath>
	<timeperimage>100</timeperimage>
	<colordiffuse>$INFO[Skin.String(SpinnerTextureColor)]</colordiffuse>
	<fadetime>0</fadetime>
	<visible>!Skin.String(SpinnerTexturePath,None)</visible>
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
This will present a selection dialog to the user to enable (or disable) views. It uses the views.xml file to display the available views (see above). When a view is disabled it will be hidden from the view selection dialog. Also, a Skin String will be set so you can check in your skin if the view has been diable (and not include it or set a visiblity condition).
The name of the Skin String that will be set by the script is: View.Disabled.[VIEWID] where [VIEWID] is the numerical ID of the view.

Example: <include condition="!Skin.HasSetting(View.Disabled.55)">View_55_BannerList</include>

________________________________________________________________________________________________________



#### Set Forced views
```
RunScript(script.skin.helper.service,action=setforcedview,contenttype=[TYPE])             
```
The script can help you to set a forced view for a specific contenttype in your skin. For example if the user wants to set the list view for all tvshow content etc. For [TYPE] you must fill in one of the content types, see above at "Views selector". When a button is pressed with the above command, a select dialog appears and the user can choose on of the available views. Disabled views and views that aren't suitable for the specified type are hidden from the list.
When the user made a choice from the list a Skin String will be filled by the script: ForcedViews.[TYPE]
The value of that skin string is the numeric ID of the selected view.

Note: It is recommended that you create a Skin toggle to enable/disable the forced views feature.

Note 2: When the user select another view in the normal viewselector, the forcedview setting will also be set to the newly chosen view.



##### How to use the forced views feature in your skin?

Example code to use in your skin settings:

```xml
<control type="radiobutton" id="6009">
	<label>Enable forced views</label>
	<onclick>Skin.ToggleSetting(ForcedViews.Enabled)</onclick>
	<selected>Skin.HasSetting(ForcedViews.Enabled)</selected>
</control>
<control type="button" id="6010">
	<onclick>RunScript(script.skin.helper.service,action=setforcedview,contenttype=movies)</onclick>
	<visible>Skin.HasSetting(ForcedViews.Enabled)</visible>
	<label>Forced view for movies: $INFO[Skin.String(ForcedViews.movies)]</label>
</control>
<control type="button" id="6011">
	<onclick>RunScript(script.skin.helper.service,action=setforcedview,contenttype=tvshows)</onclick>
	<visible>Skin.HasSetting(ForcedViews.Enabled)</visible>
	<label>Forced view for tv shows:  $INFO[Skin.String(ForcedViews.tvshows)]</label>
</control>
<control type="button" id="6012">
	<onclick>RunScript(script.skin.helper.service,action=setforcedview,contenttype=seasons)</onclick>
	<visible>Skin.HasSetting(ForcedViews.Enabled)</visible>
	<label>Forced view for seasons:  $INFO[Skin.String(ForcedViews.seasons)]</label>
</control>
<control type="button" id="6013">
	<onclick>RunScript(script.skin.helper.service,action=setforcedview,contenttype=episodes)</onclick>
	<visible>Skin.HasSetting(ForcedViews.Enabled)</visible>
	<label>Forced view for episodes: $INFO[Skin.String(ForcedViews.episodes)]</label>
	<font>Reg28</font>
</control>
<control type="button" id="6014">
	<onclick>RunScript(script.skin.helper.service,action=setforcedview,contenttype=sets)</onclick>
	<visible>Skin.HasSetting(ForcedViews.Enabled)</visible>
	<label>Forced view for movie sets: $INFO[Skin.String(ForcedViews.sets)]</label>
</control>
<control type="button" id="6015">
	<onclick>RunScript(script.skin.helper.service,action=setforcedview,contenttype=setmovies)</onclick>
	<visible>Skin.HasSetting(ForcedViews.Enabled)</visible>
	<label>Forced view for movies inside set: $INFO[Skin.String(ForcedViews.setmovies)]</label>
</control>
```

Example code to use for your views visibility conditions:
```xml
<control type="panel" id="51">
	<visible>!Skin.HasSetting(ForcedViews.Enabled) | 
	[Container.Content(movies) + Skin.String(ForcedViews.movies,None)] | 
	[Container.Content(tvshows) + Skin.String(ForcedViews.tvshows,None)] | 
	[Container.Content(seasons) + Skin.String(ForcedViews.seasons,None)] | 
	[Container.Content(episodes) + Skin.String(ForcedViews.episodes,None)] | 
	[Container.Content(movies) + Skin.String(ForcedViews.movies,None)] | 
	[Container.Content(tvshows) + Skin.String(ForcedViews.tvshows,None)] | 
	[Container.Content(seasons) + Skin.String(ForcedViews.seasons,None)] | 
	[Container.Content(episodes) + Skin.String(ForcedViews.episodes,None)] | 
	[[Container.Content(sets) | StringCompare(Container.Folderpath,videodb://movies/sets/)] + Skin.String(ForcedViews.sets,51)] | 
	[Container.Content(movies) + Skin.String(ForcedViews.movies,51) + !substring(Container.FolderPath,videodb://movies/sets/,left)] | 
	[Container.Content(movies) + Skin.String(ForcedViews.setmovies,51) + substring(Container.FolderPath,setid=)] | 
	[Container.Content(tvshows) + Skin.String(ForcedViews.tvshows,51)] | 
	[Container.Content(seasons) + Skin.String(ForcedViews.seasons,51)] | 
	[Container.Content(episodes) + Skin.String(ForcedViews.episodes,51)] | 
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
It is possible to deliver skin provided color themes. Those colorthemes are stored in the skin's extras\skinthemes folder.
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
The script comes with a backup/restore feature. It supports backup of ALL skin settings including skin shortcuts (when script.skinshortcuts is used). 

- Backup all settings to file
- Restore all settings from file
- Reset the skin to default settings (wipe all settings)

#####To backup the skin settings:
```
RunScript(script.skin.helper.service,action=backup)             
```

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

#####Next Episodes
```
plugin://script.skin.helper.service/?action=nextepisodes&limit=[LIMIT]
```
Provides a list of the nextup episodes. This can be the first episode in progress from a tv show or the next unwatched from a in progress show.
________________________________________________________________________________________________________

#####Recommended Movies
```
plugin://script.skin.helper.service/?action=recommendedmovies&limit=[LIMIT]
```
Provides a list of the in progress movies AND recommended movies based on rating.
________________________________________________________________________________________________________

#####Recommended Media
```
plugin://script.skin.helper.service/?action=recommendedmedia&limit=[LIMIT]
```
Provides a list of recommended media (movies, tv shows, music)

________________________________________________________________________________________________________

#####Recent Media
```
plugin://script.skin.helper.service/?action=recentmedia&limit=[LIMIT]
```
Provides a list of recently added media (movies, tv shows, music, tv recordings, musicvideos)

________________________________________________________________________________________________________

#####Similar Movies (because you watched...)
```
plugin://script.skin.helper.service/?action=similarmovies&limit=[LIMIT]
```
This will provide a list with movies that are similar to a random watched movie from the library.
TIP: The listitem provided by this list will have a property "originaltitle" which contains the movie from which this list is generated. That way you can create a "Because you watched $INFO[Container.ListItem.Property(originaltitle)]" label....

________________________________________________________________________________________________________

#####In progress Media
```
plugin://script.skin.helper.service/?action=inprogressmedia&limit=[LIMIT]
```
Provides a list of all in progress media (movies, tv shows, music, musicvideos)

________________________________________________________________________________________________________

#####In progress and Recommended Media
```
plugin://script.skin.helper.service/?action=inprogressandrecommendedmedia&limit=[LIMIT]
```
This combines in progress media and recommended media, usefull to prevent an empty widget when no items are in progress.

________________________________________________________________________________________________________

#####Favourite Media
```
plugin://script.skin.helper.service/?action=favouritemedia&limit=[LIMIT]
```
Provides a list of all media items that are added as favourite (movies, tv shows, songs, musicvideos)

________________________________________________________________________________________________________

#####Favourites
```
plugin://script.skin.helper.service/?action=favourites&limit=[LIMIT]
```
Provides the Kodi favourites as list content






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
