import asyncio
import json
from typing import Union

import discord
#from discord.voice_client import StreamPlayer
from discord import FFmpegPCMAudio

import commands as bot_commands
import constants

client = discord.Client()
player: FFmpegPCMAudio = None
voice = None

commands = {}
aliases = {}


def generate_help(*args):
    embed = discord.Embed(color=0xff000a, title='Help',
                          description='')

    for command in commands:
        c = commands[command]
        embed.add_field(name=c.get_name(),
                        value=c.get_description() + "\n**Aliases:** " + ', '.join(a for a in c.get_aliases()) + "\n--")

    return {'embed': embed}, None, None


class Command:
    # _function: Callable[Any, dict]

    def __init__(self, name: str, command_aliases: list, description: str):
        self._name = name
        self._aliases = command_aliases
        self._description = description

        if command != 'help':
            self._function = getattr(bot_commands, self.get_name())
        else:
            self._function = generate_help

    def get_name(self):
        return self._name

    def get_aliases(self):
        return self._aliases

    def get_description(self):
        return self._description

    def get_help(self):
        return "\n\n**%s** - %s\n__Aliases:__ *%s*" % (self.get_name(), self.get_description(),
                                                       '*, *'.join(alias for alias in self.get_aliases()))

    def run(self, *args) -> dict:
        return self._function(*args)


def register_command(command: Command):
    if command.get_name() in commands:
        raise ValueError("A command with this name is already registered.")

    commands[command.get_name()] = command

    for alias in command.get_aliases():
        aliases[alias] = command.get_name()


with open('settings.json', 'r') as f:
    settings = json.loads(f.read())
    TOKEN = settings['token']
    PREFIX = settings['prefix']

    for command in settings['commands']:
        c = settings['commands'][command]
        register_command(Command(command, c['aliases'], c['description']))


def get_settings():
    return settings


def get_command_by_name(name: str) -> Union[Command, None]:
    name = name.split(' ')[0]
    if name in commands:
        return commands[name]
    elif name in aliases:
        return commands[aliases[name]]
    else:
        return None


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')


@client.event
async def on_message(message):
    if message.content.startswith(PREFIX):
        command_input = message.content.split(PREFIX)[1]
        command = get_command_by_name(command_input)
        arguments = command_input.split(' ')[1:]

        if command:
            import mpd_utils
            mpd_utils.establish_mpd_connection()  # Establish connection to MPD if we do not have one

            return_message, extras, post_action = command.run(message, arguments)
            msg = await message.channel.send(
                content=return_message['message'] if 'message' in return_message else None,
                embed=return_message['embed'] if 'embed' in return_message else None
            )

            if extras:
                for key in extras:
                    if key != 'data' and extras[key]:
                        await globals()[key](msg, extras['data'], post_action)

            # if not mpd_utils.streaming:
            #     mpd_utils.close_mpd_connection()


async def get_reactions(num, alphabet):
    for letter in alphabet[:num]:
        yield letter


async def wait_for_reactions(message, data, post_action):
    emoji_alphabet = [i for i in range(constants.UNICODE_A_VALUE, constants.UNICODE_Z_VALUE)]

    async for letter in get_reactions(len(data), emoji_alphabet):
        await message.add_reaction(chr(letter))

    valid = False
    while not valid:
        #res = await client.wait_for_reaction(message=message)
        def _cr(reaction, user):
            return reaction.message.id == message.id
        tres = await client.wait_for('reaction_add', check=_cr)
        res = tres[0]
        user = tres[1]
        print(f"got reaction: {tres}")
        if user != message.author:
            react_emoji = res.emoji
            emoji_value = ord(react_emoji)

            if emoji_value in emoji_alphabet:
                try:
                    song = data[emoji_alphabet.index(emoji_value)]
                    await message.delete()

                    import utils

                    await post_action(client, message, song)
                    # await client.send_message(message.channel, embed=utils.send_song_embed(song))

                    valid = True
                except ValueError:
                    await message.remove_reaction(react_emoji, user)
            else:
                await message.remove_reaction(react_emoji, user)


async def join_voice(message, data, post_action):
    #if client.is_voice_connected(message.server):
    print(f"checking join_voice: {message}, {data}, {post_action}")
    if message.guild in [x.guild for x in client.voice_clients]:
        await message.edit(content="Already in voice.")
        return

    global player
    global voice

    voice = await data.connect()

    import mpd_utils
    mpd_utils.streaming = True

    import utils
    player = utils.create_player(voice)
    voice.play(player)
    mpd_utils.start_playback()

    await message.edit(content=message.content.replace("Joining", "Joined").replace("...", "."))


async def toggle_playback(message, data, post_action):
    global player
    global voice

    import mpd_utils

    if client.is_voice_connected(message.server):
        current_playlist = mpd_utils.get_current_playlist()
        if current_playlist:
            is_paused = mpd_utils.is_paused()

            mpd_utils.toggle_playback(not is_paused)

            msg = "Unpaused." if is_paused else "Paused."
        else:
            msg = "You cannot do that with an empty playlist."
    else:
        msg = "Playback cannot be toggled if I am not connected."
        mpd_utils.pause_playback()  # Pause playback just to make sure.

    await message.edit(msg)


async def leave_voice(message, data, post_action):
    global voice
    if voice:
        await voice.disconnect()
        await client.delete_message(message)


@client.event
async def on_voice_state_update(member, before, after):
    event_channel = before.voice.voice_channel
    if not any(vc.channel == event_channel for vc in client.voice_clients):
        return

    if len(event_channel.voice_members) == 1:
        # Wait in case somebody rejoins
        await asyncio.sleep(10)

        # If still empty, disconnect.
        if len(event_channel.voice_members) == 1:
            await voice.disconnect()


if __name__ == '__main__':
    client.run(TOKEN)
