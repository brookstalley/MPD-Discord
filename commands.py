import discord
from command import Command
from discord import Embed

from typing import Union, List

import mpd_utils
from config import Common as config
from utils import get_results_embed, send_song_embed, get_song_embed, get_queue_embeds
from mpd_utils import get_current_song, add_to_queue, images_for_uris

from dataclasses import dataclass, field


@dataclass
class ReturnMessage:
    message: str = None
    embed: Embed = None
    embeds: List[Embed] = field(default_factory=list)


@dataclass
class CommandResult:
    return_message: ReturnMessage = None
    extras: dict = None
    post_action: callable = None


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


async def generate_help(*args) -> CommandResult:
    embed = discord.Embed(color=0xff000a, title='Help',
                          description='')

    for command in config.commands:
        c = commands[command]
        embed.add_field(name=c.get_name(),
                        value=c.get_description() + "\n**Aliases:** " + ', '.join(a for a in c.get_aliases()) + "\n--")
    result = CommandResult(ReturnMessage(embed=embed))

    return result


async def get_playing(msg, args) -> CommandResult:
    song = await get_current_song()
    if song is None:
        embed = discord.Embed(title="Nothing playing.", color=0xff4444)
        return {'embed': embed}, None, None

    uri_images = await images_for_uris([song.uri])
    result = CommandResult(
        ReturnMessage(embed=get_song_embed(song, uri_images=uri_images))
    )
    return result


async def search(msg, query) -> CommandResult:
    results = await mpd_utils.perform_search(query)

    result = CommandResult(
        ReturnMessage(embed=get_results_embed(results)),
        extras={'wait_for_reactions': True, 'data': results},
        post_action=send_song_embed)
    return result


async def add(msg, query) -> CommandResult:
    results = await mpd_utils.perform_search(query)

    result = CommandResult(
        ReturnMessage(embed=get_results_embed(results)),
        extras={'wait_for_reactions': True, 'data': results},
        post_action=add_to_queue
    )
    return result


async def add_one(msg: discord.message.Message, query) -> CommandResult:
    results = await mpd_utils.perform_search(query)

    if len(results) == 0:
        return CommandResult(ReturnMessage(message='No results found.'))

    song = results[0]

    await add_to_queue(msg, song=song, uri_images=None)

    result = CommandResult(
        ReturnMessage(embed=get_results_embed(results)),
        extras={'wait_for_reactions': True, 'data': results},
        post_action=add_to_queue
    )
    return result


async def queue(msg, args) -> CommandResult:
    results = await mpd_utils.get_queue()
    uri_images = await images_for_uris([song.uri for song in results])
    message, embeds = get_queue_embeds(
        results, title="Current Playlist", empty="Queue is empty", uri_images=uri_images)

    result = CommandResult(
        ReturnMessage(message=message, embeds=embeds)
    )
    return result


async def pause(msg, args) -> CommandResult:
    await mpd_utils.pause_playback()

    return CommandResult()


async def play(msg, args) -> CommandResult:
    await mpd_utils.start_playback()

    return CommandResult()


async def next(msg, args) -> CommandResult:
    await mpd_utils.next_track()
    # get_playing shows skipped track, not newly playing track, so don't use this
    # return await get_playing(msg, args)
    return CommandResult()


async def clear(msg, args) -> CommandResult:
    await mpd_utils.clear_queue()

    result = CommandResult(
        ReturnMessage(message='Cleared queue')
    )
    return result
