import discord
from command import Command

from typing import Union

import mpd_utils
from config import Common as config

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


def search(msg, query):
    results = mpd_utils.perform_search(query)

    import utils
    return {'embed': utils.get_results_embed(results)}, \
           {'wait_for_reactions': True, 'data': results}, utils.send_song_embed


def add(msg, query):
    results = mpd_utils.perform_search(query)

    import utils
    return {'embed': utils.get_results_embed(results)}, \
           {'wait_for_reactions': True, 'data': results}, mpd_utils.add_to_queue


def playlist(msg, args):
    results = mpd_utils.get_current_playlist()

    import utils
    return {'embed': utils.get_results_embed(results, title="Current Playlist", empty="Empty.")}, None, None


def join(msg, args):
    connected_channel = msg.author.voice.channel

    action = None
    if connected_channel:
        message = "Joining **%s**..." % connected_channel.name
        action = {'join_voice': True, 'data': connected_channel}

    else:
        message = "You must be in a voice channel to do that."  # TODO Create decoration to handle voice channel requirement
    return {"message": message}, action, None


def pause(msg, args):
    connected_channel = msg.author.voice.channel

    action = None
    if connected_channel:
        message = "Toggling playback..."
        action = {'toggle_playback': True, 'data': mpd_utils.is_paused()}
    else:
        message = "You must be in a voice channel to do that."

    return {"message": message}, action, None


async def next(msg, args):
    await mpd_utils.next_track()
    # get_playing shows skipped track, not newly playing track, so don't use this
    #return await get_playing(msg, args)
    return None, None, None

def leave(msg, args):
    connected_channel = msg.author.voice.voice_channel

    action = None
    if connected_channel:
        message = "Leaving..."
        action = {'leave_voice': True, 'data': None}
    else:
        message = "You must be in a voice channel to do that."

    return {"message": message}, action, None
