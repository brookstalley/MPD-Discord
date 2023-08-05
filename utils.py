#import main
import requests
import discord
import constants
import string
from datetime import timedelta
import mopidy.models
from config import Common as config

def get_album_art_url(song):
    return ""
    import mpd_album_art

    grabber_settings = settings['mpd']['art_grabber']

    artist_album = '%s - %s.jpg' % (song['artist'], song['album'])

    grabber = mpd_album_art.Grabber(
        save_dir=grabber_settings['save_dir'],
        library_dir=grabber_settings['library_dir'],
        link_path=artist_album
    )

    grabber.get_local_art(song)

    return settings['download_servers']['art_url'] + requests.utils.quote(artist_album)


def get_track_download(song):
    return settings['download_servers']['music_url'] + requests.utils.quote(song['file'])

def get_song_embed(song:mopidy.models.Track, additional=None, title_prefix = ''):
    global settings
    artists = []
    artist_line = f'Artist: {", ".join(artist.name for artist in song.artists)}'
    album_line = f'Album: {song.album.name} ({song.album.date})'
    uri_line = f'URI: {song.uri}'
    
    desc_line = f'{artist_line}\n{album_line}\n{uri_line}'

    embed = discord.Embed(color=0xff0ff, title = f'{title_prefix}{song.name}',
                          description = desc_line)

    if config.mopidy['show_art']:
        embed.set_thumbnail(url=get_album_art_url(song))
    # TODO: static image if we don't download art?

    if additional:
        embed.description += '\n**%s**' % additional

    if config.mopidy['show_download']:
        download_link = get_track_download(song)
        embed.add_field(name='Download Link', value=f'[Click Here]({download_link})')

    return embed

def get_results_embed(results, title: str='Search Results', empty: str='No results.'):
    alphabet = [chr(i) for i in range(constants.UPPER_A_VALUE, constants.UPPER_Z_VALUE)]

    message = ''.join('%s: **%s** by **%s**%s (%s)\n'
                      % (alphabet[results.index(song)],
                         song['title'], song['artist'], (' (' + song.get('album', 'No album') + ')'),
                         timedelta(seconds=round(float(song['time']))))
                      for song in results) if len(results) > 0 else empty

    embed = discord.Embed(color=0xff00ff, title=title, description=message)

    return embed


async def send_song_embed(client, message, song, additional=None):
    embed = get_song_embed(song, additional)
    await message.channel.send("Song details:", embed=embed)


def create_player(voice):
    ffmpeg_options = '-analyzeduration 0 ' \
                     '-loglevel 0 ' \
                     '-f s16le ' \
                     '-ar 44100 ' \
                     '-ac 2 ' \
                     '-acodec pcm_s16le'

    return discord.FFmpegPCMAudio(settings['mpd']['fifo'], before_options=ffmpeg_options)
