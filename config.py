import json

class Common(object):
    locals = json.load(open('config-local.json', 'r'))
    
    COMMAND_PREFIX = "!"
    DISCORD_CHANNEL = "music-control"
    mopidy = {
        "server": "santacruz.illuminati.org",
        "port": 6680,
        "password": "FRNKdiscodonFRNK",
        "timeout": 10,
        "fifo": "",
        "show_art": False,
        "show_download": False,
        "art_grabber": {
            "save_dir": "",
            "library_dir": ""
        }
    }
    download_servers = {
        "art_url": "",
        "music_url": ""
    }

    commands = {
        "help": {
            "aliases": ["assist", "commands"],
            "description": "Lists commands, their aliases, and their function."
        },
        "get_playing": {
            "aliases": ["playing", "current_song", "now_playing", "np"],
            "description": "Gets the currently playing song."
        },
        "search": {
            "aliases": ["lookup", "query"],
            "description": "Searches the database for a song."
        },
        "add": {
            "aliases": ["queue", "search_add", "add_one"],
            "description": "Searches the database for a song and adds it to the queue."
        },
        "playlist": {
            "aliases": ["current_playlist", "queue", "cp"],
            "description": "Displays the songs in the current queue."
        },
        "pause": {
            "aliases": ["play", "toggle", "p"],
            "description": "Pauses the player."
        },
        "play": {
            "aliases": ["start_playing"],
            "description": "Starts playing"
        },
        "next": {
            "aliases": ["n"],
            "description": "Skips the current track."
        }
    }

