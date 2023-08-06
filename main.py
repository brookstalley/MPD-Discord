import asyncio
import discord

from mpd_utils import main_plain, images_for_uris

from command import Command
import commands as bot_commands

import constants
from config import Common as config

intent = discord.Intents.default()
intent.members = True
intent.message_content = True

client = discord.Client(intents = intent)      

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    if message.content.startswith(config.COMMAND_PREFIX):
        command_input = message.content.split(config.COMMAND_PREFIX)[1]
        command = bot_commands.get_command_by_name(command_input)
        arguments = command_input.split(' ')[1:]

        if command:
            import mpd_utils

            return_message, extras, post_action = await command.run(message, arguments)

            if return_message is not None:
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

class SongSelect(discord.ui.Select):
    def __init__(self, songs, post_action, emoji_alphabet, message):
        options = []

        # for now assuming this is always song data
        for song in songs:
            song_select = discord.SelectOption(label=song.name, description=f'{song.album.name}',
                                                value=songs.index(song), emoji=chr(emoji_alphabet[songs.index(song)]))
            options.append(song_select)

        super().__init__(placeholder="Select a song to add to the queue", options=options)
        self._songs = songs
        self._post_action = post_action
        self._message = message

    async def callback(self, interaction:discord.Interaction):
        await interaction.message.delete()
        song = self._songs[int(self.values[0])]
        uri_images = await images_for_uris([song.uri])
        await self._post_action(client, interaction.message, song, uri_images)
        await self._message.delete()

class SongView(discord.ui.View):
    def __init__(self, selector, timeout = 180):
        super().__init__(timeout=timeout)
        self.add_item(selector)


async def wait_for_reactions(message:discord.message.Message, data, post_action):
    emoji_alphabet = [i for i in range(constants.UNICODE_A_VALUE, constants.UNICODE_Z_VALUE)]

    # build a dropdown select list with all of the songs
                                                                                    
    selector = SongSelect(data, post_action, emoji_alphabet, message)
    view = SongView(selector)

    await message.channel.send(view=view)
    return

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


async def send_update(message):
    print(client.status)
    channel = discord.utils.get(client.get_all_channels(), name=config.DISCORD_CHANNEL)
    if channel is None:
        print(f'Could not find channel {config.DISCORD_CHANNEL}')
        return
    if isinstance(message, discord.embeds.Embed):
        message_id = await channel.send(embed=message)
    else:
        message_id = await channel.send(content=message)    

async def main_loop():
    mopidy_host:str = config.mopidy['server']
    mopidy_port:str = config.mopidy['port']
    mopidy_password:str = config.mopidy['password']

    for command in config.commands:

        if command != 'help':
            func = getattr(bot_commands, command)
        else:
            func = bot_commands.generate_help

        bot_commands.register_command(Command(command, config.commands[command]['aliases'], config.commands[command]['description'], func = func))

    async with client:
        client.loop.create_task(main_plain(mopidy_host, mopidy_port, message_handler=send_update))
        await client.start(config.locals['discord_token'])

if __name__ == '__main__':
    asyncio.run(main_loop())