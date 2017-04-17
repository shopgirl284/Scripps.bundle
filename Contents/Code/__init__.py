NAME = 'Scripps Networks'
ART = 'art-default.jpg'
ICON = 'icon-default.png'
PREFIX = '/video/scripps'

SHOWS_LIST = [
    {'title': 'HGTV', 'fullurl' : 'http://www.hgtv.com/shows/full-episodes', 'vidurl' : 'http://www.hgtv.com/videos', 'showurl' : 'http://www.hgtv.com/shows/shows-a-z', 'icon' : 'hgtv-icon.jpg'}, 
    {'title': 'Food Network', 'fullurl' : 'http://www.foodnetwork.com/videos/full-episodes.html', 'vidurl' : 'http://www.foodnetwork.com/videos.html', 'showurl' : 'http://www.foodnetwork.com/shows/a-z', 'icon' : 'food-icon.jpg'}, 
    {'title': 'DIY Network', 'fullurl' : 'http://www.diynetwork.com/shows/full-episodes', 'vidurl' : 'http://www.diynetwork.com/videos', 'showurl' : 'http://www.diynetwork.com/shows/shows-a-z', 'icon' : 'diy-icon.jpg'}, 
    {'title': 'Cooking Channel', 'fullurl' : 'http://www.cookingchanneltv.com/videos/players/full-episodes-player', 'vidurl' : 'http://www.cookingchanneltv.com/videos', 'showurl' : 'http://www.cookingchanneltv.com/shows/a-z', 'icon' : 'cook-icon.jpg'}, 
    {'title': 'Great American Country', 'fullurl' : 'http://www.greatamericancountry.com/shows/full-episodes', 'vidurl' : 'http://www.greatamericancountry.com/videos', 'showurl' : 'http://www.greatamericancountry.com/shows/shows-a-z', 'icon' : 'gac-icon.jpg'}
]

SMIL_NS = {'a': 'http://www.w3.org/2005/SMIL21/Language'}

# Alternative code that pulls all the playlist in a page based on the AssetInfo field for each item showing a number of videos
#  playlist = page.xpath('//span[contains(@class, "AssetInfo") and contains(text(), "Videos")]/ancestor::div[contains(@class, "TextWrap")]/parent::div')
####################################################################################################
def Start():

    ObjectContainer.title1 = NAME
    DirectoryObject.thumb = R(ICON)
    HTTP.CacheTime = CACHE_1HOUR

####################################################################################################
@handler(PREFIX, NAME, thumb=ICON, art=ART)
def MainMenu():

    oc = ObjectContainer()

    for item in SHOWS_LIST:
        oc.add(DirectoryObject(key = Callback(ShowSections, title=item['title'], fulleps_url=item['fullurl'], video_url=item['vidurl'], show_url=item['showurl'], thumb=R(item['icon'])), title=item['title'], thumb = R(item['icon'])))

    return oc

####################################################################################################
# This function produces a list of all of the playlist items from a page
@route(PREFIX + '/showsections')
def ShowSections(title, fulleps_url, video_url, show_url, thumb=''):

    oc = ObjectContainer(title2=title)
    show_title = title

    oc.add(DirectoryObject(key = Callback(GetPlaylists, title='Full Episodes', url=fulleps_url, thumb=thumb), title='Full Episodes', thumb=thumb))
    oc.add(DirectoryObject(key = Callback(GetPlaylists, title='Videos', url=video_url, thumb=thumb), title='Videos', thumb=thumb))
    oc.add(DirectoryObject(key = Callback(Alphabet, title='All Shows', url=show_url, thumb=thumb), title='All Shows', thumb=thumb))
    if 'Food Network' in show_title:
        oc.add(DirectoryObject(key=Callback(GetPlaylists, title='Most-Popular Videos', url=video_url, section_code='ContentFeed', thumb=thumb), title='Most-Popular Videos', thumb=thumb))

    return oc

####################################################################################################
# This function produces a list of playlists for a video page including the video player and a similar playlists section
# By adding a section code value (other than the default 'ListVideoPlaylist'), you can pull the video playlist from just one section of the page
@route(PREFIX + '/getplaylists')
def GetPlaylists(title, url, thumb='', section_code='ListVideoPlaylist'):

    oc = ObjectContainer(title2=title)
    try: page = HTML.ElementFromURL(url)
    except: return ObjectContainer(header='Bad Url', message='The URL for this page is not valid')

    # Check for embedded video player and add a directory
    player_check = page.xpath('//div[@class="m-VideoPlayer"]')
    # Only include the video player directory for URLs with the default section code
    if len(player_check) > 0 and section_code=='ListVideoPlaylist':
        try: player_title = page.xpath('//div[@class="o-VideoPlaylistEmbed__m-Header"]//span/text()')[0]
        except: player_title = "Featured Videos"
        oc.add(DirectoryObject(key=Callback(VideoBrowse, title=player_title, url=url), title=player_title, thumb=thumb))

    # The playlist for most pages are contained in "Mediabock--playlist" div tags but a few shows return a playlist results list
    playlist = page.xpath('//div[@role="contentWell"]//div[contains(@class, "MediaBlock--playlist")]')
    # If the playlist is empty or this is a section pull use alternative code
    if len(playlist) < 1 or section_code!='ListVideoPlaylist':
        playlist = page.xpath('//section[contains(@class, "%s")]//div[@class="m-MediaBlock" or contains(@class, "o-Capsule__m-MediaBlock")]' %section_code)

    for item in playlist:
        summary = item.xpath('.//span[contains(@class, "AssetInfo")]/text()')[0].strip()
        if not summary.split()[0].isdigit(): 
            continue
        try: url = item.xpath('.//a/@href')[0]
        except: continue
        # To bypass any formatting within the title we just join all the data in the title field
        title = ' '.join(item.xpath('.//span[contains(@class, "HeadlineText")]//text()')).strip()
        try: item_thumb = item.xpath('.//img/@data-src')[0]
        except: 
            try: item_thumb = item.xpath('.//img/@src')[0]
            except: item_thumb = thumb

        oc.add(DirectoryObject(
            key = Callback(VideoBrowse, url=url, title=title),
            title = title,
            summary = summary,
            thumb = Resource.ContentsOfURLWithFallback(url=item_thumb)
        ))

    # Check for and create a directory for Similar Playlists
    playlist_check = page.xpath('//section[contains(@class, "SimilarPlaylists")]//div[@class="m-MediaBlock"]')
    # Do not include the playlist check for URL sent to pull SimilarPlaylists
    if len(playlist_check) > 0 and section_code!='SimilarPlaylists':
        oc.add(DirectoryObject(key=Callback(GetPlaylists, title='Similar Playlists', url=url, section_code='SimilarPlaylists', thumb=thumb), title='Similar Playlists', thumb=thumb))

    if len(oc) < 1:
        return ObjectContainer(header='Empty', message='There are no full episode shows to list')
    else:
        return oc

####################################################################################################
# A to Z pull for all shows
@route(PREFIX + '/alphabet')
def Alphabet(title, url, thumb=''):

    oc = ObjectContainer(title2=title)

    for char in HTML.ElementFromURL(url, cacheTime = CACHE_1DAY).xpath('//a[contains(@class, "IndexPagination")]/text()'):

        oc.add(DirectoryObject(key=Callback(AllShows, url=url, char=char, thumb=thumb), title=char, thumb=thumb))
    
    if len(oc) < 1:
        return ObjectContainer(header='Empty', message='There are no items to list')
    else:
        return oc

####################################################################################################
# This function produces a list of shows for letter in Alphabet function
@route(PREFIX + '/allshows')
def AllShows(char, url, thumb=''):

    oc = ObjectContainer(title2=char)
    page = HTML.ElementFromURL(url, cacheTime = CACHE_1DAY)

    for show in page.xpath('//*[@id="%s"]/ancestor::section[contains(@class,"o-Capsule")]//ul/li/a' % (char.lower())):

        title = show.text
        show_url = show.xpath('./@href')[0]

        oc.add(DirectoryObject(
            key = Callback(GetVideoLinks, show_url=show_url, title=title, thumb=thumb),
            title = title,
            thumb = thumb
        ))

    if len(oc) < 1:
        return ObjectContainer(header='Empty', message='There are no shows to list')
    else:
        return oc
####################################################################################################
# This function pulls the video link from a show's main page since the format of the video page varies
@route(PREFIX + '/getvideolinks')
def GetVideoLinks(title, show_url, thumb=''):

    oc = ObjectContainer(title2=title)
    page = HTML.ElementFromURL(show_url, cacheTime = CACHE_1DAY)

    # The Videos link can vary 
    for item in page.xpath('//li[@data-type="sub-navigation-item"]/div'):
        section_title = item.xpath('./a/text()')[0].strip()
        # Skip any the navigation items that are not for videos
        if 'video' not in section_title.lower():
            continue
        section_url = item.xpath('./a/@href')[0]

        oc.add(DirectoryObject(
            key = Callback(GetPlaylists, url=section_url, title="%s %s" %(title, section_title), thumb=thumb),
            title="%s %s" %(title, section_title),
            thumb=thumb
        ))

        # Check for any additional links under the video navigation
        for subitem in item.xpath('./ul[@data-type="dropdown-menu"]/li'):
            sub_url = subitem.xpath('./a/@href')[0]
            sub_title = subitem.xpath('./a/text()')[0].strip()

            oc.add(DirectoryObject(
                key = Callback(GetPlaylists, url=sub_url, title="%s %s" %(title, sub_title), thumb=thumb),
                title="%s %s" %(title, sub_title),
                thumb=thumb
            ))

    if len(oc) < 1:
        return ObjectContainer(header='Empty', message='There are no videos for this show')
    else:
        return oc
####################################################################################################
# This function produces a list of videos from a playlist or a single video from a video player URL
@route(PREFIX + '/videobrowse')
def VideoBrowse(url, title):

    oc = ObjectContainer(title2=title)
    url_base = url.split('.com')[0] + '.com'
    page = HTML.ElementFromURL(url)
    
    try:
        # Use the outer video container code to pull the json list since the inner code varies
        json_data = page.xpath('//div[@class="m-VideoPlayer"]//script/text()')[0].strip()
        json = JSON.ObjectFromString(json_data)
    except:
        return ObjectContainer(header='Empty', message='There are no videos to produce on this page')
    #Log('the value of json is %s' %json)
    
    if json:

        # If the URL contains a playlists, create a video for each item in the playlist
        try:
            playlist = json['channels'][0]['videos']
            for video in playlist:

                smil_url = video['releaseUrl']

                if 'link.theplatform.com' in smil_url:
                    oc.add(
                        CreateVideoClipObject(
                            smil_url = smil_url,
                            title = video['title'],
                            summary = video['description'],
                            duration = int(video['length'])*1000,
                            thumb = url_base + video['thumbnailUrl']
                        )
                    )
        
        # Otherwise if the URL just contains one video, create a video item for the single video
        except:
            smil_url = json['video']['releaseUrl']

            if 'link.theplatform.com' in smil_url:
                oc.add(
                    CreateVideoClipObject(
                        smil_url = smil_url,
                        title = json['video']['title'],
                        summary = json['video']['description'],
                        duration = int(json['video']['length'])*1000,
                        thumb = url_base + json['video']['thumbnailUrl']
                    )
                )

    else:
        Log('%s does not contain a video list json or the json is incomplete' % (url))

        
    # Some pages lists the individual videos in the player instead of the player itself and break them up into pages
    # The next page code creates a player for each page of videos listed
    try: next_page = page.xpath('//li[contains(@class, "Pagination")]/a[contains(@class, "NextButton") and not (contains(@class, "is-Disabled"))]/@href')[0]
    except: next_page = None
    if next_page:

        oc.add(NextPageObject(
            key = Callback(VideoBrowse, title=title, url=next_page),
            title = 'Next Page ...'
        ))

    if len(oc) < 1:
        return ObjectContainer(header='Empty', message='There are currently no videos for this listing')
    else:
        return oc

####################################################################################################
@route(PREFIX + '/createvideoclipobject', duration=int, include_container=bool)
def CreateVideoClipObject(smil_url, title, summary, duration, thumb, include_container=False, **kwargs):

    videoclip_obj = VideoClipObject(
        key = Callback(CreateVideoClipObject, smil_url=smil_url, title=title, summary=summary, duration=duration, thumb=thumb, include_container=True),
        rating_key = smil_url,
        title = title,
        summary = summary,
        duration = duration,
        thumb = Resource.ContentsOfURLWithFallback(url=thumb),
        items = [
            MediaObject(
                parts = [
                    PartObject(key=Callback(PlayVideo, smil_url=smil_url, resolution=resolution))
                ],
                container = Container.MP4,
                video_codec = VideoCodec.H264,
                audio_codec = AudioCodec.AAC,
                audio_channels = 2,
                video_resolution = resolution
            ) for resolution in [720, 540, 480]
        ]
    )

    if include_container:
        return ObjectContainer(objects=[videoclip_obj])
    else:
        return videoclip_obj

####################################################################################################
@route(PREFIX + '/playvideo', resolution=int)
@indirect
def PlayVideo(smil_url, resolution):

    xml = XML.ElementFromURL(smil_url)
    available_versions = xml.xpath('//a:switch[1]/a:video/@height', namespaces=SMIL_NS)

    if len(available_versions) < 1:
        raise Ex.MediaNotAvailable

    closest = min((abs(int(resolution) - int(i)), i) for i in available_versions)[1]
    video_url = xml.xpath('//a:switch[1]/a:video[@height="%s"]/@src' % closest, namespaces=SMIL_NS)[0]

    return IndirectResponse(VideoClipObject, key=video_url)
