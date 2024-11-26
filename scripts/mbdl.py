import musicbrainzngs
import sys
from yaml import dump
import os
import pathlib
from pprint import pprint
import yaml

musicbrainzngs.set_useragent("beets-gdplaylists", "0.1", "rhendry@gmail.com")

def _add_track_to_file(t):
    d = t["date"]
    output_dir = pathlib.Path(
        os.path.join(pathlib.Path(__file__).parent.parent.absolute(), "beetsplug", "gdplaylists", "playlists")
    )
    playlist_file = os.path.join(str(output_dir), f"{d}.yml")

    if not os.path.isfile(playlist_file):
        print(f"Writing new playlist: {d}")
        with open(playlist_file, "w") as file:
            playlist = {}
            playlist["title"] = f"GOGD - {d} - {t['release_title']}"
            playlist["tracks"] = [t]
            dump(playlist, file, sort_keys=False)

        return

    with open(playlist_file, "r") as pf:
        existing_playlist = yaml.safe_load(pf)

    assert existing_playlist is not None

    # print(f"Checking {d}.yml for {t.get('mbid')}")
    indices = [i for i, x in enumerate(existing_playlist.get("tracks")) if x["mbid"] == t["mbid"]]
    if len(indices) > 1:
        raise ValueError(f"Duplicate tracks found in {d}")
    if len(indices) == 0:
        existing_playlist["tracks"].append(t)
    else:
        existing_playlist.get("tracks")[indices[0]] = t

    with open(playlist_file, "w") as file:
        dump(existing_playlist, file, sort_keys=False)

def download_tracks(mbid, print_only):
    try:
        # Get release information
        release_info = musicbrainzngs.get_release_by_id(mbid, 
                                                        includes=[
                                                            "recordings", 
                                                            "recording-rels", 
                                                            "recording-level-rels", 
                                                            "work-rels",
                                                            "work-level-rels",
                                                            "place-rels",
                                                        ])
    
        playlist = {}
        playlist["title"] = release_info.get("release").get("title")
        playlist["tracks"] = []

        last_date = None
        for i, m in enumerate(release_info.get('release').get('medium-list')):
            tracks = m.get('track-list')
            for j, track in enumerate(tracks):
                recording = track.get('recording')
                work_relations = recording.get("work-relation-list", [])
                performances = list(filter(lambda x: x.get("type") == "performance", work_relations))
                d = "unknown"
                if len(performances) > 0:
                    _d = performances[0].get("begin")
                    if _d is not None:
                        d = _d
                        last_date = d
                else:
                    if last_date is not None:
                        d = last_date

                playlist["tracks"].append({
                    "title": recording.get("title"),
                    "date": d,
                    "mbid": recording.get("id"),
                    "release_title": playlist.get("title"),
                    "release_mbid": release_info.get("release").get("id"),
                    "release_position": f"{i+1}-{j+1}"
                })

        if print_only:
            pprint(playlist)
        else:
            for t in playlist["tracks"]:
                _add_track_to_file(t)



    except musicbrainzngs.ResponseError as e:
        print("MusicBrainz API error:", e)

if __name__ == "__main__":
    config = pathlib.Path(
        os.path.join(pathlib.Path(__file__).parent.absolute(), "releases.yml")
    )
    with open(str(config), "r") as f_config:
        c = yaml.safe_load(f_config)
        
    print_only = "--print" in sys.argv
     
    if len(sys.argv) > 1 and "--latest" in sys.argv:
        r = c["releases"][-1]
        print(f"Getting release data for {r.get('title')} ({r.get('mbid')})")
        download_tracks(r.get("mbid"), print_only)
        sys.exit(0)

    for r in c["releases"]:
        print(f"Getting release data for {r.get('title')} ({r.get('mbid')})")
        download_tracks(r.get("mbid"), print_only)

