import discord
from command import Command

from typing import Union

import mpd_utils
from config import Common as config
from utils import get_results_embed, send_song_embed
from mpd_utils import get_current_song, add_to_queue


commands = {}
aliases = {}

def register_command(command: Command):
    if command.get_name() in commands:
        raise ValueError("A command with this name is already registered.")

    commands[command.get_name()] = command

    for alias in command.get_aliases():
        aliases[alias] = command.get_name()

def get_command_by_name(name: str) -> Union[Command, None]:
    name = name.split(' ')[0]
    if name in commands:
        return commands[name]
    elif name in aliases:
        return commands[aliases[name]]
    else:
        return None        

def generate_help(*args):
    embed = discord.Embed(color=0xff000a, title='Help',
                          description='')

    for command in config.commands:
        c = commands[command]
        embed.add_field(name=c.get_name(),
                        value=c.get_description() + "\n**Aliases:** " + ', '.join(a for a in c.get_aliases()) + "\n--")

    return {'embed': embed}, None, None

async def get_playing(msg, args):
    song = await mpd_utils.get_current_song()
    if song is None:
        embed = discord.Embed(title="Nothing playing.", color=0xff4444)
        return {'embed': embed}, None, None

    import utils
    return {'embed': utils.get_song_embed(song)}, None, None

async def search(msg, query):
    results = await mpd_utils.perform_search(query)

    return {'embed': get_results_embed(results)}, \
           {'wait_for_reactions': True, 'data': results}, send_song_embed

async def add(msg, query):
    results = await mpd_utils.perform_search(query)

    return {'embed': get_results_embed(results)}, \
           {'wait_for_reactions': True, 'data': results}, add_to_queue

async def queue(msg, args):
    results = await mpd_utils.get_queue()

    return {'embed': get_results_embed(results, title="Current Playlist", empty="Empty.")}, None, None

async def pause(msg, args):
    await mpd_utils.pause_playback()

    return None, None, None

async def play(msg, args):
    await mpd_utils.start_playback()

    return None, None, None

async def next(msg, args):
    await mpd_utils.next_track()
    # get_playing shows skipped track, not newly playing track, so don't use this
    #return await get_playing(msg, args)
    return None, None, None

async def clear(msg, args):
    await mpd_utils.clear_queue()

    return "Cleared queue", None, None