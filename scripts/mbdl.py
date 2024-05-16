import musicbrainzngs
# import sys
from yaml import dump
import os
import pathlib
import yaml

musicbrainzngs.set_useragent("beets-gogdplex", "0.1", "rhendry@gmail.com")

def download_tracks(mbid):
    try:
        print(f"Getting release data for {mbid}")
        # Get release information
        release_info = musicbrainzngs.get_release_by_id(mbid, 
                                                        includes=[
                                                            "recordings", 
                                                            "recording-rels", 
                                                            "recording-level-rels", 
                                                            "work-rels",
                                                            "work-level-rels",
                                                        ])
    
        playlist = {}
        playlist["title"] = release_info.get("release").get("title")
        playlist["tracks"] = []

        last_date = None
        for m in release_info.get('release').get('medium-list'):
            tracks = m.get('track-list')
            for track in tracks:
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
                    print(f"No performances for {track}")
                    if last_date is not None:
                        d = last_date

                print(f"Setting date for {recording.get('title')} to {_d}")
                playlist["tracks"].append({
                    "title": recording.get("title"),
                    "date": d,
                    "mbid": recording.get("id"),
                    "from": playlist.get("title"),
                    "from_mbid": release_info.get("release").get("id")
                })

        with open("playlist.yml", "w") as file:
            dump(playlist, file, sort_keys=False)

    except musicbrainzngs.ResponseError as e:
        print("MusicBrainz API error:", e)

if __name__ == "__main__":
    config = pathlib.Path(
        os.path.join(pathlib.Path(__file__).parent.absolute(), "releases.yml")
    )
    with open(str(config), "r") as f_config:
        c = yaml.safe_load(f_config)
     
    for r in c["releases"]:
        download_tracks(r.get("mbid"))

