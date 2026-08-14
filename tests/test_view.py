import pytest

from . import client, wait_one_tick

#--------------------------------------------------------------------------------
# Test view features
#--------------------------------------------------------------------------------

def test_selected_scene(client):
    client.send_message("/live/view/set/selected_scene", (1, ))
    rv = client.query("/live/view/get/selected_scene")
    assert rv == (1, )

def test_selected_track(client):
    client.send_message("/live/view/set/selected_track", (2, ))
    rv = client.query("/live/view/get/selected_track")
    assert rv == (2, )

def test_selected_clip(client):
    client.send_message("/live/view/set/selected_clip", (3, 4))
    rv = client.query("/live/view/get/selected_clip")
    assert rv == (3, 4)

def test_scroll_view_smoke(client):
    #--------------------------------------------------------------------------------
    # Smoke test: send each of the four NavDirection values and confirm the
    # selected-scene/track endpoints still respond afterwards. scroll_view itself
    # produces no OSC reply, so the assertion is "the OSC handler chain is alive
    # after the call" rather than "the cursor moved to the expected place".
    #--------------------------------------------------------------------------------
    client.send_message("/live/view/set/selected_scene", (0,))
    client.send_message("/live/view/set/selected_track", (0,))
    wait_one_tick()

    for direction in (0, 1, 2, 3):
        client.send_message("/live/view/scroll_view", (direction,))
        wait_one_tick()

    # Sanity check: the OSC server is still answering after the four scrolls.
    rv = client.query("/live/view/get/selected_track")
    assert isinstance(rv, tuple) and len(rv) == 1


#--------------------------------------------------------------------------------
# Test the Clip View envelope endpoints.
#
# These act on song.view.detail_clip -- whatever clip Clip View is showing -- so each
# test selects a clip first. The transposition pair require an AUDIO clip, hence the
# recorded clip on track 2 (a default audio input device must be set, as in test_clip).
#--------------------------------------------------------------------------------

MIDI_TRACK_ID, MIDI_CLIP_ID = 0, 0
AUDIO_TRACK_ID, AUDIO_CLIP_ID = 2, 0

@pytest.fixture(scope="module")
def _clips(client):
    client.send_message("/live/clip_slot/create_clip", [MIDI_TRACK_ID, MIDI_CLIP_ID, 8.0])

    client.send_message("/live/track/set/arm", [AUDIO_TRACK_ID, True])
    client.send_message("/live/clip_slot/fire", [AUDIO_TRACK_ID, AUDIO_CLIP_ID])
    wait_one_tick()
    client.send_message("/live/song/stop_playing")
    client.send_message("/live/song/stop_all_clips")
    client.send_message("/live/track/set/arm", [AUDIO_TRACK_ID, False])
    yield
    client.send_message("/live/track/delete_clip", [AUDIO_TRACK_ID, AUDIO_CLIP_ID])
    client.send_message("/live/track/delete_clip", [MIDI_TRACK_ID, MIDI_CLIP_ID])

def _show_clip(client, track_id, clip_id):
    """Puts a clip in Clip View, which is what detail_clip then reports."""
    client.send_message("/live/view/set/selected_clip", (track_id, clip_id))
    wait_one_tick()

def test_view_clip_envelope_show_hide(client, _clips):
    #--------------------------------------------------------------------------------
    # Neither endpoint replies, so — as with scroll_view — the assertion is that the
    # handler chain is still alive afterwards, i.e. neither call raised.
    #--------------------------------------------------------------------------------
    _show_clip(client, MIDI_TRACK_ID, MIDI_CLIP_ID)

    client.send_message("/live/view/show_clip_envelope")
    wait_one_tick()
    client.send_message("/live/view/hide_clip_envelope")
    wait_one_tick()

    assert client.query("/live/view/get/selected_clip") == (MIDI_TRACK_ID, MIDI_CLIP_ID)

def test_view_set_clip_transposition(client, _clips):
    _show_clip(client, AUDIO_TRACK_ID, AUDIO_CLIP_ID)

    for semitones in (12, -7, 0):
        assert client.query("/live/view/set_clip_transposition", (semitones,)) == (semitones,)
        wait_one_tick()
        #--------------------------------------------------------------------------------
        # Cross-check against the clip's own property, so this tests the write and not
        # just the reply.
        #--------------------------------------------------------------------------------
        assert client.query("/live/clip/get/pitch_coarse", (AUDIO_TRACK_ID, AUDIO_CLIP_ID)) == \
            (AUDIO_TRACK_ID, AUDIO_CLIP_ID, semitones)

def test_view_set_clip_transposition_clamps(client, _clips):
    _show_clip(client, AUDIO_TRACK_ID, AUDIO_CLIP_ID)

    assert client.query("/live/view/set_clip_transposition", (100,)) == (48,)
    wait_one_tick()
    assert client.query("/live/view/set_clip_transposition", (-100,)) == (-48,)
    wait_one_tick()
    client.send_message("/live/view/set_clip_transposition", (0,))

def test_view_nudge_clip_transposition(client, _clips):
    _show_clip(client, AUDIO_TRACK_ID, AUDIO_CLIP_ID)
    client.send_message("/live/view/set_clip_transposition", (0,))
    wait_one_tick()

    assert client.query("/live/view/nudge_clip_transposition", (12,)) == (12,)
    wait_one_tick()
    assert client.query("/live/view/nudge_clip_transposition", (12,)) == (24,)
    wait_one_tick()
    assert client.query("/live/view/nudge_clip_transposition", (-24,)) == (0,)
    wait_one_tick()

    # Nudging past the end clamps rather than wrapping.
    client.send_message("/live/view/set_clip_transposition", (48,))
    wait_one_tick()
    assert client.query("/live/view/nudge_clip_transposition", (12,)) == (48,)
    wait_one_tick()
    client.send_message("/live/view/set_clip_transposition", (0,))
