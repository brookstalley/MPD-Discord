from mopidy_asyncio_client import MopidyClient
import logging, asyncio
from utils import get_song_embed, send_song_embed

mopidy:MopidyClient = None
call_message_handler:callable = None

logging.basicConfig()
logging.getLogger('mopidy_asyncio_client').setLevel(logging.DEBUG)

async def track_started_handler(data):
    track:mopidy.models.Track = data['tl_track'].track
    embed = get_song_embed(track,title_prefix='Now playing: ')

    if call_message_handler:
        await call_message_handler(embed)

async def track_resumed_handler(data):
    track:mopidy.models.Track = data['tl_track'].track
    embed = get_song_embed(track,title_prefix='Resuming: ')

    if call_message_handler:
        await call_message_handler(embed)        

async def track_paused_handler(data):
    # Just eat this event
    pass  

async def track_ended_handler(data):
    # Remove the track from the playlist
    pass        

async def volume_changed_handler(data):
    # Just eat this event
    pass

async def tracklist_changed_handler(data):
    # If the tracklist changed and we're not playing, start playing
    state = await mopidy.playback.get_state()
    if state != 'playing':
        await mopidy.playback.play()
    pass 

async def playback_state_changed_handler(data):
    old_state = data['old_state']
    new_state = data['new_state']
    if old_state != new_state:
        message = f"Playback state changed: {old_state} -> {new_state}"
        await call_message_handler(message)

async def all_events_handler(event, data):
    """Callback function; catch-all function."""
    if event in ['track_playback_started', 'track_playback_paused', 'track_playback_resumed', 'track_playback_ended',
                  'volume_changed', 'playback_state_changed', 'tracklist_changed']:
        return  
    
    print(event, data)
    message = f"Event: {event} -> {data}"
    if call_message_handler:
        await call_message_handler(message)

async def main_plain(host, port, message_handler:callable):
    global mopidy,call_message_handler

    call_message_handler = message_handler
    mopidy = MopidyClient(host=host, port=port, parse_results=True)
    await mopidy.connect()

    mopidy.bind('track_playback_started', track_started_handler)
    mopidy.bind('track_playback_paused', track_paused_handler)
    mopidy.bind('track_playback_resumed', track_resumed_handler)
    mopidy.bind('track_playback_ended', track_ended_handler)
    mopidy.bind('volume_changed', volume_changed_handler)
    mopidy.bind('playback_state_changed', playback_state_changed_handler)
    mopidy.bind('tracklist_changed', tracklist_changed_handler)

    mopidy.bind('*', all_events_handler)
    await mopidy.tracklist.set_consume(True)
    await mopidy.playback.play()
    while True:
        await asyncio.sleep(1)

    await mopidy.disconnect()  # close connection implicit

async def get_current_song():
    return await mopidy.playback.get_current_track()    

async def next_track():
    return await mopidy.playback.next()

async def start_playback():
    current_state = await mopidy.playback.get_state()

    await mopidy.playback.play()
    return None, None, None

async def pause_playback():
    await mopidy.playback.pause()
    return None, None, None

async def get_queue():
    return await mopidy.tracklist.get_tracks()

async def clear_queue():
    return await mopidy.tracklist.clear()

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
    # Update each value in the dict to be enclosed in a list
    query_dict = {k: [v] for k, v in query_dict.items()}

    #return [item for k in query_dict for item in (k, query_dict[k])]
    return query_dict

async def perform_search(query):
    mopidy_query = generate_query(query)
    results = await mopidy.library.search(mopidy_query)

    SEARCH_RESULTS = 20  # TODO Include in query
    # Always the 0th result because we only submit one query at a time
    # TODO: support albums and artists
    results = results[0].tracks
    if len(results) > SEARCH_RESULTS:
        results = results[:SEARCH_RESULTS]

    return results

async def add_to_queue(client, message, song=None):
    await mopidy.tracklist.add(uris=[song.uri])

    await send_song_embed(client, message, song, additional='Added to queue.')

#####################################
### OLD STUFF BELOW
#####################################
'''
def toggle_playback(pause: bool):
    mpd_connection.pause(1 if pause else 0)

def is_paused():
    return mpd_connection.status()['state'] != 'play'


'''