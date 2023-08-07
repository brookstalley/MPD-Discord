from mopidy_asyncio_client import MopidyClient
import logging, asyncio
from asyncio import sleep
from utils import get_song_embed, send_song_embed

mopidy:MopidyClient = None

# the callback we use to alert users to events that happen in Mopidy
# it will be initialized after we're created, so must be checked before calling
call_message_handler:callable = None

logging.basicConfig()
logging.getLogger('mopidy_asyncio_client').setLevel(logging.DEBUG)

async def track_started_handler(data):
    track:mopidy.models.Track = data['tl_track'].track
    uri_images = await mopidy.library.get_images([track.uri])
    embed = get_song_embed(track,title_prefix='Now playing: ', uri_images=uri_images)

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

    # capture everything else just to build out the model
    mopidy.bind('*', all_events_handler)

    # Set the controls the way we want
    await mopidy.tracklist.set_consume(True)
    await mopidy.tracklist.set_random(False)
    await mopidy.tracklist.set_repeat(False)

    # Start playing? TODO: only do this if there is music in the queue. Maybe clear it first?
    await mopidy.playback.play()

    # We'll hang here and let asyncio do its thing
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
    renames = {'name': 'track_name', 'track': 'track_name'}
    QUERY_TYPES = [
        'artist',
        'album',
        'title',
        'track',
        'name',
        'track_name',
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
    # rename convenience keys
    query_dict = {renames.get(k, k): v for k, v in query_dict.items()}

    return query_dict

async def perform_search(query):
    mopidy_query = generate_query(query)
    results = await mopidy.library.search(mopidy_query,)

    SEARCH_RESULTS = 25 
    # Always the 0th result because we only submit one query at a time
    # TODO: support albums and artists
    results = results[0].tracks
    if len(results) > SEARCH_RESULTS:
        results = results[:SEARCH_RESULTS]

    return results

async def add_to_queue(client, message, song=None, uri_images = None):
    await mopidy.tracklist.add(uris=[song.uri])
    await send_song_embed(client, message, song, additional='Added to queue.', uri_images=uri_images)

async def images_for_uris(uris) -> dict:
    #support being called with a str
    # TODO: a local cache layer
    if isinstance(uris, str):
        uris = [uris]
    return await mopidy.library.get_images(uris)

async def is_paused() -> bool:
    return await mopidy.playback.get_state() != 'play'
