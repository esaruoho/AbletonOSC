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