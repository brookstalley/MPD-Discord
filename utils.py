from discord import Embed
from discord.utils import escape_markdown
import constants
from datetime import timedelta
import mopidy.models
from config import Common as config

def artists_to_string(artists):
    return ', '.join(artist.name for artist in artists)

def get_song_embed(song:mopidy.models.Track, additional=None, title_prefix = '', uri_images = None):
    global settings

    artists = []
    artist_line = f'Artist: {artists_to_string(song.artists)}'
    album_line = f'Album: {song.album.name} ({song.album.date})'
    uri_line = f'URI: {song.uri}'
    
    desc_line = f'{artist_line}\n{album_line}\n{uri_line}'

    embed = Embed(color=0xff0ff, title = f'{title_prefix}{song.name}',
                          description = desc_line)

    if config.locals['mopidy']['show_art']:
        if uri_images is not None:
            image = uri_images[song.uri][0]
            if image:
                embed.set_thumbnail(url=image.uri)

    if additional:
        embed.description += '\n**%s**' % additional

    return embed

def song_for_results(index:str, song:mopidy.models.Track) -> str:
    markdown = (f'{index}: **{escape_markdown(song.name)}**'
                f' by {escape_markdown(artists_to_string(song.artists))}' +
                f' from {escape_markdown(song.album.name)}'
                f'({timedelta(seconds=round(float(song.length)/1000))})\n')
    return markdown    

def get_results_embed(results, title: str='Search Results', empty: str='No results.'):
    alphabet = [chr(i) for i in range(constants.UPPER_A_VALUE, constants.UPPER_Z_VALUE)]

    message = ''

    if len(results) > len(alphabet):
        message += f'{len(results)} results found. Showing first {len(alphabet)}.\n\n'
        results = results[:len(alphabet)]

    message += ''.join(song_for_results(alphabet[results.index(song)], song) for song in results) if len(results) > 0 else empty

    embed = Embed(color=0xff00ff, title=title, description=message)

    return embed

def get_queue_embeds(queue, title: str='Current Queue', empty: str='No songs in queue.', uri_images = None):
    if len(queue) == 0:
        return empty, None
    if len(queue) > 10:
        message = f'**{len(queue)} songs in queue. Showing first 10.**\n\n'
    else:
        message = f'**{len(queue)} songs in queue.**\n\n'

    display_queue = queue[:10]
    embedList = []
    item: mopidy.models.Track
    for item in display_queue:
        desc = f'Artist: {artists_to_string(item.artists)}\nAlbum: {item.album.name} ({item.album.date})'
        embed = Embed(color=0xff0000, title=item.name, description=desc)
        if uri_images is not None:
            image = uri_images[item.uri][0]
            if image:
                embed.set_thumbnail(url=image.uri)
        embedList.append(embed)
    return message, embedList

async def send_song_embed(client, message, song, additional=None, uri_images=None):
    embed = get_song_embed(song=song, additional=additional, uri_images=uri_images)
    await message.channel.send("Song details:", embed=embed)
