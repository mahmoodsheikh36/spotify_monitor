#!/usr/bin/python3
from dbus import Interface, SessionBus
from json import loads, dumps
from datetime import datetime
from time import sleep
from sys import argv

def handle_track(name: str, album: str, artist: str, is_playing: bool, prev_track):
    if not is_playing:
        return

    data_file = "track_data.json"
    if len(argv) > 1:
        data_file = argv[1]

    tracks = None
    file_exists = True
    try:
        with open(data_file) as track_data_file:
            tracks = loads(track_data_file.read())
    except FileNotFoundError:
        tracks = []
        file_exists = False

    TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    now = datetime.now()
    now_str = now.strftime(TIME_FORMAT)

    current_track = None

    found = False
    if file_exists:
        for track in tracks:
            if track["name"] == name:
                found = True
                last_listen_date = datetime.strptime(track["last_listen_date"], TIME_FORMAT)
                listen_sec_diff = (now - last_listen_date).seconds
                track["last_listen_date"] = now_str
                if listen_sec_diff < 45 and (prev_track == None or prev_track["name"] == name):
                    track["sec_listened"] += listen_sec_diff
                current_track = track
    
    if not found:
        track = {"last_listen_date": now_str,
                 "name": name,
                 "album": album,
                 "artist": artist,
                 "sec_listened": 0}
        current_track = track
        tracks.append(track)
    
    with open(data_file, "w+") as track_data_file:
        track_data_file.write(dumps(tracks, indent=2))

    return current_track

def main():
    prev_track = None
    print("starting to monitor your spotify tracks, make sure you start the spotify client before you run this program")
    while True:
        try:
            session_bus = SessionBus()

            bus_data = ("org.mpris.MediaPlayer2.spotify", "/org/mpris/MediaPlayer2")
            spotify_bus = session_bus.get_object(*bus_data)

            interface = Interface(spotify_bus, "org.freedesktop.DBus.Properties")

            metadata = interface.Get("org.mpris.MediaPlayer2.Player", "Metadata")
            status = str(interface.Get("org.mpris.MediaPlayer2.Player", "PlaybackStatus"))
            is_playing = False

            if status == "Playing":
                is_playing = True

            data = {"artist": None, "song": None, "album": None}

            artist_data = metadata.get("xesam:albumArtist")

            artist = str(next(iter(artist_data)))
            song_name = str(metadata.get("xesam:title"))
            album = str(metadata.get("xesam:album"))

            prev_track = handle_track(song_name, album, artist, is_playing, prev_track)

            sleep(1)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    main()
