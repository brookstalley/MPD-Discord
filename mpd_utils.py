from mopidy_asyncio_client import MopidyClient
import logging, asyncio

mopidy:MopidyClient = None
call_message_handler:callable = None

logging.basicConfig()
logging.getLogger('mopidy_asyncio_client').setLevel(logging.DEBUG)

async def all_events_handler(event, data):
    """Callback function; catch-all function."""
    print(event, data)
    title = event
    if call_message_handler:
        await call_message_handler(title, data)

async def main_plain(host, port, message_handler:callable):
    global mopidy,call_message_handler

    call_message_handler = message_handler
    mopidy = MopidyClient(host=host, port=port, parse_results=True)
    await mopidy.connect()

    #mopidy.bind('track_playback_started', playback_started_handler)
    mopidy.bind('*', all_events_handler)

    await mopidy.playback.play()
    while True:
        await asyncio.sleep(1)

    await mopidy.disconnect()  # close connection implicit

async def get_current_song():
    return await mopidy.playback.get_current_track()    

async def next_track():
    return await mopidy.playback.next()

#####################################
### OLD STUFF BELOW
#####################################
'''
async def mopidy_connect(host, port):
    mopidy = await MopidyClient(host=host, port=port).connect()

    mopidy.bind('track_playback_started', playback_started_handler)
    mopidy.bind('*', all_events_handler)

async def all_events_handler(event, data):
    """Callback function; catch-all function."""
    print(event, data)

async def main_context_manager(host, port):

    async with MopidyClient(host='some_ip') as mopidy:

        #mopidy.bind('track_playback_started', playback_started_handler)
        mopidy.bind('*', all_events_handler)

        # Your program's logic:
        await mopidy.playback.play()
        while True:
            await asyncio.sleep(1)


async def establish_mopidy_connecion():
    mopidy = await MopidyClient().connect()
    mopidy.bind('*', all_events_handler)


def get_current_playlist():
    return mpd_connection.playlistinfo()


def toggle_playback(pause: bool):
    mpd_connection.pause(1 if pause else 0)


def start_playback():
    current_state = mpd_connection.status()['state']

    if current_state == 'pause':
        mpd_connection.pause(0)
    elif current_state == 'stop':
        if len(mpd_connection.playlist()) > 0:
            mpd_connection.play(0)


def pause_playback():
    mpd_connection.pause(1)

def is_paused():
    return mpd_connection.status()['state'] != 'play'


def generate_query(query):
    QUERY_TYPES = [
        'artist',
        'album',
        'title',
        'track',
        'name',
        'genre',
        'date',
        'composer',
        'performer',
        'comment',
        'disc',
        'filename',
        'any']

    query_dict = {}
    key = 'any'
    for word in query:
        if any(t in word for t in QUERY_TYPES):
            key = word.split(':')[0]
            print(f"word is {word}")
            word = word.split(':')[1]

        if key in query_dict:
            query_dict[key] += ' ' + word
        else:
            query_dict[key] = word

    return [item for k in query_dict for item in (k, query_dict[k])]


def perform_search(query):
    results = mopidy.search(*(entry for entry in generate_query(query)))

    SEARCH_RESULTS = 20  # TODO Include in query
    if len(results) > SEARCH_RESULTS:
        results = results[:SEARCH_RESULTS]

    return results


async def add_to_queue(client, message, song):
    mpd_connection.add(song['file'])

    import utils
    await utils.send_song_embed(client, message, song, additional='Added to queue.')
'''