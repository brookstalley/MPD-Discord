import json

class Common(object):
    locals = json.load(open('config-local.json', 'r'))
    
    COMMAND_PREFIX = "!"
    DISCORD_CHANNEL = "music-control"

    commands = {
        "generate_help": {
            "aliases": ["help", "assist", "commands"],
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
            "aliases": ["queue", "search_add"],
            "description": "Searches the database for a song and presents list to choose."
        },
        "add_one": {
            "aliases": ["addf", "addfirst", "addone"],
            "description": "Searches the database for a song and adds top match to queue"
        },       
        "queue": {
            "aliases": ["current_playlist", "cp"],
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
        },
        "clear": {
            "aliases": ["clear_queue"],
            "description": "Clears the current queue."
        },
    }

